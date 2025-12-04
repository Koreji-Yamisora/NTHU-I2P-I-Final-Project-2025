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

from src.core.gm_helper import gh


class GameScene(Scene):
    online_manager: OnlineManager | None
    sprite_online: Sprite
    menu_button: Button
    setting_overlay: SettingOverlay

    def __init__(self):
        super().__init__()

        gh.load()
        self.bush = Bush()

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

        self.setting_overlay = SettingOverlay()
        self.inventory = Inventory()
        self.shop_on = False
        self.db = 0.0

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

    @override
    def draw(self, screen: pg.Surface):
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
