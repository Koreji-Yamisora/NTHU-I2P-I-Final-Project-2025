import pygame as pg
from src.utils import GameSettings, Logger
from .services import scene_manager, input_manager
from src.scenes.menu_scene import MenuScene
from src.scenes.game_scene import GameScene
from src.scenes.setting_scene import SettingsScene
from src.scenes.battle_scene import BattleScene
from src.scenes.encounter_scene import EncounterScene
from src.scenes.pvp_scene import PvPScene


class Engine:
    """Engine."""
    screen: pg.Surface
    logical_surface: pg.Surface
    clock: pg.time.Clock
    running: bool
    _instance = None

    def __init__(self):
        Logger.info('Initializing Engine')
        Engine._instance = self
        self.ats_event = pg.USEREVENT + 1
        self.ats_update = pg.USEREVENT + 2
        pg.init()
        # Use RESIZABLE for window, render to logical surface and scale
        self.screen = pg.display.set_mode((GameSettings.SCREEN_WIDTH,
            GameSettings.SCREEN_HEIGHT), pg.RESIZABLE, vsync=1)
        # Logical surface for rendering at internal resolution
        self.logical_surface = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.clock = pg.time.Clock()
        self.running = True
        pg.display.set_caption(GameSettings.TITLE)
        scene_manager.register_scene('menu', MenuScene())
        scene_manager.register_scene('game', GameScene())
        """
        [TODO HACKATHON 5]
        Register the setting scene here
        """
        scene_manager.register_scene('settings', SettingsScene())
        scene_manager.register_scene('battle', BattleScene())
        scene_manager.register_scene('encounter', EncounterScene())
        scene_manager.register_scene('pvp', PvPScene())
        scene_manager.change_scene('menu')
        self.update_ats()

    @classmethod
    def apply_resolution(cls):
        """Apply new resolution - recreate logical surface and rebuild UIs."""
        if cls._instance:
            from src.interface.components.overlay import Overlay
            cls._instance.logical_surface = pg.Surface(
                (GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT)
            )
            # Rebuild all UI elements (though internal resolution stays constant,
            # this ensures any dynamic positioning logic is refreshed if needed)
            Overlay.rebuild_all()
            Logger.info(f"Resolution changed to {GameSettings.SCREEN_WIDTH}x{GameSettings.SCREEN_HEIGHT}")

    def run(self):
        """Run."""
        Logger.info('Running the Game Loop ...')
        while self.running:
            dt = self.clock.tick(GameSettings.FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()

    def update_ats(self):
        """Update ats."""
        ats = GameSettings.AUTOSAVE
        if ats > 0:
            pg.time.set_timer(self.ats_event, ats * 60000)

    def handle_events(self):
        """Handle Events."""
        input_manager.reset()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            if event.type == self.ats_event:
                from src.core import gh
                gh.save()
            if event.type == self.ats_update:
                self.update_ats()
            input_manager.handle_events(event)

    def update(self, dt: float):
        """Update."""
        scene_manager.update(dt)

    def render(self):
        """Render."""
        # Render to logical surface
        self.logical_surface.fill((0, 0, 0))
        scene_manager.draw(self.logical_surface)
        
        # Scale logical surface to fit window while preserving aspect ratio
        window_size = self.screen.get_size()
        logical_size = self.logical_surface.get_size()
        
        # Calculate scale to fit window
        scale_x = window_size[0] / logical_size[0]
        scale_y = window_size[1] / logical_size[1]
        scale = min(scale_x, scale_y)
        
        # Calculate scaled size and position (centered with black bars)
        scaled_width = int(logical_size[0] * scale)
        scaled_height = int(logical_size[1] * scale)
        offset_x = (window_size[0] - scaled_width) // 2
        offset_y = (window_size[1] - scaled_height) // 2
        
        # Clear screen and blit scaled surface
        self.screen.fill((0, 0, 0))
        scaled_surface = pg.transform.smoothscale(self.logical_surface, (scaled_width, scaled_height))
        self.screen.blit(scaled_surface, (offset_x, offset_y))
        
        pg.display.flip()

