from __future__ import annotations
import pygame as pg
from src.interface.components.overlay import Overlay
from src.interface.components.button import Button
from src.utils import GameSettings, Logger, Position
import math


class MapOverlay(Overlay):
    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.game_manager = game_manager

        # Hardcoded list of maps for quick access
        # In a real dynamic system we might scan assets/maps, but this ensures nice names
        self.available_maps = [
            ("World", "world.tmx"),
            ("House", "house.tmx"),
            ("Gym", "gym.tmx"),
            ("Hospital", "hospital.tmx"),
            ("Fire", "fire.tmx"),
            ("Water", "water.tmx"),
            ("Plant", "plant.tmx"),
            ("Arena", "arena.tmx"),
            ("Main", "map.tmx"),
        ]

        self.setup_ui()

    def setup_ui(self):
        screen_width, screen_height = pg.display.get_surface().get_size()
        panel_width = 400
        panel_height = 500

        # Center panel
        self.panel_rect = pg.Rect(
            (screen_width - panel_width) // 2,
            (screen_height - panel_height) // 2,
            panel_width,
            panel_height,
        )

        font = pg.font.Font(GameSettings.FONT, 20)

        btn_width = 150
        btn_height = 40
        spacing_y = 10
        spacing_x = 20

        start_y = self.panel_rect.top + 50

        # Create buttons in a grid (2 columns)
        for i, (name, filename) in enumerate(self.available_maps):
            col = i % 2
            row = i // 2

            x = self.panel_rect.left + 30 + col * (btn_width + spacing_x)
            y = start_y + row * (btn_height + spacing_y)

            btn = Button(
                x=x,
                y=y,
                width=btn_width,
                height=btn_height,
                text=name,
                font=font,
                text_color=(255, 255, 255),
                color=(50, 50, 50),
                hover_color=(80, 80, 80),
                on_click=lambda f=filename: self.switch_map(f),
            )
            self.components.append(btn)

        # Close button
        close_btn = Button(
            x=self.panel_rect.centerx - 50,
            y=self.panel_rect.bottom - 60,
            width=100,
            height=40,
            text="Close",
            font=font,
            text_color=(255, 255, 255),
            color=(200, 50, 50),
            hover_color=(230, 80, 80),
            on_click=self.close,
        )
        self.components.append(close_btn)

    def switch_map(self, map_file: str):
        Logger.info(f"Switching to map: {map_file}")
        self.game_manager.switch_map(map_file)
        self.close()

    def draw_content(self, screen: pg.Surface):
        # Draw panel background
        pg.draw.rect(screen, (30, 30, 30), self.panel_rect, border_radius=15)
        pg.draw.rect(screen, (255, 255, 255), self.panel_rect, 2, border_radius=15)

        # Title
        font = pg.font.Font(GameSettings.FONT, 28)
        title_surf = font.render("Map Select", True, (255, 255, 255))
        title_rect = title_surf.get_rect(
            centerx=self.panel_rect.centerx, top=self.panel_rect.top + 15
        )
        screen.blit(title_surf, title_rect)
