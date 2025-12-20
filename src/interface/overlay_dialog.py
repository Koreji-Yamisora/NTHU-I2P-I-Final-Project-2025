from __future__ import annotations
import pygame as pg
from src.interface.components.overlay import Overlay
from src.utils import GameSettings, Logger


class DialogOverlay(Overlay):
    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.message = ""
        self.callback = None
        self.is_active = False

    def setup(self, message: str, callback=None):
        self.message = message
        self.callback = callback
        self.open()

    def update(self, dt: float) -> None:
        if not self.is_open:
            return

        keys = pg.key.get_pressed()
        pass
        # Actually input is likely handled by specific event check or input_manager from scene
        # But for overlay, we often check keys here or in scene.
        # Let's rely on update loop calling proper check

    def handle_input(self, input_manager):
        if not self.is_open:
            return

        # Space or Enter to close/advance
        if input_manager.key_down(pg.K_SPACE) or input_manager.key_down(pg.K_RETURN):
            self.close()
            if self.callback:
                self.callback()

    def draw_content(self, screen: pg.Surface):
        # Draw dialog box at bottom
        width = screen.get_width()
        height = 150
        rect = pg.Rect(0, screen.get_height() - height, width, height)

        # Background
        pg.draw.rect(screen, (20, 20, 20), rect)
        pg.draw.rect(screen, (255, 255, 255), rect, 3)

        # Text
        font = pg.font.Font(GameSettings.FONT, 24)

        # Simple word wrap or render
        # For MVP, just center text
        text_surf = font.render(self.message, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)
