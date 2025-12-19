from __future__ import annotations
from src.utils import Logger, GameSettings, Position, Teleport, Direction
import json
import os
import pygame as pg
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.maps.map import Map
    from src.entities.player import Player, Bush
    from src.entities.enemy_trainer import EnemyTrainer
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
        self.fight_count = fight_count

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
        from src.entities.enemy_trainer import EnemyTrainer
        from src.entities.npc import Npc
        from src.data.bag import Bag

        Logger.info("Loading maps")
        maps_data: list[dict] = data["map"]
        maps: dict[str, Map] = {}
        player_spawns: dict[str, Position] = {}
        trainers: dict[str, list[EnemyTrainer]] = {}
        npcs: dict[str, list[Npc]] = {}
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
        for m in data["map"]:
            raw_data = m["enemy_trainers"]
            gm.enemy_trainers[m["path"]] = [
                EnemyTrainer.from_dict(t, gm) for t in raw_data
            ]
            for i, n in enumerate(gm.enemy_trainers[m["path"]]):
                n.change_skin(i)
            raw_data = m["npcs"]
            npc_list = []
            from src.entities.pc import PCEntity

            for t in raw_data:
                # Detect PC by coordinate (hack for save file compatibility)
                if m["path"] == "map.tmx" and t.get("x") == 18 and t.get("y") == 30:
                    npc_list.append(
                        PCEntity(
                            t["x"] * GameSettings.TILE_SIZE,
                            t["y"] * GameSettings.TILE_SIZE,
                            gm,
                        )
                    )
                else:
                    npc_list.append(Npc.from_dict(t, gm))

            gm.npcs[m["path"]] = npc_list
            for i, n in enumerate(gm.npcs[m["path"]]):
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
