from __future__ import annotations
import pygame as pg
from typing import Callable, override, Generator
from src.sprites.background import BackgroundSprite
from .component import UIComponent
from .button import Button, ToggleButton, Slider
from src.utils import GameSettings
from src.sprites import Text, Sprite, ColorSprite


class Overlay(UIComponent):
    """ overlay UI component."""
    is_open: bool
    active_components: list[Button | ToggleButton | Slider]
    components: list[Text | Sprite | ColorSprite]
    backgrounds: list[Sprite | ColorSprite | BackgroundSprite]
    dark_overlay: pg.Surface
    _instances: list[Overlay] = []

    def __init__(self, overlay_alpha: (int | None)=None):
        self.is_open = False
        self.is_active = False
        self.overlay_alpha = overlay_alpha
        self.active_components = []
        self.components = []
        self.components2 = []
        self.backgrounds = []
        Overlay._instances.append(self)
        if self.overlay_alpha:
            self.dark_overlay = pg.Surface((GameSettings.SCREEN_WIDTH,
                GameSettings.SCREEN_HEIGHT))
            self.dark_overlay.set_alpha(overlay_alpha)
            self.dark_overlay.fill('Black')

    def add_active(self, component: (Button | ToggleButton | Slider)) ->None:
        """Add Active."""
        self.active_components.append(component)

    def add_passive(self, component: (Sprite | Text | ColorSprite)) ->None:
        """Add Passive."""
        self.components.append(component)

    def add_passive2(self, component: (Sprite | Text)) ->None:
        """Add Passive2."""
        self.components2.append(component)

    def add_bg(self, bg: (Sprite | ColorSprite | BackgroundSprite)) ->None:
        """Add Bg."""
        self.backgrounds.append(bg)

    def open(self) ->None:
        """Open."""
        self.is_open = True
        self.is_active = True
        self.is_passive = True

    def clear(self):
        """Clear."""
        self.active_components = []
        self.components = []
        self.components2 = []
        self.backgrounds = []

    def close(self) ->None:
        """Close."""
        self.is_open = False

    def toggle(self) ->None:
        """Toggle."""
        self.is_open = not self.is_open

    @override
    def update(self, dt: float) ->None:
        """Update."""
        if self.is_open:
            if self.is_active:
                for c in self.active_components:
                    c.update(dt)
            self.update_content(dt)

    @override
    def draw(self, screen: pg.Surface) ->None:
        """Draw."""
        if self.is_open:
            if self.overlay_alpha:
                screen.blit(self.dark_overlay, (0, 0))
            for b in self.backgrounds:
                b.draw(screen)
            for c in self.active_components:
                c.draw(screen)
            for t in self.components:
                t.draw(screen)
            for t in self.components2:
                t.draw(screen)
            self.draw_content(screen)

    def update_content(self, dt: float) ->None:
        """Update content."""
        pass

    def draw_content(self, screen: pg.Surface) ->None:
        """Draw content."""
        pass
