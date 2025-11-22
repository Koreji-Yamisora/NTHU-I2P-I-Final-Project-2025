import pygame as pg
from src.core.services import resource_manager
from src.utils import Position, PositionCamera
from typing import Optional


class ColorSprite:
    image: pg.Surface
    rect: pg.Rect

    def __init__(
        self, color: tuple[int, int, int] | str, size: tuple[int, int], alpha: int = 255
    ):
        self.image = pg.Surface(size)
        self.image.set_alpha(alpha)
        self.image.fill(color)

        self.rect = self.image.get_rect()

    def draw(self, screen: pg.Surface, camera: Optional[PositionCamera] = None):
        if camera is not None:
            screen.blit(self.image, camera.transform_rect(self.rect))
        else:
            screen.blit(self.image, self.rect)


class Sprite:
    image: pg.Surface
    rect: pg.Rect

    def __init__(self, img_path: str, size: tuple[int, int] | None = None):
        self.image = resource_manager.get_image(img_path)
        if size is not None:
            self.image = pg.transform.scale(self.image, size)
        self.rect = self.image.get_rect()

    def update(self, dt: float):
        pass

    def draw(self, screen: pg.Surface, camera: Optional[PositionCamera] = None):
        if camera is not None:
            screen.blit(self.image, camera.transform_rect(self.rect))
        else:
            screen.blit(self.image, self.rect)

    def draw_hitbox(self, screen: pg.Surface, camera: Optional[PositionCamera] = None):
        if camera is not None:
            pg.draw.rect(screen, (255, 0, 0), camera.transform_rect(self.rect), 1)
        else:
            pg.draw.rect(screen, (255, 0, 0), self.rect, 1)

    def update_bar(self, width: int):
        self.rect.width = width
        self.image = pg.transform.scale(self.image, (width, self.rect.height))

    def update_pos(self, pos: Position):
        self.rect.topleft = (round(pos.x), round(pos.y))


class Text:
    font: pg.font.Font
    text: pg.Surface
    rect: pg.Rect

    def __init__(self, text: str, size: int, color: tuple[int, int, int] | str):
        self.size = size
        self.color = color
        self.font = resource_manager.get_font("Minecraft.ttf", size)
        self.text = self.font.render(text, True, color)
        self.rect = self.text.get_rect()

    def draw(self, screen: pg.Surface):
        screen.blit(self.text, self.rect)

    def change_text(self, text: str, pos: str = "topleft"):
        self.font = resource_manager.get_font("Minecraft.ttf", self.size)
        self.text = self.font.render(text, True, self.color)
        rect = self.text.get_rect()
        setattr(rect, pos, getattr(self.rect, pos))
        self.rect = rect
