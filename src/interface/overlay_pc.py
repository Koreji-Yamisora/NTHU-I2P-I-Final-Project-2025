from src.interface.components import Overlay, Button
from src.sprites import Sprite, Text
from src.utils import GameSettings, crd, color
from src.data import pokedex
import pygame as pg
from src.core.gm_helper import gh
from src.core.services import input_manager
from src.utils import color


class PCOverlay(Overlay):
    def __init__(self):
        super().__init__(overlay_alpha=128)
        self.scroll_y = 0.0
        self.selected_idx = -1
        self._build_ui()

    def _build_ui(self):
        """Build/rebuild the UI for dynamic resolution support."""
        self.clear()
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        self.bgx_size = crd(sw.per(80))
        self.bgy_size = sh.per(80)
        self.bg = Sprite(
            "UI/raw/UI_Flat_Frame03a.png",
            (self.bgx_size, self.bgy_size),
            nine_grid_margins=(45, 45, 45, 45),
        )
        self.bg.image = color.recol(self.bg.image, (120, 120, 120))
        self.bg.rect.center = sw.per(50), sh.per(50)
        self.add_bg(self.bg)

        # Close Button
        x = self.bg.rect.right - self.bgx_size.per(6)
        y = self.bg.rect.top + self.bgx_size.per(2)
        self.back_button = Button(
            "UI/button_back.png",
            "UI/button_back_hover.png",
            x,
            y,
            self.bgx_size.per(5),
            self.bgx_size.per(5),
            lambda: self.close(),
        )
        self.add_active(self.back_button)

        # Labels
        self.party_label = Text("Party", 32, "Black")
        self.party_label.rect.topleft = (
            self.bg.rect.left + self.bgx_size.per(5),
            self.bg.rect.top + self.bgy_size.per(5),
        )
        self.add_passive(self.party_label)

        self.box_label = Text("PC Box", 32, "Black")
        self.box_label.rect.topleft = (
            self.bg.rect.centerx + self.bgx_size.per(5),
            self.bg.rect.top + self.bgy_size.per(5),
        )
        self.add_passive(self.box_label)

        # Area Rects
        self.party_area = pg.Rect(
            self.bg.rect.left + self.bgx_size.per(3),
            self.bg.rect.top + self.bgy_size.per(15),
            self.bgx_size.per(45),
            self.bgy_size.per(80),
        )
        self.box_area = pg.Rect(
            self.bg.rect.centerx + self.bgx_size.per(2),
            self.bg.rect.top + self.bgy_size.per(15),
            self.bgx_size.per(45),
            self.bgy_size.per(80),
        )

        # Scroll Setup (Box)
        self.scroll_speed = 30.0
        self.slot_height = self.box_area.height // 6  # Match Bag density (was 8)
        self.scrollbar_width = 10
        self.max_scroll = 0

        if gh.gm:
            self._create_slots()

    def open(self):
        super().open()
        self.selected_idx = -1
        if gh.gm:
            # Refresh data on open
            self._create_slots()

    def _create_slots(self):
        """Create Party and Box slots."""
        # Clean up
        self.active_components = [self.back_button]
        self.components = [
            self.party_label,
            self.box_label,
        ]  # bg is already in self.backgrounds
        self.party_components = []  # Stores (Button, Sprite, Text...) for Party
        self.box_slots = []  # Stores data for Box (to generate visible components)
        self.box_visible_components = []  # Currently visible Box components
        self.box_visible_buttons = []  # For update(dt)

        if not gh.gm:
            return
        monsters = gh.gm.bag._monsters_data

        # 1. Party Slots (Static)
        for i in range(min(6, len(monsters))):
            comps = self._create_single_slot(i, True)
            self.party_components.extend(comps)

        # 2. Box Slots (Scrollable)
        box_mons = monsters[6:]
        self.box_content_height = len(box_mons) * self.slot_height
        self.max_scroll = max(0, self.box_content_height - self.box_area.height)

        for i in range(len(box_mons)):
            real_idx = 6 + i
            # For box, we store data to generate components later
            # But _create_single_slot does generation. Let's adapt it.
            # actually we can store the data dict needed to recreate.
            # adapting _create_single_slot to just return data for box?
            # or just use it to generate fixed data.
            # Let's simplify: _create_single_slot returns slot_data dict for box
            slot_data = self._create_single_slot(real_idx, False)
            self.box_slots.append(slot_data)

        self._update_positions()

    def _create_single_slot(self, idx, is_party):
        mon = gh.gm.bag._monsters_data[idx]

        rect_area = self.party_area if is_party else self.box_area

        # Get types
        types = pokedex.data[mon["id"]]["type"]
        type_sprites = []

        from src.data.bag import TYPE_MAP

        if is_party:
            y = rect_area.top + (idx * self.slot_height)
        else:
            y = rect_area.top + ((idx - 6) * self.slot_height)

        w = rect_area.width - (self.scrollbar_width if not is_party else 0) - 5

        # Highlight selected
        frame_img = "UI/raw/UI_Flat_Frame03a.png"
        if idx == self.selected_idx:
            frame_img = "UI/raw/UI_Flat_Frame02a.png"

        btn = Button(
            frame_img,
            "UI/raw/UI_Flat_Frame02a.png",
            rect_area.left,
            y,
            w,
            self.slot_height,
            lambda idx=idx: self.on_click(idx),
            nine_grid_margins=(45, 45, 45, 45),
        )
        btn.img_button_default.image = color.recol(
            btn.img_button_default.image, (120, 120, 120)
        )
        btn.img_button_hover.image = color.recol(
            btn.img_button_hover.image, (120, 120, 120)
        )

        s_path = pokedex.data[mon["id"]]["sprite_path"]

        type_sprites = []

        from src.data.bag import TYPE_MAP

        if is_party:
            # Match Bag Layout: Sprite Left, Text Right

            # Sprite: Left Side (15%)
            sprite = Sprite(s_path, (72, 72))
            sprite.rect.center = (btn.hitbox.left + crd(w).per(15), btn.hitbox.centery)

            # Text moved to Right (30%)
            name = Text(mon["name"], 24, "azure")
            name.rect.topleft = (
                btn.hitbox.left + crd(w).per(30),
                btn.hitbox.top + crd(self.slot_height).per(5),
            )

            # Add Type Icons for Party
            start_x = name.rect.right + 10
            for t_abbr in types:
                if not t_abbr:
                    continue
                t_name = TYPE_MAP.get(t_abbr)
                if t_name:
                    ts = Sprite(f"type/{t_name}.png", (16, 16))
                    ts.rect.midleft = (start_x, name.rect.centery)
                    start_x += 35
                    type_sprites.append(ts)

            curr_hp = mon.get("chp", mon.get("hp", 0))
            max_hp = mon.get("hp", 0)
            hp = Text(f"HP: {curr_hp}/{max_hp}", 24, "azure")
            hp.rect.topleft = (
                btn.hitbox.left + crd(w).per(30),
                btn.hitbox.top + crd(self.slot_height).per(35),
            )

            level = Text(f"Level: {mon['level']}", 24, "azure")
            level.rect.topleft = (
                btn.hitbox.left + crd(w).per(30),
                btn.hitbox.top + crd(self.slot_height).per(65),
            )

            # Return list of components for Party
            return [btn, sprite, name, hp, level] + type_sprites

        else:
            # Box slots: Return data dict to be managed by _update_positions
            slot_data = {}
            slot_data["btn"] = btn  # Pre-create button but position will update
            slot_data["base_y"] = y

            sprite = Sprite(s_path, (48, 48))
            sprite.rect.midleft = (btn.hitbox.left + 20, btn.hitbox.centery)

            name = Text(f"{mon['name']} Lv.{mon['level']}", 24, "azure")
            name.rect.midleft = (sprite.rect.right + 10, btn.hitbox.centery)

            # Add Type Icons for Box
            start_x = name.rect.right + 10
            for t_abbr in types:
                if not t_abbr:
                    continue
                t_name = TYPE_MAP.get(t_abbr)
                if t_name:
                    ts = Sprite(f"type/{t_name}.png", (12, 12))  # Smaller for box?
                    ts.rect.midleft = (start_x, name.rect.centery)
                    start_x += 26
                    type_sprites.append(ts)

            slot_data["sprite"] = sprite
            slot_data["name"] = name
            slot_data["type_sprites"] = type_sprites
            return slot_data

    def _update_positions(self):
        """Update box visible components."""
        self.box_visible_components = []
        self.box_visible_buttons = []

        b = self.box_area
        for slot in self.box_slots:
            y_pos = slot["base_y"] - self.scroll_y

            if b.top - self.slot_height <= y_pos <= b.bottom:
                btn = slot["btn"]
                btn.hitbox.top = int(y_pos)
                btn.img_button.rect.top = int(y_pos)

                sprite = slot["sprite"]
                sprite.rect.midleft = (btn.hitbox.left + 20, btn.hitbox.centery)

                name = slot["name"]
                name.rect.midleft = (sprite.rect.right + 10, btn.hitbox.centery)

                type_sprites = slot.get("type_sprites", [])
                for ts in type_sprites:
                    ts.rect.centery = btn.hitbox.centery
                    # Right of name + offset is cleaner, but keeping relative x is fine as stored in create

                self.box_visible_components.extend([btn, sprite, name] + type_sprites)
                self.box_visible_buttons.append(btn)

    def on_click(self, idx):
        if self.selected_idx == -1:
            self.selected_idx = idx
            self._create_slots()  # Re-create to update highlight
        else:
            # Swap
            if self.selected_idx != idx:
                (
                    gh.gm.bag._monsters_data[self.selected_idx],
                    gh.gm.bag._monsters_data[idx],
                ) = (
                    gh.gm.bag._monsters_data[idx],
                    gh.gm.bag._monsters_data[self.selected_idx],
                )
                gh.gm.bag.update_bag()

            self.selected_idx = -1
            self._create_slots()

    def update_content(self, dt):
        if input_manager.key_pressed(pg.K_ESCAPE):
            self.close()

        # Scroll
        changed = False
        if input_manager.mouse_wheel != 0:
            mx, my = input_manager.mouse_pos
            if self.box_area.collidepoint(mx, my):
                self.scroll_y -= input_manager.mouse_wheel * self.scroll_speed
                changed = True

        if changed:
            self.scroll_y = max(0, min(self.max_scroll, self.scroll_y))
            self._update_positions()

        # Navigation
        nav_changed = False
        nav_dir = None
        if input_manager.key_pressed(pg.K_UP) or input_manager.button_pressed(11):
            nav_dir = "UP"
        elif input_manager.key_pressed(pg.K_DOWN) or input_manager.button_pressed(12):
            nav_dir = "DOWN"
        elif input_manager.key_pressed(pg.K_LEFT) or input_manager.button_pressed(13):
            nav_dir = "LEFT"
        elif input_manager.key_pressed(pg.K_RIGHT) or input_manager.button_pressed(14):
            nav_dir = "RIGHT"
        elif input_manager.key_pressed(pg.K_RETURN) or input_manager.button_pressed(
            0
        ):  # Confirm/Swap
            if self.selected_idx != -1:
                # Simulate click to swap
                self.on_click(self.selected_idx)
                # self.on_click handles resetting selected_idx if swapped.
                # But if we want to "pick up" and "drop", on_click does that logic.
                pass

        if nav_dir:
            if self.selected_idx == -1:
                self.selected_idx = 0
                nav_changed = True
            else:
                is_party = self.selected_idx < 6
                total_party = min(6, len(gh.gm.bag._monsters_data))
                total_mons = len(gh.gm.bag._monsters_data)

                if nav_dir == "UP":
                    if is_party:
                        self.selected_idx = max(0, self.selected_idx - 1)
                    else:
                        self.selected_idx = max(6, self.selected_idx - 1)
                    nav_changed = True
                elif nav_dir == "DOWN":
                    if is_party:
                        self.selected_idx = min(total_party - 1, self.selected_idx + 1)
                    else:
                        self.selected_idx = min(total_mons - 1, self.selected_idx + 1)
                    nav_changed = True
                elif nav_dir == "RIGHT":
                    if is_party and total_mons > 6:
                        # Move to first box slot
                        self.selected_idx = 6
                        nav_changed = True
                elif nav_dir == "LEFT":
                    if not is_party:
                        # Move to same row in party? Or first party slot?
                        # Party has at least 1 mon usually.
                        self.selected_idx = 0
                        nav_changed = True

            if nav_changed:
                # Auto scroll if in box
                if self.selected_idx >= 6:
                    box_idx = self.selected_idx - 6
                    slot_top = self.slot_height * box_idx
                    slot_bottom = slot_top + self.slot_height

                    if slot_top < self.scroll_y:
                        self.scroll_y = slot_top
                        self._update_positions()
                    elif slot_bottom > self.scroll_y + self.box_area.height:
                        self.scroll_y = slot_bottom - self.box_area.height
                        self._update_positions()

                self._create_slots()  # Refresh UI frames

        # Update buttons
        for c in self.active_components:
            if isinstance(c, Button):
                c.update(dt)

        for c in self.party_components:
            if isinstance(c, Button):
                c.update(dt)

        for c in self.box_visible_buttons:
            c.update(dt)

    def draw_content(self, screen: pg.Surface):
        """Draw with clipping for Box."""
        if self.is_open:
            if self.overlay_alpha:
                screen.blit(self.dark_overlay, (0, 0))
            for b in self.backgrounds:
                b.draw(screen)

            # 1. Draw Global UI
            for c in self.active_components:
                c.draw(screen)
            for t in self.components:
                t.draw(screen)

            # 2. Draw Party (Static)
            for c in self.party_components:
                c.draw(screen)

            # 3. Clip and Draw Box
            prev_clip = screen.get_clip()
            screen.set_clip(self.box_area)

            for c in self.box_visible_components:
                c.draw(screen)

            screen.set_clip(prev_clip)

            # 3. Scrollbar
            if self.max_scroll > 0:
                b = self.box_area
                track_rect = pg.Rect(
                    b.right - self.scrollbar_width,
                    b.top,
                    self.scrollbar_width,
                    b.height,
                )
                pg.draw.rect(screen, (60, 60, 60), track_rect)

                thumb_height = max(
                    20, int(b.height * (b.height / self.box_content_height))
                )
                scroll_ratio = (
                    self.scroll_y / self.max_scroll if self.max_scroll > 0 else 0
                )
                thumb_y = b.top + int((b.height - thumb_height) * scroll_ratio)
                thumb_rect = pg.Rect(
                    b.right - self.scrollbar_width,
                    thumb_y,
                    self.scrollbar_width,
                    thumb_height,
                )
                pg.draw.rect(screen, (150, 150, 150), thumb_rect)
