from __future__ import annotations
from src.utils import Logger, GameSettings, Position, Teleport, Direction
import json
import os
import pygame as pg
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.maps.map import Map
    from src.entities.player import Player, Bush
    from src.entities.enemy_trainer import EnemyTrainer, EnemyTrainerClassification
    from src.entities.npc import Npc
    from src.data.bag import Bag


class GameManager:
    """Game  management system."""

    player: Player | None
    enemy_trainers: dict[str, list[EnemyTrainer]]
    npcs: dict[str, list[Npc]]
    bag: Bag
    current_map_key: str
    maps: dict[str, Map]
    player_spawns: dict[str, Position]
    should_change_scene: bool
    next_map: str
    next_spawn_pos: Position | None
    previous_map: str
    player_level: int
    fight_count: int
    username: str = "Player"

    def __init__(
        self,
        maps: dict[str, Map],
        start_map: str,
        player: (Player | None),
        enemy_trainers: dict[str, list[EnemyTrainer]],
        npcs: dict[str, list[Npc]],
        bag: (Bag | None) = None,
        player_spawns: (dict[str, Position] | None) = None,
        player_level: int = 5,
        fight_count: int = 0,
        username: str = "Player",
    ):
        from src.data.bag import Bag

        self.maps = maps
        self.current_map_key = start_map
        self.player = player
        self.enemy_trainers = enemy_trainers
        self.npcs = npcs
        self.bag = bag if bag is not None else Bag([], [])
        self.player_spawns = player_spawns if player_spawns is not None else {}
        self.current_fight: EnemyTrainer | Bush | None = None
        self.should_change_scene = False
        self.next_map = ""
        self.next_spawn_pos = None
        self.previous_map = ""
        self.player_level = player_level
        self.player_level = player_level
        self.fight_count = fight_count
        self.dialog_overlay = None  # Runtime assignment

    @property
    def current_map(self) -> Map:
        """Current Map."""
        return self.maps[self.current_map_key]

    @property
    def current_enemy_trainers(self) -> list[EnemyTrainer]:
        """Current Enemy Trainers."""
        return self.enemy_trainers[self.current_map_key]

    @property
    def current_npcs(self) -> list[Npc]:
        """Current Npcs."""
        return self.npcs[self.current_map_key]

    @property
    def current_teleporter(self) -> list[Teleport]:
        """Current Teleporter."""
        return self.maps[self.current_map_key].teleporters

    def switch_map(self, target: str, spawn_pos: Position | None = None) -> None:
        """Switch Map."""
        if target not in self.maps:
            Logger.warning(f"Map '{target}' not loaded; cannot switch.")
            return
        self.previous_map = self.current_map_key
        self.next_map = target
        self.next_spawn_pos = spawn_pos
        self.should_change_scene = True

    def try_switch_map(self) -> None:
        """Try Switch Map."""
        if self.should_change_scene:
            self.current_map_key = self.next_map
            self.next_map = ""
            self.should_change_scene = False
            if self.player:
                destination_map = self.maps[self.current_map_key]

                # Priority 1: Specific spawn position (from Teleport.to_pos)
                if self.next_spawn_pos:
                    self.player.position = self.next_spawn_pos.copy()
                    self.next_spawn_pos = None  # Reset

                # Priority 2: Find matching return teleporter (Legacy behavior)
                else:
                    tpx = None
                    for teleporter in destination_map.teleporters:
                        if teleporter.destination == self.previous_map:
                            tpx = teleporter
                            break
                    if tpx and tpx.pos:
                        offset_x = 0
                        offset_y = 0
                        if self.player.direction == Direction.DOWN:
                            offset_y = GameSettings.TILE_SIZE
                        elif self.player.direction == Direction.UP:
                            offset_y = -GameSettings.TILE_SIZE
                        elif self.player.direction == Direction.RIGHT:
                            offset_x = GameSettings.TILE_SIZE
                        elif self.player.direction == Direction.LEFT:
                            offset_x = -GameSettings.TILE_SIZE
                        offset_pos = Position(
                            tpx.pos.x + offset_x, tpx.pos.y + offset_y
                        )
                        test_rect = pg.Rect(
                            offset_pos.x,
                            offset_pos.y,
                            GameSettings.TILE_SIZE,
                            GameSettings.TILE_SIZE,
                        )
                        if not self.check_collision(test_rect):
                            self.player.position = offset_pos
                        else:
                            self.player.position = tpx.pos.copy()
                    else:
                        # Priority 3: Player Spawns or Default Map Spawn
                        spawn_pos = destination_map.spawn
                        if self.current_map_key in self.player_spawns:
                            spawn_pos = self.player_spawns[self.current_map_key]
                        self.player.position = spawn_pos
                self.player.animation.update_pos(self.player.position)

    def check_collision(self, rect: pg.Rect) -> bool:
        """Check Collision."""
        if self.maps[self.current_map_key].check_collision(rect):
            return True
        for entity in (
            self.enemy_trainers[self.current_map_key] + self.npcs[self.current_map_key]
        ):
            if rect.colliderect(entity.animation.rect):
                return True
        return False

    def check_bush(self, rect: pg.Rect) -> bool:
        """Check Bush."""
        if self.maps[self.current_map_key].check_bush(rect):
            return True
        return False

    def save(self, path: str) -> None:
        """Save."""
        try:
            with open(path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
            Logger.info(f"Game saved to {path}")
        except Exception as e:
            Logger.warning(f"Failed to save game: {e}")

    @classmethod
    def load(cls, path: str) -> "GameManager | None":
        """Load."""
        if not os.path.exists(path):
            Logger.error(f"No file found: {path}, ignoring load function")
            return None
        with open(path, "r") as f:
            Logger.info(f"Loading game from {path}")
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, object]:
        """To Dict."""
        map_blocks: list[dict[str, object]] = []
        for key, m in self.maps.items():
            block = m.to_dict()
            block["enemy_trainers"] = [
                t.to_dict() for t in self.enemy_trainers.get(key, [])
            ]
            block["npcs"] = [n.to_dict() for n in self.npcs.get(key, [])]
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
            "player_level": self.player_level,
            "fight_count": self.fight_count,
            "username": self.username,
        }

    @classmethod
    def from_dict(cls, data) -> "GameManager":
        """From Dict."""
        from src.maps.map import Map
        from src.entities.player import Player
        from src.maps.map import Map
        from src.entities.player import Player
        from src.entities.enemy_trainer import EnemyTrainer, EnemyTrainerClassification
        from src.entities.npc import Npc
        from src.entities.npc import Npc
        from src.data.bag import Bag

        # Load available maps from assets/maps (recursively)
        map_files = []
        maps_dir = "assets/maps"
        for root, dirs, files in os.walk(maps_dir):
            for file in files:
                if file.endswith(".tmx"):
                    # Create relative path from assets/maps
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, maps_dir)
                    map_files.append(rel_path)

        Logger.info(f"Found maps: {map_files}")

        Logger.info("Loading maps")
        maps_data: list[dict] = data.get("map", [])
        maps: dict[str, Map] = {}
        player_spawns: dict[str, Position] = {}
        trainers: dict[str, list[EnemyTrainer]] = {}
        npcs: dict[str, list[Npc]] = {}

        # 1. Load registered maps from save file
        loaded_map_keys = set()
        for entry in maps_data:
            path = entry["path"]
            # Try to match entry path to one of our found map_files
            actual_path = path
            # If path in save is just filename but we have relative path now
            if not os.path.exists(os.path.join(maps_dir, path)):
                for rel in map_files:
                    if os.path.basename(rel) == os.path.basename(path):
                        actual_path = rel
                        break

            if os.path.exists(os.path.join(maps_dir, actual_path)):
                # Register by FILENAME for compatibility
                key = os.path.basename(actual_path)

                # IMPORTANT: Update entry path to actual_path so Map loads correct file from disk
                # This fixes FileNotFoundError if entry["path"] was just a filename but file is nested
                entry["path"] = actual_path
                maps[key] = Map.from_dict(entry)

                loaded_map_keys.add(key)
                sp = entry.get("player")
                if sp:
                    player_spawns[key] = Position(
                        sp["x"] * GameSettings.TILE_SIZE,
                        sp["y"] * GameSettings.TILE_SIZE,
                    )

        # 2. Load missing maps found in assets/maps (fresh load)
        for rel_path in map_files:
            key = os.path.basename(rel_path)
            if key not in loaded_map_keys:
                Logger.info(f"Loading new map: {rel_path} as {key}")
                try:
                    new_map = Map(rel_path, [], Position(0, 0))  # Default spawn
                    maps[key] = new_map
                    loaded_map_keys.add(key)
                except Exception as e:
                    Logger.error(f"Failed to load map {rel_path}: {e}")

        current_map = data["current_map"]
        if current_map not in maps:
            current_map = list(maps.keys())[0] if maps else "map.tmx"

        gm = cls(
            maps,
            current_map,
            None,
            trainers,
            npcs,
            bag=None,
            player_spawns=player_spawns,
            player_level=data.get("player_level", 5),
            fight_count=data.get("fight_count", 0),
            username=data.get("username", "Player"),
        )
        gm.current_map_key = current_map

        Logger.info("Loading enemy trainers and npc")

        # Helper to get map data if exists in save
        def get_saved_map_data(key):
            for m in maps_data:
                # heuristic: match basenames
                if os.path.basename(m["path"]) == key:
                    return m
            return None

        # Process entities for all loaded maps
        for map_key, map_obj in maps.items():
            saved_data = get_saved_map_data(map_key)

            # --- Load Trainers ---
            gm.enemy_trainers[map_key] = []
            if saved_data and saved_data.get("enemy_trainers"):
                # Load from save file
                raw_data = saved_data.get("enemy_trainers", [])
                gm.enemy_trainers[map_key] = [
                    EnemyTrainer.from_dict(t, gm) for t in raw_data
                ]

            # Temporary lists for this map
            trainers_to_add = []
            npcs_to_add = []

            # Parse entities from Object Layer if available
            map_entities = map_obj.get_entities()

            for entity in map_entities:
                name = entity["name"]
                props = entity["properties"]

                # Characters (NPCs / Trainers)
                if (
                    name == "Character" or name is None
                ):  # Sometimes name is empty in Tiled
                    char_id = props.get("character_id")

                    if char_id:
                        if char_id == "Nurse":
                            npc_data = {
                                "x": entity["x"] / GameSettings.TILE_SIZE,
                                "y": entity["y"] / GameSettings.TILE_SIZE,
                                "skin": "Nurse",
                                "dialog": [
                                    "Welcome to the Pokemon Center!",
                                    "We heal your Pokemon.",
                                ],
                                "name": "Nurse",
                            }
                            npcs_to_add.append(Npc.from_dict(npc_data, gm))
                        else:
                            # Assume EnemyTrainer
                            direction_str = props.get("direction", "DOWN").upper()
                            facing = Direction.DOWN
                            if hasattr(Direction, direction_str):
                                facing = getattr(Direction, direction_str)

                            trainer_level = int(props.get("level", 5))

                            trainer = EnemyTrainer(
                                x=entity["x"],
                                y=entity["y"],
                                game_manager=gm,
                                classification=EnemyTrainerClassification.STATIONARY,
                                facing=facing,
                                level=trainer_level,
                            )
                            trainers_to_add.append(trainer)

            # Use 'Entities' object layer if not loaded from save or if we want to supplement
            if not gm.enemy_trainers[map_key]:
                gm.enemy_trainers[map_key] = trainers_to_add

            for i, n in enumerate(gm.enemy_trainers[map_key]):
                n.change_skin(i)

            # --- Load NPCs ---
            gm.npcs[map_key] = []
            if saved_data and saved_data.get("npcs"):
                raw_data = saved_data.get("npcs", [])
                npc_list = []
                from src.entities.pc import PCEntity

                for t in raw_data:
                    # Detect PC by coordinate (hack for save file compatibility)
                    if map_key == "map.tmx" and t.get("x") == 18 and t.get("y") == 30:
                        npc_list.append(
                            PCEntity(
                                t["x"] * GameSettings.TILE_SIZE,
                                t["y"] * GameSettings.TILE_SIZE,
                                gm,
                            )
                        )
                    else:
                        npc_list.append(Npc.from_dict(t, gm))
                gm.npcs[map_key] = npc_list
            else:
                gm.npcs[map_key] = npcs_to_add

                # Legacy PC check for 'map.tmx' if not in Entities
                if map_key == "map.tmx":
                    from src.entities.pc import PCEntity

                    pc_exists = any(isinstance(n, PCEntity) for n in gm.npcs[map_key])
                    if not pc_exists:
                        gm.npcs[map_key].append(
                            PCEntity(
                                18 * GameSettings.TILE_SIZE,
                                30 * GameSettings.TILE_SIZE,
                                gm,
                            )
                        )

            for i, n in enumerate(gm.npcs[map_key]):
                if not isinstance(n, PCEntity):
                    n.change_skin(i)

        Logger.info("Loading Player")
        if data.get("player"):
            gm.player = Player.from_dict(data["player"], gm)
        Logger.info("Loading bag")
        from src.data.bag import Bag as _Bag

        gm.bag = Bag.from_dict(data.get("bag", {})) if data.get("bag") else _Bag([], [])
        assert gm.bag is not None, "Bag missing after load"
        return gm
