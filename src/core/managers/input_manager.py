import pygame as pg
from src.utils import Logger, MouseBtn, Key, GameSettings


class InputManager:
    """Input  management system."""

    def __init__(self) -> None:
        self._down_keys: set[Key] = set()
        self._pressed_keys: set[Key] = set()
        self._released_keys: set[Key] = set()
        self._down_mouse: set[MouseBtn] = set()
        self._pressed_mouse: set[MouseBtn] = set()
        self._released_mouse: set[MouseBtn] = set()
        self.mouse_pos: tuple[int, int] = (0, 0)
        self.mouse_wheel: int = 0
        self.text_input: str = ""

        # Controller Support
        pg.joystick.init()
        self.joysticks = [
            pg.joystick.Joystick(i) for i in range(pg.joystick.get_count())
        ]
        for joy in self.joysticks:
            joy.init()

        self.last_input_type = "KEYBOARD"  # KEYBOARD or CONTROLLER

        self._down_buttons: set[int] = set()
        self._pressed_buttons: set[int] = set()
        self._released_buttons: set[int] = set()
        self._axis_values: dict[int, float] = {}

    def reset(self) -> None:
        """Reset."""
        self._pressed_keys.clear()
        self._released_keys.clear()
        self._pressed_mouse.clear()
        self._released_mouse.clear()
        self._pressed_buttons.clear()
        self._released_buttons.clear()
        self.text_input = ""

    def _transform_mouse_pos(self, window_pos: tuple[int, int]) -> tuple[int, int]:
        """Transform window coordinates to logical surface coordinates."""
        window_size = pg.display.get_surface().get_size()
        logical_size = (GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT)

        # Calculate scale to fit window
        scale_x = window_size[0] / logical_size[0]
        scale_y = window_size[1] / logical_size[1]
        scale = min(scale_x, scale_y)

        # Calculate offset (centered with black bars)
        scaled_width = int(logical_size[0] * scale)
        scaled_height = int(logical_size[1] * scale)
        offset_x = (window_size[0] - scaled_width) // 2
        offset_y = (window_size[1] - scaled_height) // 2

        # Transform coordinates
        logical_x = int((window_pos[0] - offset_x) / scale)
        logical_y = int((window_pos[1] - offset_y) / scale)

        # Clamp to logical bounds
        logical_x = max(0, min(logical_x, logical_size[0] - 1))
        logical_y = max(0, min(logical_y, logical_size[1] - 1))

        return (logical_x, logical_y)

    def handle_events(self, e: pg.event.Event) -> None:
        """Handle Events."""
        if e.type == pg.MOUSEMOTION:
            self.mouse_pos = self._transform_mouse_pos(e.pos)
            self.last_input_type = "KEYBOARD"
        elif e.type == pg.MOUSEBUTTONDOWN:
            self.last_input_type = "KEYBOARD"
            if e.button in (1, 2, 3):
                self._down_mouse.add(e.button)
                self._pressed_mouse.add(e.button)
            elif e.button in (4, 5):
                self.mouse_wheel += 1 if e.button == 4 else -1
        elif e.type == pg.MOUSEBUTTONUP:
            if e.button in (1, 2, 3):
                self._down_mouse.discard(e.button)
                self._released_mouse.add(e.button)
        elif e.type == pg.KEYDOWN:
            self.last_input_type = "KEYBOARD"
            self._down_keys.add(e.key)
            self._pressed_keys.add(e.key)
        elif e.type == pg.KEYUP:
            self._down_keys.discard(e.key)
            self._released_keys.add(e.key)
        elif e.type == pg.TEXTINPUT:
            self.text_input += e.text

        # Controller Events
        elif e.type == pg.JOYBUTTONDOWN:
            self.last_input_type = "CONTROLLER"
            self._down_buttons.add(e.button)
            self._pressed_buttons.add(e.button)
        elif e.type == pg.JOYBUTTONUP:
            self._down_buttons.discard(e.button)
            self._released_buttons.add(e.button)
        elif e.type == pg.JOYAXISMOTION:
            if abs(e.value) > 0.2:  # Deadzone
                self.last_input_type = "CONTROLLER"
            self._axis_values[e.axis] = e.value

    def key_down(self, k: Key) -> bool:
        """Key Down."""
        return k in self._down_keys

    def key_pressed(self, k: Key) -> bool:
        """Key Pressed."""
        return k in self._pressed_keys

    def key_released(self, k: Key) -> bool:
        """Key Released."""
        return k in self._released_keys

    def mouse_down(self, b: MouseBtn) -> bool:
        """Mouse Down."""
        return b in self._down_mouse

    def mouse_pressed(self, b: MouseBtn) -> bool:
        """Mouse Pressed."""
        return b in self._pressed_mouse

    def mouse_released(self, b: MouseBtn) -> bool:
        """Mouse Released."""
        return b in self._released_mouse

    # Controller Methods
    def button_down(self, b: int) -> bool:
        return b in self._down_buttons

    def button_pressed(self, b: int) -> bool:
        return b in self._pressed_buttons

    def get_axis(self, axis: int) -> float:
        return self._axis_values.get(axis, 0.0)
