import pygame as pg
from .sprite import Sprite
from src.utils import GameSettings


class BackgroundSprite(Sprite):
    """Background  sprite."""

    def __init__(self, image_path: str):
        super().__init__(image_path, (GameSettings.SCREEN_WIDTH,
            GameSettings.SCREEN_HEIGHT))

    def draw(self, screen: pg.Surface):
        """Draw."""
        screen.blit(self.image, (0, 0))
