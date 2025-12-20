import pygame as pg

from src.core.services import resource_manager, input_manager
from src.utils import GameSettings


class ActionHints:
    def __init__(self):
        self.actions = []  # List of (ActionKey, Description)
        self.font = resource_manager.get_font("dogicapixel.otf", 32)

        # Cache for loaded images
        self.images = {}

        # Mappings
        self.kb_map = {
            "INTERACT": "SPACE",
            "BACK": "ESC",
            "SETTING": "ESC",
            "INVENTORY": "B",
            "MAP": "M",
            "CHAT": "T",
            "CONFIRM": "ENTER",
            "UP": "ARROWUP",
            "DOWN": "ARROWDOWN",
            "LEFT": "ARROWLEFT",
            "RIGHT": "ARROWRIGHT",
        }

        self.joy_map = {
            "INTERACT": "A",
            "BACK": "B",
            "SETTING": "BACK",
            "INVENTORY": "Y",
            "MAP": "START",
            "CHAT": "X",
            "CONFIRM": "A",
            "UP": "CONTROLPADUP",
            "DOWN": "CONTROLPADDOWN",
            "LEFT": "CONTROLPADLEFT",
            "RIGHT": "CONTROLPADRIGHT",
        }

    def set_actions(self, actions: list[tuple[str, str]]):
        """Set the current list of active actions.
        Args:
            actions: List of tuples (ActionKey, Description).
                     e.g. [("INTERACT", "Talk"), ("INVENTORY", "Bag")]
        """
        self.actions = actions

    def _get_icon_path(self, action_key: str, is_controller: bool) -> str | None:
        if is_controller:
            icon_name = self.joy_map.get(action_key)
            if icon_name:
                return f"assets/images/Buttons Pack/XBOX/{icon_name}.png"
        else:
            icon_name = self.kb_map.get(action_key)
            if icon_name:
                return f"assets/images/Buttons Pack/KEYBOARD/KEYS/{icon_name}.png"
        return None

    def draw(self, screen: pg.Surface):
        if not self.actions:
            return

        is_controller = input_manager.last_input_type == "CONTROLLER"

        # Start from bottom right
        start_x = GameSettings.SCREEN_WIDTH - 20
        start_y = GameSettings.SCREEN_HEIGHT - 60

        # Draw in reverse order (right to left)
        padding = 20

        for action_key, desc in reversed(self.actions):
            # Load Icon
            path = self._get_icon_path(action_key, is_controller)
            if not path:
                continue

            if path not in self.images:
                try:
                    img = pg.image.load(path).convert_alpha()
                    # Scale if necessary, let's keep original for now or scale to 32x32
                    # The assets seem to be around ~200px, so scaling is needed
                    self.images[path] = pg.transform.scale(img, (40, 40))
                except Exception as e:
                    from src.utils import Logger

                    Logger.error(f"Failed to load action hint icon: {path}. Error: {e}")
                    continue

            icon = self.images[path]

            # Render Text
            text_surf = self.font.render(desc, True, (255, 255, 255))

            # Calculate position
            # [Icon] [Text]
            total_width = icon.get_width() + 10 + text_surf.get_width()

            x = start_x - total_width
            y = start_y

            # Draw
            screen.blit(icon, (x, y))
            screen.blit(
                text_surf, (x + icon.get_width() + 10, y + 5)
            )  # +5 for centering roughly

            # Update start_x for next item
            start_x = x - padding
