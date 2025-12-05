from __future__ import annotations
import pygame as pg
from src.interface.components import Overlay, Button, Slider, ToggleButton
from src.core.services import sound_manager, resource_manager
from src.core.managers import GameManager
from src.utils import GameSettings, Logger, crd
from typing import Callable
from src.sprites import Sprite, Text
from src.core.services import input_manager
from src.core.gm_helper import gh


class SettingOverlay(Overlay):
    """Setting  overlay UI component."""
    bg: Sprite

    def __init__(self):
        super().__init__(overlay_alpha=128)
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)
        self.bgx = crd(sw.per(70))
        self.bgy = crd(sh.per(80))
        self.bg = Sprite('UI/raw/UI_Flat_Frame03a.png', (self.bgx, self.bgy))
        self.bg.rect.center = sw.per(50), sh.per(50)
        self.add_bg(self.bg)
        x = self.bg.rect.right - self.bgx.per(8)
        y = self.bg.rect.top + self.bgx.per(4)
        back_button = Button('UI/button_back.png',
            'UI/button_back_hover.png', x, y, self.bgx.per(5), self.bgx.per
            (5), lambda : self.close())
        self.add_active(back_button)
        bgcx = crd(self.bg.rect.centerx + self.bg.rect.left)
        bgcy = crd(self.bg.rect.centery)
        voluem_label = Text('Volume', 24, 'azure')
        voluem_label.rect.topleft = bgcx.per(50
            ) - voluem_label.rect.width // 2, bgcy.per(30)
        self.add_passive(voluem_label)

        def mute_audio(state):
            """Mute Audio."""
            GameSettings.AUDIO_MUTE = not state
            sound_manager.refresh()
            if sound_manager.current_bgm:
                if GameSettings.AUDIO_MUTE:
                    sound_manager.current_bgm.set_volume(0)
                else:
                    sound_manager.current_bgm.set_volume(GameSettings.
                        AUDIO_VOLUME)
        toggle_button = ToggleButton('UI/raw/UI_Flat_ToggleOff03a.png',
            'UI/raw/UI_Flat_ToggleOn03a.png', bgcx.per(70), bgcy.per(43), 
            64, 32, state=GameSettings.AUDIO_MUTE, action=mute_audio)
        self.add_active(toggle_button)

        def set_vol(state):
            """Set vol."""
            GameSettings.AUDIO_VOLUME = state
            if sound_manager.current_bgm:
                sound_manager.current_bgm.set_volume(state)
        gx = crd(self.bgx // 2)
        volume_slider = Slider('UI/raw/UI_Flat_FrameSlot03b.png',
            'UI/raw/UI_Flat_BarFill01g.png',
            'UI/raw/UI_Flat_BarFill01e.png',
            'UI/raw/UI_Flat_FrameSlot03a.png', bgcx.per(50), bgcy.per(43),
            gx.per(60), gx.per(4), gx.per(5), gx.per(8), state=GameSettings
            .AUDIO_VOLUME, action=set_vol)
        self.add_active(volume_slider)
        save_button = Button('UI/button_save.png',
            'UI/button_save_hover.png', (self.bg.rect.right + self.bg.rect.
            centerx) // 2 - self.bgx.per(5), self.bg.rect.bottom - self.bgy
            .per(12), 75, 75, lambda : gh.save())
        self.add_active(save_button)
        load_button = Button('UI/button_load.png',
            'UI/button_load_hover.png', (self.bg.rect.right + self.bg.rect.
            centerx) // 2 + self.bgx.per(5), self.bg.rect.bottom - self.bgy
            .per(12), 75, 75, lambda : gh.load())
        self.add_active(load_button)
        exit_button = Button('UI/button_back.png',
            'UI/button_back_hover.png', (self.bg.rect.left + self.bg.rect.
            centerx) // 2, self.bg.rect.bottom - self.bgy.per(12), 75, 75, 
            lambda : self.exit_to_menu())
        self.add_active(exit_button)
        exit_label = Text('Menu', 20, 'azure')
        exit_label.rect.center = (self.bg.rect.left + self.bg.rect.centerx
            ) // 2, self.bg.rect.bottom - self.bgy.per(6)
        self.add_passive(exit_label)

    def exit_to_menu(self):
        """Exit to the main menu screen"""
        from src.core.services import scene_manager
        self.close()
        scene_manager.change_scene('menu')

    def update_content(self, dt: float) ->None:
        """Update content."""
        if input_manager.key_pressed(pg.K_ESCAPE):
            input_manager.reset()
            self.close()


class Inventory(Overlay):
    """Inventory."""
    bg: Sprite
    game_manager: GameManager

    def __init__(self):
        super().__init__(overlay_alpha=128)
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)
        self.bgx = crd(sw.per(70))
        self.bgy = sh.per(80)
        self.bg = Sprite('UI/raw/UI_Flat_Frame03a.png', (self.bgx, self.bgy))
        self.bg.rect.center = sw.per(50), sh.per(50)
        back_button = Button('UI/button_back.png',
            'UI/button_back_hover.png', sw.per(3), sh.per(3), 100, 100, lambda
            : self.close())
        self.add_active(back_button)
        bgcx = crd(self.bg.rect.centerx)
        bgcy = crd(self.bg.rect.centery)
        print(bgcx)
        font = resource_manager.get_font('Minecraft.ttf', 24)
        text_color = 255, 255, 255
        self.volume_label = font.render('Bag', True, text_color)
        self.volume_label_pos = bgcx.per(50) - self.volume_label.get_width(
            ) // 2, bgcy.per(30)
        bg_left = crd(self.bg.rect.left)
        bg_top = crd(self.bg.rect.top)
        bg_width = crd(self.bg.rect.width)
        bg_height = crd(self.bg.rect.height)
        left_col_x = bg_left + bg_width.per(10)
        left_col_y = bg_top + bg_height.per(10)
        left_col_width = bg_width.per(35)
        left_col_height = bg_height.per(80)
        self.left_col_rect = pg.Rect(left_col_x, left_col_y, left_col_width,
            left_col_height)
        right_col_x = bg_left + bg_width.per(55)
        right_col_y = bg_top + bg_height.per(10)
        right_col_width = bg_width.per(35)
        right_col_height = bg_height.per(80)
        self.right_col_rect = pg.Rect(right_col_x, right_col_y,
            right_col_width, right_col_height)
        if gh.gm:
            gh.gm.bag.my_mon()
            gh.gm.bag.add_monster_col(self.left_col_rect)
            gh.gm.bag.add_item_col(self.right_col_rect)

    def open(self):
        """Open."""
        super().open()
        if gh.gm:
            gh.gm.bag.my_mon()
            gh.gm.bag.add_monster_col(self.left_col_rect)
            gh.gm.bag.add_item_col(self.right_col_rect)

    def update_content(self, dt: float) ->None:
        """Update content."""
        if input_manager.key_pressed(pg.K_ESCAPE):
            input_manager.reset()
            self.close()

    def draw_content(self, screen: pg.Surface) ->None:
        """Draw content."""
        self.bg.draw(screen)
        if gh.gm:
            gh.gm.bag.draw(screen)
