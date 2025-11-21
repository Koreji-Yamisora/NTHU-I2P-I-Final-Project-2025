from __future__ import annotations
import pygame as pg
from typing import Callable, override, Generator
from .component import UIComponent
from .button import Button, ToggleButton, Slider
from src.utils import GameSettings
from src.sprites import Text, Sprite


class Overlay(UIComponent):
    is_open: bool
    active_components: list[Button | ToggleButton | Slider]
    components: list[Text | Sprite]
    backgrounds: list[Sprite]
    dark_overlay: pg.Surface

    def __init__(
        self,
        overlay_alpha: int | None = None,
    ):
        self.is_open = False
        self.is_active = True
        self.is_passive = True
        self.overlay_alpha = overlay_alpha
        self.active_components = []
        self.components = []
        self.backgrounds = []

        if self.overlay_alpha:
            self.dark_overlay = pg.Surface(
                (GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT)
            )
            self.dark_overlay.set_alpha(overlay_alpha)
            self.dark_overlay.fill("Black")

    def add_active(self, component: Button | ToggleButton | Slider) -> None:
        self.active_components.append(component)

    def add_passive(self, component: Sprite | Text) -> None:
        self.components.append(component)

    def add_bg(self, bg: Sprite) -> None:
        self.backgrounds.append(bg)

    def open(self) -> None:
        self.is_open = True
        self.is_active = True
        self.is_passive = True

    def close(self) -> None:
        self.is_open = False

    def toggle(self) -> None:
        self.is_open = not self.is_open

    @override
    def update(self, dt: float) -> None:
        if self.is_open:
            if self.is_active:
                for c in self.active_components:
                    c.update(dt)

            self.update_content(dt)

    @override
    def draw(self, screen: pg.Surface) -> None:
        if self.is_open:
            if self.overlay_alpha:
                screen.blit(self.dark_overlay, (0, 0))
            for b in self.backgrounds:
                b.draw(screen)
            if self.is_passive:
                for c in self.active_components:
                    c.draw(screen)
                for t in self.components:
                    t.draw(screen)
            self.draw_content(screen)

    def update_content(self, dt: float) -> None:
        pass

    def draw_content(self, screen: pg.Surface) -> None:
        pass
