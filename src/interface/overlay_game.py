from __future__ import annotations
import pygame as pg
from src.interface.components import Overlay, Button, Slider
from src.core.services import sound_manager
from src.utils import GameSettings, Logger
from typing import Callable
from src.sprites import Sprite


class SettingOverlay(Overlay):
    bg: Sprite

    def __init__(self, on_close: Callable[[], None] | None = None):
        super().__init__(on_close, overlay_alpha=128)

        # Back button
        back_button = Button(
            "UI/button_back.png",
            "UI/button_back_hover.png",
            GameSettings.SCREEN_WIDTH // 2 - 50,
            GameSettings.SCREEN_HEIGHT - 150,
            100,
            100,
            on_close,
        )
        self.add_button(back_button)

        # Create bg

        wi = GameSettings.SCREEN_WIDTH // 100
        hi = GameSettings.SCREEN_HEIGHT // 100
        self.bgx = wi * 70
        self.bgy = hi * 80
        self.bg = Sprite(
            "UI/raw/UI_Flat_Frame03a.png",
            (self.bgx, self.bgy),
        )

        self.bg.rect.center = (
            GameSettings.SCREEN_WIDTH // 2,
            GameSettings.SCREEN_HEIGHT // 2,
        )

        # Volume Slider
        def set_vol(state):
            GameSettings.AUDIO_VOLUME = state
            if sound_manager.current_bgm:
                sound_manager.current_bgm.set_volume(state)

        ax, ay = self.bgx // 100, self.bgy // 100
        cx, cy = self.bg.rect.center
        self.volume_slider = Slider(
            "UI/raw/UI_Flat_FrameSlot03b.png",
            "UI/raw/UI_Flat_BarFill01g.png",
            "UI/raw/UI_Flat_BarFill01e.png",
            "UI/raw/UI_Flat_FrameSlot03a.png",
            cx,
            cy,
            ax * 70,
            ay * 34,
            ax * 3,
            ay * 5,
            GameSettings.AUDIO_VOLUME,
            action=set_vol,
        )

    def update_content(self, dt: float) -> None:
        self.volume_slider.update(dt)

    def draw_content(self, screen: pg.Surface) -> None:
        self.bg.draw(screen)
        self.volume_slider.draw(screen)
