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
    """Position."""

    x: float
    y: float

    def copy(self):
        """Copy."""
        return Position(self.x, self.y)

    def distance_to(self, other: "Position") -> float:
        """Distance To."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


@dataclass
class PositionCamera:
    """Position Camera."""

    x: int
    y: int

    def copy(self):
        """Copy."""
        return PositionCamera(self.x, self.y)

    def to_tuple(self) -> tuple[int, int]:
        """To Tuple."""
        return self.x, self.y

    def transform_position(self, position: Position) -> tuple[int, int]:
        """Transform Position."""
        return int(position.x) - self.x, int(position.y) - self.y

    def transform_position_as_position(self, position: Position) -> Position:
        """Transform Position As Position."""
        return Position(int(position.x) - self.x, int(position.y) - self.y)

    def transform_rect(self, rect: Rect) -> Rect:
        """Transform Rect."""
        return Rect(rect.x - self.x, rect.y - self.y, rect.width, rect.height)


@dataclass
class Teleport:
    """Teleport."""

    pos: Position
    destination: str
    to_pos: Position | None = None

    @overload
    def __init__(self, x: int, y: int, destination: str, to_x: int | None = None, to_y: int | None = None) -> None: ...

    @overload
    def __init__(self, pos: Position, destination: str, to_pos: Position | None = None) -> None: ...

    def __init__(self, *args, **kwargs):
        self.to_pos = None
        if isinstance(args[0], Position):
            self.pos = args[0]
            self.destination = args[1]
            if len(args) > 2:
                self.to_pos = args[2]
        else:
            x, y, dest = args[0], args[1], args[2]
            self.pos = Position(x, y)
            self.destination = dest
            if len(args) > 4:
                 self.to_pos = Position(args[3], args[4])
            elif "to_x" in kwargs and "to_y" in kwargs:
                 self.to_pos = Position(kwargs["to_x"], kwargs["to_y"])

    def to_dict(self):
        """To Dict."""
        data = {
            "x": self.pos.x // GameSettings.TILE_SIZE,
            "y": self.pos.y // GameSettings.TILE_SIZE,
            "destination": self.destination,
        }
        if self.to_pos:
            data["to_x"] = self.to_pos.x // GameSettings.TILE_SIZE
            data["to_y"] = self.to_pos.y // GameSettings.TILE_SIZE
        return data

    @classmethod
    def from_dict(cls, data: dict):
        """From Dict."""
        to_pos = None
        if "to_x" in data and "to_y" in data:
            to_pos = Position(data["to_x"] * GameSettings.TILE_SIZE, data["to_y"] * GameSettings.TILE_SIZE)
        
        return cls(
            Position(data["x"] * GameSettings.TILE_SIZE, data["y"] * GameSettings.TILE_SIZE),
            data["destination"],
            to_pos
        )


class Monster(TypedDict):
    """Monster."""

    id: int
    name: str
    level: int
    exp: int
    hp: int
    IV: dict[str, int]
    EV: dict[str, int]
    move: dict[str, str | int]


class PokeDexEntry(TypedDict):
    """Poke Dex Entry."""

    sprite_path: str
    name: str
    hp: int
    atk: int
    defen: int
    type1: str
    type2: str


class ability(TypedDict):
    """ability."""

    name: str
    desc: str
    effect: str
    out_bt: str


class Move(TypedDict):
    """Move."""

    name: str
    cat: str
    type: str
    power: int
    acc: int


class Item(TypedDict):
    """Item."""

    name: str
    count: int
    sprite_path: str
