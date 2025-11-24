from src.core.managers import GameManager
from src.utils import Logger


class GMhelper:
    path = "saves/game0.json"

    def __init__(self):
        self.gm = None
        self.up = False

    def save(self):
        if self.gm:
            self.gm.save(self.path)

    def load(self):
        gm = GameManager.load(self.path)
        if gm is None:
            Logger.error("Failed to load game manager")
            exit(1)
        else:
            self.gm = gm
            self.up = True


gh = GMhelper()
