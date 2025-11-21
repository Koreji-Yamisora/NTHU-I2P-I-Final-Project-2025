import pygame as pg
from src.utils import GameSettings, crd, Logger, color
from src.interface.components import Overlay, Button
from src.core.services import (
    input_manager,
    resource_manager,
    sound_manager,
    scene_manager,
)
from src.sprites import Sprite, Text
import random


class HealthOverlay(Overlay):
    def __init__(self):
        super().__init__()
        self.is_open = True
        self.inited = False
        self.sw = crd(GameSettings.SCREEN_WIDTH)
        self.sh = crd(GameSettings.SCREEN_HEIGHT)
        self.bg = Sprite(
            "UI/raw/UI_Flat_FrameSlot02a.png", (self.sw.per(28), self.sh.per(15))
        )
        self.bg.image = color.recol(self.bg.image, (120, 120, 120))
        self.bg.rect.bottomright = (self.sw - self.sh.per(5), self.sh - self.sh.per(25))
        self.add_bg(self.bg)
        blank_bar = Sprite(
            "UI/raw/UI_Flat_FrameSlot01a.png", (self.sw.per(25), self.sh.per(2))
        )
        self.fill_bar1 = Sprite(
            "UI/raw/UI_Flat_FrameSlot02a.png", (self.sw.per(25), self.sh.per(2))
        )
        self.fill_bar1.rect.bottomright = blank_bar.rect.bottomright = (
            self.sw - self.sh.per(5),
            self.sh - self.sh.per(25),
        )
        self.add_passive(blank_bar)
        self.bg2 = Sprite(
            "UI/raw/UI_Flat_FrameSlot02a.png", (self.sw.per(28), self.sh.per(15))
        )
        self.bg2.image = color.recol(self.bg2.image, (120, 120, 120))
        self.bg2.rect.topleft = (self.sh.per(40) + self.sh.per(3), self.sh.per(3))
        blank_bar = Sprite(
            "UI/raw/UI_Flat_FrameSlot01a.png", (self.sw.per(25), self.sh.per(2))
        )
        self.add_bg(self.bg2)
        self.fill_bar2 = Sprite(
            "UI/raw/UI_Flat_FrameSlot02a.png", (self.sw.per(25), self.sh.per(2))
        )
        blank_bar.rect.topleft = self.fill_bar2.rect.topleft = (
            self.sh.per(40) + self.sh.per(3),
            self.sh.per(3),
        )
        self.add_passive(blank_bar)

    def load(self, mon1, mon2):
        self.mon1 = mon1
        n1 = Text(mon1["name"], 32, "Azure")
        n1.rect.topleft = (
            self.bg.rect.left + self.sh.per(3),
            self.bg.rect.top + self.sh.per(3),
        )
        l1 = Text(f"lvl: {mon1['level']}", 32, "Azure")
        l1.rect.topright = (
            self.bg.rect.right - self.sh.per(3),
            self.bg.rect.top + self.sh.per(3),
        )
        self.add_passive(n1)
        self.add_passive(l1)
        self.mon2 = mon2
        n2 = Text(mon2["name"], 32, "Azure")
        n2.rect.bottomright = (
            self.bg2.rect.right - self.sh.per(3),
            self.bg2.rect.bottom - self.sh.per(3),
        )
        l2 = Text(f"lvl: {mon2['level']}", 32, "Azure")
        l2.rect.bottomleft = (
            self.bg2.rect.left + self.sh.per(3),
            self.bg2.rect.bottom - self.sh.per(3),
        )
        self.add_passive(n2)
        self.add_passive(l2)

    def update_content(self, dt: float):
        # --- BAR 1 ---
        # Store the original left position before changing width
        # Calculate left from the right anchor point minus full bar width
        original_left = self.sw.per(100) - self.sh.per(5) - self.sw.per(25)
        original_bottom = self.sh.per(100) - self.sh.per(25)

        ratio1 = self.mon1["chp"] / self.mon1["hp"]
        self.fill_bar1.rect.width = int(self.sw.per(25) * ratio1)

        # Now set the position after width change - anchor to bottomleft so it shrinks right to left
        self.fill_bar1.rect.bottomleft = (original_left, original_bottom)

        # --- BAR 2 ---
        # Store the original left position before changing width
        original_left = self.sh.per(40) + self.sh.per(3)
        original_top = self.sh.per(3)

        ratio2 = self.mon2["chp"] / self.mon2["hp"]
        self.fill_bar2.rect.width = int(self.sw.per(25) * ratio2)

        # Now set the position after width change
        self.fill_bar2.rect.topleft = (original_left, original_top)

    def draw_content(self, screen: pg.Surface):
        self.fill_bar1.draw(screen)
        self.fill_bar2.draw(screen)


class ActionOverlay(Overlay):
    def __init__(self):
        super().__init__()
        self.Turn = True
        self.is_move = False
        self.is_item = False
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        bg2 = Sprite("UI/raw/UI_Flat_Frame01a.png", (sw, sh.per(20)))
        bg2.rect.bottom = sh
        bg2.image = color.recol(bg2.image, (90, 90, 90))
        self.add_bg(bg2)
        bg3 = Sprite("UI/raw/UI_Flat_Frame01a.png", (sw.per(55), sh.per(15)))
        bg3.rect.bottomleft = (sh.per(3), sh - sh.per(3))
        bg3.image = color.recol(bg3.image, (255, 255, 255))

        self.add_bg(bg3)
        bg = Sprite("UI/raw/UI_Flat_Frame03a.png", (sw.per(40), sh.per(15)))
        bg.rect.bottomright = (sw - sh.per(3), sh - sh.per(3))
        self.add_bg(bg)
        self.msg_srt = Text("initializing Battle...", 32, "Black")

        self.msg_srt.rect.topleft = (
            bg3.rect.left + sh.per(3),
            bg3.rect.top + sh.per(6),
        )
        self.add_passive(self.msg_srt)

        run_button = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            bg.rect.right - bg.rect.width // 2 + sh.per(3),
            bg.rect.bottom - bg.rect.height // 2,
            bg.rect.width // 2 - sh.per(6),
            bg.rect.height // 2 - sh.per(2),
            lambda: self.action(0),
        )
        self.add_active(run_button)
        switch_button = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            bg.rect.right - bg.rect.width // 2 + sh.per(3),
            bg.rect.top + sh.per(2),
            bg.rect.width // 2 - sh.per(6),
            bg.rect.height // 2 - sh.per(2),
            lambda: self.action(1),
        )
        self.add_active(switch_button)
        fight_button = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            bg.rect.left + sh.per(6),
            bg.rect.top + sh.per(2),
            bg.rect.width // 2 - sh.per(6),
            bg.rect.height // 2 - sh.per(2),
            lambda: self.action(2),
        )
        self.add_active(fight_button)
        item_button = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            bg.rect.left + sh.per(6),
            bg.rect.bottom - bg.rect.height // 2,
            bg.rect.width // 2 - sh.per(6),
            bg.rect.height // 2 - sh.per(2),
            lambda: self.action(3),
        )
        self.add_active(item_button)
        label = Text("Run", 32, "Black")
        label.rect.center = run_button.hitbox.center
        label.rect.bottom -= run_button.hitbox.height // 16
        self.add_passive(label)
        label = Text("Pokemon", 32, "Black")
        label.rect.center = switch_button.hitbox.center
        label.rect.bottom -= switch_button.hitbox.height // 16
        self.add_passive(label)
        label = Text("Fight", 32, "Black")
        label.rect.center = fight_button.hitbox.center
        label.rect.bottom -= fight_button.hitbox.height // 16
        self.add_passive(label)
        label = Text("Bag", 32, "Black")
        label.rect.center = item_button.hitbox.center
        label.rect.bottom -= item_button.hitbox.height // 16
        self.add_passive(label)

        if not self.Turn:
            bg = Sprite("UI/raw/UI_Flat_Frame03a.png", (sw.per(50), sh.per(35)))
            bg.rect.bottomright = (sw - sh.per(3), sh - sh.per(3))
            self.add_passive(bg)
            label = Text("Item", 32, "Black")
            label.rect.center = bg.rect.center
            label.rect.bottom -= bg.rect.height // 8
            self.add_passive(label)

    def action(self, key):
        match key:
            case 0:
                self.run()
            case 1:
                pass
            case 2:
                self.is_move = True
            case 3:
                self.is_item = True

    def run(self):
        self.Turn = False
        chance = random.randint(0, 100)
        if chance < 95:
            scene_manager.change_scene("game")
        else:
            pass


class MoveOverlay(Overlay):
    def __init__(self):
        super().__init__()
        self.Turn = True
        self.is_move = False
        self.is_item = False
        self.selected = False
        self.moves = []
        self.noti_cd = 0.6
        self.ntcon = False
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        bg3 = Sprite("UI/raw/UI_Flat_Frame01a.png", (sw.per(55), sh.per(15)))
        bg3.rect.bottomleft = (sh.per(3), sh - sh.per(3))
        bg3.image = color.recol(bg3.image, (255, 255, 255))
        bg = Sprite("UI/raw/UI_Flat_Frame03a.png", (sw.per(40), sh.per(15)))
        bg.rect.bottomright = (sw - sh.per(3), sh - sh.per(3))
        self.add_bg(bg)
        self.noti = Text("Choosing Move...", 32, "Black")

        self.noti.rect.topleft = (bg3.rect.left + sh.per(3), bg3.rect.top + sh.per(2))

        move1 = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            bg.rect.left + sh.per(6),
            bg.rect.top + sh.per(2),
            bg.rect.width // 2 - sh.per(6),
            bg.rect.height // 2 - sh.per(2),
            lambda: self.action(0),
        )
        self.add_active(move1)
        move2 = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            bg.rect.right - bg.rect.width // 2 + sh.per(3),
            bg.rect.top + sh.per(2),
            bg.rect.width // 2 - sh.per(6),
            bg.rect.height // 2 - sh.per(2),
        )
        self.add_active(move2)
        move3 = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            bg.rect.left + sh.per(6),
            bg.rect.bottom - bg.rect.height // 2,
            bg.rect.width // 2 - sh.per(6),
            bg.rect.height // 2 - sh.per(2),
        )
        self.add_active(move3)
        move4 = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            bg.rect.right - bg.rect.width // 2 + sh.per(3),
            bg.rect.bottom - bg.rect.height // 2,
            bg.rect.width // 2 - sh.per(6),
            bg.rect.height // 2 - sh.per(2),
        )
        self.add_active(move4)

        self.labels = []
        label = Text("1", 32, "Black")
        label.rect.center = move1.hitbox.center
        label.rect.bottom -= move1.hitbox.height // 16
        self.labels.append(label)
        label = Text("2", 32, "Black")
        label.rect.center = move2.hitbox.center
        label.rect.bottom -= move2.hitbox.height // 16
        self.labels.append(label)
        label = Text("3", 32, "Black")
        label.rect.center = move3.hitbox.center
        label.rect.bottom -= move3.hitbox.height // 16
        self.labels.append(label)
        label = Text("4", 32, "Black")
        label.rect.center = move4.hitbox.center
        label.rect.bottom -= move4.hitbox.height // 16
        self.labels.append(label)

    def action(self, key):
        self.selected = True
        self.key = key

    def _cooldown(self, text: list[str]):
        for t in text:
            yield t

    def notichange(self, text: str | list[str]):
        if isinstance(text, str):
            self.noti.change_text(text)
            self.add_passive(self.noti)
        else:
            self.run = self._cooldown(text)
            self.ntcon = True

    def update_content(self, dt: float) -> None:
        self.noti_cd -= dt
        if self.ntcon:
            if self.noti_cd <= 0:
                self.noti_cd = 1
                try:
                    self.notichange(next(self.run))
                except StopIteration:
                    self.ntcon = False

    def result(self):
        self.Turn = False
        return self.key

    def inmove(self, moves: list[dict]):
        self.moves = moves
        for i in range(len(self.moves)):
            self.labels[i].change_text(self.moves[i]["name"], "center")
            self.add_passive(self.labels[i])
        for i in range(len(self.moves), 4):
            self.add_passive(self.labels[i])


class ItemOverlay(Overlay):
    pass
