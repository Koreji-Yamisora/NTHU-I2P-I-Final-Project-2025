import pygame as pg
import json
from src.utils import GameSettings, crd
from src.utils.definition import Monster, Item
from src.sprites import Sprite
from src.core.managers.resource_manager import ResourceManager


class Bag:
    _monsters_data: list[Monster]
    monster_Sprite: list[Sprite]
    _items_data: list[Item]
    items_Sprite: list[Sprite]

    def __init__(
        self,
        monsters_data: list[Monster] | None = None,
        items_data: list[Item] | None = None,
    ):
        self._monsters_data = monsters_data if monsters_data else []
        self._items_data = items_data if items_data else []
        self.resource_manager = ResourceManager()
        self.monster_Sprite = []
        self.items_Sprite = []

    def add_monster_col(self, col_rect: pg.Rect):
        self.monster_col_rect = col_rect
        self.mon_slot_height = self.monster_col_rect.height // 6
        self.mon_slots = [
            pg.Rect(
                self.monster_col_rect.left,
                self.monster_col_rect.top + self.mon_slot_height * idx,
                self.monster_col_rect.width,
                self.mon_slot_height,
            )
            for idx in range(6)
        ]

    def monster_slot(self, _monster_data: list[Monster]):
        self.monster_Sprite.clear()
        for idx, monster in enumerate(_monster_data):
            if idx < 6:
                sprite = Sprite(monster["sprite_path"], (64, 64))
                sprite.rect.center = self.mon_slots[idx].center
                self.monster_Sprite.append(sprite)

                # TODO
                # self.computer

    def add_item_col(self, col_rect: pg.Rect):
        self.item_col_rect = col_rect
        self.item_slot_height = self.item_col_rect.height // 8
        self.item_slots = [
            pg.Rect(
                self.item_col_rect.left,
                self.item_col_rect.top + self.item_slot_height * idx,
                self.item_col_rect.width,
                self.item_slot_height,
            )
            for idx in range(8)  # TODO scroll
        ]

    def item_slot(self, _item_data: list[Item]):
        self.items_Sprite.clear()
        for idx, item in enumerate(_item_data):
            if idx < 8:
                sprite = Sprite(item["sprite_path"], (64, 64))
                sprite.rect.center = self.item_slots[idx].center
                self.items_Sprite.append(sprite)

    def update(self, dt: float):
        pass

    def draw(self, screen: pg.Surface):
        for sprite in self.monster_Sprite:
            sprite.draw(screen)
        for sprite in self.items_Sprite:
            sprite.draw(screen)

    def to_dict(self) -> dict[str, object]:
        return {"monsters": list(self._monsters_data), "items": list(self._items_data)}

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Bag":
        monsters = data.get("monsters") or []
        items = data.get("items") or []
        bag = cls(monsters, items)
        return bag
