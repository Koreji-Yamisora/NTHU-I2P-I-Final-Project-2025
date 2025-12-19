from src.core.managers import GameManager, OnlineManager
from src.utils import Logger
from src.utils.settings import GameSettings


class GMhelper:
    """G Mhelper."""

    path = "saves/game0.json"

    def __init__(self):
        self._gm = None
        self._online_manager = None
        self.path = "saves/game0.json"  # Default
        if GameSettings.IS_ONLINE:
            self._online_manager = OnlineManager()

    @property
    def gm(self):
        return self._gm

    @property
    def online_manager(self):
        return self._online_manager

    def set_save_path(self, path: str):
        self.path = path

    def get_slot_path(self, index: int) -> str:
        return f"saves/game{index}.json"

    def delete_save(self, index: int):
        import os

        path = self.get_slot_path(index)
        if os.path.exists(path):
            os.remove(path)

    def get_save_files(self) -> list[str]:
        import os
        import glob

        # Return sorted list of game*.json files
        files = glob.glob("saves/game*.json")
        files.sort()
        return files

    def get_next_save_path(self) -> str:
        import os

        i = 0
        while True:
            p = f"saves/game{i}.json"
            if not os.path.exists(p):
                return p
            i += 1

    def stop_server_process(self):
        """Stop server process."""
        if hasattr(self, "server_process") and self.server_process:
            self.server_process.terminate()
            self.server_process = None

    def start_server_process(self):
        """Start server process."""
        import subprocess
        import sys

        if hasattr(self, "server_process") and self.server_process:
            if self.server_process.poll() is None:
                return  # Already running

        # Run server.py in a subprocess
        cmd = [sys.executable, "server.py"]
        try:
            self.server_process = subprocess.Popen(cmd)
            Logger.info(f"Server process started with PID {self.server_process.pid}")
        except Exception as e:
            Logger.error(f"Failed to start server process: {e}")

    def has_save(self) -> bool:
        """Check if ANY save file (0-2) exists."""
        import os

        for i in range(3):
            if os.path.exists(self.get_slot_path(i)):
                return True
        return False

    def new_game(self, slot_index: int = 0, username: str = "Player") -> bool:
        """Start a new game using start.json as template."""
        # Use start.json as the template for a new game
        template_path = "saves/start.json"

        # Set path to the chosen slot (will overwrite)
        self.path = self.get_slot_path(slot_index)

        # If start.json doesn't exist, try loading game0 but this is risky for a 'new' game
        # Alternatively, we could hardcode a minimal state, but loading backup is safer if it exists.
        import os

        if not os.path.exists(template_path):
            Logger.warning("start.json not found, trying game0.json or failing")
            if not os.path.exists(self.path):
                return False
            template_path = self.path

        gm = GameManager.load(template_path)
        if gm is None:
            Logger.error("Failed to generate new game state")
            return False

        self._gm = gm

        # Ensure player has at least one pokemon (Starter)
        if not self._gm.bag._monsters_data:
            from src.utils.generate import generate_party

            Logger.info("Empty bag detected in new game, generating starter...")
            self._gm.bag._monsters_data = generate_party(5, 1)  # 1 pokemon, lvl 5
            self._gm.bag.update_bag()

        # Set Username
        self._gm.username = username

        # Save immediately to establish the slot
        self._gm.save(self.path)

        # Ensure we start at the default map and spawn
        # (Assuming backup.json has reasonable defaults, otherwise we could force them here)
        # self._gm.current_map_key = "map.tmx"
        return True

    def save(self):
        """Save."""
        if self.gm:
            self.gm.save(self.path)

    def load(self) -> bool:
        """Load."""
        gm = GameManager.load(self.path)
        if gm is None:
            Logger.error("Failed to load game manager")
            return False
        else:
            self._gm = gm
            return True


gh = GMhelper()
online_manager = gh.online_manager
