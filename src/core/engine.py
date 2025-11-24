import pygame as pg

from src.utils import GameSettings, Logger
from .services import scene_manager, input_manager

from src.scenes.menu_scene import MenuScene
from src.scenes.game_scene import GameScene
from src.scenes.setting_scene import SettingsScene
from src.scenes.battle_scene import BattleScene
from src.scenes.encounter_scene import EncounterScene


class Engine:
    screen: pg.Surface  # Screen Display of the Game
    clock: pg.time.Clock  # Clock for FPS control
    running: bool  # Running state of the game

    def __init__(self):
        Logger.info("Initializing Engine")
        self.ats_event = pg.USEREVENT + 1
        self.ats_update = pg.USEREVENT + 2

        pg.init()

        self.screen = pg.display.set_mode(
            (GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT)
        )
        self.clock = pg.time.Clock()
        self.running = True

        pg.display.set_caption(GameSettings.TITLE)

        scene_manager.register_scene("menu", MenuScene())
        scene_manager.register_scene("game", GameScene())
        """
        [TODO HACKATHON 5]
        Register the setting scene here
        """
        scene_manager.register_scene("settings", SettingsScene())
        scene_manager.register_scene("battle", BattleScene())
        scene_manager.register_scene("encounter", EncounterScene())
        scene_manager.change_scene("menu")

        self.update_ats()

    def run(self):
        Logger.info("Running the Game Loop ...")

        while self.running:
            dt = self.clock.tick(GameSettings.FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()

    def update_ats(self):
        ats = GameSettings.AUTOSAVE
        if ats > 0:
            pg.time.set_timer(self.ats_event, ats * 60_000)

    def handle_events(self):
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
        scene_manager.update(dt)

    def render(self):
        self.screen.fill((0, 0, 0))  # Make sure the display is cleared
        scene_manager.draw(self.screen)  # Draw the current scene
        pg.display.flip()  # Render the display
