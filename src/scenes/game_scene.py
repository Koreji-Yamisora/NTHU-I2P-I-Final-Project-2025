import pygame as pg
import threading
import time


from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import crd, Logger, PositionCamera, GameSettings, Position
from src.utils.reloader import reload
from src.core.services import sound_manager
from src.sprites import Sprite
from typing import override
from src.interface.components import Button


from src.interface import SettingOverlay, Inventory


class GameScene(Scene):
    game_manager: GameManager
    online_manager: OnlineManager | None
    sprite_online: Sprite
    menu_button: Button
    setting_overlay: SettingOverlay

    def __init__(self):
        super().__init__()
        # Game Manager
        manager = GameManager.load("saves/game0.json")
        if manager is None:
            Logger.error("Failed to load game manager")
            exit(1)
        self.game_manager = manager

        # Online Manager
        if GameSettings.IS_ONLINE:
            self.online_manager = OnlineManager()
        else:
            self.online_manager = None
        self.sprite_online = Sprite(
            "ingame_ui/options1.png", (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        )

        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)
        # overlay
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

        self.setting_overlay = SettingOverlay(self.game_manager, self.menu_button)
        self.inventory = Inventory(self.game_manager, self.inventory_button)
        self.db = 0.0
        self.overlays = [self.setting_overlay, self.inventory]

    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        if self.online_manager:
            self.online_manager.enter()

    @override
    def exit(self) -> None:
        if self.online_manager:
            self.online_manager.exit()

    @override
    def update(self, dt: float):
        # reload
        # reload(self, dt)
        #

        all_off = True
        for overlay in self.overlays:
            if overlay.is_open:
                all_off = False
                overlay.update(dt)
        for overlay in self.overlays:
            if not overlay.is_open and all_off:
                overlay.on_button.update(dt)

        self.game_manager.try_switch_map()

        if self.game_manager.player:
            self.game_manager.player.update(dt)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.update(dt)

        self.game_manager.bag.update(dt)

        if self.game_manager.player is not None and self.online_manager is not None:
            _ = self.online_manager.update(
                self.game_manager.player.position.x,
                self.game_manager.player.position.y,
                self.game_manager.current_map.path_name,
            )

    @override
    def draw(self, screen: pg.Surface):
        if self.game_manager.player:
            """
            [TODO HACKATHON 3]
            Implement the camera algorithm logic here
            Right now it's hard coded, you need to follow the player's positions
            you may use the below example, but the function still incorrect, you may trace the entity.py
            
            camera = self.game_manager.player.camera
            """
            camera = self.game_manager.player.camera
            self.game_manager.current_map.draw(screen, camera)
            self.game_manager.player.draw(screen, camera)
        else:
            camera = PositionCamera(0, 0)
            self.game_manager.current_map.draw(screen, camera)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.draw(screen, camera)

        all_off = True
        for overlay in self.overlays:
            if overlay.is_open:
                all_off = False
                overlay.draw(screen)
        for overlay in self.overlays:
            if not overlay.is_open and all_off:
                overlay.on_button.draw(screen)
        if self.online_manager and self.game_manager.player:
            list_online = self.online_manager.get_list_players()
            for player in list_online:
                if player["map"] == self.game_manager.current_map.path_name:
                    cam = self.game_manager.player.camera
                    pos = cam.transform_position_as_position(
                        Position(player["x"], player["y"])
                    )
                    self.sprite_online.update_pos(pos)
                    self.sprite_online.draw(screen)
