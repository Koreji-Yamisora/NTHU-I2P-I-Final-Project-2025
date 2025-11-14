from __future__ import annotations
import pygame as pg

from src.sprites import Sprite
from src.core.services import input_manager
from src.utils import Logger
from typing import Callable, override
from .component import UIComponent
from src.utils import Position


class Button(UIComponent):
    img_button: Sprite
    img_button_default: Sprite
    img_button_hover: Sprite
    hitbox: pg.Rect
    on_click: Callable[[], None] | None

    def __init__(
        self,
        img_path: str,
        img_hovered_path: str,
        x: int,
        y: int,
        width: int,
        height: int,
        on_click: Callable[[], None] | None = None,
    ):
        self.img_button_default = Sprite(img_path, (width, height))
        self.hitbox = pg.Rect(x, y, width, height)
        """
        [TODO HACKATHON 1]
        Initialize the properties
        
        self.img_button_hover = ...
        self.img_button = ...       --> This is a reference for which image to render
        self.on_click = ...
        """
        self.img_button_hover = Sprite(img_hovered_path, (width, height))
        self.img_button = self.img_button_default
        self.on_click = on_click

    @override
    def update(self, dt: float) -> None:
        """
        [TODO HACKATHON 1]
        Check if the mouse cursor is colliding with the button,
        1. If collide, draw the hover image
        2. If collide & clicked, call the on_click function

        if self.hitbox.collidepoint(input_manager.mouse_pos):
            ...
            if input_manager.mouse_pressed(1) and self.on_click is not None:
                ...
        else:
            ...
        """
        if self.hitbox.collidepoint(input_manager.mouse_pos):
            if input_manager.mouse_pressed(1) and self.on_click is not None:
                self.on_click()
            self.img_button = self.img_button_hover
        else:
            self.img_button = self.img_button_default

    @override
    def draw(self, screen: pg.Surface) -> None:
        """
        [TODO HACKATHON 1]
        You might want to change this too
        """
        self.img_button.rect.topleft = self.hitbox.topleft
        self.img_button.draw(screen)


class ToggleButton(UIComponent):
    off_button: Sprite
    on_button: Sprite
    hitbox: pg.Rect
    state: bool
    action: Callable[[bool], None] | None

    def __init__(
        self,
        off_button,
        on_button,
        x,
        y,
        width,
        height,
        state: bool = False,
        action: Callable[[bool], None] | None = None,
    ):
        self.off_button = Sprite(off_button, (width, height))
        self.on_button = Sprite(on_button, (width, height))
        self.hitbox = pg.Rect(0, 0, width, height)
        self.hitbox.center = (x, y)
        self.state = state
        self.action = action

    def toggle(self):
        self.state = not self.state

    @override
    def update(self, dt: float) -> None:
        if self.hitbox.collidepoint(input_manager.mouse_pos):
            if input_manager.mouse_pressed(1):
                if self.action:
                    self.action(self.state)
                    self.toggle()

    @override
    def draw(self, screen: pg.Surface) -> None:
        # keep sprites aligned with hitbox
        self.on_button.rect.topleft = self.hitbox.topleft
        self.off_button.rect.topleft = self.hitbox.topleft
        if self.state:
            self.on_button.draw(screen)
        else:
            self.off_button.draw(screen)


class Slider(UIComponent):
    state: float
    rect: pg.Rect
    button: Sprite
    active_bar: Sprite
    bar: Sprite
    is_dragging: bool
    _drag_offset: int
    action: Callable[[float], None] | None = None

    def __init__(
        self,
        button,
        bar,
        active_bar_img,
        highlight,
        x,
        y,
        width,
        height,
        width_b,
        height_b,
        state: float = 0.5,
        action: Callable[[float], None] | None = None,
    ):
        self.rect = pg.Rect(x, y, width, height)
        self.bar = Sprite(bar, (width, height))
        self._active_bar_img = active_bar_img
        self.active_bar = Sprite(active_bar_img, (width, height))
        self.button = Sprite(button, (width_b, height_b))
        self.highlight = Sprite(highlight, (width_b, height_b))
        self.bar.rect.center = (x, y)
        self.active_bar.rect.center = (x, y)
        self.state = max(0.0, min(1.0, state))
        self.is_dragging = False
        self._drag_offset = 0
        self.button_helper(0, self.bar.rect.centery)
        self.action = action
        self._sync_from_state()

    def button_helper(self, pos_x: int, pos_y: int | None = None):
        self.button.rect.centerx = pos_x
        self.highlight.rect.centerx = pos_x
        if pos_y:
            self.button.rect.centery = pos_y
            self.highlight.rect.centery = pos_y

    def _clamp_state(self) -> None:
        self.state = max(0.0, min(1.0, self.state))

    def _sync_from_state(self) -> None:
        bar_left = self.bar.rect.left
        bar_right = self.bar.rect.right
        bar_width = bar_right - bar_left
        center_x = bar_left + int(self.state * bar_width)
        self.button_helper(center_x, self.bar.rect.centery)
        new_width = max(0, center_x - bar_left)
        self.active_bar = Sprite(
            self._active_bar_img, (new_width, self.bar.rect.height)
        )
        self.active_bar.rect.centery = self.bar.rect.centery
        self.active_bar.rect.left = self.bar.rect.left

    def _sync_from_pos(self, mouse_center_x: int) -> None:
        bar_left = self.bar.rect.left
        bar_right = self.bar.rect.right
        mouse_center_x = max(bar_left, min(mouse_center_x, bar_right))
        bar_width = bar_right - bar_left
        self.state = (mouse_center_x - bar_left) / bar_width
        self._clamp_state()
        if self.action:
            self.action(self.state)

    @override
    def update(self, dt: float) -> None:
        mouse_x, mouse_y = input_manager.mouse_pos
        if input_manager.mouse_pressed(1):
            if self.button.rect.collidepoint(
                mouse_x, mouse_y
            ) or self.highlight.rect.collidepoint(mouse_x, mouse_y):
                self.is_dragging = True
                self._drag_offset = mouse_x - self.button.rect.centerx
            elif self.bar.rect.collidepoint(mouse_x, mouse_y):
                self._sync_from_pos(mouse_x)
                self._sync_from_state()
        if input_manager.mouse_released(1):
            self.is_dragging = False
        if self.is_dragging:
            self._sync_from_pos(mouse_x - self._drag_offset)
            self._sync_from_state()
        else:
            self._sync_from_state()

    @override
    def draw(self, screen: pg.Surface) -> None:
        self.bar.draw(screen)
        self.active_bar.draw(screen)
        if self.is_dragging:
            self.highlight.draw(screen)
        else:
            self.button.draw(screen)
