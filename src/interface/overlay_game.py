from __future__ import annotations
import pygame as pg
from src.interface.components import Overlay, Button, Slider, ToggleButton
from src.core.services import sound_manager, resource_manager
from src.core.managers import GameManager
from src.utils import GameSettings, Logger, crd
from typing import Callable
from src.sprites import Sprite


class SettingOverlay(Overlay):
    bg: Sprite
    game_manager: GameManager

    def __init__(self, game_manager: GameManager, on_button: Button | None = None):
        super().__init__(game_manager, overlay_alpha=128)
        self.on_button = on_button
        self.game_manager = game_manager

        # coodinator
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        self.bgx = crd(sw.per(70))
        self.bgy = sh.per(80)
        self.bg = Sprite(
            "UI/raw/UI_Flat_Frame03a.png",
            (self.bgx, self.bgy),
        )

        self.bg.rect.center = (
            sw.per(50),
            sh.per(50),
        )

        self.bag = self.game_manager.bag
        # Back button
        back_button = Button(
            "UI/button_back.png",
            "UI/button_back_hover.png",
            sw.per(3),
            sh.per(3),
            100,
            100,
            lambda: self.close(),
        )
        self.add_button(back_button)

        bgcx = crd(self.bg.rect.centerx + self.bg.rect.left)
        bgcy = crd(self.bg.rect.centery)
        print(bgcx)
        font = resource_manager.get_font("Minecraft.ttf", 24)
        text_color = (255, 255, 255)
        self.volume_label = font.render("Volume", True, text_color)
        self.volume_label_pos = (
            bgcx.per(50) - self.volume_label.get_width() // 2,
            bgcy.per(30),
        )

        def mute_audio(state):
            for channel in range(sound_manager.list_channels()):
                if state:
                    GameSettings.AUDIO_MUTE = True
                    pg.mixer.Channel(channel).set_volume(0)
                else:
                    GameSettings.AUDIO_MUTE = False
                    pg.mixer.Channel(channel).set_volume(GameSettings.AUDIO_VOLUME)

        self.toggle_button = ToggleButton(
            "UI/raw/UI_Flat_ToggleOff03a.png",
            "UI/raw/UI_Flat_ToggleOn03a.png",
            bgcx.per(70),
            bgcy.per(43),
            64,
            32,
            state=GameSettings.AUDIO_MUTE,
            action=mute_audio,
        )

        # Volume Slider
        def set_vol(state):
            GameSettings.AUDIO_VOLUME = state
            if sound_manager.current_bgm:
                sound_manager.current_bgm.set_volume(state)

        gx = crd(self.bgx // 2)

        self.volume_slider = Slider(
            "UI/raw/UI_Flat_FrameSlot03b.png",
            "UI/raw/UI_Flat_BarFill01g.png",
            "UI/raw/UI_Flat_BarFill01e.png",
            "UI/raw/UI_Flat_FrameSlot03a.png",
            bgcx.per(50),
            bgcy.per(43),
            gx.per(60),
            gx.per(4),
            gx.per(5),
            gx.per(8),
            GameSettings.AUDIO_VOLUME,
            action=set_vol,
        )

        self.save_button = Button(
            "UI/button_save.png",
            "UI/button_save_hover.png",
            sw.per(93),
            sh.per(3),
            100,
            100,
            lambda: self.game_manager.save("saves/game0.json"),
        )
        self.add_button(self.save_button)

        self.load_button = Button(
            "UI/button_load.png",
            "UI/button_load_hover.png",
            sw.per(93),
            sh.per(12),
            100,
            100,
            lambda: self.load(),
        )
        self.add_button(self.load_button)
        left_col_rect = pg.Rect(
            bgcx.per(30), bgcx.per(33), bgcx - bgcx.per(30), bgcy.per(66) - bgcy.per(33)
        )
        right_col_rect = pg.Rect(
            bgcx.per(130),
            bgcx.per(33),
            bgcx - bgcx.per(30),
            bgcy.per(66) - bgcy.per(33),
        )

    def load(self):
        manager = GameManager.load("saves/game0.json")
        if manager is None:
            Logger.error("Failed to load game manager")
            exit(1)
        self.game_manager = manager

    def update_content(self, dt: float) -> None:
        self.toggle_button.update(dt)
        self.volume_slider.update(dt)

    def draw_content(self, screen: pg.Surface) -> None:
        self.bg.draw(screen)
        screen.blit(self.volume_label, self.volume_label_pos)
        self.toggle_button.draw(screen)
        self.volume_slider.draw(screen)


class Inventory(Overlay):
    bg: Sprite
    game_manager: GameManager

    def __init__(self, game_manager: GameManager, on_button: Button | None = None):
        super().__init__(game_manager, overlay_alpha=128)
        self.game_manager = game_manager
        self.on_button = on_button

        # coodinator
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        self.bgx = crd(sw.per(70))
        self.bgy = sh.per(80)
        self.bg = Sprite(
            "UI/raw/UI_Flat_Frame03a.png",
            (self.bgx, self.bgy),
        )

        self.bg.rect.center = (
            sw.per(50),
            sh.per(50),
        )

        # Back button
        back_button = Button(
            "UI/button_back.png",
            "UI/button_back_hover.png",
            sw.per(3),
            sh.per(3),
            100,
            100,
            lambda: self.close(),
        )
        self.add_button(back_button)

        bgcx = crd(self.bg.rect.centerx)
        bgcy = crd(self.bg.rect.centery)
        print(bgcx)
        font = resource_manager.get_font("Minecraft.ttf", 24)
        text_color = (255, 255, 255)
        self.volume_label = font.render("Bag", True, text_color)
        self.volume_label_pos = (
            bgcx.per(50) - self.volume_label.get_width() // 2,
            bgcy.per(30),
        )

        bg_left = crd(self.bg.rect.left)
        bg_top = crd(self.bg.rect.top)
        bg_width = crd(self.bg.rect.width)
        bg_height = crd(self.bg.rect.height)

        left_col_x = bg_left + bg_width.per(10)
        left_col_y = bg_top + bg_height.per(10)
        left_col_width = bg_width.per(35)
        left_col_height = bg_height.per(80)
        left_col_rect = pg.Rect(left_col_x, left_col_y, left_col_width, left_col_height)

        right_col_x = bg_left + bg_width.per(55)
        right_col_y = bg_top + bg_height.per(10)
        right_col_width = bg_width.per(35)
        right_col_height = bg_height.per(80)
        right_col_rect = pg.Rect(
            right_col_x, right_col_y, right_col_width, right_col_height
        )

        self.game_manager.bag.add_monster_col(left_col_rect)
        self.game_manager.bag.add_item_col(right_col_rect)
        self.game_manager.bag.monster_slot(self.game_manager.bag._monsters_data)
        self.game_manager.bag.item_slot(self.game_manager.bag._items_data)

    def update_content(self, dt: float) -> None:
        self.game_manager.bag.update(dt)

    def draw_content(self, screen: pg.Surface) -> None:
        self.bg.draw(screen)
        screen.blit(self.volume_label, self.volume_label_pos)
        self.game_manager.bag.draw(screen)
