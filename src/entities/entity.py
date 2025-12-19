from __future__ import annotations
import pygame as pg
from typing import override
from src.sprites import Animation
from src.utils import Position, PositionCamera, Direction, GameSettings
from src.core.services import resource_manager


class Entity:
    """Entity."""

    animation: Animation
    direction: Direction
    position: Position
    game_manager: GameManager
    shadow_img: pg.Surface

    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        self.animation = Animation(
            "character/ow1.png",
            ["down", "left", "right", "up"],
            4,
            (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE),
        )
        self.position = Position(x, y)
        self.direction = Direction.DOWN
        self.skin_idx = 0
        self.animation.update_pos(self.position)
        self.game_manager = game_manager
        self.is_moving = False
        self.is_stop = True

        # Create valid shadow programmatically to ensure transparency
        # Use an ellipse drawn on an alpha surface
        s_width = GameSettings.TILE_SIZE // 1.5
        s_height = GameSettings.TILE_SIZE // 3
        self.shadow_img = pg.Surface((s_width, s_height), pg.SRCALPHA)
        pg.draw.ellipse(self.shadow_img, (0, 0, 0, 100), self.shadow_img.get_rect())

    def change_skin(self, skin_idx: int) -> None:
        """Change Skin."""
        x = skin_idx % 6 + 2
        self.animation = Animation(
            f"character/ow{x}.png",
            ["down", "left", "right", "up"],
            4,
            (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE),
        )
        self.skin_idx = skin_idx
        self.refresh_direction()
        self.animation.update_pos(self.position)

    def refresh_direction(self) -> None:
        """Refresh Direction."""
        ...

    def update(self, dt: float) -> None:
        """Update."""
        self.animation.update_pos(self.position)
        self.animation.update(dt)

    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        """Draw."""
        # Draw Shadow
        shadow_rect = self.shadow_img.get_rect()
        sprite_rect = self.animation.rect
        shadow_rect.centerx = sprite_rect.centerx
        shadow_rect.bottom = (
            sprite_rect.bottom + 8
        )  # Slightly below or exactly at bottom

        screen.blit(self.shadow_img, camera.transform_rect(shadow_rect))

        self.animation.draw(screen, camera)
        if GameSettings.DRAW_HITBOXES:
            self.animation.draw_hitbox(screen, camera)

    @staticmethod
    def _snap_to_grid(value: float) -> int:
        return round(value / GameSettings.TILE_SIZE) * GameSettings.TILE_SIZE

    @property
    def camera(self) -> PositionCamera:
        """
        [TODO HACKATHON 3]
        Implement the correct algorithm of player camera
        """
        width = GameSettings.SCREEN_WIDTH // 2
        height = GameSettings.SCREEN_HEIGHT // 2
        cam_x = self.position.x - width
        cam_y = self.position.y - height
        return PositionCamera(int(cam_x), int(cam_y))

    def to_dict(self) -> dict[str, object]:
        """To Dict."""
        return {
            "x": self.position.x / GameSettings.TILE_SIZE,
            "y": self.position.y / GameSettings.TILE_SIZE,
        }

    @classmethod
    def from_dict(
        cls, data: dict[str, float | int], game_manager: GameManager
    ) -> Entity:
        """From Dict."""
        x = float(data["x"])
        y = float(data["y"])
        return cls(x * GameSettings.TILE_SIZE, y * GameSettings.TILE_SIZE, game_manager)
