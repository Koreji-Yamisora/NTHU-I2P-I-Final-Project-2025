from dataclasses import dataclass, field


# Available resolution presets (width, height)
RESOLUTIONS = [
    (1280, 720),  # 720p
    (1600, 900),  # 900p
    (1710, 962),  # Default (original)
    (1920, 1080),  # 1080p
    (2560, 1440),  # 1440p
]


@dataclass
class Settings:
    """Settings."""

    # Resolution index into RESOLUTIONS list
    RESOLUTION_INDEX: int = 2  # Default to 1710x962
    # Internal/logical resolution (used for rendering)
    SCREEN_WIDTH: int = 1710
    SCREEN_HEIGHT: int = 962
    FPS: int = 60
    TITLE: str = "A game"
    DEBUG: bool = True
    TILE_SIZE: int = 64
    DRAW_HITBOXES: bool = True
    MAX_CHANNELS: int = 16
    BGM_VOLUME: float = 0.5
    SFX_VOLUME: float = 0.5
    AUDIO_MUTE: bool = True
    IS_ONLINE: bool = False
    ONLINE_SERVER_URL: str = "http://localhost:8989"
    AUTOSAVE: int = 10

    def set_resolution(self, index: int) -> None:
        """Set resolution index (doesn't affect internal resolution with pg.SCALED)."""
        if 0 <= index < len(RESOLUTIONS):
            self.RESOLUTION_INDEX = index


GameSettings = Settings()
