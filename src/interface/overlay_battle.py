from src.utils import GameSettings, crd, color, Logger
from src.interface.components import Overlay, Button
from src.core.services import (
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
        self.add_bg(self.bg2)

        blank_bar2 = Sprite(
            "UI/raw/UI_Flat_FrameSlot01a.png", (self.sw.per(25), self.sh.per(2))
        )
        self.fill_bar2 = Sprite(
            "UI/raw/UI_Flat_FrameSlot02a.png", (self.sw.per(25), self.sh.per(2))
        )
        blank_bar2.rect.topleft = self.fill_bar2.rect.topleft = (
            self.sh.per(40) + self.sh.per(3),
            self.sh.per(3),
        )
        self.add_passive(blank_bar2)

        self.name1_text = None
        self.level1_text = None
        self.name2_text = None
        self.level2_text = None

    def load(self):
        self.mon1 = getattr(scene_manager._current_scene, "monster1")
        self.mon2 = getattr(scene_manager._current_scene, "monster2")

        # Remove old text labels if they exist
        if self.name1_text:
            self.components.remove(self.name1_text)
        if self.level1_text:
            self.components.remove(self.level1_text)
        if self.name2_text:
            self.components.remove(self.name2_text)
        if self.level2_text:
            self.components.remove(self.level2_text)

        # Create new text labels for monster 1
        self.name1_text = Text(self.mon1["name"], 32, "Azure")
        self.name1_text.rect.topleft = (
            self.bg.rect.left + self.sh.per(3),
            self.bg.rect.top + self.sh.per(3),
        )
        self.level1_text = Text(f"lvl: {self.mon1['level']}", 32, "Azure")
        self.level1_text.rect.topright = (
            self.bg.rect.right - self.sh.per(3),
            self.bg.rect.top + self.sh.per(3),
        )
        self.add_passive(self.name1_text)
        self.add_passive(self.level1_text)

        # Create new text labels for monster 2
        self.name2_text = Text(self.mon2["name"], 32, "Azure")
        self.name2_text.rect.bottomright = (
            self.bg2.rect.right - self.sh.per(3),
            self.bg2.rect.bottom - self.sh.per(3),
        )
        self.level2_text = Text(f"lvl: {self.mon2['level']}", 32, "Azure")
        self.level2_text.rect.bottomleft = (
            self.bg2.rect.left + self.sh.per(3),
            self.bg2.rect.bottom - self.sh.per(3),
        )
        self.add_passive(self.name2_text)
        self.add_passive(self.level2_text)

    def health_ratio(self):
        self.ratio = (
            self.mon1["chp"] / self.mon1["hp"],
            self.mon2["chp"] / self.mon2["hp"],
        )

    def health_update(self):
        before = getattr(self, "ratio", None)
        if before is None:
            return
        self.health_ratio()
        Logger.debug(f"Health ratio: {before} / {self.ratio}")
        if before == self.ratio:
            return

        self.start = (self.fill_bar1.rect.width, self.fill_bar2.rect.width)
        self.target = list(map(lambda x, r: x * r, self.start, self.ratio))
        self.elapsed = 0.0
        self.duration = 3
        self.animating = True
        self.wcal = lambda i, t: int(
            self.start[i] + (self.target[i] - self.start[i]) * t
        )

    def update_content(self, dt: float):
        animating = getattr(self, "animating", False)
        if animating:
            self.elapsed += dt
            t = self.elapsed / self.duration  # 0 to 1

            self.fill_bar1.update_bar(self.wcal(0, t))
            self.fill_bar2.update_bar(self.wcal(1, t))
            if t >= 1.0:
                self.animating = False

    def draw_content(self, screen) -> None:
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
