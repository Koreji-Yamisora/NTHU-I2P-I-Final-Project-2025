import pygame as pg
from src.utils import GameSettings, Logger
import os
import pytmx


class WaterRenderer:
    def __init__(self, tmxdata):
        self.tmxdata = tmxdata
        self.frames = self.load_frames()
        self.frames = [
            pg.transform.scale(f, (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
            for f in self.frames
        ]
        # Use a set for unique positions
        self.positions = set()
        self.animation_timer = 0
        self.current_frame_index = 0
        self.frame_duration = 0.2
        self._find_water_tiles()

    def load_frames(self):
        frames = []
        base_path = "assets/maps/graphics/tilesets/water"
        try:
            for i in range(4):
                path = os.path.join(base_path, f"{i}.png")
                if os.path.exists(path):
                    img = pg.image.load(path).convert_alpha()
                    frames.append(img)
            Logger.info(f"Loaded {len(frames)} water frames")
        except Exception as e:
            Logger.error(f"Failed to load water frames: {e}")
        return frames

    def _find_water_tiles(self):
        self.positions = set()
        tile_size = GameSettings.TILE_SIZE
        scale_x = GameSettings.TILE_SIZE / self.tmxdata.tilewidth
        scale_y = GameSettings.TILE_SIZE / self.tmxdata.tileheight

        # 1. Scan Object Layers (Original Method)
        for layer in self.tmxdata.visible_layers:
            if (
                isinstance(layer, pytmx.TiledObjectGroup)
                and layer.name.lower() == "water"
            ):
                for obj in layer:
                    start_gx = int(round(obj.x * scale_x))
                    end_gx = int(round((obj.x + obj.width) * scale_x))
                    start_gy = int(round(obj.y * scale_y))
                    end_gy = int(round((obj.y + obj.height) * scale_y))

                    for x in range(start_gx, end_gx, int(tile_size)):
                        for y in range(start_gy, end_gy, int(tile_size)):
                            self.positions.add((x, y))

        # 2. Scan Tile Layers (New Method for Gaps)
        # Assuming GID 132 is the main water tile based on CSV analysis
        WATER_GIDS = {132}

        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name == "Terrain":
                for x, y, gid in layer:
                    if gid in WATER_GIDS:
                        # TiledTileLayer coordinates are in Grid units, need to multiply by TILE_SIZE
                        pos_x = x * tile_size
                        pos_y = y * tile_size
                        self.positions.add((pos_x, pos_y))

    def update(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= self.frame_duration:
            self.animation_timer = 0
            if self.frames:
                self.current_frame_index = (self.current_frame_index + 1) % len(
                    self.frames
                )

    def draw(self, screen, camera):
        if not self.frames:
            return

        current_image = self.frames[self.current_frame_index]
        for pos_x, pos_y in self.positions:
            rect = pg.Rect(pos_x, pos_y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
            screen.blit(current_image, camera.transform_rect(rect))
