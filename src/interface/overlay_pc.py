from src.interface.components import Overlay, Button
from src.sprites import Sprite, Text
from src.utils import GameSettings, crd, color
from src.data import pokedex
import pygame as pg
from src.core.gm_helper import gh
from src.core.services import input_manager


from src.interface.stats_graph import StatsHexagon


class PCOverlay(Overlay):
    def __init__(self):
        super().__init__(overlay_alpha=128)
        self.scroll_y = 0.0
        self.selected_idx = -1
        # Double-click detection
        self._last_click_idx = -1
        self._last_click_time = 0.0
        self._double_click_threshold = 0.3  # seconds
        # Stats detail panel state
        self._detail_open = False
        self._detail_mon = None
        self._detail_page = 0  # 0=Stats, 1=Moves, 2=Info
        self._build_ui()

    def _build_ui(self):
        """Build/rebuild the UI for dynamic resolution support."""
        self.clear()
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        self.bgx_size = crd(sw.per(90))  # Increase total width
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
        x = self.bg.rect.right - self.bgx_size.per(4)
        y = self.bg.rect.top + self.bgx_size.per(2)
        self.back_button = Button(
            "UI/button_back.png",
            "UI/button_back_hover.png",
            x,
            y,
            self.bgx_size.per(3),
            self.bgx_size.per(3),
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
            self.bg.rect.left + self.bgx_size.per(60),  # Right side
            self.bg.rect.top + self.bgy_size.per(5),
        )
        self.add_passive(self.box_label)

        # Area Rects - Layout: Party (25%) | Stats (30%) | Box (40%)

        # Party
        self.party_area = pg.Rect(
            self.bg.rect.left + self.bgx_size.per(3),
            self.bg.rect.top + self.bgy_size.per(15),
            self.bgx_size.per(25),
            self.bgy_size.per(80),
        )

        # Stats Middle (used for details button position, hex only shown in detail panel)
        self.stats_area = pg.Rect(
            self.bg.rect.left + self.bgx_size.per(30),
            self.bg.rect.top + self.bgy_size.per(15),
            self.bgx_size.per(28),
            self.bgy_size.per(50),
        )

        # Box
        self.box_area = pg.Rect(
            self.bg.rect.left + self.bgx_size.per(60),
            self.bg.rect.top + self.bgy_size.per(15),
            self.bgx_size.per(37),
            self.bgy_size.per(80),
        )

        # Stats Hexagon (only used in detail panel, not main page)
        self.stats_hex = StatsHexagon(self.stats_area)

        # Details Button (in stats area since hex is not shown in main page)
        details_btn_w = self.stats_area.width
        details_btn_h = self.bgy_size.per(8)
        self.details_button = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            self.stats_area.left,
            self.stats_area.bottom + self.bgy_size.per(2),
            details_btn_w,
            details_btn_h,
            lambda: self._open_detail_selected(),
            nine_grid_margins=(14, 14, 14, 14),
        )
        self.details_button.img_button_default.image = color.recol(
            self.details_button.img_button_default.image, (80, 120, 160)
        )
        self.details_button.img_button_hover.image = color.recol(
            self.details_button.img_button_hover.image, (100, 150, 200)
        )
        self.add_active(self.details_button)

        self.details_label = Text("View Details", 20, "white")
        self.details_label.rect.center = self.details_button.hitbox.center
        self.add_passive(self.details_label)

        # Scroll Setup (Box)
        self.scroll_speed = 30.0
        self.slot_height = self.box_area.height // 6
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
            if gh.gm.bag._monsters_data:
                self.stats_hex.set_stats(gh.gm.bag._monsters_data[0])

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
        self.party_buttons = []  # Track party buttons

        if not gh.gm:
            return
        monsters = gh.gm.bag._monsters_data

        # 1. Party Slots (Static)
        for i in range(min(6, len(monsters))):
            comps, btn = self._create_single_slot(i, True)
            self.party_components.extend(comps)
            self.party_buttons.append(btn)

        # 2. Box Slots (Scrollable)
        box_mons = monsters[6:]
        self.box_content_height = len(box_mons) * self.slot_height
        self.max_scroll = max(0, self.box_content_height - self.box_area.height)

        for i in range(len(box_mons)):
            real_idx = 6 + i
            slot_data = self._create_single_slot(real_idx, False)
            self.box_slots.append(slot_data)

        self._update_positions()

    def _create_single_slot(self, idx, is_party):
        mon = gh.gm.bag._monsters_data[idx]

        rect_area = self.party_area if is_party else self.box_area

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
        if is_party:
            # Compact Party Layout for 3-column view
            # Left: Sprite. Right: Name/Level over HP.
            sprite = Sprite(s_path, (48, 48))
            sprite.rect.midleft = (btn.hitbox.left + 10, btn.hitbox.centery)

            name = Text(mon["name"], 24, "azure")
            name.rect.topleft = (sprite.rect.right + 5, btn.hitbox.top + 10)

            level = Text(f"Lv.{mon['level']}", 20, "white")
            level.rect.bottomleft = (sprite.rect.right + 5, btn.hitbox.bottom - 10)

            # Types check
            # Maybe skip for compact view? Or add small icons

            return [btn, sprite, name, level], btn  # Return comps and button

        else:
            # Box slots
            slot_data = {}
            slot_data["btn"] = btn
            slot_data["base_y"] = y

            sprite = Sprite(s_path, (40, 40))
            sprite.rect.midleft = (btn.hitbox.left + 5, btn.hitbox.centery)

            name = Text(f"{mon['name']}", 22, "azure")
            name.rect.midleft = (sprite.rect.right + 5, btn.hitbox.centery)

            slot_data["sprite"] = sprite
            slot_data["name"] = name
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
                sprite.rect.midleft = (btn.hitbox.left + 5, btn.hitbox.centery)

                name = slot["name"]
                name.rect.midleft = (sprite.rect.right + 5, btn.hitbox.centery)

                self.box_visible_components.extend([btn, sprite, name])
                self.box_visible_buttons.append(btn)

    def on_click(self, idx):
        # If clicking on already selected pokemon, open detail view
        if self.selected_idx == idx:
            self._open_detail(idx)
            return

        if self.selected_idx == -1:
            # First click - select this pokemon
            self.selected_idx = idx
            self._create_slots()
            mon = gh.gm.bag._monsters_data[idx]
            self.stats_hex.set_stats(mon)
        else:
            # Different pokemon clicked while one is selected - swap them
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
            mon = gh.gm.bag._monsters_data[idx]
            self.stats_hex.set_stats(mon)

    def _open_detail(self, idx):
        """Open the detail view for a Pokemon."""
        self._detail_open = True

        # Use _monsters (calculated stats) for party pokemon (idx < 6)
        # For box pokemon (idx >= 6), we need to use _monsters_data and calculate stats
        if idx < 6 and idx < len(gh.gm.bag._monsters):
            # Party pokemon - use calculated stats from _monsters
            self._detail_mon = gh.gm.bag._monsters[idx]
        else:
            # Box pokemon - calculate stats from _monsters_data
            mon_data = gh.gm.bag._monsters_data[idx]
            base = pokedex.data.get(mon_data["id"], {})
            level = mon_data["level"]
            iv = mon_data.get("IV", {})
            ev = mon_data.get("EV", {})

            # Calculate stats using the same formula as bag.my_mon()
            hp = (
                int(
                    (2 * base.get("hp", 1) + iv.get("hp", 0) + ev.get("hp", 0) / 4)
                    * level
                    / 100
                )
                + level
                + 10
            )
            atk = (
                int(
                    (2 * base.get("atk", 1) + iv.get("atk", 0) + ev.get("atk", 0) / 4)
                    * level
                    / 100
                )
                + 5
            )
            defen = (
                int(
                    (2 * base.get("def", 1) + iv.get("def", 0) + ev.get("def", 0) / 4)
                    * level
                    / 100
                )
                + 5
            )
            spa = (
                int(
                    (2 * base.get("spa", 1) + iv.get("spa", 0) + ev.get("spa", 0) / 4)
                    * level
                    / 100
                )
                + 5
            )
            spd = (
                int(
                    (2 * base.get("spd", 1) + iv.get("spd", 0) + ev.get("spd", 0) / 4)
                    * level
                    / 100
                )
                + 5
            )
            spe = (
                int(
                    (2 * base.get("spe", 1) + iv.get("spe", 0) + ev.get("spe", 0) / 4)
                    * level
                    / 100
                )
                + 5
            )

            self._detail_mon = {
                **mon_data,
                "hp": hp,
                "atk": atk,
                "def": defen,
                "spa": spa,
                "spd": spd,
                "spe": spe,
                "chp": mon_data.get("hp", hp),  # Current HP
                "moves": mon_data.get("move", []),
            }

        self._detail_page = 0
        self.stats_hex.set_stats(self._detail_mon)

    def _close_detail(self):
        """Close the detail view."""
        self._detail_open = False
        self._detail_mon = None
        self._detail_page = 0

    def _next_detail_page(self):
        """Go to next detail page."""
        self._detail_page = (self._detail_page + 1) % 3

    def _prev_detail_page(self):
        """Go to previous detail page."""
        self._detail_page = (self._detail_page - 1) % 3

    def _open_detail_selected(self):
        """Open detail for the currently selected/viewed monster."""
        if not gh.gm or not gh.gm.bag._monsters_data:
            return
        # Use selected_idx if valid, otherwise use the first monster
        idx = self.selected_idx if self.selected_idx >= 0 else 0
        if idx < len(gh.gm.bag._monsters_data):
            self._open_detail(idx)

    def update_content(self, dt):
        # Handle detail panel mode first
        if self._detail_open:
            if input_manager.key_pressed(pg.K_ESCAPE):
                self._close_detail()
                return
            if input_manager.key_pressed(pg.K_LEFT) or input_manager.button_pressed(13):
                self._prev_detail_page()
            elif input_manager.key_pressed(pg.K_RIGHT) or input_manager.button_pressed(
                14
            ):
                self._next_detail_page()
            self.stats_hex.update(dt)
            return

        if input_manager.key_pressed(pg.K_ESCAPE):
            self.close()

        # Update stats hexagon
        self.stats_hex.update(dt)

        # Check hover for stats update (if nothing selected)
        # This provides "inspect" functionality on hover
        if self.selected_idx == -1:
            hovered_idx = -1
            mx, my = input_manager.mouse_pos

            # Check party buttons
            for i, btn in enumerate(self.party_buttons):
                if btn.hitbox.collidepoint(mx, my):
                    hovered_idx = i
                    break

            # Check box buttons
            if hovered_idx == -1:
                # We need to map visible buttons back to index
                # This is tricky because visible_buttons don't store index directly
                # But _create_single_slot assigns a lambda with idx
                # We can't easily extract it from lambda
                # Simpler: Iterate through box buttons and check collision
                # But we need index to get monster data.
                # Actually, iterate visible buttons, find match, but we need index mapping.
                # Let's rely on stored list indices.
                # box_visible_buttons matches box_slots subset? No.
                # We can add 'idx' attribute to button subclass or just assign it.
                pass
                # Implementing hover for box is harder without refactor.
                # Let's stick to click for now.

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
                    if is_party:
                        # Move to first box slot or same row
                        self.selected_idx = 6
                        nav_changed = True
                elif nav_dir == "LEFT":
                    if not is_party:
                        # Move to party
                        self.selected_idx = 0
                        nav_changed = True

            if nav_changed:
                mon = gh.gm.bag._monsters_data[self.selected_idx]
                self.stats_hex.set_stats(mon)

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

            # 3. (Hex graph removed from main page - only shown in detail panel)

            # 4. Clip and Draw Box
            prev_clip = screen.get_clip()
            screen.set_clip(self.box_area)

            for c in self.box_visible_components:
                c.draw(screen)

            screen.set_clip(prev_clip)

            # 5. Scrollbar
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

            # 6. Detail Panel (overlay on top)
            if self._detail_open and self._detail_mon:
                self._draw_detail_panel(screen)

    def _draw_detail_panel(self, screen: pg.Surface):
        """Draw the detail panel with pages."""
        sw = GameSettings.SCREEN_WIDTH
        sh = GameSettings.SCREEN_HEIGHT

        # Panel background
        panel_w = int(sw * 0.6)
        panel_h = int(sh * 0.7)
        panel_x = (sw - panel_w) // 2
        panel_y = (sh - panel_h) // 2
        panel_rect = pg.Rect(panel_x, panel_y, panel_w, panel_h)

        # Dark overlay
        overlay = pg.Surface((sw, sh), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Panel bg
        pg.draw.rect(screen, (80, 80, 90), panel_rect, border_radius=10)
        pg.draw.rect(screen, (120, 120, 130), panel_rect, 3, border_radius=10)

        # Page tabs
        tab_names = ["Stats", "Moves", "Info"]
        tab_w = panel_w // 3
        font = pg.font.SysFont("Arial", 20, bold=True)
        for i, name in enumerate(tab_names):
            tab_rect = pg.Rect(panel_x + i * tab_w, panel_y, tab_w, 40)
            tab_color = (100, 150, 200) if i == self._detail_page else (60, 60, 70)
            pg.draw.rect(screen, tab_color, tab_rect)
            txt = font.render(name, True, (255, 255, 255))
            screen.blit(txt, txt.get_rect(center=tab_rect.center))

        # Content area
        content_rect = pg.Rect(panel_x + 20, panel_y + 60, panel_w - 40, panel_h - 100)

        mon = self._detail_mon

        if self._detail_page == 0:
            # Stats page - draw hexagon
            hex_rect = pg.Rect(
                content_rect.left,
                content_rect.top,
                content_rect.width,
                content_rect.height - 60,
            )
            self.stats_hex.rect = hex_rect
            self.stats_hex.draw(screen)

            # Stat values as text below
            stats_font = pg.font.SysFont("Arial", 16)
            stat_names = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]
            stat_keys = ["hp", "atk", "def", "spa", "spd", "spe"]
            y_offset = content_rect.bottom - 50
            for i, (name, key) in enumerate(zip(stat_names, stat_keys)):
                val = mon.get(key, 0)
                txt = stats_font.render(f"{name}: {val}", True, (200, 200, 200))
                x = content_rect.left + (i % 3) * (content_rect.width // 3)
                y = y_offset + (i // 3) * 25
                screen.blit(txt, (x, y))

        elif self._detail_page == 1:
            # Moves page
            title_font = pg.font.SysFont("Arial", 24, bold=True)
            move_font = pg.font.SysFont("Arial", 18)

            title = title_font.render("Moves", True, (255, 255, 255))
            screen.blit(
                title, (content_rect.centerx - title.get_width() // 2, content_rect.top)
            )

            moves = mon.get("moves", []) or mon.get("move", [])
            for i, move in enumerate(moves[:4]):
                move_name = move if isinstance(move, str) else move.get("name", "???")
                txt = move_font.render(f"• {move_name}", True, (200, 200, 200))
                screen.blit(
                    txt, (content_rect.left + 20, content_rect.top + 50 + i * 40)
                )

        elif self._detail_page == 2:
            # Info page
            title_font = pg.font.SysFont("Arial", 24, bold=True)
            info_font = pg.font.SysFont("Arial", 18)

            title = title_font.render(mon.get("name", "???"), True, (255, 255, 255))
            screen.blit(
                title, (content_rect.centerx - title.get_width() // 2, content_rect.top)
            )

            y = content_rect.top + 50
            info_lines = [
                f"Level: {mon.get('level', 1)}",
                f"HP: {mon.get('chp', 0)} / {mon.get('hp', 0)}",
                f"ID: {mon.get('id', '???')}",
            ]

            types = pokedex.data.get(mon.get("id", ""), {}).get("type", [])
            if types:
                info_lines.append(f"Types: {', '.join([t for t in types if t])}")

            for line in info_lines:
                txt = info_font.render(line, True, (200, 200, 200))
                screen.blit(txt, (content_rect.left + 20, y))
                y += 30

        # Navigation hint
        hint_font = pg.font.SysFont("Arial", 14)
        hint = hint_font.render(
            "← → to switch pages | ESC to close", True, (150, 150, 150)
        )
        screen.blit(
            hint, (panel_rect.centerx - hint.get_width() // 2, panel_rect.bottom - 30)
        )
