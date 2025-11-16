import pygame as pg
import json
from src.utils import GameSettings, crd
from src.utils.definition import Monster, Item
from src.sprites import Sprite, Text
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
        self.monster_data = []
        self.item_data = []
        self.mbgs = []

    def refresh(self):
        # Check if slots are initialized before refreshing
        if not hasattr(self, "mon_slots") or not hasattr(self, "item_slots"):
            return  # Can't refresh if slots aren't set up yet
        self.monster_slot(self._monsters_data)
        self.item_slot(self._items_data)

    def add_monster_col(self, col_rect: pg.Rect):
        self.monster_col_rect = col_rect
        self.mon_slot_height = self.monster_col_rect.height // 6
        self.mon_slots = []

        for idx in range(6):
            mbg = Sprite(
                "UI/raw/UI_Flat_Frame03a.png",
                (self.monster_col_rect.width, crd(self.mon_slot_height)),
            )
            self.mon_slots.append(
                pg.Rect(
                    self.monster_col_rect.left,
                    self.monster_col_rect.top + self.mon_slot_height * idx,
                    self.monster_col_rect.width,
                    self.mon_slot_height,
                )
            )
            mbg.rect.center = self.mon_slots[idx].center
            self.mbgs.append(mbg)

    def monster_slot(self, _monster_data: list[Monster]):
        self.monster_data.clear()
        for idx, monster in enumerate(_monster_data):
            if idx < 6:
                sprite = Sprite(monster["sprite_path"], (64, 64))
                sprite.rect.center = self.mon_slots[idx].center
                name = Text(monster["name"], 24, "azure")
                name.rect.topleft = (
                    self.mon_slots[idx].left + crd(self.mon_slots[idx].width).per(5),
                    self.mon_slots[idx].top + crd(self.mon_slot_height).per(5),
                )
                hp = Text(f"HP: {monster['hp']}/{monster['max_hp']}", 24, "azure")
                hp.rect.topleft = (
                    self.mon_slots[idx].left + crd(self.mon_slots[idx].width).per(5),
                    self.mon_slots[idx].top + crd(self.mon_slot_height).per(35),
                )

                level = Text("Level: " + str(monster["level"]), 24, "azure")
                level.rect.topleft = (
                    self.mon_slots[idx].left + crd(self.mon_slots[idx].width).per(5),
                    self.mon_slots[idx].top + crd(self.mon_slot_height).per(65),
                )
                self.monster_data.append((sprite, name, hp, level))

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
        self.item_data.clear()
        for idx, item in enumerate(_item_data):
            if idx < 8:
                sprite = Sprite(item["sprite_path"], (48, 48))
                sprite.rect.center = self.item_slots[idx].center
                name = Text(item["name"], 24, "azure")
                name.rect.left = self.item_slots[idx].left + crd(
                    self.item_slots[idx].width
                ).per(5)
                name.rect.centery = self.item_slots[idx].top + crd(
                    self.item_slot_height
                ).per(50)

                count = Text(str(item["count"]), 24, "azure")
                count.rect.left = name.rect.right + crd(self.item_slots[idx].width).per(
                    5
                )
                count.rect.centery = self.item_slots[idx].top + crd(
                    self.item_slot_height
                ).per(50)

                self.item_data.append((sprite, name, count))

    def update(self, dt: float):
        pass

    def draw(self, screen: pg.Surface):
        for bg in self.mbgs:
            bg.draw(screen)
        for mon in self.monster_data:
            for i in mon:
                i.draw(screen)
        for item in self.item_data:
            for i in item:
                i.draw(screen)

    def to_dict(self) -> dict[str, object]:
        return {"monsters": list(self._monsters_data), "items": list(self._items_data)}

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Bag":
        monsters = data.get("monsters") or []
        items = data.get("items") or []
        bag = cls(monsters, items)
        return bag
