from __future__ import annotations
import pygame
from enum import Enum
from dataclasses import dataclass
from typing import override
from .entity import Entity
from src.sprites import Sprite
from src.core import GameManager
from src.core.services import input_manager, scene_manager
from src.utils import GameSettings, Direction, Position, PositionCamera
import random
from src.utils.generate import new_iv, new_ev, generate_party


class EnemyTrainerClassification(Enum):
    """Enemy Trainer Classification."""
    STATIONARY = 'stationary'


@dataclass
class IdleMovement:
    """Idle Movement."""

    def update(self, enemy: 'EnemyTrainer', dt: float) ->None:
        """Update."""
        return


class EnemyTrainer(Entity):
    """Enemy Trainer."""
    classification: EnemyTrainerClassification
    max_tiles: int | None
    _movement: IdleMovement
    warning_sign: Sprite
    detected: bool
    los_direction: Direction
    level: int

    @override
    def __init__(self, x: float, y: float, game_manager: GameManager,
        classification: EnemyTrainerClassification=
        EnemyTrainerClassification.STATIONARY, max_tiles: (int | None)=2,
        facing: (Direction | None)=None, level: int=random.randint(20, 40)
        ) ->None:
        super().__init__(x, y, game_manager)
        self.level = level
        self.classification = classification
        self.max_tiles = max_tiles
        if classification == EnemyTrainerClassification.STATIONARY:
            self._movement = IdleMovement()
            if facing is None:
                raise ValueError(
                    "Idle EnemyTrainer requires a 'facing' Direction at instantiation"
                    )
            self._set_direction(facing)
            self.facing = facing
        else:
            raise ValueError('Invalid classification')
        self.warning_sign = Sprite('exclamation.png', (GameSettings.
            TILE_SIZE // 2, GameSettings.TILE_SIZE // 2))
        self.warning_sign.update_pos(Position(x + GameSettings.TILE_SIZE //
            4, y - GameSettings.TILE_SIZE // 2))
        self.detected = False
        self.monsters = []

    @override
    def refresh_direction(self):
        """Refresh Direction."""
        self._set_direction(self.facing)

    @override
    def update(self, dt: float) ->None:
        """Update."""
        self._movement.update(self, dt)
        self._has_los_to_player()
        if self.detected and input_manager.key_pressed(pygame.K_SPACE):
            self.interact()
        self.animation.update_pos(self.position)

    @override
    def draw(self, screen: pygame.Surface, camera: PositionCamera) ->None:
        """Draw."""
        super().draw(screen, camera)
        if self.detected:
            self.warning_sign.draw(screen, camera)
        if GameSettings.DRAW_HITBOXES:
            los_rect = self._get_los_rect()
            if los_rect is not None:
                pygame.draw.rect(screen, (255, 255, 0), camera.
                    transform_rect(los_rect), 1)

    def interact(self):
        """Interact."""
        if not self.monsters:
            self.monsters = generate_party(40)
            scene_manager.change_scene('battle')
        else:
            self.monsters.clear()
            self.monsters = generate_party(40)
            scene_manager.change_scene('battle')

    def _set_direction(self, direction: Direction) ->None:
        self.direction = direction
        if direction == Direction.RIGHT:
            self.animation.switch('right')
        elif direction == Direction.LEFT:
            self.animation.switch('left')
        elif direction == Direction.DOWN:
            self.animation.switch('down')
        else:
            self.animation.switch('up')
        self.los_direction = self.direction

    def _get_los_rect(self) ->(pygame.Rect | None):
        if self.max_tiles is None:
            return None
        enemy_rect = self.animation.rect
        los_length = self.max_tiles * GameSettings.TILE_SIZE
        if self.los_direction == Direction.UP:
            los_rect = pygame.Rect(enemy_rect.centerx - enemy_rect.width //
                2, enemy_rect.top - los_length, enemy_rect.width, los_length)
        elif self.los_direction == Direction.DOWN:
            los_rect = pygame.Rect(enemy_rect.centerx - enemy_rect.width //
                2, enemy_rect.bottom, enemy_rect.width, los_length)
        elif self.los_direction == Direction.LEFT:
            los_rect = pygame.Rect(enemy_rect.left - los_length, enemy_rect
                .centery - enemy_rect.height // 2, los_length, enemy_rect.
                height)
        elif self.los_direction == Direction.RIGHT:
            los_rect = pygame.Rect(enemy_rect.right, enemy_rect.centery - 
                enemy_rect.height // 2, los_length, enemy_rect.height)
        else:
            return None
        return los_rect

    def _has_los_to_player(self) ->None:
        player = self.game_manager.player
        if player is None:
            self.detected = False
            return
        los_rect = self._get_los_rect()
        if los_rect is None:
            self.detected = False
            return
        if player.animation.rect.colliderect(los_rect):
            self.detected = True
        else:
            self.detected = False

    @classmethod
    @override
    def from_dict(cls, data: dict, game_manager: GameManager) ->'EnemyTrainer':
        """From Dict."""
        classification = EnemyTrainerClassification(data.get(
            'classification', 'stationary'))
        max_tiles = data.get('max_tiles')
        facing_val = data.get('facing')
        facing: Direction | None = None
        if facing_val is not None:
            if isinstance(facing_val, str):
                facing = Direction[facing_val]
            elif isinstance(facing_val, Direction):
                facing = facing_val
        if (facing is None and classification == EnemyTrainerClassification
            .STATIONARY):
            facing = Direction.DOWN
        return cls(data['x'] * GameSettings.TILE_SIZE, data['y'] *
            GameSettings.TILE_SIZE, game_manager, classification, max_tiles,
            facing)

    @override
    def to_dict(self) ->dict[str, object]:
        """To Dict."""
        base: dict[str, object] = super().to_dict()
        base['classification'] = self.classification.value
        base['facing'] = self.direction.name
        base['max_tiles'] = self.max_tiles
        return base
