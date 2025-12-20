import pygame as pg
from src.core.services import resource_manager
from src.utils import Position, PositionCamera
from typing import Optional


class ColorSprite:
    """Color  sprite."""

    image: pg.Surface
    rect: pg.Rect

    def __init__(
        self,
        color: (tuple[int, int, int] | str),
        size: tuple[int, int],
        alpha: int = 255,
    ):
        self.image = pg.Surface(size, pg.SRCALPHA)
        c = pg.Color(color)
        c.a = alpha
        self.image.fill(c)
        self.rect = self.image.get_rect()

    def draw(self, screen: pg.Surface, camera: Optional[PositionCamera] = None):
        """Draw."""
        if camera is not None:
            screen.blit(self.image, camera.transform_rect(self.rect))
        else:
            screen.blit(self.image, self.rect)


class Sprite:
    """sprite."""

    _image: pg.Surface
    rect: pg.Rect
    nine_grid_margins: tuple[int, int, int, int] | None

    scale: float = 1.0

    def __init__(
        self,
        img_path: str,
        size: (tuple[int, int] | None) = None,
        nine_grid_margins: tuple[int, int, int, int] | None = None,
    ):
        self._image = resource_manager.get_image(img_path)
        self.nine_grid_margins = nine_grid_margins
        self.nine_grid = None
        self.shake_offset = (0, 0)
        self.shake_timer = 0.0
        self.shake_intensity = 0
        self.flash_timer = 0.0
        self.flash_color = None
        self.flash_alpha = 180

        if size is not None:
            if nine_grid_margins:
                # Keep original image for high-res corners
                pass
            else:
                self._image = pg.transform.scale(self._image, size)

        self.rect = self._image.get_rect()
        if size and nine_grid_margins:
            self.rect.size = size

        # Initialize NineGrid with the current image
        self._refresh_nine_grid()

    @property
    def image(self) -> pg.Surface:
        """Get the sprite image."""
        if self.flash_timer > 0 and self.flash_color:
            # Create a flashed version of the image
            flashed_image = self._image.copy()
            # method: fill a surface with the flash color and blit it onto a copy of the original
            # using BLEND_RGB_ADD to saturate the image to the flash color (e.g. white).
            flash_surf = pg.Surface(flashed_image.get_size(), pg.SRCALPHA)
            flash_surf.fill((*self.flash_color, self.flash_alpha))
            flashed_image.blit(flash_surf, (0, 0), special_flags=pg.BLEND_RGB_ADD)
            return flashed_image

        return self._image

    @image.setter
    def image(self, value: pg.Surface):
        """Set the sprite image and reinitialize NineGrid if needed."""
        self._image = value
        self._refresh_nine_grid()

    def _refresh_nine_grid(self):
        """Initialize NineGrid logic with scaling."""
        if self.nine_grid_margins:
            left, right, top, bottom = self.nine_grid_margins
            img_w, img_h = self._image.get_size()

            # Heuristic: Scale image up if margins are large
            # We enforce that the image is at least (margins * 2) in size
            # This ensures we have enough "visual data" to make the border look chunky
            req_w = (left + right) * 2
            req_h = (top + bottom) * 2

            scale_w = req_w / img_w
            scale_h = req_h / img_h
            scale = max(1.0, scale_w, scale_h)

            if scale > 1.0:
                new_w = int(img_w * scale)
                new_h = int(img_h * scale)
                self._image = pg.transform.scale(self._image, (new_w, new_h))

            from src.utils.nine_grid import NineGrid

            self.nine_grid = NineGrid(self._image, *self.nine_grid_margins)
        else:
            self.nine_grid = None

    def shake(self, intensity: int = 5, duration: float = 0.5):
        """Start shaking the sprite."""
        self.shake_intensity = intensity
        self.shake_timer = duration

    def flash(
        self,
        color: tuple[int, int, int] = (255, 0, 0),
        duration: float = 0.5,
        alpha: int = 180,
    ):
        """Flash the sprite with a color."""
        self.flash_color = color
        self.flash_timer = duration
        self.flash_alpha = alpha

    def update(self, dt: float):
        """Update."""
        import random

        if self.shake_timer > 0:
            self.shake_timer -= dt
            if self.shake_timer <= 0:
                self.shake_offset = (0, 0)
            else:
                self.shake_offset = (
                    random.randint(-self.shake_intensity, self.shake_intensity),
                    random.randint(-self.shake_intensity, self.shake_intensity),
                )

        if self.flash_timer > 0:
            self.flash_timer -= dt

    def draw(self, screen: pg.Surface, camera: Optional[PositionCamera] = None):
        """Draw."""
        draw_rect = self.rect.copy()
        draw_rect.x += self.shake_offset[0]
        draw_rect.y += self.shake_offset[1]

        if self.nine_grid:
            # Use NineGrid to draw
            if camera is not None:
                self.nine_grid.draw(screen, camera.transform_rect(draw_rect))
            else:
                self.nine_grid.draw(screen, draw_rect)
        elif camera is not None:
            screen.blit(self.image, camera.transform_rect(draw_rect))
        else:
            screen.blit(self.image, draw_rect)

    def draw_hitbox(self, screen: pg.Surface, camera: Optional[PositionCamera] = None):
        """Draw hitbox."""
        if camera is not None:
            pg.draw.rect(screen, (255, 0, 0), camera.transform_rect(self.rect), 1)
        else:
            pg.draw.rect(screen, (255, 0, 0), self.rect, 1)

    def update_bar(self, width: int):
        """Update bar."""
        self.rect.width = width
        # Only scale image if not using NineGrid (NineGrid uses rect for dimensions)
        if not self.nine_grid:
            self.image = pg.transform.scale(self._image, (width, self.rect.height))

    def update_height(self, height: int):
        """Update height."""
        self.rect.height = height
        # Only scale image if not using NineGrid (NineGrid uses rect for dimensions)
        if not self.nine_grid:
            self.image = pg.transform.scale(self._image, (self.rect.width, height))

    def update_pos(self, pos: Position):
        """Update pos."""
        self.rect.topleft = round(pos.x), round(pos.y)


class Text:
    """Text."""

    font: pg.font.Font
    text: pg.Surface
    rect: pg.Rect

    def __init__(self, text: str, size: int, color: (tuple[int, int, int] | str)):
        self.size = size
        self.color = color
        self.font = resource_manager.get_font(None, size)
        self.text = self.font.render(text, True, color)
        self.rect = self.text.get_rect()

    def draw(self, screen: pg.Surface):
        """Draw."""
        screen.blit(self.text, self.rect)

    @property
    def image(self) -> pg.Surface:
        """Get the text surface (alias for compatibility)."""
        return self.text

    @image.setter
    def image(self, value: pg.Surface):
        """Set the text surface."""
        self.text = value

    def change_text(
        self,
        text: str,
        pos: str = "topleft",
        color: (tuple[int, int, int] | str) = None,
    ):
        """Change Text."""
        if color:
            self.color = color
        self.font = resource_manager.get_font(None, self.size)
        self.text = self.font.render(text, True, self.color)
        rect = self.text.get_rect()
        setattr(rect, pos, getattr(self.rect, pos))
        self.rect = rect
