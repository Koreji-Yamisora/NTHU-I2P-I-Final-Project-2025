import pygame as pg
from src.scenes.scene import Scene
from src.utils import Logger, GameSettings, crd


class SceneManager:
    """Scene  management system."""
    _scenes: dict[str, Scene]
    _current_scene: Scene | None = None
    _next_scene: str | None = None
    _is_menu = False

    # Fade attributes
    fade_state: str = "IDLE" # IDLE, FADE_OUT, FADE_IN
    fade_alpha: float = 0.0
    fade_speed: float = 600.0 # Speed of fade
    fade_surface: pg.Surface

    def __init__(self):
        Logger.info('Initializing SceneManager')
        self._scenes = {}
        
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)
        self.fade_surface = pg.Surface((sw, sh))
        self.fade_surface.fill((0, 0, 0))
        self.fade_surface.set_alpha(0)

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

    def is_menu(self) ->bool:
        """Check if menu."""
        return self._is_menu

    def update(self, dt: float) ->None:
        """Update."""
        # Fade Logic
        if self._next_scene is not None and self.fade_state == "IDLE":
             self.fade_state = "FADE_OUT"
        
        if self.fade_state == "FADE_OUT":
            self.fade_alpha += self.fade_speed * dt
            if self.fade_alpha >= 255:
                self.fade_alpha = 255
                self._perform_scene_switch()
                self.fade_state = "FADE_IN"
        elif self.fade_state == "FADE_IN":
            self.fade_alpha -= self.fade_speed * dt
            if self.fade_alpha <= 0:
                self.fade_alpha = 0
                self.fade_state = "IDLE"
                
        if self.fade_surface:
            self.fade_surface.set_alpha(int(self.fade_alpha))

        if self._current_scene:
            self._current_scene.update(dt)

    def draw(self, screen: pg.Surface) ->None:
        """Draw."""
        if self._current_scene:
            self._current_scene.draw(screen)
        
        if self.fade_alpha > 0:
            screen.blit(self.fade_surface, (0, 0))

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
