from src.utils import GameSettings, crd, color, Logger
from src.interface.components import Overlay, Button
from src.core.services import (
    scene_manager,
)
from src.sprites import Sprite, Text, ColorSprite
import pygame as pg
import random


class Victory(Overlay):
    def __init__(self):
        super().__init__()
        self.bg = ColorSprite(
            "Black", (GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), 128
        )

        self.add_bg(
            self.bg,
        )

        text = Text("Victory!", 64, "Azure")
        text.rect.center = (
            GameSettings.SCREEN_WIDTH / 2,
            GameSettings.SCREEN_HEIGHT / 2,
        )

        self.add_passive(text)


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
        self.fill_bar1_original = self.fill_bar1.image.copy()

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
        self.fill_bar2_original = self.fill_bar2.image.copy()

        blank_bar2.rect.topleft = self.fill_bar2.rect.topleft = (
            self.sh.per(40) + self.sh.per(3),
            self.sh.per(3),
        )
        self.add_passive(blank_bar2)

        # Text labels
        self.name1_text = None
        self.level1_text = None
        self.name2_text = None
        self.level2_text = None

        # Animation state
        self.animating = False
        self.max_width1 = self.fill_bar1.rect.width
        self.max_width2 = self.fill_bar2.rect.width

    def load(self):
        """Load monster data and create text labels"""
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

        # text labels for monster 1
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

        # text labels for monster 2
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

        self.health_ratio()
        self.update_bar_color(self.fill_bar1, self.ratio1)
        self.update_bar_color(self.fill_bar2, self.ratio2)
        self.fill_bar1.update_bar(int(self.max_width1 * self.ratio1))
        self.fill_bar2.update_bar(int(self.max_width2 * self.ratio2))

    def health_ratio(self):
        """Calculate current health ratios"""
        if hasattr(scene_manager._current_scene, "monster1") and hasattr(
            scene_manager._current_scene, "monster2"
        ):
            mon1 = getattr(scene_manager._current_scene, "monster1")
            mon2 = getattr(scene_manager._current_scene, "monster2")
            self.ratio1 = mon1["chp"] / mon1["hp"]
            self.ratio2 = mon2["chp"] / mon2["hp"]
        else:
            self.ratio1 = 1.0
            self.ratio2 = 1.0

    def health_update(self):
        """Start the health bar animation"""
        # Store previous ratios
        before1 = getattr(self, "ratio1", 1.0)
        before2 = getattr(self, "ratio2", 1.0)

        # Calculate new ratios
        self.health_ratio()

        # Check if anything changed
        if before1 == self.ratio1 and before2 == self.ratio2:
            return

        # Update colors ONCE before animation starts
        self.update_bar_color(self.fill_bar1, self.ratio1)
        self.update_bar_color(self.fill_bar2, self.ratio2)

        # Set up animation
        self.start_width1 = self.fill_bar1.rect.width
        self.target_width1 = int(self.max_width1 * self.ratio1)
        self.start_width2 = self.fill_bar2.rect.width
        self.target_width2 = int(self.max_width2 * self.ratio2)

        self.elapsed = 0.0
        self.duration = 1.0
        self.animating = True

    def update_content(self, dt: float):
        """Animate the health bars"""
        if self.animating:
            self.elapsed += dt
            t = min(self.elapsed / self.duration, 1.0)  # Clamp to 0-1

            # Interpolate bar widths
            new_width1 = int(
                self.start_width1 + (self.target_width1 - self.start_width1) * t
            )
            new_width2 = int(
                self.start_width2 + (self.target_width2 - self.start_width2) * t
            )

            # Update bar colors
            self.update_bar_color(self.fill_bar1, self.ratio1)
            self.update_bar_color(self.fill_bar2, self.ratio2)

            # Update bars
            self.fill_bar1.update_bar(new_width1)
            self.fill_bar2.update_bar(new_width2)

            # Stop animation when complete
            if t >= 1.0:
                self.animating = False

    def update_bar_color(self, bar, ratio):
        # G100 -> Y50 -> R0
        if ratio > 0.5:
            t = (1.0 - ratio) * 2
            r = int(255 * t)
            g = 255
            b = 0
        else:
            t = (0.5 - ratio) * 2
            r = 255
            g = int(255 * (1 - t))
            b = 0

        if bar == self.fill_bar1:
            original = pg.transform.grayscale(self.fill_bar1_original)
        else:
            original = pg.transform.grayscale(self.fill_bar2_original)

        bar.image = color.recolor_multiply_screen(original, (r, g, b))

    def draw_content(self, screen) -> None:
        """Draw the health bars"""
        self.fill_bar1.draw(screen)
        self.fill_bar2.draw(screen)


class ActionOverlay(Overlay):
    def __init__(self):
        super().__init__()
        self.is_open = True
        self.is_item = False
        self.is_move = False
        self.first = True
        self.try_run = False

        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        bg = Sprite("UI/raw/UI_Flat_Frame03a.png", (sw.per(40), sh.per(15)))
        bg.rect.bottomright = (sw - sh.per(3), sh - sh.per(3))
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
        if 95 > random.randint(0, 100):
            scene_manager.change_scene("game")
        else:
            if hasattr(scene_manager._current_scene, "noti"):
                setattr(scene_manager._current_scene, "player_turn", False)
                scene_manager._current_scene.notichange("You fail to run away.")


class MoveOverlay(Overlay):
    def __init__(self):
        super().__init__()
        self.selected = False
        self.moves = []
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        bg = Sprite("UI/raw/UI_Flat_Frame03a.png", (sw.per(40), sh.per(15)))
        bg.rect.bottomright = (sw - sh.per(3), sh - sh.per(3))

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
            lambda: self.action(1),
        )
        self.add_active(move2)

        move3 = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            bg.rect.left + sh.per(6),
            bg.rect.bottom - bg.rect.height // 2,
            bg.rect.width // 2 - sh.per(6),
            bg.rect.height // 2 - sh.per(2),
            lambda: self.action(2),
        )
        self.add_active(move3)

        move4 = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            bg.rect.right - bg.rect.width // 2 + sh.per(3),
            bg.rect.bottom - bg.rect.height // 2,
            bg.rect.width // 2 - sh.per(6),
            bg.rect.height // 2 - sh.per(2),
            lambda: self.action(3),
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
        if hasattr(scene_manager._current_scene, "move"):
            setattr(scene_manager._current_scene, "move", key)
            Logger.debug(f"Move {key} selected")

    def inmove(self, moves: list[dict]):
        self.moves = moves
        for i in range(len(self.moves)):
            self.labels[i].change_text(self.moves[i]["name"], "center")
            self.add_passive(self.labels[i])
        for i in range(len(self.moves), 4):
            self.add_passive(self.labels[i])


class ItemOverlay(Overlay):
    pass

    def __init__(self):
        super().__init__()
        self.selected = False

        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        bg = Sprite("UI/raw/UI_Flat_Frame03a.png", (sw.per(40), sh.per(15)))
        bg.rect.bottomright = (sw - sh.per(3), sh - sh.per(3))

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
            lambda: self.action(1),
        )
        self.add_active(move2)

        move3 = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            bg.rect.left + sh.per(6),
            bg.rect.bottom - bg.rect.height // 2,
            bg.rect.width // 2 - sh.per(6),
            bg.rect.height // 2 - sh.per(2),
            lambda: self.action(2),
        )
        self.add_active(move3)

        move4 = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            bg.rect.right - bg.rect.width // 2 + sh.per(3),
            bg.rect.bottom - bg.rect.height // 2,
            bg.rect.width // 2 - sh.per(6),
            bg.rect.height // 2 - sh.per(2),
            lambda: self.action(3),
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
        if hasattr(scene_manager._current_scene, "move"):
            setattr(scene_manager._current_scene, "move", key)
            Logger.debug(f"Move {key} selected")
        self.add_active(use)
