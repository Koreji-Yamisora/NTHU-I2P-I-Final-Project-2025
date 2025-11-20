import pygame as pg
from src.utils import load_sound, GameSettings


class SoundManager:
    def __init__(self):
        pg.mixer.init()
        pg.mixer.set_num_channels(GameSettings.MAX_CHANNELS)
        self.current_bgm = None

    def play_bgm(self, filepath: str):
        if self.current_bgm:
            self.current_bgm.stop()
        audio = load_sound(filepath)
        # Set volume based on mute state
        if GameSettings.AUDIO_MUTE:
            audio.set_volume(0)
        else:
            audio.set_volume(GameSettings.AUDIO_VOLUME)
        audio.play(-1)
        self.current_bgm = audio
        # Also refresh all channels to ensure consistency
        self.refresh()

    def refresh(self):
        for channel in range(pg.mixer.get_num_channels()):
            if GameSettings.AUDIO_MUTE:
                pg.mixer.Channel(channel).set_volume(0)
            else:
                pg.mixer.Channel(channel).set_volume(GameSettings.AUDIO_VOLUME)

    def pause_all(self):
        pg.mixer.pause()

    def resume_all(self):
        pg.mixer.unpause()

    def play_sound(self, filepath, volume=0.7):
        sound = load_sound(filepath)
        sound.set_volume(volume)
        sound.play()

    def stop_all_sounds(self):
        pg.mixer.stop()
        self.current_bgm = None
