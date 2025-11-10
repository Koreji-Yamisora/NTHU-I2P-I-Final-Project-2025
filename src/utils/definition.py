from pygame import Rect
from .settings import GameSettings
from dataclasses import dataclass
from enum import Enum
from typing import overload, TypedDict, Protocol

MouseBtn = int
Key = int

Direction = Enum("Direction", ["UP", "DOWN", "LEFT", "RIGHT", "NONE"])


@dataclass
class Position:
    x: float
    y: float

    def copy(self):
        return Position(self.x, self.y)

    def distance_to(self, other: "Position") -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


@dataclass
class PositionCamera:
    x: int
    y: int

    def copy(self):
        return PositionCamera(self.x, self.y)

    def to_tuple(self) -> tuple[int, int]:
        return (self.x, self.y)

    def transform_position(self, position: Position) -> tuple[int, int]:
        return (int(position.x) - self.x, int(position.y) - self.y)

    def transform_position_as_position(self, position: Position) -> Position:
        return Position(int(position.x) - self.x, int(position.y) - self.y)

    def transform_rect(self, rect: Rect) -> Rect:
        return Rect(rect.x - self.x, rect.y - self.y, rect.width, rect.height)


@dataclass
class Teleport:
    pos: Position
    destination: str
    one_way: bool

    @overload
    def __init__(self, x: int, y: int, destination: str, one_way=False) -> None: ...
    @overload
    def __init__(self, pos: Position, destination: str, one_way=False) -> None: ...

    def __init__(self, *args, **kwargs):
        if isinstance(args[0], Position):
            self.pos = args[0]
            self.destination = args[1]
            self.one_way = args[2] if len(args) > 2 else kwargs.get("one_way", False)
        else:
            if len(args) >= 4:
                x, y, dest, one_way = args[0], args[1], args[2], args[3]
            else:
                x, y, dest = args[0], args[1], args[2]
                one_way = kwargs.get("one_way", False)
            self.pos = Position(x, y)
            self.destination = dest
            self.one_way = one_way

    def to_dict(self):
        return {
            "x": self.pos.x // GameSettings.TILE_SIZE,
            "y": self.pos.y // GameSettings.TILE_SIZE,
            "destination": self.destination,
            "one_way": self.one_way,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            data["destination"],
            data.get("one_way", False),
        )


class Monster(TypedDict):
    name: str
    hp: int
    max_hp: int
    level: int
    sprite_path: str


class Item(TypedDict):
    name: str
    count: int
    sprite_path: str

