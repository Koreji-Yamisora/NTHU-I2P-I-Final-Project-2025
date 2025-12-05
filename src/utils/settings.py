from dataclasses import dataclass


@dataclass
class Settings:
    """Settings."""
    SCREEN_WIDTH: int = 1710
    SCREEN_HEIGHT: int = 962
    FPS: int = 60
    TITLE: str = 'I2P Final'
    DEBUG: bool = True
    TILE_SIZE: int = 64
    DRAW_HITBOXES: bool = True
    MAX_CHANNELS: int = 16
    AUDIO_VOLUME: float = 0.5
    AUDIO_MUTE: bool = False
    IS_ONLINE: bool = True
    ONLINE_SERVER_URL: str = 'http://localhost:8989'
    AUTOSAVE: int = 10


GameSettings = Settings()
