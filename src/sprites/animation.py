import pygame as pg
from .sprite import Sprite
from src.utils import GameSettings, Logger, PositionCamera
from typing import Optional, Callable


class Animation(Sprite):
    """Animation."""

    animations: dict[str, list[pg.Surface]]
    cur_row: str
    accumulator: float
    loop: float
    n_keyframes: int

    def __init__(
        self,
        image_path: str,
        rows: list[str],
        n_keyframes: int,
        size: tuple[int, int],
        loop: float = 1,
    ):
        super().__init__(image_path)
        sheet_w, sheet_h = self.image.get_size()
        frame_w = sheet_w // n_keyframes
        frame_h = sheet_h // len(rows)
        if len(rows) <= 0 or n_keyframes <= 0:
            Logger.error("Invalid number of rows")
        self.animations = {}
        for r, name in enumerate(rows):
            anim: list[pg.Surface] = []
            for c in range(n_keyframes):
                frame = self.image.subsurface(
                    pg.Rect(c * frame_w, r * frame_h, frame_w, frame_h)
                )
                anim.append(pg.transform.smoothscale(frame, size))
            self.animations[name] = anim
        self.accumulator = 0
        self.cur_row = rows[0]
        self.loop = loop
        self.n_keyframes = n_keyframes
        self.rect = pg.Rect(0, 0, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)

    def switch(self, name: str):
        """Switch."""
        if name not in self.animations:
            Logger.error(f"name {name} not in animations list!")
        if name == self.cur_row:
            return
        self.cur_row = name
        self.accumulator = 0

    def update(self, dt: float):
        """Update."""
        self.accumulator = (self.accumulator + dt) % self.loop

    def draw(self, screen: pg.Surface, camera: Optional[PositionCamera] = None):
        """Draw."""
        frames = self.animations[self.cur_row]
        idx = int(self.accumulator / self.loop * self.n_keyframes)
        if camera:
            screen.blit(frames[idx], camera.transform_rect(self.rect))
        else:
            screen.blit(frames[idx], self.rect)


class SequenceAnimation(Sprite):
    """Sequence of separate images for animation."""

    frames: list[pg.Surface]
    duration: float
    accumulator: float
    is_playing: bool
    on_finish: Optional[Callable] = None

    def __init__(self, folder_path: str, duration: float = 1.0, size: tuple[int, int] | None = None):
        # We don't use the parent __init__ because we load multiple images
        self.frames = []
        try:
            from src.core.services import resource_manager
            import os
            
            base_path = os.path.join("assets", "images", folder_path)
            if not os.path.exists(base_path):
                 base_path = os.path.join("graphics", "other", folder_path)

            if os.path.exists(base_path):
                files = sorted([f for f in os.listdir(base_path) if f.endswith(".png")])
                for f in files:
                    img = pg.image.load(os.path.join(base_path, f))
                    
                    # If it's a typical sparkle/effect, it often needs black as colorkey
                    # even if it has an alpha channel (sometimes exported poorly)
                    if not img.get_flags() & pg.SRCALPHA:
                         img.set_colorkey((0, 0, 0))
                    
                    img = img.convert_alpha()
                    if size:
                        img = pg.transform.smoothscale(img, size)
                    self.frames.append(img)
            else:
                Logger.error(f"SequenceAnimation: Path not found {folder_path} (checked {base_path})")

        except Exception as e:
            Logger.error(f"Failed to load sequence animation from {folder_path}: {e}")

        # Fallback
        if not self.frames:
            surface = pg.Surface(size if size else (32, 32), pg.SRCALPHA)
            surface.fill((255, 0, 255, 0))
            self.frames = [surface]

        # Initialize Sprite attributes before setting self.image (which triggers setter)
        self.nine_grid_margins = None
        self.nine_grid = None
        self.shake_offset = (0, 0)
        self.shake_timer = 0.0
        self.shake_intensity = 0
        self.flash_timer = 0.0
        self.flash_color = None
        self._alpha = 255

        self._image = self.frames[0]
        self.rect = self._image.get_rect()
        self.duration = duration
        self.accumulator = 0
        self.is_playing = False

    def set_alpha(self, value: int):
        """Set transparency for the animation."""
        self._alpha = value

    def get_alpha(self) -> int:
        """Get current transparency value."""
        return self._alpha

    def play(self, callback: Optional[Callable] = None):
        """Start animation."""
        self.accumulator = 0
        self.is_playing = True
        self.on_finish = callback
        
    def update(self, dt: float):
        """Update."""
        if not self.is_playing:
            return
            
        self.accumulator += dt
        if self.accumulator >= self.duration:
            self.accumulator = self.duration
            self.is_playing = False
            if self.on_finish:
                self.on_finish()
                self.on_finish = None
        
        # Update current frame
        if self.frames:
            idx = int((self.accumulator / self.duration) * (len(self.frames) - 1))
            idx = max(0, min(idx, len(self.frames) - 1))
            self._image = self.frames[idx]

    def draw(self, screen: pg.Surface, camera: Optional[PositionCamera] = None):
        """Draw."""
        if self.is_playing:
            draw_image = self._image
            if self._alpha < 255:
                 # Create a copy to avoid modifying the original and apply alpha
                 draw_image = self._image.copy()
                 draw_image.set_alpha(self._alpha)
            
            if camera:
                screen.blit(draw_image, camera.transform_rect(self.rect))
            else:
                screen.blit(draw_image, self.rect)
