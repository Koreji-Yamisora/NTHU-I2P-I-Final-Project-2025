from __future__ import annotations
from src.utils import Logger, GameSettings, Position, Teleport, Direction
import json, os
import pygame as pg
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.maps.map import Map
    from src.entities.player import Player
    from src.entities.enemy_trainer import EnemyTrainer
    from src.data.bag import Bag


class GameManager:
    # Entities
    player: Player | None
    enemy_trainers: dict[str, list[EnemyTrainer]]
    bag: "Bag"

    # Map properties
    current_map_key: str
    maps: dict[str, Map]
    player_spawns: dict[str, Position]

    # Changing Scene properties
    should_change_scene: bool
    next_map: str
    previous_map: str  # Store the map we came from for teleport positioning

    def __init__(
        self,
        maps: dict[str, Map],
        start_map: str,
        player: Player | None,
        enemy_trainers: dict[str, list[EnemyTrainer]],
        bag: Bag | None = None,
        player_spawns: dict[str, Position] | None = None,
    ):
        from src.data.bag import Bag

        # Game Properties
        self.maps = maps
        self.current_map_key = start_map
        self.player = player
        self.enemy_trainers = enemy_trainers
        self.bag = bag if bag is not None else Bag([], [])
        self.player_spawns = player_spawns if player_spawns is not None else {}

        # Check If you should change scene
        self.should_change_scene = False
        self.next_map = ""
        self.previous_map = ""

    @property
    def current_map(self) -> Map:
        return self.maps[self.current_map_key]

    @property
    def current_enemy_trainers(self) -> list[EnemyTrainer]:
        return self.enemy_trainers[self.current_map_key]

    @property
    def current_teleporter(self) -> list[Teleport]:
        return self.maps[self.current_map_key].teleporters

    def switch_map(self, target: str) -> None:
        if target not in self.maps:
            Logger.warning(f"Map '{target}' not loaded; cannot switch.")
            return

        # Store where we're coming from before switching
        self.previous_map = self.current_map_key
        self.next_map = target
        self.should_change_scene = True

    def try_switch_map(self) -> None:
        if self.should_change_scene:
            self.current_map_key = self.next_map
            self.next_map = ""
            self.should_change_scene = False
            if self.player:
                destination_map = self.maps[self.current_map_key]
                
                # Try to find a teleporter pointing back to where we came from
                teleporter_pos = None
                if self.previous_map:
                    for teleporter in destination_map.teleporters:
                        if teleporter.destination == self.previous_map:
                            teleporter_pos = teleporter.pos
                            break
                
                # If teleporter found, try offset in player direction first
                # If that collides, use teleporter position (no offset)
                if teleporter_pos:
                    # Calculate offset in player's facing direction
                    offset_x = 0
                    offset_y = 0
                    
                    if self.player.direction == Direction.DOWN:
                        offset_y = GameSettings.TILE_SIZE  # Exit below teleporter
                    elif self.player.direction == Direction.UP:
                        offset_y = -GameSettings.TILE_SIZE  # Exit above teleporter
                    elif self.player.direction == Direction.RIGHT:
                        offset_x = GameSettings.TILE_SIZE  # Exit to the right of teleporter
                    elif self.player.direction == Direction.LEFT:
                        offset_x = -GameSettings.TILE_SIZE  # Exit to the left of teleporter
                    # If direction is NONE, no offset (use teleporter position)
                    
                    # Calculate the offset position
                    offset_pos = Position(
                        teleporter_pos.x + offset_x,
                        teleporter_pos.y + offset_y
                    )
                    
                    # Create a test rect to check collision
                    test_rect = pg.Rect(
                        offset_pos.x,
                        offset_pos.y,
                        GameSettings.TILE_SIZE,
                        GameSettings.TILE_SIZE
                    )
                    
                    # Use offset position if it's safe (no collision)
                    # Otherwise use teleporter position directly (no offset)
                    if not self.check_collision(test_rect):
                        self.player.position = offset_pos
                    else:
                        # If player direction has collision, use teleporter position (no offset)
                        self.player.position = teleporter_pos.copy()
                else:
                    spawn_pos = destination_map.spawn
                    if self.current_map_key in self.player_spawns:
                        spawn_pos = self.player_spawns[self.current_map_key]
                    self.player.position = spawn_pos
                
                # Update animation position immediately after teleporting
                self.player.animation.update_pos(self.player.position)

    def check_collision(self, rect: pg.Rect) -> bool:
        if self.maps[self.current_map_key].check_collision(rect):
            return True
        for entity in self.enemy_trainers[self.current_map_key]:
            if rect.colliderect(entity.animation.rect):
                return True

        return False

    def save(self, path: str) -> None:
        try:
            with open(path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
            Logger.info(f"Game saved to {path}")
        except Exception as e:
            Logger.warning(f"Failed to save game: {e}")

    @classmethod
    def load(cls, path: str) -> "GameManager | None":
        if not os.path.exists(path):
            Logger.error(f"No file found: {path}, ignoring load function")
            return None

        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, object]:
        map_blocks: list[dict[str, object]] = []
        for key, m in self.maps.items():
            block = m.to_dict()
            block["enemy_trainers"] = [
                t.to_dict() for t in self.enemy_trainers.get(key, [])
            ]
            # Use player_spawns if available, otherwise use map spawn
            spawn = self.player_spawns.get(key)
            if spawn is None:
                spawn = m.spawn
            block["player"] = {
                "x": spawn.x / GameSettings.TILE_SIZE,
                "y": spawn.y / GameSettings.TILE_SIZE,
            }
            map_blocks.append(block)
        return {
            "map": map_blocks,
            "current_map": self.current_map_key,
            "player": self.player.to_dict() if self.player is not None else None,
            "bag": self.bag.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "GameManager":
        from src.maps.map import Map
        from src.entities.player import Player
        from src.entities.enemy_trainer import EnemyTrainer
        from src.data.bag import Bag

        Logger.info("Loading maps")
        maps_data = data["map"]
        maps: dict[str, Map] = {}
        player_spawns: dict[str, Position] = {}
        trainers: dict[str, list[EnemyTrainer]] = {}

        for entry in maps_data:
            path = entry["path"]
            maps[path] = Map.from_dict(entry)
            sp = entry.get("player")
            if sp:
                player_spawns[path] = Position(
                    sp["x"] * GameSettings.TILE_SIZE, sp["y"] * GameSettings.TILE_SIZE
                )
        current_map = data["current_map"]
        gm = cls(
            maps,
            current_map,
            None,  # Player
            trainers,
            bag=None,
            player_spawns=player_spawns,
        )
        gm.current_map_key = current_map

        Logger.info("Loading enemy trainers")
        for m in data["map"]:
            raw_data = m["enemy_trainers"]
            gm.enemy_trainers[m["path"]] = [
                EnemyTrainer.from_dict(t, gm) for t in raw_data
            ]

        Logger.info("Loading Player")
        if data.get("player"):
            gm.player = Player.from_dict(data["player"], gm)

        Logger.info("Loading bag")
        from src.data.bag import Bag as _Bag

        gm.bag = Bag.from_dict(data.get("bag", {})) if data.get("bag") else _Bag([], [])

        return gm
