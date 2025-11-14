import importlib
import pygame as pg
from src.core.services import input_manager
from src.utils import GameSettings, Logger
import sys


def reload(part, dt):
    if not GameSettings.DEBUG:
        return

    if not hasattr(part, "db"):
        part.db = 0.0

    part.db -= dt
    if input_manager.key_pressed(pg.K_e) or part.db <= 0.0:
        # Reload modules in dependency order (bottom-up: dependencies first)
        # Order matters: reload base classes first, then modules that import them
        modules_to_reload = [
            "src.interface.components.overlay",
            "src.interface.components",
            "src.interface.overlay_game",
            "src.interface",
        ]

        for module_name in modules_to_reload:
            try:
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                    Logger.info(f"Reloaded {module_name}")
                else:
                    module = importlib.import_module(module_name)
                    importlib.reload(module)
                    Logger.info(f"Imported and reloaded {module_name}")
            except Exception as e:
                Logger.error(f"Failed to reload {module_name}: {e}")

        og = sys.modules.get("src.interface.overlay_game")
        if og is None:
            import src.interface.overlay_game as og

        was_open = part.setting_overlay.is_open
        part.setting_overlay = og.SettingOverlay(
            part.game_manager, on_close=lambda: part.setting_overlay.close()
        )
        if was_open:
            part.setting_overlay.open()
        part.db = 3.0
        if input_manager.key_pressed(pg.K_e):
            Logger.info("Reloaded overlay_game module")
