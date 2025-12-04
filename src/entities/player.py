from __future__ import annotations
import pygame as pg
from .entity import Entity
from src.core.services import input_manager, scene_manager
from src.utils import Position, PositionCamera, GameSettings, Logger, Direction
from src.core import GameManager
import math
from typing import override
from src.sprites import Sprite, Animation
from src.utils.generate import generate_party


class Player(Entity):
    speed: float = 8.0 * GameSettings.TILE_SIZE
    game_manager: GameManager
    tp_cooldown: float

    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        super().__init__(x, y, game_manager)
        self.tp_cooldown = 0.0
        self.sm = False
        self.lr = True
        self.bush_cd = 0.0
        self.bush_dt = False
        self.bush_enter = False
        self.warning_sign = Sprite(
            "exclamation.png",
            (GameSettings.TILE_SIZE // 2, GameSettings.TILE_SIZE // 2),
        )

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
            self.is_moving = True
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
        else:
            self.is_stop = True
        if self.is_stop:
            self.animation.accumulator = 0
            if self.is_moving:
                self.sm = True
                self.is_stop = False

        if self.sm:
            if self.lr:
                self.animation.accumulator = 0.25
            else:
                self.animation.accumulator = 0.75
            self.lr = not self.lr

            self.sm = False
            self.is_moving = False

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

        # bush
        self.warning_sign.update_pos(
            Position(self.animation.rect.left + 16, self.animation.rect.top - 30)
        )
        self.bush_cd -= dt
        if self.game_manager.check_bush(self.animation.rect) and self.bush_cd <= 0:
            self.bush_dt = True
            if input_manager.key_down(pg.K_SPACE):
                getattr(scene_manager._current_scene, "bush").interact()

                self.bush_cd = 2

        else:
            self.bush_dt = False

        super().update(dt)

    @override
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        if self.bush_dt:
            self.warning_sign.draw(screen, camera)

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


class Bush:
    def __init__(self) -> None:
        self.monsters = None

    def interact(self):
        if not self.monsters:
            self.monsters = generate_party(40, 1)
            scene_manager.change_scene("encounter")
        else:
            self.monsters.clear()
            self.monsters = generate_party(40, 1)
            scene_manager.change_scene("encounter")
