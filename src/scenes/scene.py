from __future__ import annotations
import pygame as pg


class Scene:
    """ scene."""

    def __init__(self) ->None:
        ...

    def enter(self) ->None:
        """Enter."""
        ...

    def exit(self) ->None:
        """Exit."""
        ...

    def update(self, dt: float) ->None:
        """Update."""
        ...

    def draw(self, screen: pg.Surface) ->None:
        """Draw."""
        ...
