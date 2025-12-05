import pygame as pg
import json
from src.utils import GameSettings, crd, Logger
from src.utils.definition import Monster, Item
from src.sprites import Sprite, Text
from src.core.managers.resource_manager import ResourceManager
from src.data import pokedex


class Bag:
    """Bag."""
    _monsters_data: list[Monster]
    _items_data: list[Item]
    monsters: list[dict]

    def __init__(self, monsters_data: (list[Monster] | None)=None,
        items_data: (list[Item] | None)=None):
        self._monsters_data = monsters_data if monsters_data else []
        self._items_data = items_data if items_data else []
        self.resource_manager = ResourceManager()
        self.monster_data = []
        self.item_data = []
        self.mbgs = []
        self.monsters = []

    def save_battle(self, monsters: list[dict]):
        """Save battle."""
        self.monsters = monsters
        for i in range(len(monsters)):
            self._monsters_data[i]['hp'] = monsters[i]['chp']

    def get_items(self):
        """Get items."""
        item = []
        for i in range(len(self._items_data)):
            item.append(self.idx_to_item(i))
        return item

    def idx_to_item(self, idx):
        """Idx To Item."""
        item = {}
        item['sprite'] = self._items_data[idx]['sprite_path']
        item['name'] = self._items_data[idx]['name']
        item['count'] = self._items_data[idx]['count']
        return item

    def add_item(self, item):
        """Add Item."""
        if item['name'] not in [i['name'] for i in self._items_data]:
            self._items_data.append(item)
        else:
            for i in range(len(self._items_data)):
                if self._items_data[i]['name'] == item['name']:
                    self._items_data[i]['count'] += 1
                    break

    def add_monster_col(self, col_rect: pg.Rect):
        """Add Monster Col."""
        self.monster_col_rect = col_rect
        self.mon_slot_height = self.monster_col_rect.height // 6
        self.mon_slots = []
        for idx in range(6):
            mbg = Sprite('UI/raw/UI_Flat_Frame03a.png', (self.
                monster_col_rect.width, self.mon_slot_height))
            self.mon_slots.append(pg.Rect(self.monster_col_rect.left, self.
                monster_col_rect.top + self.mon_slot_height * idx, self.
                monster_col_rect.width, crd(self.mon_slot_height).per(50)))
            mbg.rect = self.mon_slots[idx]
            self.mbgs.append(mbg)
        self.monster_slot()

    def my_mon(self):
        """My Mon."""
        stat = 'atk', 'def', 'spa', 'spd', 'spe'
        mod = 1
        self.monsters = []
        for i, mon in enumerate(self._monsters_data):
            if i == 6:
                break
            base = pokedex.data[mon['id']]
            hp = int((2 * base['hp'] + mon['IV']['hp'] + mon['EV']['hp'] / 
                4) * mon['level'] / 100) + mon['level'] + 10
            stats = []
            for s in stat:
                stats.append((int((2 * base[s] + mon['IV'][s] + mon['EV'][s
                    ] / 4) * mon['level'] / 100) + 5) * mod)
            atk, defen, spa, spd, spe = stats
            self.monsters.append({'idx': i, 'id': mon['id'], 'name': mon[
                'name'], 'level': mon['level'], 'chp': mon['hp'], 'hp': hp,
                'atk': atk, 'def': defen, 'spa': spa, 'spd': spd, 'spe':
                spe, 'type': base['type'], 'move': mon['move']})

    def monster_slot(self):
        """Monster Slot."""
        self.monster_data.clear()
        for idx, monster in enumerate(self.monsters):
            sprite = Sprite(pokedex.data[monster['id']]['sprite_path'], (72,
                72))
            sprite.rect.center = self.mon_slots[idx].centerx + crd(self.
                mon_slots[idx].width).per(15), self.mon_slots[idx
                ].centery + crd(self.mon_slot_height).per(25)
            name = Text(monster['name'], 24, 'azure')
            name.rect.topleft = self.mon_slots[idx].left + crd(self.
                mon_slots[idx].width).per(8), self.mon_slots[idx].top + crd(
                self.mon_slot_height).per(5)
            hp = Text(f"HP: {monster['chp']}/{monster['hp']}", 24, 'azure')
            hp.rect.topleft = self.mon_slots[idx].left + crd(self.mon_slots
                [idx].width).per(8), self.mon_slots[idx].top + crd(self.
                mon_slot_height).per(35)
            level = Text('Level: ' + str(monster['level']), 24, 'azure')
            level.rect.topleft = self.mon_slots[idx].left + crd(self.
                mon_slots[idx].width).per(8), self.mon_slots[idx].top + crd(
                self.mon_slot_height).per(65)
            self.monster_data.append((sprite, name, hp, level))

    def add_item_col(self, col_rect: pg.Rect):
        """Add Item Col."""
        self.item_col_rect = col_rect
        self.item_slot_height = self.item_col_rect.height // 8
        self.item_slots = [pg.Rect(self.item_col_rect.left, self.
            item_col_rect.top + self.item_slot_height * idx, self.
            item_col_rect.width, self.item_slot_height) for idx in range(8)]
        self.item_slot()

    def item_slot(self):
        """Item Slot."""
        self.item_data.clear()
        for idx, item in enumerate(self._items_data):
            if idx < 8:
                sprite = Sprite(item['sprite_path'], (64, 64))
                sprite.rect.center = self.item_slots[idx].center
                name = Text(item['name'], 24, 'azure')
                name.rect.left = self.item_slots[idx].left + crd(self.
                    item_slots[idx].width).per(5)
                name.rect.centery = self.item_slots[idx].top + crd(self.
                    item_slot_height).per(50)
                count = Text(str(item['count']), 24, 'azure')
                count.rect.left = name.rect.right + crd(self.item_slots[idx
                    ].width).per(5)
                count.rect.centery = self.item_slots[idx].top + crd(self.
                    item_slot_height).per(50)
                self.item_data.append((sprite, name, count))

    def update(self, dt: float):
        """Update."""
        pass

    def update_bag(self):
        """Update bag."""
        self.my_mon()
        self.monster_slot()
        self.item_slot()

    def draw(self, screen: pg.Surface):
        """Draw."""
        for bg in self.mbgs:
            bg.draw(screen)
        for mon in self.monster_data:
            for i in mon:
                i.draw(screen)
        for item in self.item_data:
            for i in item:
                i.draw(screen)

    def to_dict(self) ->dict[str, object]:
        """To Dict."""
        return {'monsters': list(self._monsters_data), 'items': list(self.
            _items_data)}

    @classmethod
    def from_dict(cls, data: dict[str, object]) ->'Bag':
        """From Dict."""
        monsters = data.get('monsters') or []
        items = data.get('items') or []
        bag = cls(monsters, items)
        return bag
