import pygame as pg
import pytmx
from src.utils import Logger
from src.utils import load_tmx, Position, GameSettings, PositionCamera, Teleport


class Map:
    """Map."""

    path_name: str
    tmxdata: pytmx.TiledMap
    spawn: Position
    teleporters: list[Teleport]
    _surface: pg.Surface
    _collision_map: list[pg.Rect]
    _bush: list[pg.Rect]

    def __init__(
        self,
        path: str,
        tp: list[Teleport],
        spawn: Position,
    ):
        self.path_name = path
        self.tmxdata = load_tmx(path)
        self.spawn = spawn
        self.teleporters = tp
        self.ratio = self.tmxdata.width / self.tmxdata.height
        pixel_w = self.tmxdata.width * GameSettings.TILE_SIZE
        pixel_h = self.tmxdata.height * GameSettings.TILE_SIZE
        self._surface = pg.Surface((pixel_w, pixel_h), pg.SRCALPHA)
        self._render_all_layers(self._surface)
        self._collision_map = self._create_collision_map()
        self._bush = self._create_bush()
        self.lights = self._create_lights()

    def update(self, dt: float):
        """Update."""
        return

    def draw(self, screen: pg.Surface, camera: PositionCamera):
        """Draw."""
        screen.blit(self._surface, camera.transform_position(Position(0, 0)))
        if GameSettings.DRAW_HITBOXES:
            for rect in self._collision_map:
                pg.draw.rect(screen, (255, 0, 0), camera.transform_rect(rect), 1)
            for rect in self._bush:
                pg.draw.rect(screen, (0, 255, 0), camera.transform_rect(rect), 1)

    def check_collision(self, rect: pg.Rect) -> bool:
        """
        [TODO HACKATHON 4]
        Return True if collide if rect param collide with self._collision_map
        Hint: use API colliderect and iterate each rectangle to check
        """
        for collision_rect in self._collision_map:
            if rect.colliderect(collision_rect):
                return True
        return False

    def check_bush(self, rect: pg.Rect) -> bool:
        """Check Bush."""
        for bush in self._bush:
            if rect.colliderect(bush):
                return True
        return False

    def check_teleport(self, rect: pg.Rect) -> Teleport | None:
        """Check Teleport."""
        for teleporter in self.teleporters:
            tp_rect = pg.Rect(
                teleporter.pos.x,
                teleporter.pos.y,
                GameSettings.TILE_SIZE,
                GameSettings.TILE_SIZE,
            )
            if rect.colliderect(tp_rect):
                return teleporter
        return None



    def minimap_surface(
        self, pixelated: int = 4, sfact=2, surface: (pg.Surface | None) = None
    ) -> pg.Surface:
        """Minimap Surface."""
        if surface is None:
            pixel_w = self.tmxdata.width * pixelated
            pixel_h = self.tmxdata.height * pixelated
            minimap = pg.Surface((pixel_w, pixel_h), pg.SRCALPHA)
        for layer in self.tmxdata.visible_layers:
            if (
                isinstance(layer, pytmx.TiledTileLayer)
                and "pokemonbush" not in layer.name.lower()
            ):
                size = self._render_tile_layer(minimap, layer, pixelated, sfact)
        return minimap

    def _render_all_layers(self, target: pg.Surface) -> None:
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                self._render_tile_layer(target, layer)
            elif isinstance(layer, pytmx.TiledObjectGroup):
                self.get_object_layer(target, layer)

    def get_object_layer(
        self, target: pg.Surface, layer: pytmx.TiledObjectGroup
    ) -> None:
        scale_x = GameSettings.TILE_SIZE / self.tmxdata.tilewidth
        scale_y = GameSettings.TILE_SIZE / self.tmxdata.tileheight
        for obj in layer:
            if obj.gid:
                image = self.tmxdata.get_tile_image_by_gid(obj.gid)
                if image:
                    w = obj.width * scale_x
                    h = obj.height * scale_y
                    image = pg.transform.scale(image, (int(w), int(h)))
                    x = obj.x * scale_x
                    y = (obj.y - obj.height) * scale_y
                    target.blit(image, (x, y))

    def _render_tile_layer(
        self,
        target: pg.Surface,
        layer: pytmx.TiledTileLayer,
        pixelated: int = 0,
        s: int = 1,
    ) -> None:
        pixel_w = self.tmxdata.width * pixelated
        pixel_h = self.tmxdata.height * pixelated
        temp = pg.Surface((pixel_w, pixel_h), pg.SRCALPHA)
        for x, y, gid in layer:
            if gid == 0:
                continue
            image = self.tmxdata.get_tile_image_by_gid(gid)
            if image is None:
                continue
            if pixelated:
                image = pg.transform.smoothscale(image, (s, s))
                size = target.get_size()
                image = pg.transform.scale(image, (pixelated, pixelated))
                temp.blit(image, (x * pixelated, y * pixelated))
            else:
                image = pg.transform.scale(
                    image, (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
                )
                target.blit(
                    image, (x * GameSettings.TILE_SIZE, y * GameSettings.TILE_SIZE)
                )
        if pixelated:
            temp = pg.transform.scale(temp, target.get_size())
            target.blit(temp, (0, 0))

    def _create_collision_map(self) -> list[pg.Rect]:
        rects = []
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and (
                "collision" in layer.name.lower() or "house" in layer.name.lower()
            ):
                for x, y, gid in layer:
                    if gid != 0:
                        """
                        [TODO HACKATHON 4]
                        rects.append(pg.Rect(...))
                        Append the collision rectangle to the rects[] array
                        Remember scale the rectangle with the TILE_SIZE from settings
                        """
                        rects.append(
                            pg.Rect(
                                x * GameSettings.TILE_SIZE,
                                y * GameSettings.TILE_SIZE,
                                GameSettings.TILE_SIZE,
                                GameSettings.TILE_SIZE,
                            )
                        )
        return rects

    def _create_bush(self) -> list[pg.Rect]:
        rects = []
        for layer in self.tmxdata.visible_layers:
            if (
                isinstance(layer, pytmx.TiledTileLayer)
                and "pokemonbush" in layer.name.lower()
            ):
                for x, y, gid in layer:
                    if gid != 0:
                        rects.append(
                            pg.Rect(
                                x * GameSettings.TILE_SIZE,
                                y * GameSettings.TILE_SIZE,
                                GameSettings.TILE_SIZE,
                                GameSettings.TILE_SIZE,
                            )
                        )
        return rects

    def _create_lights(self) -> list[Position]:
        """Create lights from map objects or tiles."""
        lights = []
        for layer in self.tmxdata.visible_layers:
            # 1. Prioritize Object Groups explicitly named "Light" or "Lights"
            if isinstance(layer, pytmx.TiledObjectGroup) and "light" in layer.name.lower():
                for obj in layer:
                    # Center of the object
                    lights.append(Position(obj.x + obj.width/2, obj.y + obj.height/2))
            
            # 2. Fallback: Check for "House" or "Building" tile layers to simulate window lights
            elif isinstance(layer, pytmx.TiledTileLayer) and (
                "house" in layer.name.lower() or "building" in layer.name.lower()
            ):
                 for x, y, gid in layer:
                    if gid != 0:
                        lights.append(
                            Position(
                                x * GameSettings.TILE_SIZE + GameSettings.TILE_SIZE / 2,
                                y * GameSettings.TILE_SIZE + GameSettings.TILE_SIZE / 2,
                            )
                        )
        return lights

    @classmethod
    def from_dict(cls, data: dict) -> "Map":
        """From Dict."""
        tp = [Teleport.from_dict(t) for t in data["teleport"]]
        pos = Position(
            data["player"]["x"] * GameSettings.TILE_SIZE,
            data["player"]["y"] * GameSettings.TILE_SIZE,
        )
        return cls(data["path"], tp, pos)

    def to_dict(self):
        """To Dict."""
        return {
            "path": self.path_name,
            "teleport": [t.to_dict() for t in self.teleporters],
            "player": {
                "x": self.spawn.x // GameSettings.TILE_SIZE,
                "y": self.spawn.y // GameSettings.TILE_SIZE,
            },
        }
