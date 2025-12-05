import pygame as pg
from typing import Protocol


class UIComponent(Protocol):
    """U I Component."""

    def update(self, dt: float) ->None:
        """Update."""
        ...

    def draw(self, screen: pg.Surface) ->None:
        """Draw."""
        ...


MonsterInfoType = UIComponent
ItemInfoType = UIComponent
