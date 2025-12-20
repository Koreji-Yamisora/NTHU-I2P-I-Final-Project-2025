from __future__ import annotations
import pygame as pg
from src.interface.components import Overlay, Button
from src.utils import GameSettings, crd, Logger
from src.sprites import Sprite, Text
from src.data import pokedex
from src.utils import color
from typing import Callable


class StarterOverlay(Overlay):
    """Starter Selection Overlay - Choose your first Pokémon!"""

    STARTER_IDS = [1, 2, 4]  # Pikachu, Charizard, Venusaur

    def __init__(self, on_select: Callable[[int], None]):
        super().__init__(overlay_alpha=200)
        self.on_select = on_select
        self.selected_id = None
        self._build_ui()

    def _build_ui(self):
        """Build the starter selection UI."""
        self.clear()
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        # Background
        self.bgx = crd(sw.per(80))
        self.bgy = sh.per(70)
        self.bg = Sprite(
            "UI/raw/UI_Flat_Frame03a.png",
            (self.bgx, self.bgy),
            nine_grid_margins=(45, 45, 45, 45),
        )
        self.bg.image = color.recol(self.bg.image, (120, 120, 120))
        self.bg.rect.center = sw.per(50), sh.per(50)
        self.add_bg(self.bg)

        # Title
        title = Text("Choose Your Starter!", 36, "Gold")
        title.rect.centerx = self.bg.rect.centerx
        title.rect.top = self.bg.rect.top + sh.per(8)
        self.add_passive(title)

        # Create 3 starter selection slots
        slot_width = self.bgx.per(25)
        slot_height = self.bgy.per(50)
        spacing = self.bgx.per(5)
        start_x = self.bg.rect.centerx - (slot_width * 1.5 + spacing)

        for idx, starter_id in enumerate(self.STARTER_IDS):
            self._create_starter_slot(
                starter_id,
                start_x + (slot_width + spacing) * idx,
                self.bg.rect.centery - slot_height // 2,
                slot_width,
                slot_height,
            )

    def _create_starter_slot(
        self, starter_id: int, x: int, y: int, width: int, height: int
    ):
        """Create a single starter selection slot."""
        # Slot background
        slot_bg = Sprite(
            "UI/raw/UI_Flat_Frame01a.png",
            (width, height),
            nine_grid_margins=(45, 45, 45, 45),
        )
        slot_bg.image = color.recol(slot_bg.image, (60, 60, 60))
        slot_bg.rect.topleft = (x, y)
        self.add_bg(slot_bg)

        # Pokémon data
        poke_data = pokedex.data[starter_id]

        # Pokémon sprite
        sprite_path = poke_data.get("sprite_path", "menu_sprites/menusprite1.png")
        poke_sprite = Sprite(sprite_path, (120, 120))
        poke_sprite.rect.centerx = slot_bg.rect.centerx
        poke_sprite.rect.top = slot_bg.rect.top + 20
        self.add_passive(poke_sprite)

        # Name
        name_text = Text(poke_data["name"], 24, "azure")
        name_text.rect.centerx = slot_bg.rect.centerx
        name_text.rect.top = poke_sprite.rect.bottom + 10
        self.add_passive(name_text)

        # Type display
        types = poke_data.get("type", [])
        type_text = " / ".join([t.upper() if t else "" for t in types if t])
        type_label = Text(type_text, 18, "lightgray")
        type_label.rect.centerx = slot_bg.rect.centerx
        type_label.rect.top = name_text.rect.bottom + 5
        self.add_passive(type_label)

        # Select button
        btn_width = width - 20
        btn_height = 50
        select_btn = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            slot_bg.rect.centerx - btn_width // 2,
            slot_bg.rect.bottom - btn_height - 10,
            btn_width,
            btn_height,
            lambda sid=starter_id: self._select_starter(sid),
            nine_grid_margins=(14, 14, 14, 14),
        )
        select_btn.img_button_default.image = color.recol(
            select_btn.img_button_default.image, (50, 150, 50)
        )
        select_btn.img_button_hover.image = color.recol(
            select_btn.img_button_hover.image, (80, 200, 80)
        )
        self.add_active(select_btn)

        # Button label
        btn_label = Text("Choose", 20, "White")
        btn_label.rect.center = select_btn.hitbox.center
        self.add_passive(btn_label)

    def _select_starter(self, starter_id: int):
        """Handle starter selection."""
        Logger.info(f"Selected starter ID: {starter_id}")
        self.selected_id = starter_id
        self.close()
        if self.on_select:
            self.on_select(starter_id)

    def update_content(self, dt: float) -> None:
        """Update content."""
        # Close on ESC
        from src.core.services import input_manager

        if input_manager.key_pressed(pg.K_ESCAPE):
            input_manager.reset()
            # Don't allow closing without selection
            pass  # Starter selection is mandatory
