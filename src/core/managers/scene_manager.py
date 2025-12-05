import pygame as pg
from src.scenes.scene import Scene
from src.utils import Logger


class SceneManager:
    """Scene  management system."""
    _scenes: dict[str, Scene]
    _current_scene: Scene | None = None
    _next_scene: str | None = None

    def __init__(self):
        Logger.info('Initializing SceneManager')
        self._scenes = {}

    def register_scene(self, name: str, scene: Scene) ->None:
        """Register Scene."""
        self._scenes[name] = scene

    def change_scene(self, scene_name: str) ->None:
        """Change Scene."""
        if scene_name in self._scenes:
            Logger.info(f"Changing scene to '{scene_name}'")
            self._next_scene = scene_name
            if scene_name == 'menu':
                self._is_menu = True
            else:
                self._is_menu = False
        else:
            raise ValueError(f"Scene '{scene_name}' not found")
    _is_menu = False

    def is_menu(self) ->bool:
        """Check if menu."""
        return self._is_menu

    def update(self, dt: float) ->None:
        """Update."""
        if self._next_scene is not None:
            self._perform_scene_switch()
        if self._current_scene:
            self._current_scene.update(dt)

    def draw(self, screen: pg.Surface) ->None:
        """Draw."""
        if self._current_scene:
            self._current_scene.draw(screen)

    def _perform_scene_switch(self) ->None:
        if self._next_scene is None:
            return
        if self._current_scene:
            self._current_scene.exit()
        self._current_scene = self._scenes[self._next_scene]
        if self._current_scene:
            Logger.info(f'Entering {self._next_scene} scene')
            self._current_scene.enter()
        self._next_scene = None
