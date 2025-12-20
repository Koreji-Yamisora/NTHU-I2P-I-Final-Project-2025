import pygame as pg
import time
from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import crd, Logger, PositionCamera, GameSettings, Position, color
from src.core.services import sound_manager, input_manager, scene_manager
from src.sprites import Sprite, Animation
from typing import override
from src.interface.components import Button
from src.interface import SettingOverlay, Inventory
from src.entities.player import Bush
from src.interface.components import Overlay
from src.core.gm_helper import gh
from src.interface.overlay_chat import ChatOverlay
from src.interface.overlay_evolution import EvolutionOverlay
from src.sprites import Text


class PvPBattleContext:
    """Context for PvP Battles"""

    def __init__(self, opponent_id: int):
        self.opponent_id = opponent_id
        # Placeholder for opponent's monsters - will be synced during battle
        self.monsters = [
            {
                "id": 1,  # Default pokemon
                "name": "Opponent",
                "level": 5,
                "hp": 100,
                "chp": 100,
                "atk": 10,
                "def": 10,
                "spe": 10,
                "move": [],
                # Add missing visual fields
                "sprite_path": "pokemon/1.png",
                "sprite_back_path": "pokemon/back/1.png",
            }
        ]


class GameScene(Scene):
    """Game  scene."""

    online_manager: OnlineManager | None
    sprite_online: Sprite
    menu_button: Button
    setting_overlay: SettingOverlay
    debug_text: Text

    def __init__(self):
        super().__init__()
        # gh.load() -> Removed, handled by MenuScene
        self.bush = Bush()

        # Use GMHelper's online manager
        self.online_manager = gh.online_manager

        # Animated sprite for online players
        self.anim_online = Animation(
            "character/ow5.png",
            ["down", "left", "right", "up"],
            4,
            (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE),
            loop=0.5,
        )
        self.debug_text = Text("Debug", 20, "White")
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)
        self.menu_button = Button(
            "UI/button_setting.png",
            "UI/button_setting_hover.png",
            sw.per(3),
            sh.per(3),
            100,
            100,
            lambda: self.setting_overlay.open(),
        )
        self.inventory_button = Button(
            "UI/button_backpack.png",
            "UI/button_backpack_hover.png",
            sw.per(3),
            sh.per(13),
            100,
            100,
            lambda: self.inventory.open(),
        )
        self.setting_overlay = SettingOverlay()
        self.inventory = Inventory()
        self.evolution_overlay = EvolutionOverlay()
        self.shop_on = False
        self.db = 0.0
        self.mt = False
        self.old = None
        self.tile_pos: Position | None = None
        self.map_on = True
        self.small_map()

        # Day/Night Cycle
        from src.interface.light_overlay import LightOverlay

        self.light_overlay = LightOverlay()

        # Chat Overlay: Use gh.online_manager
        self.chat_overlay = ChatOverlay(
            send_callback=self.handle_chat_input,
            get_messages=lambda n: gh.online_manager.get_recent_chat(n)
            if gh.online_manager
            else [],
        )

        from src.interface.action_hints import ActionHints

        self.action_hints = ActionHints()

    def small_map(self):
        """Small Map."""
        sw = crd(GameSettings.SCREEN_WIDTH)
        if gh.gm:
            self.minimap_frame = Sprite(
                "UI/raw/UI_Flat_Frame01a.png",
                (sw // 4, sw // 4 // gh.gm.current_map.ratio),
                nine_grid_margins=(45, 45, 45, 45),
            )
            self.minimap_frame.image = color.recol(
                self.minimap_frame.image, (120, 120, 120)
            )
        # Only set rect if initialized
        if hasattr(self, "minimap_frame"):
            self.minimap_frame.rect.topright = sw - 32, 32

    def large_map(self):
        """Large Map."""
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)
        if gh.gm:
            # Reduce size to 70% width
            target_w = sw.per(70)
            target_h = target_w // gh.gm.current_map.ratio

            # Clamp height to screen height - margin
            if target_h > sh.per(90):
                target_h = sh.per(90)
                target_w = int(target_h * gh.gm.current_map.ratio)

            self.minimap_frame = Sprite(
                "UI/raw/UI_Flat_Frame01a.png",
                (target_w, target_h),
                nine_grid_margins=(45, 45, 45, 45),
            )
            self.minimap_frame.image = color.recol(
                self.minimap_frame.image, (120, 120, 120)
            )
            # Center it but shifted left slightly to make room for buttons?
            # Or just center and put buttons on right overlay
            self.minimap_frame.rect.center = sw // 2, sh // 2

            # Destination Buttons
            self.setup_dest_buttons(sw, sh)

    def setup_dest_buttons(self, sw, sh):
        """Setup destination buttons for large map."""
        # Always refresh buttons to ensure updates apply
        if hasattr(self, "dest_buttons"):
            self.dest_buttons.clear()

        self.dest_buttons = []

        # Panel Background for buttons
        # Force position to be on the right side of the screen
        sw = crd(GameSettings.SCREEN_WIDTH)
        panel_x = sw - 140  # Fixed position from right
        panel_y = 100

        # Define destinations (Name, x, y)
        dests = [
            ("Home", 18, 29),  # Quest Destination
        ]

        for i, (name, tx, ty) in enumerate(dests):
            # Define callback with logging wrapper
            def make_callback(target_x, target_y):
                def callback():
                    Logger.info(
                        f"Button '{name}' clicked! Attempting to walk to ({target_x}, {target_y})"
                    )
                    self.go_to_dest(target_x, target_y)

                return callback

            btn = Button(
                "UI/raw/UI_Flat_Frame01a.png",
                "UI/raw/UI_Flat_Frame02a.png",
                panel_x,
                panel_y + (i * 60),
                120,
                50,
                make_callback(tx, ty),  # Use wrapped callback
                nine_grid_margins=(45, 45, 45, 45),
            )
            self.dest_buttons.append(btn)

            # Create text for button
            from src.sprites import Text

            t_obj = Text(name, 20, "Black")
            t_obj.rect.center = btn.hitbox.center
            self.dest_buttons.append(t_obj)

    def go_to_dest(self, tx, ty):
        """Navigate to destination."""
        Logger.info(f"go_to_dest called with tx={tx}, ty={ty}")
        if gh.gm and gh.gm.player:
            start_pos = Position(
                int(gh.gm.player.position.x // GameSettings.TILE_SIZE),
                int(gh.gm.player.position.y // GameSettings.TILE_SIZE),
            )
            Logger.info(
                f"Pathfinding from ({start_pos.x}, {start_pos.y}) to ({tx}, {ty})"
            )

            # Clamp or check bounds in bfs
            path = self.bfs(start_pos, Position(tx, ty))
            if path:
                Logger.info(f"Auto-pathing to {tx}, {ty}. Path length: {len(path)}")
                gh.gm.player.set_path(path)
                # Close map? or keep open? Keep open
            else:
                sound_manager.play_se("notichange.ogg")  # Error sound
                Logger.info("Cannot reach destination - No path found")
        else:
            Logger.error("GameManager or Player is None!")

    @override
    def enter(self) -> None:
        """Enter."""
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")

        # Ensure minimap is initialized if GM is loaded
        if gh.gm and (not hasattr(self, "minimap_frame") or self.minimap_frame is None):
            self.small_map()

        # Ensure online manager is running if it exists
        if gh.online_manager:
            gh.online_manager.start()
            self.init_online_events()

    @override
    def exit(self) -> None:
        """Exit."""
        # Do not stop online manager here
        pass

    @override
    def update(self, dt: float):
        """Update."""
        if (
            self.setting_overlay.is_open
            or self.inventory.is_open
            or self.shop_on
            or self.chat_overlay.is_open
        ):
            pass
        else:
            self.menu_button.update(dt)
            self.inventory_button.update(dt)
        if self.setting_overlay.is_open:
            self.setting_overlay.update(dt)
        if self.inventory.is_open:
            self.inventory.update(dt)
        if self.evolution_overlay.is_open:
            self.evolution_overlay.update(dt)
        if gh.gm:
            gh.gm.try_switch_map()
            if gh.gm.player:
                gh.gm.player.update(dt)
                for enemy in gh.gm.current_enemy_trainers:
                    if enemy.detected:
                        if gh.gm.current_fight is None:
                            gh.gm.current_fight = enemy
                    elif gh.gm.current_fight == enemy:
                        gh.gm.current_fight = None
                    enemy.update(dt)
                for npc in gh.gm.current_npcs:
                    npc.update(dt)

                # DEBUG: Unstuck / Teleport to Spawn
                keys = pg.key.get_pressed()
                if keys[pg.K_p]:
                    Logger.info("Attempting to teleport to world.tmx spawn...")
                    target_map_key = "world.tmx"

                    if target_map_key in gh.gm.maps:
                        target_map = gh.gm.maps[target_map_key]
                        best_spawn = None
                        max_score = -1

                        # Search objects in target map
                        if hasattr(target_map, "tmxdata"):
                            for obj in target_map.tmxdata.objects:
                                if obj.name and "spawn" in obj.name.lower():
                                    score = obj.x + obj.y
                                    if score > max_score:
                                        max_score = score
                                        best_spawn = obj

                        if best_spawn:
                            Logger.info(
                                f"Found spawn '{best_spawn.name}' at ({best_spawn.x}, {best_spawn.y}). Switching..."
                            )
                            # Create generic Position (ensure imports or use gh.gm.player.position type)
                            # Actually Position is in utils

                            pos = Position(best_spawn.x, best_spawn.y)
                            gh.gm.switch_map(target_map_key, spawn_pos=pos)
                        else:
                            Logger.warning(
                                f"No 'spawn' object found in {target_map_key}"
                            )
                    else:
                        Logger.warning(
                            f"Map '{target_map_key}' not found in GameManager"
                        )
                self.shop_on = any(
                    (hasattr(npc, "shop_ov") and npc.shop_ov.is_open)
                    or (hasattr(npc, "pc_overlay") and npc.pc_overlay.is_open)
                    for npc in gh.gm.current_npcs
                )
                if gh.gm.player.bush_dt:
                    gh.gm.current_fight = self.bush
                    gh.gm.player.bush_enter = False
            gh.gm.bag.update(dt)

            # Update Debug Text
            if gh.gm.player:
                p = gh.gm.player.position
                tx = int(p.x // GameSettings.TILE_SIZE)
                ty = int(p.y // GameSettings.TILE_SIZE)
                self.debug_text.change_text(
                    f"Pos: ({p.x:.1f}, {p.y:.1f}) Tile: ({tx}, {ty})", color="White"
                )

            # DIAGNOSTIC: Check online state
            if self.online_manager:
                pass
            else:
                if GameSettings.ONLINE_LOGGING:
                    Logger.info("[ONLINE DEBUG] online_manager is None!")

            if gh.gm.player and self.online_manager:
                _ = self.online_manager.update(
                    gh.gm.player.position.x,
                    gh.gm.player.position.y,
                    gh.gm.current_map.path_name,
                    gh.gm.player.direction.name,
                    gh.gm.player.skin_idx,
                    gh.gm.player.is_moving,
                )
                self.update_online_players(dt)
            if hasattr(gh.gm.current_map, "update"):
                gh.gm.current_map.update(dt)
            # Update Day/Night Cycle
            if hasattr(self, "light_overlay") and gh.gm.current_map.path_name in (
                "map.tmx",
                "world.tmx",
            ):
                self.light_overlay.update(dt)

            # Update PvP Request Overlay
            if hasattr(self, "battle_request_ov") and self.battle_request_ov.is_open:
                self.battle_request_ov.update(dt)

            # INPUT HANDLING - Only process if chat is NOT open
            if not self.chat_overlay.is_open:
                # Toggle Inventory
                if input_manager.key_pressed(pg.K_b) or input_manager.button_pressed(
                    3
                ):  # Y button
                    if not self.inventory.is_open:
                        self.inventory.open()
                    else:
                        self.inventory.close()

                # Toggle Map (Minimap Size)
                if input_manager.key_pressed(pg.K_m) or input_manager.button_pressed(
                    4
                ):  # L1
                    if self.map_on:
                        # Toggle between small and large
                        if hasattr(self, "minimap_frame"):
                            if (
                                self.minimap_frame.rect.width
                                < GameSettings.SCREEN_WIDTH
                            ):
                                self.large_map()
                            else:
                                self.small_map()

                # Settings / Exit Overlay
                if input_manager.key_pressed(
                    pg.K_ESCAPE
                ) or input_manager.button_pressed(6):  # Select/Back
                    # Check if any overlay is open - if so, close it instead of opening settings
                    any_overlay_open = (
                        self.inventory.is_open
                        or self.setting_overlay.is_open
                        or self.shop_on
                        or self.evolution_overlay.is_open
                        or (
                            hasattr(self, "battle_request_ov")
                            and self.battle_request_ov.is_open
                        )
                    )

                    if self.inventory.is_open:
                        self.inventory.close()
                    elif self.setting_overlay.is_open:
                        self.setting_overlay.close()
                    elif self.shop_on:
                        # Close any open shop/PC overlays
                        for npc in gh.gm.current_npcs:
                            if hasattr(npc, "shop_ov") and npc.shop_ov.is_open:
                                npc.shop_ov.close()
                            if hasattr(npc, "pc_overlay") and npc.pc_overlay.is_open:
                                npc.pc_overlay.close()
                    elif (
                        hasattr(self, "battle_request_ov")
                        and self.battle_request_ov.is_open
                    ):
                        self.battle_request_ov.close()
                    elif not any_overlay_open:
                        # Only open settings if nothing else is open
                        self.setting_overlay.open()

                # Interact / Coop Challenge
                if input_manager.key_pressed(
                    pg.K_SPACE
                ) or input_manager.button_pressed(0):  # A button
                    # Interact is usually handled by Player update checking inputs,
                    # but for coop challenge or explicit interaction we might need checks here.
                    pass
            else:
                # Chat is open - only handle Escape to close chat
                if input_manager.key_pressed(pg.K_ESCAPE):
                    self.chat_overlay.close()

        if gh.gm:
            # Pass controller inputs to player movement if needed
            # Player update handles WASD, we might need to patch it for Joystick
            pass

        # Update Action Hints
        actions = []
        if self.setting_overlay.is_open:
            actions = [("BACK", "Close"), ("CONFIRM", "Select")]
        elif self.inventory.is_open:
            actions = [
                ("BACK", "Close"),
                ("CONFIRM", "Use"),
                ("UP", "Nav"),
                ("DOWN", "Nav"),
            ]
        elif self.chat_overlay.is_open:
            actions = [("BACK", "Close")]
        elif hasattr(self, "shop_on") and self.shop_on:
            actions = [
                ("BACK", "Leave"),
                ("CONFIRM", "Buy"),
                ("UP", "Nav"),
                ("DOWN", "Nav"),
            ]
        else:
            # Normal Game
            actions = [
                ("INTERACT", "Interact"),
                ("INVENTORY", "Bag"),
                ("MAP", "Map"),
                ("CHAT", "Chat"),
                ("SETTING", "Setting"),
            ]

        self.action_hints.set_actions(actions)

        # Update PvP Request Overlay
        if hasattr(self, "battle_request_ov") and self.battle_request_ov.is_open:
            self.battle_request_ov.update(dt)

        # Update Destination Buttons (Large Map Only)
        any_button_hovered = False
        if self.map_on and self.mt and hasattr(self, "dest_buttons"):
            for btn in self.dest_buttons:
                if hasattr(btn, "update"):
                    btn.update(dt)
                    if getattr(btn, "is_hovered", False):
                        any_button_hovered = True

        # Chat input handling (works offline too for commands)
        t_pressed = input_manager.key_pressed(pg.K_t)
        slash_pressed = input_manager.key_pressed(pg.K_SLASH)

        if (t_pressed or slash_pressed) and not self.chat_overlay.is_open:
            # Only open if no other overlay is open?
            if not (
                self.setting_overlay.is_open
                or self.inventory.is_open
                or self.shop_on
                or self.evolution_overlay.is_open
            ):
                initial = "/" if slash_pressed else ""
                self.chat_overlay.open(initial_text=initial)

        if self.chat_overlay.is_open:
            self.chat_overlay.update(dt)

        # (ESC handling moved to consolidated block above - removed duplicate)
        if input_manager.key_pressed(pg.K_m):
            input_manager.reset()
            for overlay in Overlay._instances:
                overlay.close()
            self.map_toggle()
        if (
            self.map_on
            and self.mt
            and input_manager.mouse_pressed(1)
            and not any_button_hovered
        ):
            self.tile_pos = self.get_tile_from_mouse()
            if self.tile_pos:
                Logger.info(f"Clicked Tile Position: {self.tile_pos}")
                if gh.gm and gh.gm.player:
                    start_pos = Position(
                        int(gh.gm.player.position.x // GameSettings.TILE_SIZE),
                        int(gh.gm.player.position.y // GameSettings.TILE_SIZE),
                    )
                    path = self.bfs(start_pos, self.tile_pos)
                    if path:
                        Logger.info(f"Path found: {len(path)} steps")
                        gh.gm.player.set_path(path)
                        self.map_toggle()
                    else:
                        Logger.info("No path found")

    def update_online_players(self, dt: float):
        """Update online players visuals and handle interactions."""
        if not self.online_manager:
            return

        players = self.online_manager.get_list_players()

        if players:
            if GameSettings.ONLINE_LOGGING:
                Logger.info(f"[ONLINE] Found {len(players)} online players")

        current_map = gh.gm.current_map.path_name if gh.gm else ""

        # Dictionary to store animations: self.online_animations = {pid: animation}
        # Initialize if not exists
        if not hasattr(self, "online_animations"):
            self.online_animations = {}
            if GameSettings.ONLINE_LOGGING:
                Logger.info("[ONLINE] Initialized online_animations dict")

        # Clean up old players
        active_ids = set()
        for p in players:
            active_ids.add(p["id"])

        to_remove = []
        for pid in self.online_animations:
            if pid not in active_ids:
                to_remove.append(pid)
        for pid in to_remove:
            del self.online_animations[pid]

        for p in players:
            if p["map"] != current_map:
                if GameSettings.ONLINE_LOGGING:
                    Logger.info(
                        f"[ONLINE] Skipping player {p['id']} - different map ({p['map']} vs {current_map})"
                    )
                continue

            if GameSettings.ONLINE_LOGGING:
                Logger.info(
                    f"[ONLINE] Processing player {p['id']} at ({p['x']}, {p['y']}) on map {p['map']}"
                )

            pid = p["id"]
            skin_idx = p.get("skin", 0)
            direction_name = p.get("direction", "DOWN").lower()
            is_moving = p.get("moving", False)

            # Create or get animation
            if pid not in self.online_animations:
                # Determine skin file
                x = skin_idx % 6 + 2  # Matches Entity logic
                self.online_animations[pid] = {
                    "anim": Animation(
                        f"character/ow{x}.png",
                        ["down", "left", "right", "up"],
                        4,
                        (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE),
                        loop=0.5,  # Always use non-zero loop value
                    ),
                    "skin": skin_idx,
                }

            anim_data = self.online_animations[pid]
            anim = anim_data["anim"]

            # Check if skin changed
            if anim_data["skin"] != skin_idx:
                x = skin_idx % 6 + 2
                anim = Animation(
                    f"character/ow{x}.png",
                    ["down", "left", "right", "up"],
                    4,
                    (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE),
                    loop=0.5,  # Always use non-zero loop value
                )
                anim_data["anim"] = anim
                anim_data["skin"] = skin_idx

            # Update direction
            if anim.cur_row != direction_name:
                anim.switch(direction_name)

            # Update animation state (play/stop) manually if needed or via loop
            # The Animation class might need 'stop()' or we just don't update if not moving
            if is_moving:
                anim.update(dt)
            else:
                anim.accumulator = 0  # Reset frame

            # Update position
            # Interpolation could accept dt here for smoothing
            # Set WORLD position, draw() will handle camera transform
            anim.update_pos(Position(p["x"], p["y"]))

            # Interaction Logic (PvP Request)
            # Check distance to player
            if gh.gm.player:
                dist = gh.gm.player.position.distance_to(Position(p["x"], p["y"]))

                # DIAGNOSTIC LOG (throttled)
                if (
                    hasattr(self, "_last_log_time")
                    and time.time() - self._last_log_time > 2.0
                ):
                    Logger.info(
                        f"[PvP DEBUG] PID {pid} dist: {dist:.1f}, Threshold: {GameSettings.TILE_SIZE * 1.5}"
                    )
                    if dist < GameSettings.TILE_SIZE * 1.5:
                        Logger.info(
                            f"[PvP DEBUG] Player {pid} is in range! Press E to challenge."
                        )
                    self._last_log_time = time.time()
                elif not hasattr(self, "_last_log_time"):
                    self._last_log_time = time.time()

                if dist < GameSettings.TILE_SIZE * 1.5:
                    # Show prompts?
                    if input_manager.key_pressed(pg.K_e):
                        Logger.info(
                            f"[PvP DEBUG] 'E' pressed! Sending Battle Request to {pid}"
                        )
                        success = self.online_manager.send_event(
                            pid,
                            {
                                "type": "battle_request",
                                "from_id": self.online_manager.player_id,
                            },
                        )
                        if success:
                            Logger.info("[PvP DEBUG] Event send returned True")
                        else:
                            Logger.error(
                                "[PvP DEBUG] Event send returned False (Queue full?)"
                            )

    def init_online_events(self):
        if self.online_manager:
            self.online_manager.register_event_callback(self.handle_online_event)

    def handle_online_event(self, event: dict):
        ev_type = event.get("type")
        if GameSettings.ONLINE_LOGGING:
            Logger.info(f"[PvP DEBUG] Received event: {event}")

        if ev_type == "battle_request":
            sender = event.get("from_id")
            if GameSettings.ONLINE_LOGGING:
                Logger.info(f"[PvP DEBUG] Processing battle request from {sender}")
            # Open Overlay
            from src.interface.overlay_battle_request import BattleRequestOverlay

            try:
                self.battle_request_ov = BattleRequestOverlay(
                    sender, lambda sid: self.accept_battle(sid), lambda: None
                )
                self.battle_request_ov.open()
                if GameSettings.ONLINE_LOGGING:
                    Logger.info(
                        f"[PvP DEBUG] Overlay opened: {self.battle_request_ov.is_open}"
                    )
            except Exception as e:
                Logger.error(f"[PvP DEBUG] Failed to open overlay: {e}")

        elif ev_type == "battle_accept":
            # Start Battle
            opponent_id = event.get("from_id")
            if GameSettings.ONLINE_LOGGING:
                Logger.info(f"Battle Accepted by {opponent_id}")
            # Transition to PvP scene
            self.start_pvp_battle(opponent_id)

    def accept_battle(self, sender_id: int):
        """Accept a battle request and start PvP combat"""
        if self.online_manager:
            # Send acceptance message
            self.online_manager.send_event(
                sender_id,
                {"type": "battle_accept", "from_id": self.online_manager.player_id},
            )
            if GameSettings.ONLINE_LOGGING:
                Logger.info("Sent battle acceptance, starting PvP...")
            # Start battle
            self.start_pvp_battle(sender_id)

    def start_pvp_battle(self, opponent_id: int):
        """Initialize and start a PvP battle"""
        # Set current fight to PvP context
        gh.gm.current_fight = PvPBattleContext(opponent_id)

        if GameSettings.ONLINE_LOGGING:
            Logger.info(f"Starting PvP battle with opponent {opponent_id}")
        scene_manager.change_scene("pvp")

    # Update Day/Night Cycle
    def _update_lighting(self, dt):
        if hasattr(self, "light_overlay") and gh.gm.current_map.path_name in (
            "map.tmx",
            "world.tmx",
        ):
            self.light_overlay.update(dt)
        # (ESC handling consolidated in main update() - removed duplicate)
        if input_manager.key_pressed(pg.K_m):
            input_manager.reset()
            for overlay in Overlay._instances:
                overlay.close()
            self.map_toggle()
        if self.map_on and self.mt:
            # Update Destination Buttons
            if hasattr(self, "dest_buttons"):
                for btn in self.dest_buttons:
                    if hasattr(btn, "update"):
                        btn.update(dt)

            if input_manager.mouse_pressed(1):
                self.tile_pos = self.get_tile_from_mouse()
                if self.tile_pos:
                    Logger.info(f"Clicked Tile Position: {self.tile_pos}")
                    if gh.gm and gh.gm.player:
                        start_pos = Position(
                            int(gh.gm.player.position.x // GameSettings.TILE_SIZE),
                            int(gh.gm.player.position.y // GameSettings.TILE_SIZE),
                        )
                        path = self.bfs(start_pos, self.tile_pos)
                        if path:
                            Logger.info(f"Path found: {len(path)} steps")
                            gh.gm.player.set_path(path)
                            self.map_toggle()
                        else:
                            Logger.info("No path found")

    def bfs(self, start: Position, end: Position) -> list[Position] | None:
        """Bfs."""
        if not gh.gm:
            return None
        queue = [(start, [])]
        visited = {(start.x, start.y)}
        map_width = gh.gm.current_map.tmxdata.width
        map_height = gh.gm.current_map.tmxdata.height
        while queue:
            current, path = queue.pop(0)
            if current.x == end.x and current.y == end.y:
                return path
            neighbors = [
                Position(current.x, current.y - 1),
                Position(current.x, current.y + 1),
                Position(current.x - 1, current.y),
                Position(current.x + 1, current.y),
            ]
            for next_pos in neighbors:
                if (next_pos.x, next_pos.y) in visited:
                    continue
                if not (0 <= next_pos.x < map_width and 0 <= next_pos.y < map_height):
                    continue
                test_rect = pg.Rect(
                    next_pos.x * GameSettings.TILE_SIZE,
                    next_pos.y * GameSettings.TILE_SIZE,
                    GameSettings.TILE_SIZE,
                    GameSettings.TILE_SIZE,
                )
                end_rect = pg.Rect(
                    end.x * GameSettings.TILE_SIZE,
                    end.y * GameSettings.TILE_SIZE,
                    GameSettings.TILE_SIZE,
                    GameSettings.TILE_SIZE,
                )
                if gh.gm.current_map.check_teleport(end_rect):
                    if gh.gm.check_collision(test_rect):
                        continue
                elif gh.gm.check_collision(
                    test_rect
                ) or gh.gm.current_map.check_teleport(test_rect):
                    continue
                visited.add((next_pos.x, next_pos.y))
                queue.append((next_pos, path + [next_pos]))
        return None

    def get_tile_from_mouse(self) -> Position | None:
        """Get tile from mouse."""
        if not gh.gm or not self.mt:
            return None
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)
        padding = crd(self.minimap_frame.rect.width).per(3)
        map_width = self.minimap_frame.rect.width - padding
        map_height = self.minimap_frame.rect.height - padding
        map_left = sw.per(50) - map_width // 2
        map_top = sh.per(50) - map_height // 2
        mouse_x, mouse_y = input_manager.mouse_pos
        if (
            mouse_x < map_left
            or mouse_x > map_left + map_width
            or mouse_y < map_top
            or mouse_y > map_top + map_height
        ):
            return None
        rel_x = mouse_x - map_left
        rel_y = mouse_y - map_top
        map_w = gh.gm.current_map.tmxdata.width * GameSettings.TILE_SIZE
        map_h = gh.gm.current_map.tmxdata.height * GameSettings.TILE_SIZE
        scale_x = map_width / map_w
        scale_y = map_height / map_h
        world_x = rel_x / scale_x
        world_y = rel_y / scale_y
        tile_x = int(world_x // GameSettings.TILE_SIZE)
        tile_y = int(world_y // GameSettings.TILE_SIZE)
        return Position(tile_x, tile_y)

    def map_toggle(self):
        """Map Toggle."""
        self.mt = not self.mt
        if self.mt:
            self.large_map()
        else:
            self.small_map()

    @override
    def draw(self, screen: pg.Surface):
        """Draw."""
        if gh.gm:
            # Draw Ground Layer
            if gh.gm.player:
                camera = gh.gm.player.camera
                gh.gm.current_map.draw(screen, camera)
            else:
                camera = PositionCamera(0, 0)
                gh.gm.current_map.draw(screen, camera)

            # Collect all renderable objects for Y-Sorting
            render_queue = []

            # 1. Map Sortable Objects (Trees, Houses, etc.)
            if hasattr(gh.gm.current_map, "sortable_objects"):
                render_queue.extend(gh.gm.current_map.sortable_objects)

            # 2. Player
            if gh.gm.player:
                render_queue.append(gh.gm.player)

            # 3. Enemies
            render_queue.extend(gh.gm.current_enemy_trainers)

            # 4. NPCs
            render_queue.extend(gh.gm.current_npcs)

            # 5. Online Players
            if hasattr(self, "online_animations"):
                for pid, anim_data in self.online_animations.items():
                    # Create a wrapper or ensure anim has rect and draw
                    # Animation class has rect and draw.
                    render_queue.append(anim_data["anim"])

            # Sort by bottom Y coordinate
            # We use a lambda that checks if the object has a 'rect' attribute
            # Most entities have 'animation.rect', but we might need to unify this.
            # Player/Enemy/NPC are Entities, and Entity has self.animation.rect, but also self.draw uses self.animation
            # Wait, Entity.draw calls self.animation.draw.
            # But render_queue needs uniform objects or we need to handle difference.

            # Entity class has 'animation' attribute which has 'rect'.
            # SortableItem has 'rect'.
            # Online players are 'Animation' objects (from my previous code reading of update_online_players).

            # Let's verify Entity structure.
            # Entity has 'animation' field. It does NOT have 'rect' directly exposed usually?
            # Let's check Entity.py again.
            # Entity: self.animation = Animation(...)
            # It does not seem to expose self.rect.

            # Use a wrapper or helper to get sort key?
            def get_sort_key(obj):
                # 1. Entity (Player, NPC, Enemy) - has 'animation' attribute
                if hasattr(obj, "animation") and hasattr(obj.animation, "rect"):
                    return obj.animation.rect.bottom
                # 2. Online Players - are 'Animation' instances
                # We identify them by checking for specific Animation attributes
                elif hasattr(obj, "cur_row") and hasattr(obj, "rect"):
                    return obj.rect.bottom
                # 3. Map Objects (Trees, Bushes) - default Sortable Objects
                elif hasattr(obj, "rect"):
                    return obj.rect.bottom
                return 0

            render_queue.sort(key=get_sort_key)

            # Draw all
            for obj in render_queue:
                obj.draw(screen, camera)

            # Draw Day/Night Cycle (Darkness + Lights)
            # Draw after entities but before UI
            if hasattr(self, "light_overlay") and gh.gm.current_map.path_name in (
                "map.tmx",
                "world.tmx",
            ):
                self.light_overlay.draw(screen, camera)

            # Draw NPC/PC Overlays after lighting (so they are bright)
            # Draw NPC/PC Overlays after lighting (so they are bright)
            for npc in gh.gm.current_npcs:
                if hasattr(npc, "shop_ov") and npc.shop_ov.is_open:
                    npc.shop_ov.draw(screen)
                if hasattr(npc, "pc_overlay") and npc.pc_overlay.is_open:
                    npc.pc_overlay.draw(screen)

            # Draw Debug Text
            if hasattr(self, "debug_text"):
                self.debug_text.draw(screen)

        if self.setting_overlay.is_open or self.inventory.is_open or self.shop_on:
            pass
        else:
            self.menu_button.draw(screen)
            self.inventory_button.draw(screen)
        if self.setting_overlay.is_open:
            self.setting_overlay.draw(screen)
        if self.inventory.is_open:
            self.inventory.draw(screen)

        # Draw chat overlay (works offline too)
        self.chat_overlay.draw(screen)

        if self.evolution_overlay.is_open:
            self.evolution_overlay.draw(screen)

        if gh.gm and not (
            self.setting_overlay.is_open
            or self.inventory.is_open
            or self.shop_on
            or self.evolution_overlay.is_open
        ):
            self.draw_minimap(screen)

            # Draw Destination Buttons (Large Map Only)
            if self.mt and hasattr(self, "dest_buttons"):
                for btn in self.dest_buttons:
                    if hasattr(btn, "draw"):
                        btn.draw(screen)

            if hasattr(self, "online_animations"):
                cam = gh.gm.player.camera
                count = len(self.online_animations)
                if count > 0:
                    Logger.info(f"[ONLINE] Drawing {count} online player(s)")
                for pid, anim_data in self.online_animations.items():
                    anim = anim_data["anim"]
                    anim.draw(screen, cam)
                    Logger.info(f"[ONLINE] Drew player {pid} at rect {anim.rect}")

            if hasattr(self, "battle_request_ov") and self.battle_request_ov.is_open:
                self.battle_request_ov.draw(screen)

        # Draw Action Hints
        self.action_hints.draw(screen)

    def draw_minimap(self, screen: pg.Surface):
        """Draw minimap."""
        if not gh.gm:
            return

        # Check for cache invalidation
        current_map_path = gh.gm.current_map.path_name

        # Initialize cache variables if they don't exist
        if not hasattr(self, "_cached_minimap_surface"):
            self._cached_minimap_surface = None
            self._cached_minimap_params = (None, None)  # (map_path, is_large)

        params = (current_map_path, self.mt)

        # Regenerate cache if needed
        if (
            self._cached_minimap_surface is None
            or self._cached_minimap_params != params
        ):
            Logger.info("Regenerating minimap cache...")
            if self.mt:
                # Large map settings
                pixel_scale = 2
                frame_inner_w = self.minimap_frame.rect.width - crd(
                    self.minimap_frame.rect.width
                ).per(3)
                frame_inner_h = self.minimap_frame.rect.height - crd(
                    self.minimap_frame.rect.width
                ).per(3)
            else:
                # Small map settings
                pixel_scale = 1
                frame_inner_w = self.minimap_frame.rect.width - crd(
                    self.minimap_frame.rect.width
                ).per(8)
                frame_inner_h = self.minimap_frame.rect.height - crd(
                    self.minimap_frame.rect.width
                ).per(8)

            raw_surface = gh.gm.current_map.minimap_surface(4, pixel_scale)
            self._cached_minimap_surface = pg.transform.scale(
                raw_surface, (frame_inner_w, frame_inner_h)
            )
            self._cached_minimap_params = params

        # 1. Draw the Frame
        self.minimap_frame.draw(screen)

        # 2. Draw the cached map surface centered on the frame
        s = self._cached_minimap_surface
        rect = s.get_rect()
        rect.center = (
            self.minimap_frame.rect.center
        )  # Use rect.center, not image.rect.center
        screen.blit(s, rect)

        # 3. Draw Entities on top
        if gh.gm.player:
            map_w = gh.gm.current_map.tmxdata.width * GameSettings.TILE_SIZE
            map_h = gh.gm.current_map.tmxdata.height * GameSettings.TILE_SIZE
            scale_x = s.get_width() / map_w
            scale_y = s.get_height() / map_h

            # Map toggle determines tile size for "dots" on minimap?
            # Original code: mt -> TILE_SIZE//2, else TILE_SIZE
            if self.mt:
                ts = GameSettings.TILE_SIZE // 2
            else:
                ts = GameSettings.TILE_SIZE

            # Helper to draw rect relative to minimap screen position
            def draw_on_map(color, world_pos):
                r = pg.Rect(
                    rect.left + world_pos.x * scale_x,
                    rect.top + world_pos.y * scale_y,
                    ts * scale_x,
                    ts * scale_y,
                )
                pg.draw.rect(screen, color, r)

            # Draw Path
            if gh.gm.player and gh.gm.player.path:
                for tile_pos in gh.gm.player.path:
                    # Convert tile pos to world pixel pos for draw_on_map
                    world_pixel_pos = Position(
                        tile_pos.x * GameSettings.TILE_SIZE,
                        tile_pos.y * GameSettings.TILE_SIZE,
                    )
                    draw_on_map((0, 191, 255), world_pixel_pos)  # Deep Sky Blue

            # Player (Green)
            draw_on_map("GREEN", gh.gm.player.position)

            # Draw Enemy Trainers (Red)
            for enemy in gh.gm.current_enemy_trainers:
                draw_on_map("RED", enemy.position)

            # Draw NPCs (Blue)
            for npc in gh.gm.current_npcs:
                draw_on_map("BLUE", npc.position)

            # Draw Online Players (Purple)
            if self.online_manager:
                for player in self.online_manager.get_list_players():
                    if player["map"] == gh.gm.current_map.path_name:
                        # Construct a position object purely for drawing
                        p_pos = Position(player["x"], player["y"])
                        draw_on_map("PURPLE", p_pos)

            # Camera View Box
            b = pg.Rect(
                rect.left
                + (gh.gm.player.position.x - GameSettings.SCREEN_WIDTH // 2) * scale_x,
                rect.top
                + (gh.gm.player.position.y - GameSettings.SCREEN_HEIGHT // 2) * scale_y,
                GameSettings.SCREEN_WIDTH * scale_x,
                GameSettings.SCREEN_HEIGHT * scale_y,
            )
            pg.draw.rect(screen, "AZURE", b, 2)

            # Target Tile
            if self.tile_pos:
                # tile_pos is in Tile Coords, convert to pixels for drawing logic which expects pixels
                t_pixel_pos = Position(
                    self.tile_pos.x * GameSettings.TILE_SIZE,
                    self.tile_pos.y * GameSettings.TILE_SIZE,
                )
                draw_on_map("GREEN", t_pixel_pos)

    def handle_chat_input(self, text: str) -> bool:
        """Handle chat input, intercepting commands."""
        text = text.strip()
        if not text:
            return False

        if text.startswith("/"):
            # It's a command
            parts = text.split()
            cmd = parts[0].lower()
            args = parts[1:]

            if cmd == "/evolve":
                if not args:
                    Logger.info("Usage: /evolve <pokemon_id>")
                    return True  # Return True to clear input

                try:
                    target_id = int(args[0])
                except ValueError:
                    Logger.error("Invalid ID format")
                    return True

                if gh.gm and gh.gm.bag:
                    # Find Pokemon with this ID in the bag (monsters_data)
                    found_mon = None
                    for i in range(min(6, len(gh.gm.bag._monsters_data))):
                        if gh.gm.bag._monsters_data[i]["id"] == target_id:
                            found_mon = gh.gm.bag._monsters_data[i]
                            break

                    if found_mon:
                        Logger.info(f"Force evolving Pokemon ID {target_id}")
                        self.chat_overlay.close()  # Close chat

                        def on_evolve_finish():
                            # Perform evolution logic
                            gh.gm.bag.evolve(found_mon)
                            Logger.info(
                                f"Forced evolution for ID {target_id} complete."
                            )

                        self.evolution_overlay.setup(found_mon, on_evolve_finish)
                    else:
                        Logger.warning(f"No Pokemon with ID {target_id} found in bag.")
                return True

        # Not a local command, send to server
        if self.online_manager:
            return self.online_manager.send_chat(text)

        return False
