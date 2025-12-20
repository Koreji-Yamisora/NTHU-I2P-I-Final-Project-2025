import pygame as pg
from src.utils import GameSettings, Logger
import os


class CoastRenderer:
    def __init__(self, tmxdata):
        self.tmxdata = tmxdata
        self.coast_objects = []
        self.images = {}  # tuple(terrain, side) -> list[Surface]
        self.animation_timer = 0
        self.current_frame_index = 0
        self.frame_duration = 0.2

        # Load coast assets
        self._load_coast_assets()
        # Parse objects
        self._load_coast_objects()

    def _import_tilemap(self, cols, rows, path):
        frames = {}
        try:
            surf = pg.image.load(path).convert_alpha()
            # Calculate cell size based on image size and rows/cols
            cell_width = surf.get_width() / cols
            cell_height = surf.get_height() / rows

            for col in range(cols):
                for row in range(rows):
                    cutout_rect = pg.Rect(
                        col * cell_width, row * cell_height, cell_width, cell_height
                    )
                    cutout_surf = pg.Surface((cell_width, cell_height), pg.SRCALPHA)
                    cutout_surf.blit(surf, (0, 0), cutout_rect)
                    cutout_surf = pg.transform.scale(
                        cutout_surf, (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
                    )
                    frames[(col, row)] = cutout_surf
        except Exception as e:
            Logger.error(f"Failed to load coast tilemap {path}: {e}")
        return frames

    def _load_coast_assets(self):
        path = "assets/maps/graphics/tilesets/coast.png"
        if not os.path.exists(path):
            Logger.error(f"Coast tileset not found at {path}")
            return

        cols = 24
        rows = 12
        frame_dict = self._import_tilemap(cols, rows, path)

        terrains = [
            "grass",
            "grass_i",
            "sand_i",
            "sand",
            "rock",
            "rock_i",
            "ice",
            "ice_i",
        ]
        sides = {
            "topleft": (0, 0),
            "top": (1, 0),
            "topright": (2, 0),
            "left": (0, 1),
            "right": (2, 1),
            "bottomleft": (0, 2),
            "bottom": (1, 2),
            "bottomright": (2, 2),
        }

        for index, terrain in enumerate(terrains):
            self.images[terrain] = {}  # Nested dict: images[terrain][side]
            for key, pos in sides.items():
                # Extract animation frames
                # Guide: returns list of frames
                frames = [
                    frame_dict[(pos[0] + index * 3, pos[1] + row)]
                    for row in range(0, rows, 3)
                ]
                self.images[terrain][key] = frames

    def _load_coast_objects(self):
        for layer in self.tmxdata.visible_layers:
            if layer.name == "Coast":
                for obj in layer:
                    side = obj.properties.get("side")
                    terrain = obj.properties.get("terrain", "sand")

                    if side:
                        self.coast_objects.append(
                            {
                                "x": obj.x,
                                "y": obj.y,
                                "width": obj.width,
                                "height": obj.height,
                                "side": side,
                                "terrain": terrain,
                            }
                        )

    def update(self, dt):
        self.animation_timer += dt
        if self.animation_timer >= self.frame_duration:
            self.animation_timer = 0
            self.current_frame_index = (self.current_frame_index + 1) % 4

    def draw(self, screen, camera):
        scale_x = GameSettings.TILE_SIZE / self.tmxdata.tilewidth
        scale_y = GameSettings.TILE_SIZE / self.tmxdata.tileheight

        for obj in self.coast_objects:
            side = obj["side"]
            terrain = obj["terrain"]

            # Access from nested dict
            if terrain in self.images and side in self.images[terrain]:
                frames = self.images[terrain][side]
                img = frames[self.current_frame_index]

                # Standard Tiled Object adjustment: (TopLeft) = x, y - height
                # Assuming map loading preserves raw Tiled Coordinates for objects
                x = obj["x"] * scale_x
                y = (obj["y"] - obj["height"]) * scale_y

                rect = pg.Rect(x, y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
                screen.blit(img, camera.transform_rect(rect))
