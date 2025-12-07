import pygame as pg
import threading
import time
from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import crd, Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager, input_manager, scene_manager
from src.sprites import Sprite
from typing import override
from src.interface.components import Button
from src.interface import SettingOverlay, Inventory
from src.entities.player import Bush
from src.interface.components import Overlay
from src.core.gm_helper import gh, online_manager


class GameScene(Scene):
    """Game  scene."""

    online_manager: OnlineManager | None
    sprite_online: Sprite
    menu_button: Button
    setting_overlay: SettingOverlay

    def __init__(self):
        super().__init__()
        gh.load()
        self.bush = Bush()
        self.online_manager = online_manager
        self.sprite_online = Sprite(
            "ingame_ui/options1.png", (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        )
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
        self.shop_on = False
        self.db = 0.0
        self.mt = False
        self.old = None
        self.tile_pos: Position | None = None
        self.map_on = True
        self.small_map()

    def small_map(self):
        """Small Map."""
        sw = crd(GameSettings.SCREEN_WIDTH)
        if gh.gm:
            self.minimap_frame = Sprite(
                "UI/raw/UI_Flat_Frame01a.png",
                (sw // 4, sw // 4 // gh.gm.current_map.ratio),
            )
        self.minimap_frame.rect.topright = sw - 32, 32

    def large_map(self):
        """Large Map."""
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)
        if gh.gm:
            self.minimap_frame = Sprite(
                "UI/raw/UI_Flat_Frame01a.png", (sw, sw // gh.gm.current_map.ratio)
            )
            self.minimap_frame.rect.center = sw // 2, sh // 2

    @override
    def enter(self) -> None:
        """Enter."""
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        if self.online_manager:
            self.online_manager.enter()

    @override
    def exit(self) -> None:
        """Exit."""
        if self.online_manager:
            self.online_manager.exit()

    @override
    def update(self, dt: float):
        """Update."""
        if self.setting_overlay.is_open or self.inventory.is_open or self.shop_on:
            pass
        else:
            self.menu_button.update(dt)
            self.inventory_button.update(dt)
        if self.setting_overlay.is_open:
            self.setting_overlay.update(dt)
        if self.inventory.is_open:
            self.inventory.update(dt)
        if gh.gm:
            gh.gm.try_switch_map()
            if gh.gm.player:
                gh.gm.player.update(dt)
                for enemy in gh.gm.current_enemy_trainers:
                    if enemy.detected:
                        gh.gm.current_fight = enemy
                    enemy.update(dt)
                for npc in gh.gm.current_npcs:
                    npc.update(dt)
                self.shop_on = any(npc.shop_ov.is_open for npc in gh.gm.current_npcs)
                if gh.gm.player.bush_dt:
                    gh.gm.current_fight = self.bush
                    gh.gm.player.bush_enter = False
            gh.gm.bag.update(dt)
            if gh.gm.player and self.online_manager:
                _ = self.online_manager.update(
                    gh.gm.player.position.x,
                    gh.gm.player.position.y,
                    gh.gm.current_map.path_name,
                )
        if input_manager.key_pressed(pg.K_ESCAPE) and not self.inventory.is_open:
            input_manager.reset()
            self.setting_overlay.open()
        if input_manager.key_pressed(pg.K_m):
            input_manager.reset()
            for overlay in Overlay._instances:
                overlay.close()
            self.map_toggle()
        if self.map_on and self.mt and input_manager.mouse_pressed(1):
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
            if gh.gm.player:
                camera = gh.gm.player.camera
                gh.gm.current_map.draw(screen, camera)
                gh.gm.player.draw(screen, camera)
            else:
                camera = PositionCamera(0, 0)
                gh.gm.current_map.draw(screen, camera)
            for enemy in gh.gm.current_enemy_trainers:
                enemy.draw(screen, camera)
            for npc in gh.gm.current_npcs:
                npc.draw(screen, camera)
        if self.setting_overlay.is_open or self.inventory.is_open or self.shop_on:
            pass
        else:
            self.menu_button.draw(screen)
            self.inventory_button.draw(screen)
        if self.setting_overlay.is_open:
            self.setting_overlay.draw(screen)
        if self.inventory.is_open:
            self.inventory.draw(screen)
        if gh.gm:
            self.draw_minimap(screen)
            if self.online_manager and gh.gm.player:
                list_online = self.online_manager.get_list_players()
                for player in list_online:
                    if player["map"] == gh.gm.current_map.path_name:
                        cam = gh.gm.player.camera
                        pos = cam.transform_position_as_position(
                            Position(player["x"], player["y"])
                        )
                        self.sprite_online.update_pos(pos)
                        self.sprite_online.draw(screen)

    def draw_minimap(self, screen: pg.Surface):
        """Draw minimap."""
        if gh.gm:
            if self.mt:
                s = pg.transform.scale(
                    gh.gm.current_map.minimap_surface(4, 2),
                    (
                        self.minimap_frame.rect.width
                        - crd(self.minimap_frame.rect.width).per(3),
                        self.minimap_frame.rect.height
                        - crd(self.minimap_frame.rect.width).per(3),
                    ),
                )
            else:
                s = pg.transform.scale(
                    gh.gm.current_map.minimap_surface(4, 1),
                    (
                        self.minimap_frame.rect.width
                        - crd(self.minimap_frame.rect.width).per(8),
                        self.minimap_frame.rect.height
                        - crd(self.minimap_frame.rect.width).per(8),
                    ),
                )
            rect = s.get_rect()
            rect.center = self.minimap_frame.image.get_rect().center
            if gh.gm.player:
                map_w = gh.gm.current_map.tmxdata.width * GameSettings.TILE_SIZE
                map_h = gh.gm.current_map.tmxdata.height * GameSettings.TILE_SIZE
                scale_x = s.get_width() / map_w
                scale_y = s.get_height() / map_h
                if self.mt:
                    ts = GameSettings.TILE_SIZE // 2
                else:
                    ts = GameSettings.TILE_SIZE
                r = pg.Rect(
                    gh.gm.player.position.x * scale_x,
                    gh.gm.player.position.y * scale_y,
                    ts * scale_x,
                    ts * scale_y,
                )
                pg.draw.rect(s, "RED", r)
                b = pg.Rect(
                    (gh.gm.player.position.x - GameSettings.SCREEN_WIDTH // 2)
                    * scale_x,
                    (gh.gm.player.position.y - GameSettings.SCREEN_HEIGHT // 2)
                    * scale_y,
                    GameSettings.SCREEN_WIDTH * scale_x,
                    GameSettings.SCREEN_HEIGHT * scale_y,
                )
                pg.draw.rect(s, "AZURE", b, 2)
                if self.tile_pos:
                    w = pg.Rect(
                        self.tile_pos.x * scale_x * GameSettings.TILE_SIZE,
                        self.tile_pos.y * scale_y * GameSettings.TILE_SIZE,
                        ts * scale_x,
                        ts * scale_y,
                    )
                    pg.draw.rect(s, "GREEN", w)
            self.minimap_frame.image.blit(s, rect)
            self.minimap_frame.draw(screen)
