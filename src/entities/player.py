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
import random
from src.core.gm_helper import gh
from src.core.services import scene_manager as sm


class Player(Entity):
    """Player character entity with movement, collision, and pathfinding.

    The player can be controlled via keyboard input or auto-walk pathfinding.
    Handles collision detection, teleportation, warp zones, and bush interactions.

    Attributes:
        speed (float): Movement speed in pixels per second
        position (Position): Current world position
        direction (Direction): Current facing direction
        path (list[Position]): Auto-walk pathfinding queue
        is_moving (bool): Whether player is currently moving

    Example:
        >>> player = Player(x=100, y=100, game_manager=gm)
        >>> player.update(dt)  # Updates position based on input
        >>> player.set_path([(5, 10), (5, 11)])  # Set auto-walk path
    """

    # Type annotations
    speed: float = 8.0 * GameSettings.TILE_SIZE
    SPRINT_MULTIPLIER: float = 1.75  # Speed multiplier when sprinting
    game_manager: GameManager
    tp_cooldown: float
    path: list[Position]
    warning_sign: Sprite
    sm: bool
    lr: bool
    bush_cd: float
    bush_dt: bool
    bush_enter: bool

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
        self.path: list[Position] = []
        # Initialize camera position centered on player initially or at 0,0
        # Check boundaries immediately if possible, but safe default is ok
        self.camera_pos = Position(x, y)

    def set_path(self, path: list[Position]) -> None:
        """Set path."""
        self.path = path

    @override
    def update(self, dt: float) -> None:
        """Update."""
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
        # Check if any overlay is blocking input
        overlay_blocking = False
        if hasattr(sm, "_current_scene") and sm._current_scene:
            scene = sm._current_scene
            if hasattr(scene, "setting_overlay") and scene.setting_overlay.is_open:
                overlay_blocking = True
            elif hasattr(scene, "inventory") and scene.inventory.is_open:
                overlay_blocking = True
            elif hasattr(scene, "chat_overlay") and scene.chat_overlay.is_open:
                overlay_blocking = True
            elif (
                hasattr(scene, "evolution_overlay") and scene.evolution_overlay.is_open
            ):
                overlay_blocking = True
            elif hasattr(scene, "shop_on") and scene.shop_on:
                overlay_blocking = True

        if not overlay_blocking:
            if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
                dis.x -= 1
                self.path = []
            if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
                dis.x += 1
                self.path = []
            if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
                dis.y -= 1
                self.path = []
            if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
                dis.y += 1
                self.path = []

            # Controller Input (Left Joystick)
            if dis.x == 0 and dis.y == 0:
                axis_x = input_manager.get_axis(0)
                axis_y = input_manager.get_axis(1)

                if abs(axis_x) > 0.2:
                    dis.x = axis_x
                    self.path = []
                if abs(axis_y) > 0.2:
                    dis.y = axis_y
                    self.path = []

        if (
            not (dis.x != 0 or dis.y != 0)
            and self.path
            and not gh.gm.should_change_scene
        ):
            target_tile = self.path[0]
            target_pos = Position(
                target_tile.x * GameSettings.TILE_SIZE,
                target_tile.y * GameSettings.TILE_SIZE,
            )
            diff_x = target_pos.x - self.position.x
            diff_y = target_pos.y - self.position.y
            if abs(diff_x) < 4 and abs(diff_y) < 4:
                self.path.pop(0)
                self.position.x = target_pos.x
                self.position.y = target_pos.y
            else:
                # Corner-safe movement: Prioritize alignment
                ALIGN_THRESHOLD = 2.0

                if abs(diff_x) > abs(diff_y):
                    # Trying to move horizontally
                    if abs(diff_y) > ALIGN_THRESHOLD:
                        dis.x = 0  # STOP forward movement
                        dis.y = diff_y  # CORRECT vertical alignment first
                    else:
                        dis.x = diff_x
                        dis.y = diff_y
                else:
                    # Trying to move vertically
                    if abs(diff_x) > ALIGN_THRESHOLD:
                        dis.y = 0  # STOP forward movement
                        dis.x = diff_x  # CORRECT horizontal alignment first
                    else:
                        dis.x = diff_x
                        dis.y = diff_y
        norm = math.sqrt(dis.x**2 + dis.y**2)
        if norm != 0:
            dis.x /= norm
            dis.y /= norm

        # Apply sprint multiplier if Shift is held
        current_speed = self.speed
        if input_manager.key_down(pg.K_LSHIFT) or input_manager.key_down(pg.K_RSHIFT):
            current_speed *= self.SPRINT_MULTIPLIER

        dis.x *= current_speed * dt
        dis.y *= current_speed * dt
        if dis.x != 0 or dis.y != 0:
            self.is_moving = True

            # Determine facing direction
            # If auto-navigating, use the target difference (diff) to avoid twitching during alignment slides
            if self.path:
                target_tile = self.path[0]
                target_pos = Position(
                    target_tile.x * GameSettings.TILE_SIZE,
                    target_tile.y * GameSettings.TILE_SIZE,
                )
                dx = target_pos.x - self.position.x
                dy = target_pos.y - self.position.y

                if abs(dx) > abs(dy):
                    if dx < 0:
                        self.direction = Direction.LEFT
                        self.animation.switch("left")
                    else:
                        self.direction = Direction.RIGHT
                        self.animation.switch("right")
                else:
                    if dy < 0:
                        self.direction = Direction.UP
                        self.animation.switch("up")
                    else:
                        self.direction = Direction.DOWN
                        self.animation.switch("down")
            else:
                # Manual movement: use velocity vector
                if abs(dis.y) > abs(dis.x):
                    if dis.y < 0:
                        self.direction = Direction.UP
                        self.animation.switch("up")
                    else:
                        self.direction = Direction.DOWN
                        self.animation.switch("down")
                elif dis.x < 0:
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
        # Collision Handling with Sub-pixel precision (Wall Sliding)
        # Use a smaller hitbox for collision to allow passing through tight gaps
        # Rect is 64x64, we want ~40x40 for collision -> inset by ~12px each side (-24 total)
        HITBOX_INSET = -24

        # 1. Test X Movement
        next_x = self.position.x + dis.x
        test_rect_x = self.animation.rect.copy()
        test_rect_x.x = int(next_x)

        # Shrink the rect for collision check only
        collision_rect_x = test_rect_x.inflate(HITBOX_INSET, HITBOX_INSET)

        if self.game_manager.check_collision(collision_rect_x):
            dis.x = 0  # Block X movement
        else:
            self.position.x = next_x

        # 2. Test Y Movement
        next_y = self.position.y + dis.y
        test_rect_y = self.animation.rect.copy()
        test_rect_y.x = int(self.position.x)  # Use validated X
        test_rect_y.y = int(next_y)

        collision_rect_y = test_rect_y.inflate(HITBOX_INSET, HITBOX_INSET)

        if self.game_manager.check_collision(collision_rect_y):
            dis.y = 0  # Block Y movement
        else:
            self.position.y = next_y
        if self.tp_cooldown > 0:
            self.tp_cooldown -= dt
        elif self.tp_cooldown <= 0:
            self.animation.update_pos(self.position)
            tp = self.game_manager.current_map.check_teleport(self.animation.rect)
            if tp:
                dest = tp.destination
                if dest != self.game_manager.current_map_key:
                    self.game_manager.switch_map(dest, tp.to_pos)
                    self.tp_cooldown = 0.5
        self.warning_sign.update_pos(
            Position(self.animation.rect.left + 16, self.animation.rect.top - 30)
        )
        self.bush_cd -= dt
        # New Bush Mechanics:
        # 1. Check if in bush
        if self.game_manager.check_bush(self.animation.rect):
            # 2. Only check if moving and cooldown expired
            if self.is_moving and self.bush_cd <= 0:
                self.bush_cd = 0.5  # Check every 0.5s walking in bush

                # 3. 40% chance encounter
                if random.random() < 0.4:
                    # 4. Check for alive pokemon
                    if not gh.gm.bag.has_alive_pokemon():
                        # Maybe show popup? or just ignore
                        pass
                    else:
                        self.bush_dt = True  # Show exclamation
                        self.bush_enter = True  # Flag to enter battle
                        # Stop player? (For now we just let them slide into it)

        # If bush_enter flag is set, wait a brief moment (popup) then start
        if self.bush_enter and self.bush_dt:
            # Just use a timer or speed up entrance
            # For simplicity, trigger immediately after one frame of popup?
            # Or we can let it linger. Let's trigger interact() on Bush class which we will modify
            getattr(scene_manager._current_scene, "bush").interact()
            self.bush_enter = False
            self.bush_dt = False
            self.bush_cd = 3.0  # Global cooldown after fight

        # Smooth Camera Logic
        if self.game_manager.current_map:
            map_width = (
                self.game_manager.current_map.tmxdata.width * GameSettings.TILE_SIZE
            )
            map_height = (
                self.game_manager.current_map.tmxdata.height * GameSettings.TILE_SIZE
            )
            screen_width = GameSettings.SCREEN_WIDTH
            screen_height = GameSettings.SCREEN_HEIGHT

            # Calculate target position (centered on player)
            target_x = self.position.x - screen_width // 2
            target_y = self.position.y - screen_height // 2

            # Clamp to map boundaries
            target_x = max(0, min(target_x, map_width - screen_width))
            target_y = max(0, min(target_y, map_height - screen_height))

            # Lerp towards target
            lerp_speed = 5.0
            self.camera_pos.x += (target_x - self.camera_pos.x) * lerp_speed * dt
            self.camera_pos.y += (target_y - self.camera_pos.y) * lerp_speed * dt

        super().update(dt)

    @property
    @override
    def camera(self) -> PositionCamera:
        """Get the smoothed camera position."""
        return PositionCamera(int(self.camera_pos.x), int(self.camera_pos.y))

    @override
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        """Draw."""
        super().draw(screen, camera)
        if self.bush_dt:
            self.warning_sign.draw(screen, camera)

        # Draw breadcrumbs for auto-navigation path
        if self.path:
            for tile_pos in self.path:
                # Calculate world position (center of tile)
                world_x = (
                    tile_pos.x * GameSettings.TILE_SIZE + GameSettings.TILE_SIZE // 2
                )
                world_y = (
                    tile_pos.y * GameSettings.TILE_SIZE + GameSettings.TILE_SIZE // 2
                )

                # Transform to screen coordinates
                screen_pos = camera.transform_position(Position(world_x, world_y))

                # Draw the breadcrumb (small circle)
                pg.draw.circle(screen, (0, 191, 255), screen_pos, 4)  # Deep Sky Blue

    @override
    def to_dict(self) -> dict[str, object]:
        """To Dict."""
        return super().to_dict()

    @classmethod
    @override
    def from_dict(cls, data: dict[str, object], game_manager: GameManager) -> Player:
        """From Dict."""
        return cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager,
        )


class Bush:
    """Bush."""

    def __init__(self) -> None:
        self.monsters = None

    def interact(self):
        """Interact."""
        # Double check party just in case called manually (though currently only via update)
        if not gh.gm.bag.has_alive_pokemon():
            return

        if not self.monsters:
            self.monsters = generate_party(gh.gm.player_level, 1)
            gh.gm.current_fight = self
            scene_manager.change_scene("encounter")
        else:
            self.monsters.clear()
            self.monsters = generate_party(gh.gm.player_level, 1)
            gh.gm.current_fight = self
            scene_manager.change_scene("encounter")
