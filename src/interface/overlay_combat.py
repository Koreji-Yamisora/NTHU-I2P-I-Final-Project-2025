from src.utils import GameSettings, crd, color, Logger
from src.interface.components import Overlay, Button
from src.core.services import (
    scene_manager,
)
from src.sprites import Sprite, Text, ColorSprite
import pygame as pg
import random
from src.core import gh
from src.data import pokedex


sw = crd(GameSettings.SCREEN_WIDTH)
sh = crd(GameSettings.SCREEN_HEIGHT)


class Victory(Overlay):
    def __init__(self, s, exp_data: dict = None):
        super().__init__()
        self.is_open = True
        self.sw = crd(GameSettings.SCREEN_WIDTH)
        self.sh = crd(GameSettings.SCREEN_HEIGHT)

        # Background with fade
        self.bg = ColorSprite(
            "Black", (GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), 0
        )
        self.add_bg(self.bg)

        # Panel
        self.panel = Sprite(
            "UI/raw/UI_Flat_Frame01a.png",
            (self.sw.per(40), self.sh.per(30)),
            nine_grid_margins=(45, 45, 45, 45),
        )
        self.panel.image = color.recol(self.panel.image, (240, 240, 240))
        # Start off-screen (top)
        self.target_y = self.sh.per(35)
        self.start_y = -self.sh.per(40)
        self.panel.rect.centerx = self.sw // 2
        self.panel.rect.y = self.start_y
        self.add_active(self.panel)

        # Text
        message = "You Win!" if s else "You Lose!"
        color_name = "Blue" if s else "Red"
        self.text = Text(message, 64, color_name)
        self.text.rect.center = self.panel.rect.center
        self.add_passive(self.text)

        # EXP Animation Data
        self.exp_data = exp_data
        self.exp_bar_bg = None
        self.exp_bar_fill = None
        self.level_text = None

        if self.exp_data:
            self.setup_exp_bar()

        # Animation state
        self.animating = True
        self.elapsed = 0.0
        self.duration = 0.8
        self.exp_animating = False

    def setup_exp_bar(self):
        # Create EXP Bar Background
        w, h = self.sw.per(30), self.sh.per(3)
        self.exp_bar_bg = ColorSprite((50, 50, 50), (w, h))
        self.exp_bar_bg.rect.centerx = self.panel.rect.centerx
        self.exp_bar_bg.rect.bottom = self.panel.rect.bottom - self.sh.per(5)
        self.add_passive(self.exp_bar_bg)

        # Create EXP Bar Fill
        self.exp_bar_fill = ColorSprite((0, 200, 255), (0, h))  # Start empty
        self.exp_bar_fill.rect.left = self.exp_bar_bg.rect.left
        self.exp_bar_fill.rect.top = self.exp_bar_bg.rect.top
        self.add_passive(self.exp_bar_fill)

        # Level Text
        lvl = self.exp_data["start_level"]
        self.level_text = Text(f"Lv. {lvl}", 32, "Black")
        self.level_text.rect.bottom = self.exp_bar_bg.rect.top - 5
        self.level_text.rect.centerx = self.exp_bar_bg.rect.centerx
        self.add_passive(self.level_text)

        # EXP State
        self.current_level = self.exp_data["start_level"]
        self.current_exp = self.exp_data["start_exp"]
        self.target_end_exp = self.exp_data["end_exp"]
        self.target_end_level = self.exp_data["end_level"]
        self.req_exp = (self.current_level + 1) ** 3

    def update_exp_bar(self, dt):
        if not self.exp_animating or not self.exp_data:
            return

        # Animate EXP filling
        # Pixels per second speed
        speed = self.req_exp * 1.5  # Fill full bar in ~0.6s
        self.current_exp += speed * dt

        # Check Level Up
        if self.current_level < self.target_end_level:
            if self.current_exp >= self.req_exp:
                self.current_level += 1
                self.current_exp = 0
                self.req_exp = (self.current_level + 1) ** 3
                self.level_text.change_text(f"Lv. {self.current_level}", "center")
                # SFX?
        else:
            # Reached target level, cap at target exp
            if self.current_exp >= self.target_end_exp:
                self.current_exp = self.target_end_exp
                self.exp_animating = False

        # Update Bar Width
        ratio = min(1.0, self.current_exp / self.req_exp) if self.req_exp > 0 else 0
        max_w = self.exp_bar_bg.rect.width
        cur_w = int(max_w * ratio)

        # Resize logic (hacky for sprite reuse, assuming simple ColorSprite)
        # Create new surface for fill
        fill_surf = pg.Surface((max(1, cur_w), self.exp_bar_bg.rect.height))
        fill_surf.fill((0, 200, 255))
        self.exp_bar_fill.image = fill_surf
        self.exp_bar_fill.rect = fill_surf.get_rect(
            topleft=self.exp_bar_bg.rect.topleft
        )

    def update(self, dt: float):
        # Panel Slide Logic
        if self.animating:
            self.elapsed += dt
            t = min(self.elapsed / self.duration, 1.0)

            ease = 1 - (1 - t) ** 3
            current_y = self.start_y + (self.target_y - self.start_y) * ease
            self.panel.rect.y = int(current_y)
            self.text.rect.center = self.panel.rect.center
            self.bg.image.set_alpha(int(128 * t))

            # Sync EXP bar position
            if self.exp_bar_bg:
                self.exp_bar_bg.rect.centerx = self.panel.rect.centerx
                # Offset relative to panel bottom
                # Since panel moves, bar moves
                # Relayout relative to current panel position
                self.exp_bar_bg.rect.bottom = self.panel.rect.bottom - self.sh.per(5)
                self.exp_bar_fill.rect.topleft = self.exp_bar_bg.rect.topleft
                self.level_text.rect.bottom = self.exp_bar_bg.rect.top - 5
                self.level_text.rect.centerx = self.exp_bar_bg.rect.centerx

            if t >= 1.0:
                self.animating = False
                # Start EXP animation after slide in
                if self.exp_data:
                    self.exp_animating = True

        # EXP Animation Logic
        self.update_exp_bar(dt)


class HPbar(Overlay):
    def __init__(self, p1: str, p2: str, w: int, h: int):
        super().__init__()
        self._animate_scale = False  # Disable scale animation for combat overlays
        self.is_open = True
        self.inited = False
        self.sw = crd(GameSettings.SCREEN_WIDTH)
        self.sh = crd(GameSettings.SCREEN_HEIGHT)
        self.w = w
        self.h = h

        self.blank_bar = Sprite(
            p1, (self.w, self.h), nine_grid_margins=(45, 45, 45, 45)
        )
        self.blank_bar.image = color.recol(self.blank_bar.image, (120, 120, 120))

        self.fill_bar = Sprite(p2, (self.w, self.h), nine_grid_margins=(45, 45, 45, 45))
        self.og = self.fill_bar.image.copy()

        self.add_passive(self.blank_bar)

        self.animating = False
        self.max_width = self.fill_bar.rect.width

    def update_rect(self, pos, key: str):
        setattr(self.fill_bar.rect, key, pos)
        setattr(self.blank_bar.rect, key, pos)

    def load(self):
        """Load HP bar with charge-up animation from 0."""
        self.update_bar_color()
        # Animate from 0 to current ratio on first load
        if not self.inited:
            self.animate_from_zero()
            self.inited = True
        else:
            self.fill_bar.update_bar(int(self.max_width * self.ratio))

    def animate_from_zero(self):
        """Start HP bar at 0 and animate to current ratio."""
        self.fill_bar.update_bar(0)
        self.start_width = 0
        self.target_width = int(self.max_width * self.ratio)
        self.elapsed = 0.0
        self.duration = 0.8  # Faster charge animation
        self.animating = True

    def health_ratio(self, mon):
        self.ratio = mon["chp"] / mon["hp"]

    def health_update(self, mon):
        before = getattr(self, "ratio", 1.0)

        self.health_ratio(mon)

        if before == self.ratio:
            return

        self.update_bar_color()

        self.start_width = self.fill_bar.rect.width
        self.target_width = int(self.max_width * self.ratio)

        self.elapsed = 0.0
        self.duration = 1.0
        self.animating = True

    def update_content(self, dt: float):
        """Animate the health bars"""
        if self.animating:
            self.elapsed += dt
            t = min(self.elapsed / self.duration, 1.0)

            new_width = int(
                self.start_width + (self.target_width - self.start_width) * t
            )

            self.update_bar_color()

            self.fill_bar.update_bar(new_width)

            if t >= 1.0:
                self.animating = False

    def update_bar_color(self):
        if self.ratio > 0.5:
            t = (1.0 - self.ratio) * 2
            r = int(255 * t)
            g = 255
            b = 0
        elif self.ratio > 0.01:
            t = (0.5 - self.ratio) * 2
            r = 255
            g = int(255 * (1 - t))
            b = 0
        else:
            r = 255
            g = 0
            b = 0
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        original = pg.transform.grayscale(self.og)
        self.fill_bar.image = color.recolor_multiply_screen(original, (r, g, b))

    def draw_content(self, screen) -> None:
        """Draw the health bars"""
        self.fill_bar.draw(screen)


class HealthOverlay(Overlay):
    def __init__(self):
        super().__init__()
        self._animate_scale = False  # Disable scale animation for combat overlays
        self.is_open = True
        self.inited = False
        self.animating = False
        self.sw = crd(GameSettings.SCREEN_WIDTH)
        self.sh = crd(GameSettings.SCREEN_HEIGHT)

        self.bar1 = HPbar(
            "UI/raw/UI_Flat_FrameSlot01a.png",
            "UI/raw/UI_Flat_FrameSlot02a.png",
            self.sw.per(25),
            self.sh.per(2),
        )
        self.bg = Sprite(
            "UI/raw/UI_Flat_FrameSlot02a.png",
            (self.sw.per(28), self.sh.per(15)),
            nine_grid_margins=(45, 45, 45, 45),
        )
        self.bg.image = color.recol(self.bg.image, (120, 120, 120))
        self.bg.rect.bottomright = (self.sw - self.sh.per(5), self.sh - self.sh.per(25))
        self.add_bg(self.bg)

        self.bar1.update_rect(
            (self.sw - self.sh.per(5), self.sh - self.sh.per(25)), "bottomright"
        )
        self.bg2 = Sprite(
            "UI/raw/UI_Flat_FrameSlot02a.png",
            (self.sw.per(28), self.sh.per(15)),
            nine_grid_margins=(45, 45, 45, 45),
        )
        self.bg2.image = color.recol(self.bg2.image, (120, 120, 120))
        self.bg2.rect.topleft = (self.sh.per(40) + self.sh.per(3), self.sh.per(3))
        self.add_bg(self.bg2)

        self.bar2 = HPbar(
            "UI/raw/UI_Flat_FrameSlot01a.png",
            "UI/raw/UI_Flat_FrameSlot02a.png",
            self.sw.per(25),
            self.sh.per(2),
        )

        self.bar2.update_rect(
            (self.sh.per(40) + self.sh.per(3), self.sh.per(3)), "topleft"
        )

        self.name1_text = None
        self.level1_text = None
        self.name2_text = None
        self.level2_text = None

    def load(self):
        self.mon1 = getattr(scene_manager._current_scene, "m1")
        self.mon2 = getattr(scene_manager._current_scene, "m2")

        if self.name1_text:
            self.components.remove(self.name1_text)
        if self.level1_text:
            self.components.remove(self.level1_text)
        if self.name2_text:
            self.components.remove(self.name2_text)
        if self.level2_text:
            self.components.remove(self.level2_text)

        if hasattr(self, "type_sprites1"):
            for ts in self.type_sprites1:
                if ts in self.components:
                    self.components.remove(ts)
        if hasattr(self, "type_sprites2"):
            for ts in self.type_sprites2:
                if ts in self.components:
                    self.components.remove(ts)

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

        # Type Icons for Combat
        from src.data.bag import TYPE_MAP

        # Player 1 Types (Top Left)
        types1 = self.mon1.get("type", [])
        start_x = self.name1_text.rect.left
        y_pos = self.name1_text.rect.bottom + 5
        self.type_sprites1 = []
        for t_abbr in types1:
            if not t_abbr:
                continue
            t_name = TYPE_MAP.get(t_abbr)
            if t_name:
                ts = Sprite(f"type/{t_name}.png", (24, 24))
                ts.rect.topleft = (start_x, y_pos)
                start_x += 35
                self.add_passive(ts)
                self.type_sprites1.append(ts)  # Keep ref if needed to clear

        # Player 2 Types (Bottom Right)
        types2 = self.mon2.get("type", [])
        # Iterate backwards/right-aligned? Or just left aligned below name?
        # Name is at bottomright relative to bg2
        # Let's align below name, right aligned?
        # text.rect.bottomright
        start_x = self.name2_text.rect.right
        y_pos = self.name2_text.rect.bottom + 5
        self.type_sprites2 = []
        for t_abbr in types2:
            if not t_abbr:
                continue
            t_name = TYPE_MAP.get(t_abbr)
            if t_name:
                ts = Sprite(f"type/{t_name}.png", (24, 24))
                ts.rect.topright = (start_x, y_pos)
                start_x -= 35
                self.add_passive(ts)
                self.type_sprites2.append(ts)
        self.health_ratio()
        self.bar1.load()
        self.bar2.load()

    def health_ratio(self):
        """Calculate current health ratios"""
        self.bar1.health_ratio(getattr(scene_manager._current_scene, "m1"))
        self.bar2.health_ratio(getattr(scene_manager._current_scene, "m2"))

    def health_update(self):
        """Start the health bar animation"""

        self.bar1.health_update(getattr(scene_manager._current_scene, "m1"))
        self.bar2.health_update(getattr(scene_manager._current_scene, "m2"))

    def update_content(self, dt: float):
        self.animating = self.bar1.animating or self.bar2.animating
        self.bar1.update(dt)
        self.bar2.update(dt)

    def draw_content(self, screen: pg.Surface):
        self.bar1.draw(screen)
        self.bar2.draw(screen)


class SwitchOverlay(Overlay):
    def __init__(self):
        super().__init__()
        self._animate_scale = False  # Disable scale animation for combat overlays
        self.selected = False
        self.next = None

    def init(self, forced=False):
        self.clear()
        self.selected = False
        self.forced = forced
        bg = Sprite(
            "UI/raw/UI_Flat_Frame03a.png",
            (sw.per(40), sh.per(80)),
            nine_grid_margins=(45, 45, 45, 45),
        )
        bg.image = color.recol(bg.image, (120, 120, 120))
        bg.rect.bottomright = (sw - sh.per(3), sh - sh.per(3))
        b = bg.rect.copy()
        slot_height = b.height // 6
        self.cur = getattr(scene_manager._current_scene, "ci1", None)
        monsters = getattr(gh, "gm").bag.monsters.copy()
        monsters.pop(self.cur)
        self.monsters = monsters
        self.hp = []

        bg.update_height(slot_height * len(monsters))
        bg.rect.bottomright = (sw - sh.per(3), sh - sh.per(3))

        self.add_bg(bg)
        back_button = Button(
            "UI/button_back.png",
            "UI/button_back_hover.png",
            sw.per(3),
            sh.per(3),
            sh.per(10),
            sh.per(10),
            lambda: self.close2(),
        )

        if not self.forced:
            self.add_active(back_button)

        self.ds = []
        for idx in range(min(len(monsters), 6)):
            monster = monsters[idx].copy()
            if monster["chp"] == 0:
                mbg = Button(
                    "UI/raw/UI_Flat_Frame03a.png",
                    "UI/raw/UI_Flat_Frame03a.png",
                    b.left,
                    b.top + slot_height * idx,
                    b.width,
                    crd(slot_height).per(90),
                    nine_grid_margins=(45, 45, 45, 45),
                )
                mbg.img_button.image = color.recol(
                    mbg.img_button.image, (120, 120, 120)
                )
                mbg.hitbox.bottom = b.bottom - slot_height * idx
                dead = pg.Surface((b.width, crd(slot_height).per(90)), pg.SRCALPHA)
                dead.fill((255, 0, 0, 128))
                rect = dead.get_rect()
                rect.bottomleft = (mbg.hitbox.left, mbg.hitbox.bottom)
                self.ds.append([dead, rect, idx])

            else:
                mbg = Button(
                    "UI/raw/UI_Flat_Frame03a.png",
                    "UI/raw/UI_Flat_Frame02a.png",
                    b.left,
                    b.top + slot_height * idx,
                    b.width,
                    crd(slot_height).per(90),
                    lambda idx=monster["idx"]: self.action(idx),
                    nine_grid_margins=(45, 45, 45, 45),
                )
                mbg.img_button_default.image = color.recol(
                    mbg.img_button_default.image, (120, 120, 120)
                )
                mbg.img_button_hover.image = color.recol(
                    mbg.img_button_hover.image, (120, 120, 120)
                )
                mbg.hitbox.bottom = b.bottom - slot_height * idx
                mbg.hitbox.bottom = b.bottom - slot_height * idx
            self.add_active(mbg)

            # IconBG
            icon_bg_size = 96
            icon_bg = Sprite(
                "UI/raw/UI_Flat_Frame01a.png",
                (icon_bg_size, icon_bg_size),
                nine_grid_margins=(45, 45, 45, 45),
            )
            icon_bg.image = color.recol(icon_bg.image, (60, 60, 60))
            icon_bg.rect.left = mbg.hitbox.left + crd(mbg.hitbox.width).per(2)
            icon_bg.rect.centery = mbg.hitbox.centery
            self.add_passive(icon_bg)

            sprite = Sprite(pokedex.data[monster["id"]]["sprite_path"], (96, 96))
            sprite.rect.center = icon_bg.rect.center
            self.add_passive(sprite)

            name = Text(monster["name"], 24, "azure")
            name.rect.topleft = (
                icon_bg.rect.right + crd(mbg.hitbox.width).per(2),
                mbg.hitbox.top + crd(slot_height).per(10),
            )
            self.add_passive(name)
            hp = HPbar(
                "UI/raw/UI_Flat_FrameSlot01a.png",
                "UI/raw/UI_Flat_FrameSlot02a.png",
                crd(mbg.hitbox.width).per(25),
                crd(slot_height).per(10),
            )
            text = Text("HP", 24, "azure")
            text.rect.topleft = (
                icon_bg.rect.right + crd(mbg.hitbox.width).per(2),
                mbg.hitbox.top + crd(slot_height).per(45),
            )
            self.add_passive(text)
            hp.update_rect(
                (
                    text.rect.right + crd(mbg.hitbox.width).per(2),
                    mbg.hitbox.top + crd(slot_height).per(45),
                ),
                "topleft",
            )
            hp.health_ratio(monster)
            hp.load()

            self.hp.append(hp)

            level = Text("Level: " + str(monster["level"]), 24, "azure")
            level.rect.topleft = (
                name.rect.right + crd(mbg.hitbox.width).per(4),
                name.rect.top,
            )
            self.add_passive(level)

    def update_content(self, dt: float):
        """Update HP bars to reflect current monster states"""

        current_monsters = getattr(gh, "gm").bag.monsters.copy()

        for idx, hp_bar in enumerate(self.hp):
            if idx < len(self.monsters):
                monster_idx = self.monsters[idx]["idx"]
                for current_mon in current_monsters:
                    if current_mon["idx"] == monster_idx:
                        hp_bar.health_ratio(current_mon)
                        hp_bar.load()
                        break

        for hp_bar in self.hp:
            hp_bar.update(dt)

    def draw_content(self, screen):
        for hp in self.hp:
            hp.draw(screen)

        current_monsters = getattr(gh, "gm").bag.monsters.copy()
        for dead_surface, rect, mon_idx in self.ds:
            for current_mon in current_monsters:
                if current_mon["idx"] == self.monsters[mon_idx]["idx"]:
                    if current_mon["chp"] == 0:
                        screen.blit(dead_surface, rect)
                    break

    def action(self, idx):
        self.selected = True
        Logger.debug(f"idx: {idx}")
        self.next = idx

    def close2(self):
        getattr(scene_manager._current_scene, "action_overlay").is_switch = False
        self.is_open = False


class ActionOverlay(Overlay):
    def __init__(self):
        super().__init__()
        self._animate_scale = False  # Disable scale animation for combat overlays
        self.is_open = True
        self.is_item = False
        self.is_move = False
        self.is_switch = False
        self.is_run = False
        self.first = True
        self.try_run = False
        bg = Sprite(
            "UI/raw/UI_Flat_Frame03a.png",
            (sw.per(40), sh.per(15)),
            nine_grid_margins=(45, 45, 45, 45),
        )
        bg.image = color.recol(bg.image, (120, 120, 120))
        bg.rect.bottomright = (sw - sh.per(3), sh - sh.per(3))
        run_button = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            bg.rect.right - bg.rect.width // 2 + sh.per(3),
            bg.rect.bottom - bg.rect.height // 2,
            bg.rect.width // 2 - sh.per(6),
            bg.rect.height // 2 - sh.per(2),
            lambda: self.action(0),
            nine_grid_margins=(14, 14, 14, 14),
        )
        run_button.img_button_default.image = color.recol(
            run_button.img_button_default.image, (120, 120, 120)
        )
        run_button.img_button_hover.image = color.recol(
            run_button.img_button_hover.image, (120, 120, 120)
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
            nine_grid_margins=(14, 14, 14, 14),
        )
        switch_button.img_button_default.image = color.recol(
            switch_button.img_button_default.image, (120, 120, 120)
        )
        switch_button.img_button_hover.image = color.recol(
            switch_button.img_button_hover.image, (120, 120, 120)
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
            nine_grid_margins=(14, 14, 14, 14),
        )
        fight_button.img_button_default.image = color.recol(
            fight_button.img_button_default.image, (120, 120, 120)
        )
        fight_button.img_button_hover.image = color.recol(
            fight_button.img_button_hover.image, (120, 120, 120)
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
            nine_grid_margins=(14, 14, 14, 14),
        )
        item_button.img_button_default.image = color.recol(
            item_button.img_button_default.image, (120, 120, 120)
        )
        item_button.img_button_hover.image = color.recol(
            item_button.img_button_hover.image, (120, 120, 120)
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
                self.is_run = True
            case 1:
                self.is_switch = True
            case 2:
                self.is_move = True
            case 3:
                self.is_item = True


class MoveOverlay(Overlay):
    def __init__(self):
        super().__init__()
        self._animate_scale = False  # Disable scale animation for combat overlays
        self.selected = False
        self.moves = []
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        bg = Sprite(
            "UI/raw/UI_Flat_Frame03a.png",
            (sw.per(40), sh.per(15)),
            nine_grid_margins=(45, 45, 45, 45),
        )
        bg.image = color.recol(bg.image, (120, 120, 120))
        bg.rect.bottomright = (sw - sh.per(3), sh - sh.per(3))

        back_button = Button(
            "UI/button_back.png",
            "UI/button_back_hover.png",
            sw.per(3),
            sh.per(3),
            sh.per(10),
            sh.per(10),
            lambda: self.close2(),
        )

        self.add_active(back_button)
        move1 = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            bg.rect.left + sh.per(6),
            bg.rect.top + sh.per(2),
            bg.rect.width // 2 - sh.per(6),
            bg.rect.height // 2 - sh.per(2),
            lambda: self.action(0),
            nine_grid_margins=(14, 14, 14, 14),
        )
        move1.img_button_default.image = color.recol(
            move1.img_button_default.image, (120, 120, 120)
        )
        move1.img_button_hover.image = color.recol(
            move1.img_button_hover.image, (120, 120, 120)
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
            nine_grid_margins=(14, 14, 14, 14),
        )
        move2.img_button_default.image = color.recol(
            move2.img_button_default.image, (120, 120, 120)
        )
        move2.img_button_hover.image = color.recol(
            move2.img_button_hover.image, (120, 120, 120)
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
            nine_grid_margins=(14, 14, 14, 14),
        )
        move3.img_button_default.image = color.recol(
            move3.img_button_default.image, (120, 120, 120)
        )
        move3.img_button_hover.image = color.recol(
            move3.img_button_hover.image, (120, 120, 120)
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
            nine_grid_margins=(14, 14, 14, 14),
        )
        move4.img_button_default.image = color.recol(
            move4.img_button_default.image, (120, 120, 120)
        )
        move4.img_button_hover.image = color.recol(
            move4.img_button_hover.image, (120, 120, 120)
        )
        self.add_active(move4)

        # Store move buttons for coloring
        self.move_buttons = [move1, move2, move3, move4]

        # Type color mapping
        self.type_colors = {
            "nor": (168, 168, 120),
            "fir": (240, 128, 48),
            "wat": (104, 144, 240),
            "ele": (248, 208, 48),
            "gra": (120, 200, 80),
            "ice": (152, 216, 216),
            "fig": (192, 48, 40),
            "poi": (160, 64, 160),
            "gro": (224, 192, 104),
            "fly": (168, 144, 240),
            "psy": (248, 88, 136),
            "bug": (168, 184, 32),
            "roc": (184, 160, 56),
            "gho": (112, 88, 152),
            "dra": (112, 56, 248),
            "dar": (112, 88, 72),
            "ste": (184, 184, 208),
            "fai": (238, 153, 172),
        }

        self.labels = []
        self.pp_labels = []
        label = Text("1", 32, "Black")
        label.rect.center = move1.hitbox.center
        label.rect.bottom -= move1.hitbox.height // 16
        self.labels.append(label)
        pp_label = Text("", 16, "Black")
        pp_label.rect.center = move1.hitbox.center
        pp_label.rect.top = label.rect.bottom + 2
        self.pp_labels.append(pp_label)

        label = Text("2", 32, "Black")
        label.rect.center = move2.hitbox.center
        label.rect.bottom -= move2.hitbox.height // 16
        self.labels.append(label)
        pp_label = Text("", 16, "Black")
        pp_label.rect.center = move2.hitbox.center
        pp_label.rect.top = label.rect.bottom + 2
        self.pp_labels.append(pp_label)

        label = Text("3", 32, "Black")
        label.rect.center = move3.hitbox.center
        label.rect.bottom -= move3.hitbox.height // 16
        self.labels.append(label)
        pp_label = Text("", 16, "Black")
        pp_label.rect.center = move3.hitbox.center
        pp_label.rect.top = label.rect.bottom + 2
        self.pp_labels.append(pp_label)

        label = Text("4", 32, "Black")
        label.rect.center = move4.hitbox.center
        label.rect.bottom -= move4.hitbox.height // 16
        self.labels.append(label)
        pp_label = Text("", 16, "Black")
        pp_label.rect.center = move4.hitbox.center
        pp_label.rect.top = label.rect.bottom + 2
        self.pp_labels.append(pp_label)

    def action(self, key):
        if key < len(self.moves):
            self.selected = True
            if hasattr(scene_manager._current_scene, "move"):
                setattr(scene_manager._current_scene, "move", key)
                Logger.debug(
                    f"MoveOverlay: Move {key} selected. self.selected set to True."
                )

    def inmove(self, moves: list[dict]):
        from src.data.pokedex import PokeItems

        self.moves = moves
        # Remove old PP labels
        for pp in self.pp_labels:
            if pp in self.components:
                self.components.remove(pp)

        for i in range(len(self.moves)):
            move = self.moves[i]
            move_name = move.get("name", "")
            self.labels[i].change_text(move_name, "center")
            self.add_passive(self.labels[i])

            # Look up move data from PokeItems if PP/type missing
            static_move = PokeItems.moves.get(move_name, {})
            max_pp = move.get("pp") or static_move.get("pp", 10)
            current_pp = move.get("cpp", max_pp)
            move_type = move.get("type") or static_move.get("type", "nor")
            power = move.get("power") or static_move.get("power", 0)
            acc = move.get("acc") or static_move.get("acc", 100)

            # Show PP, Power, Accuracy
            info = f"PP:{current_pp}/{max_pp} Pwr:{power} Acc:{acc}"
            self.pp_labels[i].change_text(info, "center")
            self.add_passive(self.pp_labels[i])

            # Color button based on move type
            type_color = self.type_colors.get(move_type, (120, 120, 120))
            btn = self.move_buttons[i]
            btn.img_button_default.image = color.recol(
                btn.img_button_default.image, type_color
            )
            # Make hover slightly brighter
            hover_color = tuple(min(255, c + 30) for c in type_color)
            btn.img_button_hover.image = color.recol(
                btn.img_button_hover.image, hover_color
            )

        for i in range(len(self.moves), 4):
            self.labels[i].change_text("---", "center")
            self.add_passive(self.labels[i])
            # Reset button color for empty slots
            btn = self.move_buttons[i]
            btn.img_button_default.image = color.recol(
                btn.img_button_default.image, (80, 80, 80)
            )
            btn.img_button_hover.image = color.recol(
                btn.img_button_hover.image, (80, 80, 80)
            )

    def close2(self):
        getattr(scene_manager._current_scene, "action_overlay").is_move = False
        self.is_open = False


class ItemOverlay(Overlay):
    def __init__(self):
        super().__init__()
        self._animate_scale = False  # Disable scale animation for combat overlays
        self.selected = False
        self.selected_item = None
        self.scroll_offset = 0
        self.max_visible = 5  # Number of items visible at once
        self.items_cache = []

    def init(self):
        self.clear()
        self.selected = False
        self.scroll_offset = 0

        # Get items from bag
        self.items_cache = getattr(gh, "gm").bag._items_data.copy()

        # Background
        bg = Sprite(
            "UI/raw/UI_Flat_Frame03a.png",
            (sw.per(40), sh.per(75)),
            nine_grid_margins=(45, 45, 45, 45),
        )
        bg.image = color.recol(bg.image, (120, 120, 120))
        bg.rect.bottomright = (sw - sh.per(3), sh - sh.per(3))
        self.bg_rect = bg.rect.copy()
        self.add_bg(bg)

        # Back button
        back_button = Button(
            "UI/button_back.png",
            "UI/button_back_hover.png",
            sw.per(3),
            sh.per(3),
            sh.per(10),
            sh.per(10),
            lambda: self.close2(),
        )
        self.add_active(back_button)

        # Scroll buttons
        if len(self.items_cache) > self.max_visible:
            scroll_up = Button(
                "UI/raw/UI_Flat_Button01a_4.png",
                "UI/raw/UI_Flat_Button01a_3.png",
                bg.rect.right - sh.per(8),
                bg.rect.top + sh.per(2),
                sh.per(6),
                sh.per(6),
                lambda: self.scroll(-1),
                nine_grid_margins=(14, 14, 14, 14),
            )
            scroll_up.img_button_default.image = color.recol(
                scroll_up.img_button_default.image, (100, 100, 100)
            )
            scroll_up.img_button_hover.image = color.recol(
                scroll_up.img_button_hover.image, (150, 150, 150)
            )
            self.add_active(scroll_up)

            up_label = Text("^", 24, "White")
            up_label.rect.center = scroll_up.hitbox.center
            self.add_passive(up_label)

            scroll_down = Button(
                "UI/raw/UI_Flat_Button01a_4.png",
                "UI/raw/UI_Flat_Button01a_3.png",
                bg.rect.right - sh.per(8),
                bg.rect.bottom - sh.per(8),
                sh.per(6),
                sh.per(6),
                lambda: self.scroll(1),
                nine_grid_margins=(14, 14, 14, 14),
            )
            scroll_down.img_button_default.image = color.recol(
                scroll_down.img_button_default.image, (100, 100, 100)
            )
            scroll_down.img_button_hover.image = color.recol(
                scroll_down.img_button_hover.image, (150, 150, 150)
            )
            self.add_active(scroll_down)

            down_label = Text("v", 24, "White")
            down_label.rect.center = scroll_down.hitbox.center
            self.add_passive(down_label)

        self._build_item_slots()

    def scroll(self, direction):
        max_offset = max(0, len(self.items_cache) - self.max_visible)
        self.scroll_offset = max(0, min(max_offset, self.scroll_offset + direction))
        self._rebuild_slots()

    def _rebuild_slots(self):
        # Remove old item components (keep bg and scroll buttons)
        components_to_keep = []
        for comp in self.active_components:
            # Keep back button and scroll buttons
            if hasattr(comp, "hitbox") and comp.hitbox.width == sh.per(10):
                components_to_keep.append(comp)
            elif hasattr(comp, "hitbox") and comp.hitbox.width == sh.per(6):
                components_to_keep.append(comp)

        # Clear and rebuild
        old_bgs = self.backgrounds.copy()
        old_scroll_active = components_to_keep.copy()

        self.active_components.clear()
        self.components.clear()

        self.backgrounds = old_bgs
        for comp in old_scroll_active:
            self.active_components.append(comp)

        self._build_item_slots()

    def _build_item_slots(self):
        from src.data.pokedex import PokeItems

        slot_height = self.bg_rect.height // (self.max_visible + 1)
        visible_items = self.items_cache[
            self.scroll_offset : self.scroll_offset + self.max_visible
        ]

        for idx, item in enumerate(visible_items):
            real_idx = self.scroll_offset + idx

            # Item button
            mbg = Button(
                "UI/raw/UI_Flat_Frame03a.png",
                "UI/raw/UI_Flat_Frame02a.png",
                self.bg_rect.left,
                self.bg_rect.top + slot_height * idx + sh.per(2),
                self.bg_rect.width - sh.per(10),
                crd(slot_height).per(90),
                lambda i=real_idx: self.action(i),
                nine_grid_margins=(45, 45, 45, 45),
            )
            mbg.img_button_default.image = color.recol(
                mbg.img_button_default.image, (120, 120, 120)
            )
            mbg.img_button_hover.image = color.recol(
                mbg.img_button_hover.image, (140, 140, 140)
            )
            self.add_active(mbg)

            # Get item data from PokeItems
            static_data = PokeItems.items.get(item["name"], {})
            sprite_path = item.get("sprite_path") or static_data.get(
                "sprite_path", "ingame_ui/potion.png"
            )

            # Icon background
            icon_bg_size = 56
            icon_bg = Sprite(
                "UI/raw/UI_Flat_Frame01a.png",
                (icon_bg_size, icon_bg_size),
                nine_grid_margins=(45, 45, 45, 45),
            )
            icon_bg.image = color.recol(icon_bg.image, (60, 60, 60))
            icon_bg.rect.left = mbg.hitbox.left + crd(mbg.hitbox.width).per(3)
            icon_bg.rect.centery = mbg.hitbox.centery
            self.add_passive(icon_bg)

            # Sprite
            sprite = Sprite(sprite_path, (48, 48))
            sprite.rect.center = icon_bg.rect.center
            self.add_passive(sprite)

            # Name
            name = Text(item["name"], 22, "azure")
            name.rect.topleft = (
                icon_bg.rect.right + crd(mbg.hitbox.width).per(3),
                mbg.hitbox.top + crd(slot_height).per(15),
            )
            self.add_passive(name)

            # Count
            count = Text(f"x{item['count']}", 20, "azure")
            count.rect.topleft = (
                name.rect.right + crd(mbg.hitbox.width).per(3),
                name.rect.top,
            )
            self.add_passive(count)

            # Description based on item type
            desc = self._get_item_description(static_data)
            if desc:
                desc_text = Text(desc, 16, "lightgray")
                desc_text.rect.topleft = (
                    icon_bg.rect.right + crd(mbg.hitbox.width).per(3),
                    name.rect.bottom + 2,
                )
                self.add_passive(desc_text)

    def _get_item_description(self, static_data):
        """Generate description based on item properties."""
        parts = []

        if "healing" in static_data:
            if static_data.get("revive"):
                parts.append(f"Revive +{static_data['healing']}HP")
            else:
                parts.append(f"Heal {static_data['healing']}HP")

        if "catch_rate" in static_data:
            rate = static_data["catch_rate"]
            if rate >= 255:
                parts.append("100% Catch")
            elif rate >= 2:
                parts.append(f"{rate}x Catch")
            elif rate < 1:
                parts.append(f"{rate}x Catch")
            else:
                parts.append("Pokeball")

        if "stat_boost" in static_data:
            stat = static_data["stat_boost"].upper()
            amount = static_data.get("boost_amount", 1)
            parts.append(f"+{amount} {stat}")

        if static_data.get("is_evolution_stone"):
            parts.append("Evolve Pokemon")

        return " | ".join(parts) if parts else ""

    def action(self, idx):
        if idx >= len(self.items_cache):
            return

        item = self.items_cache[idx]

        if item["count"] <= 0:
            return

        # Get the actual item from bag (not cache) and decrease count
        bag_items = getattr(gh, "gm").bag._items_data
        for bag_item in bag_items:
            if bag_item["name"] == item["name"]:
                bag_item["count"] -= 1
                break

        self.selected_item = item.copy()
        self.selected = True

        getattr(gh, "gm").bag.update_bag()

        if "ball" in item["name"].lower():
            setattr(scene_manager._current_scene, "catching", True)

    def close2(self):
        getattr(scene_manager._current_scene, "action_overlay").is_item = False
        self.is_open = False
