from src.core.managers import GameManager, OnlineManager
from src.utils import Logger
from src.utils.settings import GameSettings


class GMhelper:
    """G Mhelper."""

    path = "saves/game0.json"

    def __init__(self):
        self.gm = None
        self.up = False

    def save(self):
        """Save."""
        if self.gm:
            self.gm.save(self.path)

    def load(self):
        """Load."""
        gm = GameManager.load(self.path)
        if gm is None:
            Logger.error("Failed to load game manager")
            exit(1)
        else:
            self.gm = gm
            self.up = True


if GameSettings.IS_ONLINE:
    online_manager = OnlineManager()
else:
    online_manager = None


gh = GMhelper()
