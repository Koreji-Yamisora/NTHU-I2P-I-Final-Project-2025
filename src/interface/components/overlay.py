from __future__ import annotations
import pygame as pg
from typing import Callable, override
from .component import UIComponent
from .button import Button
from src.utils import GameSettings
from src.core.managers.game_manager import GameManager


class Overlay(UIComponent):
    """
    Base overlay class that handles:
    - Dark semi-transparent background
    - Back button to close
    - Content area for subclasses to override
    """

    is_open: bool
    buttons: list[Button]
    dark_overlay: pg.Surface

    def __init__(
        self,
        game_manager: GameManager,
        overlay_alpha: int | None = None,
    ):
        self.is_open = False
        self.overlay_alpha = overlay_alpha
        self.buttons = []

        self.dark_overlay = pg.Surface(
            (GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT)
        )
        self.dark_overlay.set_alpha(overlay_alpha)
        self.dark_overlay.fill((0, 0, 0))

    def add_button(self, button: Button) -> None:
        self.buttons.append(button)

    def open(self) -> None:
        self.is_open = True

    def close(self) -> None:
        self.is_open = False

    def toggle(self) -> None:
        self.is_open = not self.is_open

    @override
    def update(self, dt: float) -> None:
        if self.is_open:
            for button in self.buttons:
                button.update(dt)

            self.update_content(dt)

    @override
    def draw(self, screen: pg.Surface) -> None:
        if not self.is_open:
            return

        screen.blit(self.dark_overlay, (0, 0))
        self.draw_content(screen)
        for button in self.buttons:
            button.draw(screen)

    def update_content(self, dt: float) -> None:
        pass

    def draw_content(self, screen: pg.Surface) -> None:
        pass
