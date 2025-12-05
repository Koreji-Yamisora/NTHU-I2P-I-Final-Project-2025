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


class Shop(Overlay):
    """Shop."""
    bg: Sprite
    rf: float
    restocking: bool

    def __init__(self, shop_data):
        super().__init__(overlay_alpha=128)
        self.restocking = False
        self.rf = 0
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)
        self.shop_data = shop_data
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
        self.volume_label = font.render('Shop', True, text_color)
        self.volume_label_pos = bgcx.per(50) - self.volume_label.get_width(
            ) // 2, bgcy.per(30)
        bg_left = crd(self.bg.rect.left)
        bg_top = crd(self.bg.rect.top)
        bg_width = crd(self.bg.rect.width)
        bg_height = crd(self.bg.rect.height)
        x = bg_left + bg_width.per(10)
        y = bg_top + bg_height.per(10)
        w = bg_width.per(80)
        h = bg_height.per(80)
        rect = pg.Rect(x, y, w, h)
        self.height = rect.height // 8
        self.slots = [pg.Rect(rect.left, rect.top + self.height * idx, rect
            .width, self.height) for idx in range(8)]
        self.refresh()

    def refresh(self):
        """Refresh."""
        self.slot_buttons = []
        self.item_slot = []
        items = self.shop_data.get('items')
        for idx, item in enumerate(items):
            if idx < 8:
                self.slot_buttons.append(Button(
                    'UI/raw/UI_Flat_Frame03a.png',
                    'UI/raw/UI_Flat_Frame02a.png', self.slots[idx].left,
                    self.slots[idx].top, self.slots[idx].width, self.slots[
                    idx].height, lambda idx=idx: self.action(idx)))
                sprite = Sprite(item['sprite_path'], (64, 64))
                sprite.rect.center = self.slots[idx].center
                name = Text(item['name'], 24, 'azure')
                name.rect.left = self.slots[idx].left + crd(self.slots[idx]
                    .width).per(5)
                name.rect.centery = self.slots[idx].top + crd(self.height).per(
                    50)
                count = Text(f"Available : {item['count'][0]}", 24, 'azure')
                count.rect.left = name.rect.right + crd(self.slots[idx].width
                    ).per(5)
                count.rect.centery = self.slots[idx].top + crd(self.height
                    ).per(50)
                self.item_slot.append((sprite, name, count))

    def action(self, idx):
        """Action."""
        input_manager.reset()
        assert gh.gm is not None
        item = self.shop_data['items'][idx]
        if item['count'][0] > 0:
            item['count'][0] -= 1
            self.item_slot[idx][2].change_text(
                f"Available : {item['count'][0]}")
            gh.gm.bag.add_item(item)

    def close(self):
        """Close."""
        super().close()
        self.rf = 10
        self.restocking = True

    def open(self):
        """Open."""
        super().open()
        Logger.info('Shop opened')

    def update_content(self, dt: float) ->None:
        """Update content."""
        if input_manager.key_pressed(pg.K_ESCAPE):
            input_manager.reset()
            self.close()
        for i in self.slot_buttons:
            i.update(dt)

    def timer_tick(self, dt: float):
        """Timer Tick."""
        if self.rf > 0:
            self.rf -= dt
        elif self.restocking:
            for item in self.shop_data['items']:
                Logger.debug('Restocking shop item' + item['name'])
                item['count'][0] = item['count'][1]
            self.refresh()
            self.restocking = False

    def draw_content(self, screen: pg.Surface) ->None:
        """Draw content."""
        self.bg.draw(screen)
        for i in range(len(self.item_slot)):
            self.slot_buttons[i].draw(screen)
            for j in self.item_slot[i]:
                j.draw(screen)
