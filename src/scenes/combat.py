import pygame as pg
from src.utils import GameSettings, crd, Logger, color
from src.sprites import Sprite, Text, BackgroundSprite
from src.scenes.scene import Scene
from src.core.services import scene_manager, sound_manager, input_manager
from src.core.gm_helper import gh
from typing import override, Optional, Union, Generator
from src.interface import overlay_combat as oc
from src.data import pokedex, pokeitems
import random

from src.utils.combat import CombatLogic, CombatAI
from src.utils.combat import CombatType as ct
from src.utils.combat.combat_online import OnlineCombatHandler


class CombatScene(Scene):
    """Unified combat framework"""

    combat_type: ct
    catching_enabled: bool
    background: BackgroundSprite
    m1: dict
    m2: dict
    ci1: int
    ci2: int

    # UI
    bg2: Sprite
    bg3: Sprite
    bg: Sprite
    victory: Optional[oc.Victory]  # type: ignore
    noti: Text

    # Logic
    logic: Optional[CombatLogic]
    ai: Optional[CombatAI]
    handler: Optional[OnlineCombatHandler]

    # State
    player_action: dict | None
    turn_queue: list
    executing_turn: bool
    turn_timer: float
    current_action_idx: int

    # Flags
    pfainted: bool
    efainted: bool
    catching: bool
    done: bool
    win: bool
    lose: bool
    swapping: bool
    waiting_for_action: bool
    player_turn: bool

    # Misc
    exit_cd: float
    noti_cd: float
    ntcon: bool
    move: int | None
    run_iter: Optional[Generator]

    def __init__(self, combat_type: Union[ct, str] = ct.WILD) -> None:
        super().__init__()
        if isinstance(combat_type, str):
            try:
                combat_type = ct(combat_type)
            except ValueError:
                combat_type = ct.WILD

        self.combat_type = combat_type
        self.catching_enabled = self.combat_type == ct.WILD

        self.logic = None
        self.ai = None
        self.handler = None

        self.exit_cd = 0.0
        self.pfainted = False
        self.efainted = False
        self.catching = False
        self.done = False
        self.win = False
        self.lose = False
        self.swapping = False
        self.waiting_for_action = False
        self.player_turn = False
        self.executing_turn = False
        self.turn_queue = []
        self.player_action = None
        self.current_action_idx = 0
        self.turn_timer = 0.0

        self.background = BackgroundSprite("backgrounds/background2.png")
        self.noti_cd = 0.6
        self.ntcon = False
        self.run_iter = None
        self.move = None

        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)
        self.bg2 = Sprite(
            "UI/raw/UI_Flat_Frame01a.png",
            (sw, sh.per(20)),
            nine_grid_margins=(45, 45, 45, 45),
        )
        self.bg2.image = color.recol(self.bg2.image, (120, 120, 120))
        self.bg3 = Sprite(
            "UI/raw/UI_Flat_Frame01a.png",
            (sw.per(55), sh.per(15)),
            nine_grid_margins=(45, 45, 45, 45),
        )
        self.bg3.image = color.recol(self.bg3.image, (120, 120, 120))
        self.bg = Sprite(
            "UI/raw/UI_Flat_Frame03a.png",
            (sw.per(40), sh.per(15)),
            nine_grid_margins=(45, 45, 45, 45),
        )
        self.bg2.rect.bottomleft = (0, sh)
        self.bg3.rect.bottomleft = (sh.per(3), sh - sh.per(3))
        self.bg.image = color.recol(self.bg.image, (120, 120, 120))
        self.bg.rect.bottomright = sw - sh.per(3), sh - sh.per(3)
        self.victory = None

        self._init_overlays()
        self.noti = Text("", 32, "Black")

        # Effectiveness display
        self.effectiveness_text = Text("", 48, "White")
        self.effectiveness_timer = 0
        self.effectiveness_y_offset = 0

    def _init_overlays(self):
        self.item_overlay = oc.ItemOverlay()
        self.action_overlay = oc.ActionOverlay()
        self.health_overlay = oc.HealthOverlay()
        self.switch_UI = oc.SwitchOverlay()
        self.move_overlay = oc.MoveOverlay()

    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 101 Opening (Part 1).ogg")
        self.clear()
        self.load_data()
        self.action_overlay.open()

    @override
    def exit(self) -> None:
        self.save()
        self.clear()

    def clear(self):
        self.m1 = {}
        self.m2 = {}
        self.turn_queue = []
        self.player_action = None
        self.executing_turn = False
        self.victory = None

        # Reset all battle state flags
        self.exit_cd = 0.0
        self.pfainted = False
        self.efainted = False
        self.catching = False
        self.done = False
        self.win = False
        self.lose = False
        self.swapping = False
        self.waiting_for_action = False
        self.player_turn = False
        self.current_action_idx = 0
        self.turn_timer = 0.0
        self.catching_active = False
        self.catching_enemy_alpha = 255  # Full opacity by default

    def load_data(self):
        """Child classes must implement this to load specific data"""
        raise NotImplementedError("Subclasses must implement load_data")

    def common_ui_init(self):
        """Common UI initialization for all combat scenes"""
        sh = crd(GameSettings.SCREEN_HEIGHT)
        self.noti = Text(f"What will {self.m1['name']} do?", 32, "Black")
        self.noti.rect.topleft = (
            self.bg3.rect.left + sh.per(3),
            self.bg3.rect.top + sh.per(2),
        )

        self.waiting_for_action = True
        self.player_turn = True
        self.executing_turn = False
        self.turn_timer = 0.0

    def init_logic(self):
        self.logic = CombatLogic(self.m1, self.m2)
        if self.combat_type != ct.PVP:
            self.ai = CombatAI(self.logic, self.combat_type.value)
        elif (
            gh.gm.current_fight
            and hasattr(gh.gm.current_fight, "opponent_id")
            and gh.gm.current_fight.opponent_id
        ):
            self.init_handler(gh.gm.current_fight.opponent_id)

    def init_handler(self, opponent_id: int):
        self.logic = CombatLogic(self.m1, self.m2)  # Re-init logic just in case
        self.handler = OnlineCombatHandler(self.logic, opponent_id)
        Logger.info(f"Initialized PVP Handler with opponent {opponent_id}")

    def _img(self):
        "Load Pokemon Sprites"
        try:
            wid, hid = crd(GameSettings.SCREEN_WIDTH), crd(GameSettings.SCREEN_HEIGHT)
            self.m1_sprite = Sprite(
                pokedex.data[self.m1["id"]]["fight_path"], (wid, hid)
            )
            w, h = self.m1_sprite.image.get_size()
            new = w // 2
            frame = self.m1_sprite.image.subsurface(pg.Rect(new, 0, new, h))
            self.m1_sprite.image = frame
            self.m1_sprite.rect.bottom = hid - hid.per(20)

            self.m2_sprite = Sprite(
                pokedex.data[self.m2["id"]]["fight_path"], (wid // 2, hid // 2)
            )
            w, h = self.m2_sprite.image.get_size()
            new = w // 2
            frame = self.m2_sprite.image.subsurface(pg.Rect(0, 0, new, h))
            self.m2_sprite.image = frame
            self.m2_sprite.rect.centerx = wid
        except Exception as e:
            Logger.error(f"Error loading sprites: {e}")

    def move_refresh(self):
        self.move_overlay = oc.MoveOverlay()
        if self.m1:
            self.move_overlay.inmove(self.m1.get("move", []))

    def save(self):
        if hasattr(self, "m1") and self.m1 and self.m1.get("id"):
            # Only save if we have valid monster data and ci1 is in bounds
            if hasattr(self, "ci1") and 0 <= self.ci1 < len(gh.gm.bag.monsters):
                gh.gm.bag.monsters[self.ci1] = self.m1
        gh.gm.bag.save_battle()
        gh.gm.bag.update_bag()

    def notichange(self, text: (str | list[str])):
        def _cooldown(text: list[str]):
            for t in text:
                yield t

        if isinstance(text, str):
            self.noti.change_text(text)
        else:
            self.run_iter = _cooldown(text)
            self.ntcon = True

    def text_update(self, dt):
        self.noti_cd -= dt
        if self.ntcon:
            if self.noti_cd <= 0:
                self.noti_cd = 1.0  # 1 second delay
                try:
                    if self.run_iter:
                        self.notichange(next(self.run_iter))
                except StopIteration:
                    self.ntcon = False
                    self.run_iter = None

    def show_effectiveness(self, effectiveness: float, hit: bool):
        """Display effectiveness multiplier with animation."""
        if not hit:
            text = "MISS!"
            text_color = "Gray"
        elif effectiveness == 0:
            text = "No Effect!"
            text_color = "Gray"
        elif effectiveness >= 4:
            text = "4x!"
            text_color = "Gold"
        elif effectiveness >= 2:
            text = "Super Effective!"
            text_color = "LightGreen"
        elif effectiveness > 1:
            text = f"{effectiveness}x"
            text_color = "LightGreen"
        elif effectiveness < 0.5:
            text = "Resist!"
            text_color = "LightCoral"
        elif effectiveness < 1:
            text = "Not Very Effective"
            text_color = "LightCoral"
        else:
            # Normal effectiveness (1x), don't show
            return

        self.effectiveness_text.change_text(text, color=text_color)
        self.effectiveness_timer = 2.0  # Display for 2 seconds
        self.effectiveness_y_offset = 0  # Reset position

    def switch_mon(self, idx: int):
        self.save()
        for i, mon in enumerate(gh.gm.bag.monsters):
            if mon["idx"] == idx:
                self.ci1 = i
                self.m1 = mon
                break

        # Update Logic with new monster
        if self.logic:
            self.logic.pc1 = self.m1

        self.health_overlay.load()
        self.move_refresh()
        self._img()
        self.notichange(f"You sent out {self.m1['name']}!")

    def switch_enemy(self, n: int):
        self.ci2 = n
        self.m2 = gh.gm.current_fight.monsters[n]
        if self.logic:
            self.logic.pc2 = self.m2

        self.health_overlay.load()
        self._img()
        self.notichange(f"Enemy sent out {self.m2['name']}!")

    def resolve_turn(self):
        actions = []
        # Player Action
        if self.player_action:
            p_act = self.player_action
            if p_act["type"] == "move":
                actions.append(
                    (
                        self.m1["spe"],
                        self.m1,
                        self.m2,
                        p_act["value"],
                        True,
                        p_act.get("seed", 0),
                    )
                )
            else:
                # High/Infinite speed for non-move actions
                actions.append(
                    (999, self.m1, self.m2, p_act, True, p_act.get("seed", 0))
                )

        # Enemy Action
        if self.combat_type == ct.PVP and self.handler:
            self.handler.send_action(self.player_action, self.player_action.get("seed"))
            # PvP resolution is handled asynchronously when opponent action arrives
            return  # Don't build queue yet

        elif self.ai:
            e_act = self.ai.get_enemy_action(self.m2)
            if e_act["type"] == "move":
                actions.append(
                    (self.m2["spe"], self.m2, self.m1, e_act["value"], False, 0)
                )
            else:
                actions.append((999, self.m2, self.m1, e_act, False, 0))

        actions.sort(key=lambda x: x[0], reverse=True)
        self.turn_queue = actions
        self.executing_turn = True
        self.turn_timer = 0.0
        self.current_action_idx = 0

    def execute_next_action(self):
        if self.current_action_idx >= len(self.turn_queue):
            self.executing_turn = False
            self.player_action = None
            self.waiting_for_action = True
            self.player_turn = True

            # Refresh move overlay to show updated PP
            self.move_refresh()

            # PVP cleanup
            if self.combat_type == ct.PVP and self.handler:
                self.handler.reset_turn()
            return

        speed, attacker, defender, action, is_player, _ = self.turn_queue[
            self.current_action_idx
        ]
        self.current_action_idx += 1

        if attacker["chp"] <= 0:
            return

        is_non_move_action = (
            isinstance(action, dict)
            and "type" in action
            and action["type"] in ["switch", "item", "catch", "run"]
        )

        if is_non_move_action:
            if action["type"] == "switch":
                if is_player:
                    self.switch_mon(action["value"])
                else:
                    self.switch_enemy(action["value"])
            elif action["type"] == "item":
                if is_player:
                    self.handle_item(action["value"])
            elif action["type"] == "catch":
                self.do_catching(action["value"])
            elif action["type"] == "run":
                self.run_attempt()
        else:
            # Attacking
            self.notichange([f"{attacker['name']} used {action['name']}!", ""])

            # Decrement PP for the used move
            move_name = action.get("name", "")
            for move in attacker.get("move", []):
                if move.get("name") == move_name:
                    if "cpp" in move:
                        move["cpp"] = max(0, move["cpp"] - 1)
                    break

            # Set seed if available
            if isinstance(action, dict) and "seed" in action:
                if self.logic:
                    self.logic.set_seed(action["seed"])
            elif self.player_action and "seed" in self.player_action and is_player:
                # Fallback for player action if seed not in action dict directly
                if self.logic:
                    self.logic.set_seed(self.player_action["seed"])

            # Logic attack - now returns (damage, effectiveness, hit)
            if self.logic:
                dmg, effectiveness, hit = self.logic.attack(attacker, defender, action)
            else:
                dmg, effectiveness, hit = 0, 1.0, False

            defender["chp"] = max(0, defender["chp"] - dmg)
            self.health_overlay.health_update()

            # Animation: Shake and Flash
            if dmg > 0:
                target_sprite = None
                if is_player:
                    # Player attacked Enemy -> Enemy takes damage
                    target_sprite = self.m2_sprite
                else:
                    # Enemy attacked Player -> Player takes damage
                    target_sprite = self.m1_sprite

                if target_sprite:
                    target_sprite.shake(intensity=5, duration=0.4)
                    target_sprite.flash(color=(255, 0, 0), duration=0.4)

            # Display effectiveness message
            self.show_effectiveness(effectiveness, hit)

            if defender["chp"] <= 0:
                if is_player:
                    self.enemy_fainted()
                else:
                    self.fainted()

        self.save()

    def handle_item(self, item):
        if not self.logic:
            return
        if "healing" in item:
            success, msg = self.logic.use_potion(self.m1, item)
            self.notichange(msg)
            if success:
                self.health_overlay.health_update()
        elif "stat_boost" in item:
            success, msg = self.logic.use_stat_boost(self.m1, item, True)
            self.notichange(msg)

    def do_catching(self, item=None):
        if not self.catching_enabled:
            self.notichange("Can't catch here!")
            return

        catch_rate = 1.0
        ball_sprite_name = "poke"  # default
        if item:
            # Look up catch rate from static data
            static_data = pokeitems.items.get(item["name"], {})
            catch_rate = static_data.get("catch_rate", 1.0)
            # Get ball sprite (e.g. "Poke Ball" -> "poke")
            ball_name = item["name"].lower().replace(" ball", "").replace(" ", "")
            ball_sprite_name = ball_name if ball_name else "poke"

        base_chance = 50.0
        max_hp = self.m2["hp"]
        cur_hp = self.m2["chp"]
        hp_factor = (1.0 - (cur_hp / max_hp)) * 50.0 if max_hp > 0 else 50.0
        final_chance = (base_chance + hp_factor) * catch_rate

        Logger.info(
            f"Catching {self.m2['name']} with {item['name']}. Chance: {final_chance}%"
        )

        # Determine success/failure
        success = random.uniform(0, 100) < final_chance

        # Start catching animation
        self.start_catching_animation(ball_sprite_name, success)

    def start_catching_animation(self, ball_sprite: str, success: bool):
        """Start the pokeball catching animation."""
        self.catching_active = True
        self.catching_success = success
        self.catching_phase = "throw"  # throw, shake, result
        self.catching_timer = 0.0
        self.catching_shakes = 0
        self.catching_max_shakes = random.randint(1, 3) if not success else 3

        # Create pokeball sprite
        try:
            self.pokeball_sprite = Sprite(f"ball/{ball_sprite}.png", (48, 48))
        except Exception:
            self.pokeball_sprite = Sprite("ball/poke.png", (48, 48))

        # Start position (bottom left, player side)
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)
        self.pokeball_start = (sw.per(20), sh.per(70))
        self.pokeball_end = (self.m2_sprite.rect.centerx, self.m2_sprite.rect.centery)
        self.pokeball_sprite.rect.center = self.pokeball_start

        self.notichange("...")

    def update_catching_animation(self, dt: float):
        """Update the catching animation state machine."""
        if not getattr(self, "catching_active", False):
            return False

        self.catching_timer += dt

        if self.catching_phase == "throw":
            # Arc throw animation (0.5 seconds)
            t = min(self.catching_timer / 0.5, 1.0)
            # Lerp position with arc
            x = (
                self.pokeball_start[0]
                + (self.pokeball_end[0] - self.pokeball_start[0]) * t
            )
            y = (
                self.pokeball_start[1]
                + (self.pokeball_end[1] - self.pokeball_start[1]) * t
            )
            # Add arc (parabola)
            arc_height = -150 * (4 * t * (1 - t))  # Peak at t=0.5
            y += arc_height
            self.pokeball_sprite.rect.center = (int(x), int(y))

            if t >= 1.0:
                self.catching_phase = "shake"
                self.catching_timer = 0.0
                self.catching_enemy_alpha = 100  # Store alpha for faded enemy

        elif self.catching_phase == "shake":
            # Shake animation (0.5 seconds per shake)
            shake_duration = 0.5
            if self.catching_timer >= shake_duration:
                self.catching_shakes += 1
                self.catching_timer = 0.0

                # Shake movement
                if self.catching_shakes < self.catching_max_shakes:
                    self.notichange("...")
                else:
                    self.catching_phase = "result"
                    self.catching_timer = 0.0
            else:
                # Wobble effect
                wobble = int(
                    5 * pg.math.Vector2(1, 0).rotate(self.catching_timer * 720).x
                )
                self.pokeball_sprite.rect.centerx = self.pokeball_end[0] + wobble

        elif self.catching_phase == "result":
            if self.catching_timer >= 0.3:
                self.catching_enemy_alpha = 255  # Restore enemy visibility
                self.catching_active = False

                if self.catching_success:
                    self.notichange(["Caught successfully!"])
                    gh.gm.bag.add_captured(self.m2)
                    self.done = True
                else:
                    self.notichange(["Failed to catch!"])
                return False

        return True  # Animation still running

    def run_attempt(self):
        if random.randint(0, 100) < 95:
            scene_manager.change_scene("game")
        else:
            self.notichange("Failed to run away.")

    def enemy_fainted(self):
        self.notichange(f"{self.m2['name']} fainted!")

        # Calculate EXP
        start_exp = self.m1["exp"]
        start_level = self.m1["level"]
        exp_gain = 0
        leveled_up = False

        if self.logic:
            exp_gain, leveled_up = self.logic.add_exp(
                self.m2, self.m1, self.combat_type == ct.TRAINER
            )
            self.logic.add_yield(self.m2, self.m1)

        self.efainted = True
        self.next_enemy = None

        enemy_monsters = gh.gm.current_fight.monsters
        for i, mon in enumerate(enemy_monsters):
            if mon["chp"] > 0:
                self.next_enemy = i
                break

        if self.next_enemy is None:
            self.win = True

            # Update Player Level Logic
            gh.gm.fight_count += 1
            if gh.gm.fight_count % 2 == 0:
                gh.gm.player_level += 1
                self.notichange(f"Player Level grew to {gh.gm.player_level}!")

            # Pass EXP data to Victory overlay
            exp_data = {
                "mon": self.m1,
                "start_exp": start_exp,
                "start_level": start_level,
                "end_exp": self.m1["exp"],
                "end_level": self.m1["level"],
                "gain": exp_gain,
            }

            self.victory = oc.Victory(1, exp_data=exp_data)

    def fainted(self):
        self.pfainted = True
        self.switch_UI.forced = True
        self.switch_UI.init(forced=True)
        self.switch_UI.open()

    def try_switching(self):
        if self.combat_type == ct.PVP:
            return

        if not self.health_overlay.animating and self.efainted:
            if self.next_enemy is not None:
                self.switch_enemy(self.next_enemy)
                self.player_turn = True
                self.waiting_for_action = True
                self.efainted = False

    def try_team(self):
        if self.pfainted and not self.health_overlay.animating:
            # Check if we have any health pokemon left
            alive = any(m["chp"] > 0 for m in gh.gm.bag.monsters)
            if not alive:
                self.lose = True
                self.victory = oc.Victory(0)
            elif self.switch_UI.next is not None:
                if self.logic:
                    # Reset active monster in logic if needed?
                    # self.switch_mon handles it.
                    pass
                self.switch_mon(self.switch_UI.next)

                if self.combat_type == ct.PVP and self.handler:
                    self.handler.send_action(
                        {
                            "type": "switch",
                            "value": self.switch_UI.next,
                            "seed": random.randint(0, 1000000),
                        }
                    )

                self.pfainted = False
                self.switch_UI.close()
                self.switch_UI.next = None
                self.waiting_for_action = True
                self.player_turn = True

    def wait_exit(self, dt):
        self.exit_cd += dt
        self.action_overlay.close()
        self.move_overlay.close()
        self.item_overlay.close()
        if self.exit_cd >= 3:
            if self.combat_type == ct.PVP and self.handler:
                self.handler.send_battle_end(self.win)
            gh.gm.current_fight = None
            scene_manager.change_scene("game")

    @override
    def update(self, dt: float) -> None:
        self.save()
        self.text_update(dt)
        self.health_overlay.update(dt)

        # Update effectiveness display animation
        if self.effectiveness_timer > 0:
            self.effectiveness_timer -= dt
            self.effectiveness_y_offset += dt * 20  # Slow upward float

        if hasattr(self, "m1_sprite"):
            self.m1_sprite.update(dt)
        if hasattr(self, "m2_sprite"):
            self.m2_sprite.update(dt)

        if self.win or self.lose or self.done:
            # Update victory overlay animation
            if self.victory:
                self.victory.update(dt)
                if getattr(self.victory, "animating", False):
                    return  # Wait for animation to finish

            if not self.health_overlay.animating:
                self.wait_exit(dt)
            return

        # Update catching animation
        if self.update_catching_animation(dt):
            return  # Block other input while catching

        # Check faint states
        self.try_switching()
        self.try_team()

        if self.pfainted or self.efainted:
            if self.pfainted:
                self.switch_UI.update(dt)
                if self.switch_UI.selected:
                    self.switch_UI.selected = False
            return

        # Poll for Online Events
        if self.combat_type == ct.PVP and self.handler and gh.online_manager:
            # We need to keep connection alive and fetch events
            # Use current player position if possible, or dummy values
            if gh.gm and gh.gm.player:
                p = gh.gm.player
                # Keep sending position updates to maintain presence/visuals
                gh.online_manager.update(
                    p.position.x,
                    p.position.y,
                    gh.gm.current_map.path_name,
                    p.direction.name.lower(),
                    p.skin_idx if hasattr(p, "skin_idx") else 0,
                    False,
                )

        # Turn Execution
        if self.executing_turn:
            self.action_overlay.close()
            if not self.ntcon and not self.health_overlay.animating:
                self.turn_timer += dt
                if self.turn_timer > 1.0:
                    self.execute_next_action()
                    self.turn_timer = 0.0
            return

        # PvP: Handle opponent switch if they are fainted
        if self.combat_type == ct.PVP and self.efainted and self.handler:
            if self.handler.opponent_action_received:
                action = self.handler.get_opponent_action()
                if action and action.get("type") == "switch":
                    self.switch_enemy(action["value"])
                    self.efainted = False
                    self.handler.reset_turn()
            return

        # Player Input / Waiting
        if self.player_turn and not self.health_overlay.animating:
            # PVP specific
            if self.combat_type == ct.PVP and self.handler:
                # Check/Poll
                if self.player_action and (
                    self.handler.waiting_for_opponent
                    or self.handler.opponent_action_received
                ):
                    if self.handler.is_ready_to_resolve():
                        op_action = self.handler.get_opponent_action()
                        # Build queue
                        # Build queue
                        actions = []
                        if self.player_action:
                            p_val = self.player_action["value"]
                            # Inject seed into value if it's a dict (move)
                            if isinstance(p_val, dict):
                                p_val = p_val.copy()
                                if "seed" in self.player_action:
                                    p_val["seed"] = self.player_action["seed"]

                            if self.player_action["type"] == "move":
                                actions.append(
                                    (
                                        self.m1["spe"],
                                        self.m1,
                                        self.m2,
                                        p_val,
                                        True,
                                        self.player_action.get("seed", 0),
                                    )
                                )
                            else:
                                actions.append(
                                    (
                                        999,
                                        self.m1,
                                        self.m2,
                                        self.player_action,
                                        True,
                                        self.player_action.get("seed", 0),
                                    )
                                )

                        if op_action:
                            op_val = op_action.get("value")
                            # Inject seed into value if it's a dict (move)
                            if isinstance(op_val, dict):
                                op_val = op_val.copy()
                                if "seed" in op_action:
                                    op_val["seed"] = op_action["seed"]

                            if op_action["type"] == "move":
                                actions.append(
                                    (
                                        self.m2["spe"],
                                        self.m2,
                                        self.m1,
                                        op_val,
                                        False,
                                        op_action.get("seed", 0),
                                    )
                                )
                            # Handle other opponent actions if supported (switch etc)

                        # Sort by Speed (descending), then Seed (descending) for deterministic tie-break
                        actions.sort(key=lambda x: (x[0], x[5]), reverse=True)
                        self.turn_queue = actions
                        self.executing_turn = True
                        self.current_action_idx = 0
                        self.turn_timer = 0.0
                    else:
                        self.notichange("Waiting for opponent...")
                    return

            if self.waiting_for_action:
                self.handle_input_overlays(dt)

    def handle_input_overlays(self, dt):
        if self.action_overlay.is_move:
            self.action_overlay.close()
            self.move_overlay.open()
            self.move_overlay.update(dt)
            if self.move_overlay.selected:
                if self.move is not None:
                    self.player_action = {
                        "type": "move",
                        "value": self.m1["move"][self.move],
                        "seed": random.randint(0, 1000000),  # Generate random seed
                    }
                    self.waiting_for_action = False
                    self.move_overlay.selected = False
                    self.move_overlay.close()
                    self.action_overlay.is_move = False
                    self.resolve_turn()
        elif self.action_overlay.is_switch:
            self.action_overlay.close()
            self.switch_UI.open()
            self.switch_UI.update(dt)
            if self.switch_UI.selected:
                self.player_action = {
                    "type": "switch",
                    "value": self.switch_UI.next,
                    "seed": random.randint(0, 1000000),
                }
                self.waiting_for_action = False
                self.switch_UI.selected = False
                self.switch_UI.close()
                self.action_overlay.is_switch = False
                self.resolve_turn()
        elif self.action_overlay.is_item:
            self.action_overlay.close()
            self.item_overlay.open()
            self.item_overlay.update(dt)
            if self.item_overlay.selected:
                item = self.item_overlay.selected_item
                action_type = "item"
                # Check if it's a ball
                if "ball" in item["name"].lower():
                    action_type = "catch"

                self.player_action = {
                    "type": action_type,
                    "value": item,
                    "seed": random.randint(0, 1000000),
                }
                self.waiting_for_action = False
                self.item_overlay.selected = False
                self.item_overlay.close()
                self.action_overlay.is_item = False
                self.resolve_turn()
        elif self.action_overlay.is_run:
            self.player_action = {
                "type": "run",
                "value": None,
                "seed": random.randint(0, 1000000),
            }
            self.waiting_for_action = False
            self.action_overlay.is_run = False
            self.resolve_turn()
        else:
            self.action_overlay.open()
            self.action_overlay.update(dt)

    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)
        self.bg2.draw(screen)
        self.bg3.draw(screen)
        self.bg.draw(screen)

        if hasattr(self, "m1_sprite"):
            self.m1_sprite.draw(screen)
        if hasattr(self, "m2_sprite"):
            # Handle alpha during catching animation using SRCALPHA
            alpha = getattr(self, "catching_enemy_alpha", 255)
            if alpha < 255:
                # Create alpha-blended copy of enemy sprite
                sprite_img = self.m2_sprite.image.copy()
                alpha_surface = pg.Surface(sprite_img.get_size(), pg.SRCALPHA)
                alpha_surface.fill((255, 255, 255, alpha))
                sprite_img.blit(alpha_surface, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
                screen.blit(sprite_img, self.m2_sprite.rect)
            else:
                self.m2_sprite.draw(screen)

        # Draw pokeball during catching animation
        if getattr(self, "catching_active", False) and hasattr(self, "pokeball_sprite"):
            self.pokeball_sprite.draw(screen)

        self.action_overlay.draw(screen)
        self.health_overlay.draw(screen)
        self.noti.draw(screen)

        # Draw effectiveness text with animation
        if self.effectiveness_timer > 0:
            # Fade out effect using SRCALPHA
            alpha = min(255, int((self.effectiveness_timer / 2.0) * 255))

            # Position center-screen, slightly above center with upward float
            sw = crd(GameSettings.SCREEN_WIDTH)
            sh = crd(GameSettings.SCREEN_HEIGHT)
            self.effectiveness_text.rect.center = (
                sw // 2,
                sh // 2 - 100 - int(self.effectiveness_y_offset),
            )

            # Create alpha surface and blit text onto it
            text_surface = self.effectiveness_text.text.copy()
            alpha_surface = pg.Surface(text_surface.get_size(), pg.SRCALPHA)
            alpha_surface.fill((255, 255, 255, alpha))
            text_surface.blit(alpha_surface, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
            screen.blit(text_surface, self.effectiveness_text.rect)

        self.move_overlay.draw(screen)
        self.item_overlay.draw(screen)
        self.switch_UI.draw(screen)

        if self.victory:
            self.victory.draw(screen)
