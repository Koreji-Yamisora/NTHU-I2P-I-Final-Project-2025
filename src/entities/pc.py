from src.entities.entity import Entity
from src.core import GameManager
from src.utils import Direction, GameSettings, Position, Logger
from src.interface.overlay_pc import PCOverlay
from src.sprites import Sprite, Animation
from src.core.services import input_manager
import pygame


class PCEntity(Entity):
    def __init__(self, x: float, y: float, game_manager: GameManager):
        # Initialize Entity without Npc overhead
        super().__init__(x, y, game_manager)

        # Override default animation with PC sprite
        # Assets check failed, so we use a placeholder or generic sprite.
        # Ideally we'd use a computer sprite.
        # Since I can't find one, I'll use a specific character sprite as PC for now,
        # OR create a single-frame animation from a tile if possible.
        # Let's try to load a known sprite but single frame.
        # Use separate sprite from additional_assets
        # The folder name has a typo "additonal_assets" based on previous ls
        try:
            # Load the PC sprite
            self.animation = Animation(
                "sprites/pc.png",
                ["down"],
                1,
                (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE),
            )
            self.animation.update_pos(self.position)
        except Exception as e:
            # Fallback
            Logger.error(f"Failed to load PC sprite 'images/sprites/pc.png': {e}")
            print(f"Failed to load PC sprite 'images/sprites/pc.png': {e}")
            self.animation = Animation(
                "character/ow6.png",
                ["down"],
                1,
                (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE),
            )
            self.animation.update_pos(self.position)

        self.pc_overlay = PCOverlay()
        self.detected = False
        self.max_tiles = 1
        self.warning_sign = Sprite(
            "exclamation.png",
            (GameSettings.TILE_SIZE // 2, GameSettings.TILE_SIZE // 2),
        )
        self.warning_sign.update_pos(
            Position(x + GameSettings.TILE_SIZE // 4, y - GameSettings.TILE_SIZE // 2)
        )

    def interact(self):
        self.pc_overlay.open()

    def update(self, dt: float) -> None:
        # Standard entity update
        super().update(dt)

        # Line of sight / Proximity check manually since we lost Npc's _has_los_to_player
        self._check_proximity()

        # Update warning sign position in case PC moves (unlikely but good practice) or initial set
        self.warning_sign.update_pos(
            Position(
                self.position.x + GameSettings.TILE_SIZE // 4,
                self.position.y - GameSettings.TILE_SIZE // 2,
            )
        )

        if self.detected:
            if input_manager.key_pressed(pygame.K_SPACE):
                print("DEBUG: PC Interaction triggered!")
                self.interact()

        if self.pc_overlay.is_open:
            self.pc_overlay.update(dt)

    def draw(self, screen: pygame.Surface, camera):
        super().draw(screen, camera)
        if self.detected:
            self.warning_sign.draw(screen, camera)

        if self.detected and GameSettings.DRAW_HITBOXES:
            # Draw some indicator?
            pass

    def _check_proximity(self):
        player = self.game_manager.player
        if not player:
            self.detected = False
            return

        # Simple distance check instead of directional LOS
        dist = self.position.distance_to(player.position)
        if dist <= self.max_tiles * GameSettings.TILE_SIZE * 1.5:  # 1.5 tiles radius
            self.detected = True
        else:
            self.detected = False
