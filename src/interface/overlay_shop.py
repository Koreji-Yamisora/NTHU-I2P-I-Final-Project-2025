from __future__ import annotations
import pygame as pg
from src.interface.components import Overlay, Button, Slider, ToggleButton
from src.core.services import sound_manager, resource_manager
from src.core.managers import GameManager
from src.utils import GameSettings, Logger, crd, color
from typing import Callable
from src.sprites import Sprite, Text
from src.core.services import input_manager
from src.core.gm_helper import gh
from src.data import pokeitems


class Shop(Overlay):
    """Shop."""

    bg: Sprite
    rf: float
    restocking: bool

    def __init__(self, shop_data):
        super().__init__(overlay_alpha=128)
        self.restocking = False
        self.rf = 0
        self.shop_data = shop_data
        self.scroll_y = 0.0
        self.mode = "buy"  # buy, sell_item, sell_mon
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
        self.bg_rect = self.bg.rect.copy()  # For clipping

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

        # Title Label
        self.title_label = Text("Shop", 32, "white")
        self.title_label.rect.midtop = (
            bgcx.per(50),
            bgcy.per(8),
        )
        self.add_passive(self.title_label)

        # Money Label
        money_amount = gh.gm.bag.money if (gh.gm and gh.gm.bag) else 0
        self.money_label = Text(f"Money: ${money_amount}", 24, "gold")
        self.money_label.rect.topright = (
            self.bg.rect.right - crd(sw.per(5)),
            self.bg.rect.top + crd(sh.per(5)),
        )
        self.add_passive(self.money_label)

        # Tabs
        tab_y = bgcy.per(20)
        self.btn_buy = Button(
            "UI/raw/UI_Flat_Button01a_1.png",
            "UI/raw/UI_Flat_Button01a_2.png",
            bgcx.per(20),
            tab_y,
            150,
            40,
            lambda: self.set_mode("buy"),
            nine_grid_margins=(14, 14, 14, 14),
        )
        self.btn_sell_item = Button(
            "UI/raw/UI_Flat_Button01a_1.png",
            "UI/raw/UI_Flat_Button01a_2.png",
            bgcx.per(40),
            tab_y,
            150,
            40,
            lambda: self.set_mode("sell_item"),
            nine_grid_margins=(14, 14, 14, 14),
        )
        self.btn_sell_mon = Button(
            "UI/raw/UI_Flat_Button01a_1.png",
            "UI/raw/UI_Flat_Button01a_2.png",
            bgcx.per(60),
            tab_y,
            150,
            40,
            lambda: self.set_mode("sell_mon"),
            nine_grid_margins=(14, 14, 14, 14),
        )

        self.add_active(self.btn_buy)
        self.add_active(self.btn_sell_item)
        self.add_active(self.btn_sell_mon)

        # Tab Texts
        t1 = Text("Buy", 20, "white")
        t1.rect.center = self.btn_buy.hitbox.center
        self.add_passive(t1)

        t2 = Text("Sell Item", 20, "white")
        t2.rect.center = self.btn_sell_item.hitbox.center
        self.add_passive(t2)

        t3 = Text("Sell Pokemon", 20, "white")
        t3.rect.center = self.btn_sell_mon.hitbox.center
        self.add_passive(t3)

        bg_left = crd(self.bg.rect.left)
        bg_top = crd(self.bg.rect.top)
        bg_width = crd(self.bg.rect.width)
        bg_height = crd(self.bg.rect.height)

        # Scroll Area Setup
        x = bg_left + bg_width.per(10)
        y = bg_top + bg_height.per(10)
        w = bg_width.per(80)
        h = bg_height.per(80)
        self.scroll_area = pg.Rect(x, y, w, h)

        self.height = self.scroll_area.height // 8
        self.scroll_speed = 30.0
        self.scrollbar_width = 10

        self._create_item_slots()

    def set_mode(self, mode):
        self.mode = mode

        if mode == "buy":
            self.title_label.change_text("Shop")
        elif mode == "sell_item":
            self.title_label.change_text("Sell Items")
        elif mode == "sell_mon":
            self.title_label.change_text("Sell Pokemon")

        self.scroll_y = 0
        self._create_item_slots()

    def _create_item_slots(self):
        """Create all item slots."""
        self.active_components = [
            c for c in self.active_components if not getattr(c, "_is_item_slot", False)
        ]
        self.components = [
            c for c in self.components if not getattr(c, "_is_item_slot", False)
        ]

        self.item_slots = []
        items = []

        if self.mode == "buy":
            items = self.shop_data.get("items", [])
        elif self.mode == "sell_item":
            if gh.gm and gh.gm.bag:
                items = (
                    gh.gm.bag.get_items()
                )  # Returns list of dicts similar to shop items
        elif self.mode == "sell_mon":
            if gh.gm and gh.gm.bag:
                monsters = gh.gm.bag.monsters
                # Convert to list adaptable for loop
                items = monsters

        self.content_height = self.height * len(items)
        self.max_scroll = max(0, self.content_height - self.scroll_area.height)
        # Clamp scroll_y to valid range (don't reset to 0)
        self.scroll_y = max(0, min(self.max_scroll, self.scroll_y))

        for idx, item in enumerate(items):
            slot_data = {}
            name_text = ""
            count_text = ""
            price = 0
            sprite_path = "ingame_ui/potion.png"

            if self.mode == "buy":
                # Static Data
                static_data = pokeitems.items.get(item["name"], {})
                sprite_path = item.get("sprite_path") or static_data.get(
                    "sprite_path", "ingame_ui/potion.png"
                )
                name_text = item["name"]
                price = static_data.get("price", 0)
                count_text = f"Stock: {item['count'][0]} | ${price}"

            elif self.mode == "sell_item":
                static_data = pokeitems.items.get(item["name"], {})
                sprite_path = item.get("sprite") or static_data.get(
                    "sprite_path", "ingame_ui/potion.png"
                )
                name_text = item["name"]
                price = int(static_data.get("price", 0) * 0.5)
                count_text = f"Owned: {item['count']} | Sell: ${price}"

            elif self.mode == "sell_mon":
                from src.data import pokedex

                p_data = pokedex.data[item["id"]]
                sprite_path = p_data["sprite_path"]
                name_text = item["name"]
                price = item["level"] * 100
                count_text = f"Lvl: {item['level']} | Sell: ${price}"

            # Button (Slot Background)
            mbg = Button(
                "UI/raw/UI_Flat_Frame03a.png",
                "UI/raw/UI_Flat_Frame02a.png",
                self.scroll_area.left,
                self.scroll_area.top + self.height * idx,
                self.scroll_area.width - self.scrollbar_width - 5,
                self.height,
                lambda idx=idx: self.action(idx),
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
            slot_data["base_y"] = self.scroll_area.top + self.height * idx

            slot_data["base_y"] = self.scroll_area.top + self.height * idx

            # IconBG
            icon_bg_size = int(self.height * 0.9)
            icon_bg = Sprite(
                "UI/raw/UI_Flat_Frame01a.png",
                (icon_bg_size, icon_bg_size),
                nine_grid_margins=(45, 45, 45, 45),
            )
            icon_bg.image = color.recol(icon_bg.image, (60, 60, 60))
            icon_bg._is_item_slot = True
            slot_data["icon_bg"] = icon_bg

            # Sprite
            sprite = Sprite(sprite_path, (64, 64))
            sprite._is_item_slot = True
            slot_data["sprite"] = sprite

            # Text
            name = Text(name_text, 24, "azure")
            name._is_item_slot = True
            slot_data["name"] = name

            count = Text(count_text, 24, "azure")
            count._is_item_slot = True
            slot_data["count"] = count

            self.item_slots.append(slot_data)

        self._update_slot_positions()

    def _update_slot_positions(self):
        """Update slot positions based on scroll_y."""
        self.active_components = [
            c for c in self.active_components if not getattr(c, "_is_item_slot", False)
        ]
        self.components = [
            c for c in self.components if not getattr(c, "_is_item_slot", False)
        ]

        b = self.scroll_area

        for idx, slot in enumerate(self.item_slots):
            y_pos = slot["base_y"] - self.scroll_y

            # Render if visible
            if b.top - self.height <= y_pos <= b.bottom:
                mbg = slot["mbg"]
                mbg.hitbox.top = int(y_pos)
                mbg.img_button.rect.top = int(y_pos)
                self.add_active(mbg)

                self.add_active(mbg)

                icon_bg = slot["icon_bg"]
                icon_bg.rect.left = mbg.hitbox.left + crd(mbg.hitbox.width).per(2)
                icon_bg.rect.centery = mbg.hitbox.centery
                self.add_passive(icon_bg)

                sprite = slot["sprite"]
                sprite.rect.center = icon_bg.rect.center
                self.add_passive(sprite)

                name = slot["name"]
                name.rect.left = icon_bg.rect.right + crd(mbg.hitbox.width).per(2)
                name.rect.centery = mbg.hitbox.top + crd(self.height).per(50)
                self.add_passive(name)

                count = slot["count"]
                count.rect.left = name.rect.right + crd(mbg.hitbox.width).per(5)
                count.rect.centery = mbg.hitbox.top + crd(self.height).per(50)
                self.add_passive(count)

    def refresh(self):
        """Refresh."""
        if gh.gm and gh.gm.bag:
            self.money_label.change_text(f"Money: ${gh.gm.bag.money}")
        self._create_item_slots()

    def action(self, idx):
        """Action."""
        input_manager.reset()
        assert gh.gm is not None

        if self.mode == "buy":
            items = self.shop_data["items"]
            if 0 <= idx < len(items):
                item = items[idx]
                static_data = pokeitems.items.get(item["name"], {})
                price = static_data.get("price", 0)

                if item["count"][0] > 0:
                    if gh.gm.bag.money >= price:
                        gh.gm.bag.money -= price
                        item["count"][0] -= 1
                        gh.gm.bag.add_item(item)
                        self.refresh()
                        Logger.info(f"Bought {item['name']} for {price}")
                    else:
                        Logger.info("Not enough money")

        elif self.mode == "sell_item":
            my_items = gh.gm.bag.get_items()
            if 0 <= idx < len(my_items):
                item = my_items[idx]
                static_data = pokeitems.items.get(item["name"], {})
                price = int(static_data.get("price", 0) * 0.5)

                gh.gm.bag.remove_item(item["name"])
                gh.gm.bag.money += price
                self.refresh()
                Logger.info(f"Sold {item['name']} for {price}")

        elif self.mode == "sell_mon":
            monsters = gh.gm.bag.monsters
            if 0 <= idx < len(monsters):
                # Don't sell the last Pokemon!
                if len(monsters) <= 1:
                    Logger.info("Cannot sell last Pokemon")
                    return

                mon = monsters[idx]
                price = mon["level"] * 100
                gh.gm.bag.remove_monster(idx)
                gh.gm.bag.money += price
                self.refresh()
                Logger.info(f"Released {mon['name']} for {price}")

    def close(self):
        """Close."""
        super().close()
        self.rf = 10
        self.restocking = True

    def open(self):
        """Open."""
        super().open()
        Logger.info("Shop opened")

    def update_content(self, dt: float) -> None:
        """Update content."""
        if input_manager.key_pressed(pg.K_ESCAPE):
            input_manager.reset()
            self.close()

        changed = False
        if input_manager.mouse_wheel != 0:
            self.scroll_y -= input_manager.mouse_wheel * self.scroll_speed
            changed = True

        if changed:
            self.scroll_y = max(0, min(self.max_scroll, self.scroll_y))
            self._update_slot_positions()

        # Keyboard/Controller Navigation
        nav_change = 0
        if input_manager.key_pressed(pg.K_UP) or input_manager.button_pressed(11):
            nav_change = -1
        elif input_manager.key_pressed(pg.K_DOWN) or input_manager.button_pressed(12):
            nav_change = 1

        if nav_change != 0:
            if self.selected_index == -1:
                self.selected_index = 0
            else:
                self.selected_index += nav_change

            # Clamp
            self.selected_index = max(
                0, min(self.selected_index, len(self.item_slots) - 1)
            )

            # Auto-scroll
            slot_top = self.height * self.selected_index
            slot_bottom = slot_top + self.height

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

        # Update buttons
        for c in self.active_components:
            if isinstance(c, Button):
                c.update(dt)

    def timer_tick(self, dt: float):
        """Timer Tick."""
        if self.rf > 0:
            self.rf -= dt
        elif self.restocking:
            for item in self.shop_data["items"]:
                Logger.debug("Restocking shop item" + item["name"])
                item["count"][0] = item["count"][1]
            self.refresh()
            self.restocking = False

    def draw_content(self, screen: pg.Surface) -> None:
        """Draw content with clipping."""
        self.bg.draw(screen)

        # Draw non-scroll components
        for c in self.active_components:
            if not getattr(c, "_is_item_slot", False):
                c.draw(screen)
        for t in self.components:
            if not getattr(t, "_is_item_slot", False):
                t.draw(screen)

        # Clip
        prev_clip = screen.get_clip()
        screen.set_clip(self.scroll_area)

        # Draw scroll components
        for c in self.active_components:
            if getattr(c, "_is_item_slot", False):
                c.draw(screen)
        for t in self.components:
            if getattr(t, "_is_item_slot", False):
                t.draw(screen)

        screen.set_clip(prev_clip)

        # Draw Scrollbar
        if self.max_scroll > 0:
            b = self.scroll_area
            track_rect = pg.Rect(
                b.right - self.scrollbar_width, b.top, self.scrollbar_width, b.height
            )
            pg.draw.rect(screen, (60, 60, 60), track_rect)

            thumb_height = max(20, int(b.height * (b.height / self.content_height)))
            scroll_ratio = self.scroll_y / self.max_scroll if self.max_scroll > 0 else 0
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
            slot = self.item_slots[self.selected_index]
            mbg = slot["mbg"]
            if mbg in self.active_components:
                pg.draw.rect(screen, (255, 255, 0), mbg.hitbox, 2)
