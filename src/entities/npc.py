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
from src.utils import Logger
from src.utils.generate import new_iv, new_ev, generate_party
from src.interface.overlay_shop import Shop


class NpcClassification(Enum):
    """Npc Classification."""
    STATIONARY = 'stationary'


@dataclass
class IdleMovement:
    """Idle Movement."""

    def update(self, npc: Npc, dt: float) ->None:
        """Update."""
        return


class Npc(Entity):
    """Non-player character with line-of-sight detection and shop interactions.
    
    NPCs can be stationary or have movement patterns. They detect the player
    within their line-of-sight cone and can be interacted with to open shops
    or initiate conversations.
    
    Attributes:
        classification (NpcClassification): NPC behavior type (stationary, etc.)
        max_tiles (int): Line-of-sight range in tiles
        detected (bool): Whether player is in line-of-sight
        shop_data (list): Shop inventory data if this NPC is a shopkeeper
        facing (Direction): Direction the NPC is facing
        
    Example:
        >>> npc = Npc(x=100, y=200, gm, facing=Direction.DOWN)
        >>> npc.update(dt)  # Updates LOS detection
        >>> if npc.detected:
        ...     npc.interact()  # Opens shop or dialogue
    """
    # Type annotations
    classification: NpcClassification
    max_tiles: int | None
    _movement: IdleMovement
    warning_sign: Sprite
    detected: bool
    los_direction: Direction
    shop_data: list | None
    level: int
    facing: Direction
    shop_ov: Shop

    @override
    def __init__(self, x: float, y: float, game_manager: GameManager,
        classification: NpcClassification=NpcClassification.STATIONARY,
        max_tiles: (int | None)=2, shop_data: (list | None)=None, facing: (
        Direction | None)=None, level: int=random.randint(20, 40)) ->None:
        super().__init__(x, y, game_manager)
        self.shop_data = shop_data
        self.level = level
        self.classification = classification
        self.max_tiles = max_tiles
        if classification == NpcClassification.STATIONARY:
            self._movement = IdleMovement()
            if facing is None:
                raise ValueError(
                    "Idle npcTrainer requires a 'facing' Direction at instantiation"
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
        if self.shop_data:
            self.shop_ov = Shop(self.shop_data)

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
        if self.shop_data:
            self.shop_ov.update(dt)
            if not self.shop_ov.is_open:
                self.shop_ov.timer_tick(dt)

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
        if self.shop_data:
            self.shop_ov.draw(screen)

    def interact(self):
        """Interact."""
        Logger.info('Interacting with npc')
        self.shop_ov.open()

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
        npc_rect = self.animation.rect
        los_length = self.max_tiles * GameSettings.TILE_SIZE
        if self.los_direction == Direction.UP:
            los_rect = pygame.Rect(npc_rect.centerx - npc_rect.width // 2, 
                npc_rect.top - los_length, npc_rect.width, los_length)
        elif self.los_direction == Direction.DOWN:
            los_rect = pygame.Rect(npc_rect.centerx - npc_rect.width // 2,
                npc_rect.bottom, npc_rect.width, los_length)
        elif self.los_direction == Direction.LEFT:
            los_rect = pygame.Rect(npc_rect.left - los_length, npc_rect.
                centery - npc_rect.height // 2, los_length, npc_rect.height)
        elif self.los_direction == Direction.RIGHT:
            los_rect = pygame.Rect(npc_rect.right, npc_rect.centery - 
                npc_rect.height // 2, los_length, npc_rect.height)
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
    def from_dict(cls, data: dict, game_manager: GameManager) ->Npc:
        """From Dict."""
        classification = NpcClassification(data.get('classification',
            'stationary'))
        max_tiles = data.get('max_tiles')
        facing_val = data.get('facing')
        facing: Direction | None = None
        if facing_val is not None:
            if isinstance(facing_val, str):
                facing = Direction[facing_val]
            elif isinstance(facing_val, Direction):
                facing = facing_val
        if facing is None and classification == NpcClassification.STATIONARY:
            facing = Direction.DOWN
        shop_data = data.get('shop')
        return cls(data['x'] * GameSettings.TILE_SIZE, data['y'] *
            GameSettings.TILE_SIZE, game_manager, classification, max_tiles,
            shop_data, facing)

    @override
    def to_dict(self) ->dict[str, object]:
        """To Dict."""
        base: dict[str, object] = super().to_dict()
        base['classification'] = self.classification.value
        base['facing'] = self.direction.name
        base['max_tiles'] = self.max_tiles
        base['shop'] = self.shop_ov.shop_data
        return base
