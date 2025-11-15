from __future__ import annotations
import pygame as pg
from .entity import Entity
from src.core.services import input_manager
from src.utils import Position, PositionCamera, GameSettings, Logger, Direction
from src.core import GameManager
import math
from typing import override


class Player(Entity):
    speed: float = 4.0 * GameSettings.TILE_SIZE
    game_manager: GameManager
    tp_cooldown: float

    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        super().__init__(x, y, game_manager)
        self.tp_cooldown = 0.0

    @override
    def update(self, dt: float) -> None:
        dis = Position(0, 0)
        """
        [TODO HACKATHON 2]
        Calculate the distance change, and then normalize the distance
        
        [TODO HACKATHON 4]
        Check if there is collision, if so try to make the movement smooth
        Hint #1 : use entity.py _snap_to_grid function or create a similar function
        Hint #2 : Beware of glitchy movement, you must do
                    1. Update X
                    2. If collide, snap to grid
                    3. Update Y
                    4. If collide, snap to grid
                  instead of update both x, y, then snap to grid
        
        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            dis.x -= ...
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            dis.x += ...
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            dis.y -= ...
        if input_manager.key_down(jpg.K_DOWN) or input_manager.key_down(pg.K_s):
            dis.y += ...
        
        self.position = ...
        """

        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            dis.x -= 1
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            dis.x += 1
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            dis.y -= 1
        if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
            dis.y += 1

        norm = math.sqrt(dis.x**2 + dis.y**2)
        if norm != 0:
            dis.x /= norm
            dis.y /= norm

        dis.x *= self.speed * dt
        dis.y *= self.speed * dt

        if dis.x != 0 or dis.y != 0:
            if abs(dis.y) > abs(dis.x):
                if dis.y < 0:
                    self.direction = Direction.UP
                    self.animation.switch("up")
                else:
                    self.direction = Direction.DOWN
                    self.animation.switch("down")
            else:
                if dis.x < 0:
                    self.direction = Direction.LEFT
                    self.animation.switch("left")
                else:
                    self.direction = Direction.RIGHT
                    self.animation.switch("right")

        np_rectx = self.animation.rect.copy()
        np_rectx.x += int(dis.x)

        if self.game_manager.check_collision(np_rectx):
            self.position.x = self._snap_to_grid(self.position.x)
        else:
            self.position.x += dis.x

        np_recty = self.animation.rect.copy()
        np_recty.y += int(dis.y)
        if self.game_manager.check_collision(np_recty):
            self.position.y = self._snap_to_grid(self.position.y)
        else:
            self.position.y += dis.y

        if self.tp_cooldown > 0:
            self.tp_cooldown -= dt
        elif self.tp_cooldown <= 0:
            self.animation.update_pos(self.position)

            warp = self.game_manager.current_map.check_warp(self.animation.rect)
            if warp:
                self.game_manager.warp(warp)
                self.tp_cooldown = 0.5
            else:
                tp = self.game_manager.current_map.check_teleport(self.animation.rect)
                if tp:
                    dest = tp.destination
                    if dest != self.game_manager.current_map_key:
                        self.game_manager.switch_map(dest)
                        self.tp_cooldown = 0.5

        super().update(dt)

    @override
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)

    @override
    def to_dict(self) -> dict[str, object]:
        return super().to_dict()

    @classmethod
    @override
    def from_dict(cls, data: dict[str, object], game_manager: GameManager) -> Player:
        return cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager,
        )
