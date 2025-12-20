import pygame as pg
import pytmx
from src.utils import Logger
from src.utils import load_tmx, Position, GameSettings, PositionCamera, Teleport
from .water_renderer import WaterRenderer
from .coast_renderer import CoastRenderer


class SortableItem:
    """Item that can be Y-sorted."""

    def __init__(self, image: pg.Surface, pos: Position, width: int, height: int):
        self.image = image
        self.rect = pg.Rect(pos.x, pos.y, width, height)
        # We usually sort by the "bottom" or "feet" of the object
        # but the rect already has 'bottom'.
        # However, for drawing, we need the top-left position (rect.x, rect.y) or simple rect.
        # We'll just use self.rect for sorting and drawing position.

    def draw(self, screen: pg.Surface, camera: PositionCamera):
        screen.blit(self.image, camera.transform_rect(self.rect))


class Map:
    """Map."""

    path_name: str
    tmxdata: pytmx.TiledMap
    spawn: Position
    teleporters: list[Teleport]
    _surface: pg.Surface
    _collision_map: list[pg.Rect]
    _bush: list[pg.Rect]
    sortable_objects: list[SortableItem]

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
        self.sortable_objects = []  # Initialize before rendering
        self._render_all_layers(self._surface)
        self._collision_map = self._create_collision_map()
        self._bush = self._create_bush()
        self.lights = self._create_lights()
        self._parse_teleporters()

        # Extended Rendering
        self.water_renderer = WaterRenderer(self.tmxdata)
        self.coast_renderer = CoastRenderer(self.tmxdata)

    def draw(self, screen: pg.Surface, camera: PositionCamera):
        """Draw ground surface only."""
        screen.blit(self._surface, camera.transform_position(Position(0, 0)))

        # Render Animated Water
        if hasattr(self, "water_renderer"):
            self.water_renderer.draw(screen, camera)

        # Render Coast
        if hasattr(self, "coast_renderer"):
            self.coast_renderer.draw(screen, camera)

        if GameSettings.DRAW_HITBOXES:
            for rect in self._collision_map:
                pg.draw.rect(screen, (255, 0, 0), camera.transform_rect(rect), 1)
            for rect in self._bush:
                pg.draw.rect(screen, (0, 255, 0), camera.transform_rect(rect), 1)

    def check_collision(self, rect: pg.Rect) -> bool:
        """
        Return True if collide if rect param collide with self._collision_map
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
            layer_name = layer.name.lower()

            # If layer is House or Tree or Bush or Objects or Monsters, we extract it as Sortable objects
            if (
                "house" in layer_name
                or "tree" in layer_name
                or "bush" in layer_name
                or "building" in layer_name
                or "objects" in layer_name
                or "monsters" in layer_name
            ):
                self._extract_sortable_layer(layer)
            elif isinstance(layer, pytmx.TiledTileLayer):
                self._render_tile_layer(target, layer)
            elif isinstance(layer, pytmx.TiledObjectGroup):
                self.get_object_layer(target, layer)

    def _extract_sortable_layer(self, layer):
        """Extract tiles/objects into sortable_objects list."""
        count = 0
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                if gid != 0:
                    image = self.tmxdata.get_tile_image_by_gid(gid)
                    if image:
                        image = pg.transform.scale(
                            image, (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
                        )
                        # Position is top-left
                        pos = Position(
                            x * GameSettings.TILE_SIZE, y * GameSettings.TILE_SIZE
                        )
                        item = SortableItem(
                            image, pos, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE
                        )
                        self.sortable_objects.append(item)
                        count += 1
        elif isinstance(layer, pytmx.TiledObjectGroup):
            # Not typically used for visual tiles unless they are Object Tiles
            scale_x = GameSettings.TILE_SIZE / self.tmxdata.tilewidth
            scale_y = GameSettings.TILE_SIZE / self.tmxdata.tileheight
            for obj in layer:
                if obj.gid:
                    image = self.tmxdata.get_tile_image_by_gid(obj.gid)
                    w = obj.width * scale_x
                    h = obj.height * scale_y
                    image = pg.transform.scale(image, (int(w), int(h)))
                    x = obj.x * scale_x
                    # Tiled Object Y is bottom-left (mostly), but pytmx might handle it.
                    # pytmx obj.y                        # Tiled saves bottom-left for objects.
                    # y = (obj.y - obj.height) * scale_y
                    # Let's verify this assumption.
                    y = obj.y * scale_y
                    pos = Position(x, y)
                    item = SortableItem(image, pos, int(w), int(h))
                    self.sortable_objects.append(item)
                    count += 1
        Logger.info(f"-> Extracted {count} items from {layer.name}")

    def get_object_layer(
        self, target: pg.Surface, layer: pytmx.TiledObjectGroup
    ) -> None:
        # Don't draw logic layers like Collisions, Transition, etc.
        if layer.name in ("Collisions", "Transition", "Monsters", "Entities"):
            return

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
            # 1. Tile Layer Collisions (Legacy)
            if isinstance(layer, pytmx.TiledTileLayer) and (
                "collision" in layer.name.lower()
                or "house" in layer.name.lower()
                or "tree" in layer.name.lower()
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

            # 2. Object Layer Collisions
            elif isinstance(layer, pytmx.TiledObjectGroup):
                # Case A: Explicit collision layer (Raw coordinates)
                if "collisions" in layer.name.lower():
                    for obj in layer:
                        rects.append(pg.Rect(obj.x, obj.y, obj.width, obj.height))

                # Case B: Renderable Object Layers (Scaled coordinates)
                elif (
                    "house" in layer.name.lower()
                    or "tree" in layer.name.lower()
                    or "objects" in layer.name.lower()
                    or "building" in layer.name.lower()
                ):
                    scale_x = GameSettings.TILE_SIZE / self.tmxdata.tilewidth
                    scale_y = GameSettings.TILE_SIZE / self.tmxdata.tileheight
                    for obj in layer:
                        # Filter Bushes (No Collision)
                        if obj.name and "bush" in obj.name.lower():
                            continue

                        # Scale Coordinates
                        r_x = obj.x * scale_x
                        # Correction: Tiled Objects (Tile Objects) Y is Bottom-Left.
                        # Visuals are drawing at `obj.y * scale` (effectively shifted down by height relative to top-left).
                        # User says Hitbox at `obj.y` is "Below".
                        # So we shift Hitbox UP to `obj.y - height` (Natural Top-Left).
                        r_y = obj.y * scale_y
                        r_w = obj.width * scale_x
                        r_h = obj.height * scale_y

                        # Specialized Collision logic
                        if obj.name and "tree" in obj.name.lower():
                            # Tree: small hitbox at the bottom (stump)
                            # Let's say bottom 20% or fixed 20px
                            stump_h = min(r_h * 0.3, 30)
                            r_y += r_h - stump_h
                            r_h = stump_h
                            # Also shrink width slightly?
                            inset = r_w * 0.2
                            r_x += inset
                            r_w -= inset * 2

                        # LOGGING (Optional, keep for debugging if needed)
                        # Logger.info(f"Collision Gen: {obj.name} -> Rect({r_x}, {r_y}, {r_w}, {r_h})")

                        rects.append(pg.Rect(r_x, r_y, r_w, r_h))
        return rects

    def _create_bush(self) -> list[pg.Rect]:
        rects = []
        for layer in self.tmxdata.visible_layers:
            # 1. Tile Layer Bush (Legacy)
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
            # 2. Object Layer Bush/Monsters (Python-Monsters)
            elif (
                isinstance(layer, pytmx.TiledObjectGroup)
                and "monsters" in layer.name.lower()
            ):
                for obj in layer:
                    rects.append(pg.Rect(obj.x, obj.y, obj.width, obj.height))

        return rects

    def _create_lights(self) -> list[Position]:
        """Create lights from map objects or tiles."""
        lights = []
        for layer in self.tmxdata.visible_layers:
            # 1. Prioritize Object Groups explicitly named "Light" or "Lights"
            if (
                isinstance(layer, pytmx.TiledObjectGroup)
                and "light" in layer.name.lower()
            ):
                for obj in layer:
                    # Center of the object
                    lights.append(
                        Position(obj.x + obj.width / 2, obj.y + obj.height / 2)
                    )

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

            # 3. Object Layers for Houses (if houses are objects)
            elif isinstance(layer, pytmx.TiledObjectGroup) and (
                "house" in layer.name.lower() or "building" in layer.name.lower()
            ):
                for obj in layer:
                    # Place light at the center of the object (or maybe slightly lower for door?)
                    # Using center for now as it's general.
                    lights.append(
                        Position(obj.x + obj.width / 2, obj.y + obj.height / 2)
                    )
        return lights

    def _parse_teleporters(self) -> None:
        """Parse object layer for teleporters."""
        for layer in self.tmxdata.visible_layers:
            if (
                isinstance(layer, pytmx.TiledObjectGroup)
                and "transition" in layer.name.lower()
            ):
                for obj in layer:
                    target_map = obj.properties.get("target")
                    target_pos_tuple = obj.properties.get("pos")  # (x, y)

                    if target_map:
                        # Python-Monsters maps use 'pos' property which is tuple (x, y)
                        # We convert this to our Position object for destination
                        to_pos = None
                        if target_pos_tuple:
                            to_pos = Position(target_pos_tuple[0], target_pos_tuple[1])

                        tp = Teleport(
                            pos=Position(obj.x, obj.y),
                            destination=target_map,  # e.g. "house" (will act as key)
                            to_pos=to_pos,
                        )
                        self.teleporters.append(tp)

    def get_entities(self) -> list[dict]:
        """Parse 'Entities' object layer."""
        entities = []
        for layer in self.tmxdata.visible_layers:
            if (
                isinstance(layer, pytmx.TiledObjectGroup)
                and "entities" in layer.name.lower()
            ):
                for obj in layer:
                    entity_data = {
                        "name": obj.name,
                        "x": obj.x,
                        "y": obj.y,
                        "width": obj.width,
                        "height": obj.height,
                        "properties": obj.properties,
                    }
                    entities.append(entity_data)
        return entities

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

    # Added Update for Animations
    def update(self, dt: float):
        """Update."""
        if hasattr(self, "water_renderer"):
            self.water_renderer.update(dt)
        if hasattr(self, "coast_renderer"):
            self.coast_renderer.update(dt)
