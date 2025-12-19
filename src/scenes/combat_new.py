import pygame as pg
from src.utils import GameSettings, crd, Logger, color
from src.sprites import Sprite, Text, BackgroundSprite
from src.scenes.scene import Scene
from src.core.services import scene_manager, sound_manager, input_manager
from typing import override, Optional, Union, Generator
from src.interface import overlay_combat as oc
from src.core import gh
from src.data import pokedex
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

    def load_data(self):
        if not gh.gm:
            gh.load()
        if not gh.gm.current_fight:
            # If no fight data, exit
            scene_manager.change_scene("game")
            return

        # Setup monsters
        self.ci1 = 0
        # Find first non-fainted monster
        for i, mon in enumerate(gh.gm.bag.monsters):
            if mon["chp"] > 0:
                self.ci1 = i
                break

        self.ci2 = 0
        # Deep copy to prevent reference aliasing
        self.m1 = gh.gm.bag.monsters[self.ci1]
        self.m2 = gh.gm.current_fight.monsters[self.ci2]

        self.init_logic()
        self._img()

        self.health_overlay.load()
        self.switch_UI.init()
        self.item_overlay.init()
        self.move_refresh()
        self.move_overlay.inmove(self.m1["move"])

        # Notification
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
        if hasattr(self, "m1") and self.m1:
            gh.gm.bag.monsters[self.ci1] = self.m1
        gh.gm.bag.save_battle(gh.gm.bag.monsters)
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
                    (0, self.m1["spe"], self.m1, self.m2, p_act["value"], True)
                )
            else:
                # High/Infinite speed for non-move actions
                actions.append((1, 999, self.m1, self.m2, p_act, True))

        # Enemy Action
        if self.combat_type == ct.PVP and self.handler:
            self.handler.send_action(self.player_action)
            # PvP resolution is handled asynchronously when opponent action arrives
            return  # Don't build queue yet

        elif self.ai:
            e_act = self.ai.get_enemy_action(self.m2)
            if e_act["type"] == "move":
                actions.append(
                    (0, self.m2["spe"], self.m2, self.m1, e_act["value"], False)
                )
            else:
                actions.append((1, 999, self.m2, self.m1, e_act, False))

        actions.sort(key=lambda x: (x[0], x[1]), reverse=True)
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

            # PVP cleanup
            if self.combat_type == ct.PVP and self.handler:
                self.handler.reset_turn()
            return

        priority, speed, attacker, defender, action, is_player = self.turn_queue[
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
                self.do_catching()
            elif action["type"] == "run":
                self.run_attempt()
        else:
            # Attacking
            self.notichange([f"{attacker['name']} used {action['name']}!", ""])
            # Logic attack
            dmg = self.logic.attack(attacker, defender, action) if self.logic else 0
            defender["chp"] = max(0, defender["chp"] - dmg)
            self.health_overlay.health_update()

            # Check effectiveness (simplification as logic doesn't return it yet)
            # eff = self.logic.eff_mes(...)

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

    def do_catching(self):
        if not self.catching_enabled:
            self.notichange("Can't catch here!")
            return

        chance = 85
        if random.randint(0, 100) < chance:
            self.notichange(["Catching...", "Caught successfully!"])
            gh.gm.bag.add_captured(self.m2)
            self.done = True
        else:
            self.notichange(["Catching...", "Failed to catch!"])

    def run_attempt(self):
        if random.randint(0, 100) < 95:
            scene_manager.change_scene("game")
        else:
            self.notichange("Failed to run away.")

    def enemy_fainted(self):
        self.notichange(f"{self.m2['name']} fainted!")
        if self.logic:
            self.logic.add_exp(self.m2, self.m1, self.combat_type == ct.TRAINER)
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
            self.victory = oc.Victory(1)

    def fainted(self):
        self.pfainted = True
        self.switch_UI.forced = True
        self.switch_UI.init(forced=True)
        self.switch_UI.open()

    def try_switching(self):
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
            scene_manager.change_scene("game")

    @override
    def update(self, dt: float) -> None:
        self.save()
        self.text_update(dt)
        self.health_overlay.update(dt)

        if self.win or self.lose or self.done:
            if not self.health_overlay.animating:
                self.wait_exit(dt)
            return

        # Check faint states
        self.try_switching()
        self.try_team()

        if self.pfainted or self.efainted:
            if self.pfainted:
                self.switch_UI.update(dt)
                if self.switch_UI.selected:
                    self.switch_UI.selected = False
            return

        # Turn Execution
        if self.executing_turn:
            self.action_overlay.close()
            if not self.ntcon and not self.health_overlay.animating:
                self.turn_timer += dt
                if self.turn_timer > 1.0:
                    self.execute_next_action()
                    self.turn_timer = 0.0
            return

        # Player Input / Waiting
        if self.player_turn and not self.health_overlay.animating:
            # PVP specific
            if self.combat_type == ct.PVP and self.handler:
                # Check/Poll
                if self.handler.waiting_for_opponent:
                    if self.handler.is_ready_to_resolve():
                        op_action = self.handler.get_opponent_action()
                        # Build queue
                        # We need to construct queue here since we skipped it in resolve_turn
                        actions = []
                        if self.player_action:
                            if self.player_action["type"] == "move":
                                actions.append(
                                    (
                                        0,
                                        self.m1["spe"],
                                        self.m1,
                                        self.m2,
                                        self.player_action["value"],
                                        True,
                                    )
                                )
                            else:
                                actions.append(
                                    (1, 999, self.m1, self.m2, self.player_action, True)
                                )

                        if op_action:
                            if op_action["type"] == "move":
                                # Note: op_action["value"] might be dict.
                                # We trust handler/online sync passes correct struct.
                                actions.append(
                                    (
                                        0,
                                        self.m2["spe"],
                                        self.m2,
                                        self.m1,
                                        op_action["value"],
                                        False,
                                    )
                                )
                            # Handle other opponent actions if supported (switch etc)

                        actions.sort(key=lambda x: (x[0], x[1]), reverse=True)
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
                move_idx = self.move
                # Move index comes from overlay? overlay usually sets scene attribute?
                # Looking at combat.py: self.move is set.
                # Let's ensure MoveOverlay sets self.move on the scene or we read it from overlay.
                # self.move_overlay.selected_move_index?
                # Assuming self.move is updated by overlay interaction (e.g. key press).
                # Wait, combat.py uses `self.move` which is an int.
                if self.move is not None:
                    self.player_action = {
                        "type": "move",
                        "value": self.m1["move"][self.move],
                    }
                    self.waiting_for_action = False
                    self.move_overlay.selected = False
                    self.action_overlay.is_move = False
                    self.resolve_turn()
        elif self.action_overlay.is_switch:
            self.action_overlay.close()
            self.switch_UI.open()
            self.switch_UI.update(dt)
            if self.switch_UI.selected:
                self.player_action = {"type": "switch", "value": self.switch_UI.next}
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
                self.player_action = {"type": "item", "value": item}
                self.waiting_for_action = False
                self.item_overlay.selected = False
                self.action_overlay.is_item = False
                self.resolve_turn()
        elif self.action_overlay.is_run:
            self.player_action = {"type": "run", "value": None}
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
            self.m2_sprite.draw(screen)

        self.action_overlay.draw(screen)
        self.health_overlay.draw(screen)
        self.noti.draw(screen)
        self.move_overlay.draw(screen)
        self.item_overlay.draw(screen)
        self.switch_UI.draw(screen)

        if self.victory:
            self.victory.draw(screen)
