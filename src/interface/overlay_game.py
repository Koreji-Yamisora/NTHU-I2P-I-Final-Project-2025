from __future__ import annotations
import pygame as pg
from src.interface.components import Overlay, Button, Slider, ToggleButton
from src.core.services import sound_manager, resource_manager
from src.core.managers import GameManager
from src.utils import GameSettings, Logger, crd
from src.utils.settings import RESOLUTIONS
from typing import Callable
from src.sprites import Sprite, Text
from src.core.services import input_manager
from src.core.gm_helper import gh
from src.data import pokeitems
from src.utils import color


class SettingOverlay(Overlay):
    """Setting  overlay UI component."""

    bg: Sprite

    def __init__(self):
        super().__init__(overlay_alpha=128)
        self._build_ui()

    def _build_ui(self):
        """Build all UI elements based on current GameSettings resolution."""
        self.clear()  # Clear existing components

        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        # Reduced background size (approx 40% width, 70% height)
        self.bgx = crd(sw.per(40))
        self.bgy = crd(sh.per(70))
        self.bg = Sprite(
            "UI/raw/UI_Flat_Frame03a.png",
            (self.bgx, self.bgy),
            nine_grid_margins=(45, 45, 45, 45),
        )
        self.bg.image = color.recol(self.bg.image, (120, 120, 120))
        self.bg.rect.center = sw.per(50), sh.per(50)
        self.add_bg(self.bg)

        # Center X of the background
        cx = crd(self.bg.rect.centerx)
        # Top Y of the background
        top_y = crd(self.bg.rect.top)

        # Close/Back Button (Top Right of Background)
        back_button = Button(
            "UI/button_back.png",
            "UI/button_back_hover.png",
            self.bg.rect.right - self.bgx.per(10),
            self.bg.rect.top + self.bgx.per(5),
            self.bgx.per(8),
            self.bgx.per(8),
            lambda: self.close(),
        )
        self.add_active(back_button)

        # --- Audio Settings ---
        current_y = top_y + self.bgy.per(15)
        # Dynamic spacing based on available height
        spacing = self.bgy.per(8)

        # Mute Toggle
        mute_label = Text("Mute Audio", 24, "azure")
        mute_label.rect.center = (cx, current_y)
        self.add_passive(mute_label)

        current_y += self.bgy.per(5)

        def mute_audio(state):
            """Mute Audio."""
            GameSettings.AUDIO_MUTE = not state
            sound_manager.refresh()
            if sound_manager.current_bgm:
                if GameSettings.AUDIO_MUTE:
                    sound_manager.current_bgm.set_volume(0)
                else:
                    sound_manager.current_bgm.set_volume(GameSettings.BGM_VOLUME)

        toggle_button = ToggleButton(
            "UI/raw/UI_Flat_ToggleOff03a.png",
            "UI/raw/UI_Flat_ToggleOn03a.png",
            cx,
            current_y,
            64,
            32,
            state=GameSettings.AUDIO_MUTE,
            action=mute_audio,
        )
        self.add_active(toggle_button)

        current_y += spacing

        # Music Slider
        music_label = Text("Music Volume", 24, "azure")
        music_label.rect.center = (cx, current_y)
        self.add_passive(music_label)

        current_y += self.bgy.per(5)

        def set_music_vol(state):
            """Set music vol."""
            GameSettings.BGM_VOLUME = state
            if sound_manager.current_bgm and not GameSettings.AUDIO_MUTE:
                sound_manager.current_bgm.set_volume(state)

        slider_width = self.bgx.per(50)
        gx = crd(slider_width)

        music_slider = Slider(
            "UI/raw/UI_Flat_FrameSlot03b.png",
            "UI/raw/UI_Flat_BarFill01g.png",
            "UI/raw/UI_Flat_BarFill01e.png",
            "UI/raw/UI_Flat_FrameSlot03a.png",
            cx,
            current_y,
            gx,
            gx.per(8),
            gx.per(8),
            gx.per(17),
            state=GameSettings.BGM_VOLUME,
            action=set_music_vol,
        )
        self.add_active(music_slider)

        current_y += spacing

        # SFX Slider
        sfx_label = Text("SFX Volume", 24, "azure")
        sfx_label.rect.center = (cx, current_y)
        self.add_passive(sfx_label)

        current_y += self.bgy.per(5)

        def set_sfx_vol(state):
            """Set sfx vol."""
            GameSettings.SFX_VOLUME = state

        sfx_slider = Slider(
            "UI/raw/UI_Flat_FrameSlot03b.png",
            "UI/raw/UI_Flat_BarFill01g.png",
            "UI/raw/UI_Flat_BarFill01e.png",
            "UI/raw/UI_Flat_FrameSlot03a.png",
            cx,
            current_y,
            gx,
            gx.per(8),
            gx.per(8),
            gx.per(17),
            state=GameSettings.SFX_VOLUME,
            action=set_sfx_vol,
        )
        self.add_active(sfx_slider)

        current_y += spacing * 1.5

        # --- Hitbox Toggle ---
        hitbox_label = Text("Show Hitboxes", 24, "azure")
        hitbox_label.rect.center = (cx, current_y)
        self.add_passive(hitbox_label)

        current_y += self.bgy.per(5)

        def toggle_hitboxes(state):
            GameSettings.DRAW_HITBOXES = state

        hitbox_btn = ToggleButton(
            "UI/raw/UI_Flat_ToggleOff03a.png",
            "UI/raw/UI_Flat_ToggleOn03a.png",
            cx,
            current_y,
            64,
            32,
            state=GameSettings.DRAW_HITBOXES,
            action=toggle_hitboxes,
        )
        self.add_active(hitbox_btn)

        current_y += spacing

        # --- FPS Selector ---
        fps_label = Text("Target FPS", 24, "azure")
        fps_label.rect.center = (cx, current_y)
        self.add_passive(fps_label)

        current_y += self.bgy.per(5)

        self._update_fps_text()
        self.fps_text.rect.center = (cx, current_y)
        self.add_passive(self.fps_text)

        # FPS Buttons
        btn_size = 40
        fps_offset = 60  # px offset from center

        fps_left_btn = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            cx - fps_offset - btn_size // 2,
            current_y - btn_size // 2,
            btn_size,
            btn_size,
            lambda: self._change_fps(-1),
            nine_grid_margins=(14, 14, 14, 14),
        )
        fps_left_btn.img_button_default.image = color.recol(
            fps_left_btn.img_button_default.image, (120, 120, 120)
        )
        fps_left_btn.img_button_hover.image = color.recol(
            fps_left_btn.img_button_hover.image, (120, 120, 120)
        )
        self.add_active(fps_left_btn)
        left_arrow = Text("<", 24, "Black")
        left_arrow.rect.center = fps_left_btn.hitbox.center
        self.add_passive(left_arrow)

        fps_right_btn = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            cx + fps_offset - btn_size // 2,
            current_y - btn_size // 2,
            btn_size,
            btn_size,
            lambda: self._change_fps(1),
            nine_grid_margins=(14, 14, 14, 14),
        )
        fps_right_btn.img_button_default.image = color.recol(
            fps_right_btn.img_button_default.image, (120, 120, 120)
        )
        fps_right_btn.img_button_hover.image = color.recol(
            fps_right_btn.img_button_hover.image, (120, 120, 120)
        )
        self.add_active(fps_right_btn)
        right_arrow = Text(">", 24, "Black")
        right_arrow.rect.center = fps_right_btn.hitbox.center
        self.add_passive(right_arrow)

        current_y += spacing

        # --- LAN Server ---
        lan_label = Text("Open to LAN", 24, "azure")
        lan_label.rect.center = (cx, current_y)
        self.add_passive(lan_label)

        current_y += self.bgy.per(5)

        def toggle_server(state):
            if state:  # ToggleButton implementation toggles state AFTER action?
                # No, ToggleButton.update calls action(self.state) then toggle().
                # Wait, ToggleButton passes the OLD state?
                # src/interface/components/button.py: self.action(self.state); self.toggle()
                # If state is False (Off), it calls action(False), then sets to True.
                # So if we want to turn ON, we need to handle False input implies "Turn On"?
                # Or does it mean "Current state is False, so do On logic"?
                # Let's check mute_audio: GameSettings.AUDIO_MUTE = not state.
                # If state is False (unmuted), new state will be True (muted).
                # So action(False) -> enable mute.
                # Here: action(False) -> start server. action(True) -> stop server.
                if not state:
                    gh.start_server_process()
                    # Also auto-connect?
                    if gh.online_manager:
                        gh.online_manager.ws_url = "ws://localhost:8989"
                        gh.online_manager.start()
                else:
                    gh.stop_server_process()

        is_server_running = (
            getattr(gh, "server_process", None) is not None
            and gh.server_process.poll() is None
        )

        lan_btn = ToggleButton(
            "UI/raw/UI_Flat_ToggleOff03a.png",
            "UI/raw/UI_Flat_ToggleOn03a.png",
            cx,
            current_y,
            64,
            32,
            state=is_server_running,
            action=toggle_server,
        )
        self.add_active(lan_btn)
        bottom_y = self.bg.rect.bottom - self.bgy.per(10)
        btn_spacing = self.bgx.per(25)

        save_button = Button(
            "UI/button_save.png",
            "UI/button_save_hover.png",
            cx - btn_spacing,
            bottom_y - 37,  # Center vertically on bottom_y
            75,
            75,
            lambda: gh.save(),
        )
        self.add_active(save_button)

        exit_button = Button(
            "UI/button_back.png",
            "UI/button_back_hover.png",
            cx,
            bottom_y - 37,
            75,
            75,
            lambda: self.exit_to_menu(),
        )
        self.add_active(exit_button)

        load_button = Button(
            "UI/button_load.png",
            "UI/button_load_hover.png",
            cx + btn_spacing,
            bottom_y - 37,
            75,
            75,
            lambda: gh.load(),
        )
        self.add_active(load_button)

        exit_label = Text("Menu", 18, "azure")
        exit_label.rect.center = (cx, bottom_y + 30)
        self.add_passive(exit_label)

    def _update_fps_text(self):
        """Update FPS text display."""
        if hasattr(self, "fps_text"):
            self.fps_text.change_text(str(GameSettings.FPS), "center")
        else:
            self.fps_text = Text(str(GameSettings.FPS), 24, "azure")

    def _change_fps(self, direction: int):
        """Change FPS setting."""
        options = [24, 30, 60]
        try:
            current_idx = options.index(GameSettings.FPS)
        except ValueError:
            current_idx = 2  # Default to 60 if odd value

        new_idx = (current_idx + direction) % len(options)
        GameSettings.FPS = options[new_idx]
        self._update_fps_text()

    def exit_to_menu(self):
        """Exit to the main menu screen"""
        from src.core.services import scene_manager

        self.close()
        scene_manager.change_scene("menu")

    def update_content(self, dt: float) -> None:
        """Update content."""
        if gh.gm:
            gh.gm.bag.update(dt)

        if input_manager.key_pressed(pg.K_ESCAPE):
            input_manager.reset()
            self.close()


class Inventory(Overlay):
    """Inventory."""

    bg: Sprite
    game_manager: GameManager

    def __init__(self):
        super().__init__(overlay_alpha=128)
        self.dragging_item_idx = None
        self.drag_pos = None
        self.scroll_y = 0.0
        self.selected_index = -1
        self._build_ui()

    def _build_ui(self):
        """Build/rebuild the UI for dynamic resolution support."""
        self.clear()
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)
        self.bgx = crd(sw.per(70))
        self.bgy = sh.per(80)
        self.bg = Sprite(
            "UI/raw/UI_Flat_Frame03a.png",
            (self.bgx, self.bgy),
            nine_grid_margins=(45, 45, 45, 45),
        )
        self.bg.image = color.recol(self.bg.image, (120, 120, 120))
        self.bg.rect.center = sw.per(50), sh.per(50)
        back_button = Button(
            "UI/button_back.png",
            "UI/button_back_hover.png",
            sw.per(3),
            sh.per(3),
            100,
            100,
            lambda: self.close(),
        )
        self.add_active(back_button)
        bgcx = crd(self.bg.rect.centerx)
        bgcy = crd(self.bg.rect.centery)

        font = resource_manager.get_font(None, 24)
        text_color = 255, 255, 255
        self.volume_label = font.render("Bag", True, text_color)
        self.volume_label_pos = (
            bgcx.per(50) - self.volume_label.get_width() // 2,
            bgcy.per(30),
        )

        # Player Level Label
        self.level_label = Text("Lvl: ?", 24, "azure")
        self.level_label.rect.right = self.bg.rect.right - sw.per(5)
        self.level_label.rect.top = self.bg.rect.top + sh.per(5)
        self.add_passive(self.level_label)

        bg_left = crd(self.bg.rect.left)
        bg_top = crd(self.bg.rect.top)
        bg_width = crd(self.bg.rect.width)
        bg_height = crd(self.bg.rect.height)
        left_col_x = bg_left + bg_width.per(10)
        left_col_y = bg_top + bg_height.per(10)
        left_col_width = bg_width.per(35)
        left_col_height = bg_height.per(80)
        self.left_col_rect = pg.Rect(
            left_col_x, left_col_y, left_col_width, left_col_height
        )
        right_col_x = bg_left + bg_width.per(55)
        right_col_y = bg_top + bg_height.per(10)
        right_col_width = bg_width.per(35)
        right_col_height = bg_height.per(80)
        self.right_col_rect = pg.Rect(
            right_col_x, right_col_y, right_col_width, right_col_height
        )

        if gh.gm:
            gh.gm.bag.my_mon()
            gh.gm.bag.add_monster_col(self.left_col_rect)

        # Scroll Setup
        self.scroll_area = self.right_col_rect.copy()
        self.item_height = self.scroll_area.height // 8
        self.scroll_speed = 30.0
        self.scrollbar_width = 10

        # Pagination Buttons (Box)
        self.prev_btn = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            self.left_col_rect.left,
            self.left_col_rect.bottom + sh.per(2),
            sh.per(10),
            sh.per(6),
            lambda: gh.gm.bag.change_page(-1),
            nine_grid_margins=(14, 14, 14, 14),
        )
        self.prev_btn.img_button_default.image = color.recol(
            self.prev_btn.img_button_default.image, (120, 120, 120)
        )
        self.prev_btn.img_button_hover.image = color.recol(
            self.prev_btn.img_button_hover.image, (120, 120, 120)
        )
        self.next_btn = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            self.left_col_rect.right - sh.per(10),
            self.left_col_rect.bottom + sh.per(2),
            sh.per(10),
            sh.per(6),
            lambda: gh.gm.bag.change_page(1),
            nine_grid_margins=(14, 14, 14, 14),
        )
        self.next_btn.img_button_default.image = color.recol(
            self.next_btn.img_button_default.image, (120, 120, 120)
        )
        self.next_btn.img_button_hover.image = color.recol(
            self.next_btn.img_button_hover.image, (120, 120, 120)
        )

        prev_label = Text("Prev", 20, "Black")
        prev_label.rect.center = self.prev_btn.hitbox.center
        next_label = Text("Next", 20, "Black")
        next_label.rect.center = self.next_btn.hitbox.center
        self.prev_btn_comp = [self.prev_btn, prev_label]
        self.next_btn_comp = [self.next_btn, next_label]

        # Initialize Items
        if gh.gm:
            self._create_item_slots()

    def _create_item_slots(self):
        """Create item slots directly from bag data."""
        self.active_components = [
            c for c in self.active_components if not getattr(c, "_is_item_slot", False)
        ]
        self.components = [
            c for c in self.components if not getattr(c, "_is_item_slot", False)
        ]

        self.item_slots = []
        self.content_height = 0
        self.max_scroll = 0
        if not gh.gm:
            return

        items = gh.gm.bag._items_data
        self.content_height = self.item_height * len(items)
        self.max_scroll = max(0, self.content_height - self.scroll_area.height)

        for idx, item in enumerate(items):
            static_data = pokeitems.items.get(item["name"], {})
            # Get sprite_path with a fallback for missing items
            sprite_path = item.get("sprite_path") or static_data.get(
                "sprite_path", "ingame_ui/potion.png"
            )
            item = {**static_data, **item}

            slot_data = {}
            # Button (Background)
            mbg = Button(
                "UI/raw/UI_Flat_Frame03a.png",
                "UI/raw/UI_Flat_Frame02a.png",
                self.scroll_area.left,
                self.scroll_area.top + self.item_height * idx,
                self.scroll_area.width - self.scrollbar_width - 5,
                self.item_height,
                lambda idx=idx: None,
                nine_grid_margins=(45, 45, 45, 45),
            )
            mbg.img_button_default.image = color.recol(
                mbg.img_button_default.image, (120, 120, 120)
            )
            mbg.img_button_hover.image = color.recol(
                mbg.img_button_hover.image, (120, 120, 120)
            )
            mbg._is_item_slot = True
            slot_data["mbg"] = mbg
            slot_data["base_y"] = self.scroll_area.top + self.item_height * idx

            # Icon Background (New Square)
            icon_bg_size = int(self.item_height * 0.9)
            icon_bg = Sprite(
                "UI/raw/UI_Flat_Frame01a.png",
                (icon_bg_size, icon_bg_size),
                nine_grid_margins=(45, 45, 45, 45),
            )
            icon_bg.image = color.recol(icon_bg.image, (60, 60, 60))
            icon_bg._is_item_slot = True
            slot_data["icon_bg"] = icon_bg

            sprite = Sprite(sprite_path, (48, 48))
            sprite._is_item_slot = True
            slot_data["sprite"] = sprite

            name = Text(item["name"], 20, "azure")
            name._is_item_slot = True
            slot_data["name"] = name

            count = Text(f"x{item['count']}", 20, "azure")
            count._is_item_slot = True
            slot_data["count"] = count

            self.item_slots.append((slot_data, idx))

        self._update_slot_positions()

    def _update_slot_positions(self):
        """Update positions based on scroll."""
        self.active_components = [
            c for c in self.active_components if not getattr(c, "_is_item_slot", False)
        ]
        self.components = [
            c for c in self.components if not getattr(c, "_is_item_slot", False)
        ]

        b = self.scroll_area

        for slot_data, idx in self.item_slots:
            y_pos = slot_data["base_y"] - self.scroll_y

            if b.top - self.item_height <= y_pos <= b.bottom:
                mbg = slot_data["mbg"]
                mbg.hitbox.top = int(y_pos)
                mbg.img_button.rect.top = int(y_pos)
                self.add_active(mbg)

                icon_bg = slot_data["icon_bg"]
                icon_bg.rect.left = mbg.hitbox.left + crd(mbg.hitbox.width).per(2)
                icon_bg.rect.centery = mbg.hitbox.centery
                self.add_passive(icon_bg)

                sprite = slot_data["sprite"]
                sprite.rect.center = icon_bg.rect.center
                self.add_passive(sprite)

                name = slot_data["name"]
                name.rect.left = icon_bg.rect.right + crd(mbg.hitbox.width).per(2)
                name.rect.centery = mbg.hitbox.centery
                self.add_passive(name)

                count = slot_data["count"]
                count.rect.right = mbg.hitbox.right - crd(mbg.hitbox.width).per(5)
                count.rect.centery = mbg.hitbox.centery
                self.add_passive(count)

    def open(self):
        """Open."""
        super().open()
        if gh.gm:
            gh.gm.bag.my_mon()
            gh.gm.bag.add_monster_col(self.left_col_rect)
            # Re-create slots on open to refresh data
            self._create_item_slots()

            # Update Level Label
            self.level_label.change_text(f"Lvl: {gh.gm.player_level}")
            # Re-position if width changed
            sw = crd(GameSettings.SCREEN_WIDTH)
            sh = crd(GameSettings.SCREEN_HEIGHT)
            self.level_label.rect.right = self.bg.rect.right - sw.per(5)
            self.level_label.rect.top = self.bg.rect.top + sh.per(5)

    def update_content(self, dt: float) -> None:
        """Update content."""
        if input_manager.key_pressed(pg.K_ESCAPE):
            input_manager.reset()
            self.close()

        # Update visibility of pagination buttons
        if gh.gm:
            is_box = gh.gm.bag.current_tab == "box"

            def set_visible(components, visible):
                for c in components:
                    if visible:
                        if isinstance(c, Button):
                            if c not in self.active_components:
                                self.add_active(c)
                        elif isinstance(c, (Text, Sprite)):
                            if c not in self.components:
                                self.add_passive(c)
                    else:
                        if isinstance(c, Button):
                            if c in self.active_components:
                                self.active_components.remove(c)
                        elif c in self.components:
                            self.components.remove(c)

            set_visible(self.prev_btn_comp, is_box)
            set_visible(self.next_btn_comp, is_box)

            # Scroll Logic
            changed = False
            if input_manager.mouse_wheel != 0:
                self.scroll_y -= input_manager.mouse_wheel * self.scroll_speed
                changed = True

            # Keyboard/Controller Navigation
            nav_change = 0
            if input_manager.key_pressed(pg.K_UP) or input_manager.button_pressed(
                11
            ):  # Up
                nav_change = -1
            elif input_manager.key_pressed(pg.K_DOWN) or input_manager.button_pressed(
                12
            ):  # Down
                nav_change = 1

            if nav_change != 0:
                # Initialize selection if none
                if self.selected_index == -1:
                    self.selected_index = 0
                else:
                    self.selected_index += nav_change

                # Clamp
                items_len = len(gh.gm.bag._items_data)
                self.selected_index = max(0, min(self.selected_index, items_len - 1))

                # Auto-scroll to selected
                # Slot Y range
                slot_top = self.item_height * self.selected_index
                slot_bottom = slot_top + self.item_height

                # Visible range
                vis_top = self.scroll_y
                vis_bottom = self.scroll_y + self.scroll_area.height

                if slot_top < vis_top:
                    self.scroll_y = slot_top
                    changed = True
                elif slot_bottom > vis_bottom:
                    self.scroll_y = slot_bottom - self.scroll_area.height
                    changed = True

            if changed:
                self.scroll_y = max(0, min(self.max_scroll, self.scroll_y))
                self._update_slot_positions()

            # Drag and Drop Logic
            mouse_pos = input_manager.mouse_pos

            # Start Drag
            if input_manager.mouse_pressed(1):
                # Iterate over our managed slots
                for slot_data, idx in self.item_slots:
                    mbg = slot_data["mbg"]
                    if mbg in self.active_components:  # Only interact if visible
                        if mbg.hitbox.collidepoint(mouse_pos):
                            Logger.info(f"Start dragging item {idx}")
                            self.dragging_item_idx = idx
                            self.drag_offset = (
                                mouse_pos[0] - mbg.hitbox.x,
                                mouse_pos[1] - mbg.hitbox.y,
                            )
                            break

            # Update Drag
            if input_manager.mouse_down(1) and self.dragging_item_idx is not None:
                self.drag_pos = mouse_pos

            # End Drag (Drop)
            if input_manager.mouse_released(1):
                if self.dragging_item_idx is not None:
                    Logger.info(
                        f"Released item {self.dragging_item_idx} at {mouse_pos}"
                    )
                    if hasattr(gh.gm.bag, "mon_slots"):
                        for m_idx, m_slot in enumerate(gh.gm.bag.mon_slots):
                            if m_idx < len(gh.gm.bag.monster_data):
                                if m_slot.collidepoint(mouse_pos):
                                    Logger.info(f"Dropping on monster {m_idx}")
                                    gh.gm.bag.use_item(self.dragging_item_idx, m_idx)
                                    # Refresh after use (count change)
                                    self._create_item_slots()
                                    break
                    self.dragging_item_idx = None
                    self.drag_pos = None

    def draw_content(self, screen: pg.Surface) -> None:
        """Draw content."""
        self.bg.draw(screen)
        if gh.gm:
            gh.gm.bag.draw_monsters(screen)  # Only draw monsters!

            # Draw non-item components
            for c in self.active_components:
                if not getattr(c, "_is_item_slot", False):
                    c.draw(screen)
            for t in self.components:
                if not getattr(t, "_is_item_slot", False):
                    t.draw(screen)

            # Clip and Draw Items
            prev_clip = screen.get_clip()
            screen.set_clip(self.scroll_area)
            for c in self.active_components:
                if getattr(c, "_is_item_slot", False):
                    c.draw(screen)
            for t in self.components:
                if getattr(t, "_is_item_slot", False):
                    t.draw(screen)
            screen.set_clip(prev_clip)

            # Scrollbar
            if self.max_scroll > 0:
                b = self.scroll_area
                track_rect = pg.Rect(
                    b.right - self.scrollbar_width,
                    b.top,
                    self.scrollbar_width,
                    b.height,
                )
                pg.draw.rect(screen, (60, 60, 60), track_rect)
                thumb_height = max(20, int(b.height * (b.height / self.content_height)))
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

            # Draw Selection Highlight
            if self.selected_index != -1 and self.selected_index < len(self.item_slots):
                # Find the slot data
                # self.item_slots is list of (slot_data, idx)
                # We can access by index directly since list is ordered by index?
                # Yes, appended in order.
                slot_data, _ = self.item_slots[self.selected_index]
                mbg = slot_data["mbg"]
                # Draw border if visible
                if mbg in self.active_components:
                    pg.draw.rect(screen, (255, 255, 0), mbg.hitbox, 2)

            # Draw dragged item
            if self.dragging_item_idx is not None and self.dragging_item_idx < len(
                gh.gm.bag._items_data
            ):
                item = gh.gm.bag._items_data[self.dragging_item_idx]
                # Get sprite_path with fallback
                static_data = pokeitems.items.get(item["name"], {})
                img_path = static_data.get("sprite_path", "ingame_ui/potion.png")
                temp_sprite = Sprite(img_path, (48, 48))
                rect = (
                    temp_sprite.image.get_rect(center=self.drag_pos)
                    if self.drag_pos
                    else temp_sprite.image.get_rect(topleft=input_manager.mouse_pos)
                )
                screen.blit(temp_sprite.image, rect)
