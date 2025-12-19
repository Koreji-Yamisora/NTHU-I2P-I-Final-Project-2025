import pygame as pg
import json
from src.utils import GameSettings, crd, Logger
from src.utils.definition import Monster, Item
from src.sprites import Sprite, Text
from src.core.managers.resource_manager import ResourceManager
from src.data import pokedex
import random
from src.utils import color


TYPE_MAP = {
    "nor": "normal",
    "fir": "fire",
    "wat": "water",
    "ele": "electric",
    "gra": "grass",
    "ice": "ice",
    "fig": "fighting",
    "poi": "poison",
    "gro": "ground",
    "fly": "flying",
    "psy": "psychic",
    "bug": "bug",
    "roc": "rock",
    "gho": "ghost",
    "dra": "dragon",
    "dar": "dark",
    "ste": "steel",
    "fai": "fairy",
}


class Bag:
    """Bag."""

    _monsters_data: list[Monster]
    _items_data: list[Item]
    _monsters: list[dict]

    def __init__(
        self,
        monsters_data: (list[Monster] | None) = None,
        items_data: (list[Item] | None) = None,
        money: int = 3000,
    ):
        self._monsters_data = monsters_data if monsters_data else []
        self._items_data = items_data if items_data else []
        self.money = money
        self.resource_manager = ResourceManager()
        self.monster_data = []
        self.item_data = []
        self.mbgs = []
        self.mbgs = []
        self._monsters = []
        self.current_tab = "items"  # Default tab

        # Initialize internal state from data
        self.update_bag()

    @property
    def monsters(self):
        return self._monsters

    @monsters.setter
    def monsters(self, value):
        self._monsters = value

    def save_battle(self):
        """Save battle."""
        for i in range(len(self._monsters)):
            self._monsters_data[i]["hp"] = self._monsters[i]["chp"]
            for ev in self._monsters[i]["EVA"].keys():
                self._monsters_data[i]["EV"][ev] += self._monsters[i]["EVA"][ev]
            self._monsters_data[i]["exp"] += self._monsters[i]["exp"]
        self.check()

    def check(self) -> None:
        # level
        for m in self._monsters_data:
            while m["exp"] >= (m["level"] + 1) ** 3:
                m["level"] += 1
            # evolve
            e = m["level"] % 15
            if e >= 13 or e <= 2:
                roll = random.randint(1, 100)
                chance = 20
                if roll <= chance:
                    self.evolve(m)

    def evolve(self, mon):
        """Perform the actual evolution data update."""
        if mon["id"] % 3 == 2:
            return
        else:
            mon["id"] += 1
            # Update name from pokedex
            from src.data import PokeDex

            if mon["id"] in PokeDex.data:
                mon["name"] = PokeDex.data[mon["id"]]["name"]

            self.my_mon()

    def lvl_to_exp_check(self):
        """Lvl To Exp Check."""
        for m in self._monsters_data:
            required_exp = m["level"] ** 3
            if m["exp"] < required_exp:
                m["exp"] = required_exp

    def get_items(self):
        """Get items."""
        item = []
        for i in range(len(self._items_data)):
            item.append(self.idx_to_item(i))
        return item

    def idx_to_item(self, idx):
        """Idx To Item."""
        from src.data.pokedex import PokeItems

        item_data = self._items_data[idx]
        item = {}

        # Get sprite_path with fallback to PokeItems metadata
        if "sprite_path" in item_data:
            item["sprite"] = item_data["sprite_path"]
        else:
            meta = PokeItems.items.get(item_data["name"])
            if meta and "sprite_path" in meta:
                item["sprite"] = meta["sprite_path"]
            else:
                item["sprite"] = "ingame_ui/ball.png"  # Safe fallback

        item["name"] = item_data["name"]
        item["count"] = item_data["count"]
        return item

    def use_item(self, item_idx, monster_idx):
        """Use item on monster."""
        from src.data.pokedex import PokeItems

        if item_idx >= len(self._items_data) or monster_idx >= len(self._monsters):
            return

        item = self._items_data[item_idx]
        monster_display = self._monsters[monster_idx]
        monster_data = self._monsters_data[monster_display["idx"]]

        # Look up effects
        meta = PokeItems.items.get(item["name"])
        if not meta:
            return

        # Basic consumability check
        if item["count"] <= 0:
            return

        used = False

        # Healing
        if "healing" in meta:
            is_revive = meta.get("revive", False)
            current_hp = monster_data["hp"]
            max_hp = monster_display["hp"]

            if is_revive:
                if current_hp == 0:  # Is dead
                    heal = meta["healing"]
                    monster_data["hp"] = min(max_hp, heal)
                    used = True
            else:
                if current_hp > 0 and current_hp < max_hp:
                    monster_data["hp"] += meta["healing"]
                    if monster_data["hp"] > max_hp:
                        monster_data["hp"] = max_hp
                    used = True

        # Stat Boosts (EV)
        if "stat_boost" in meta:
            stat = meta["stat_boost"]
            amount = meta.get("boost_amount", 1)
            if "EV" in monster_data:
                if monster_data["EV"][stat] < 252:
                    monster_data["EV"][stat] = min(
                        252, monster_data["EV"][stat] + amount
                    )
                    used = True

        # Evolution Stone
        if meta.get("is_evolution_stone"):
            # Check if evolvable
            from src.data import PokeDex

            pid = monster_data["id"]
            evo_data = PokeDex.data.get(pid, {}).get("evolution")

            if (
                evo_data
                and evo_data.get("stone")
                and monster_data["level"] >= evo_data.get("level", 0)
            ):
                # Close inventory and trigger evolution overlay
                from src.core.services import scene_manager
                from src.scenes.game_scene import GameScene

                scene = scene_manager.get_current_scene()
                if isinstance(scene, GameScene):
                    scene.inventory.close()  # Close bag

                    # Define callback for when animation finishes
                    def on_evolve_finish():
                        self.evolve(monster_data)
                        self.remove_item(item["name"], 1)  # Consume item here
                        Logger.info(
                            f"Evolution from stone completed for {monster_display['name']}"
                        )

                    scene.evolution_overlay.setup(monster_data, on_evolve_finish)
                    used = False  # Consumption handled by callback
            else:
                if not evo_data or not evo_data.get("stone"):
                    Logger.info("This Pokemon cannot evolve with a stone.")
                else:
                    Logger.info(
                        f"Level too low! Needs level {evo_data.get('level')} to evolve."
                    )

        if used:
            item["count"] -= 1
            self.update_bag()
            Logger.info(f"Used {item['name']} on {monster_display['name']}")

    def add_item(self, item):
        """Add Item."""
        # Normalize count to integer (shop items use [current, max] format)
        add_count = item.get("count", 1)
        if isinstance(add_count, list):
            add_count = 1  # Adding 1 item from shop

        if item["name"] not in [i["name"] for i in self._items_data]:
            # Create new item entry with integer count
            new_item = {"name": item["name"], "count": add_count}
            if "sprite_path" in item:
                new_item["sprite_path"] = item["sprite_path"]
            self._items_data.append(new_item)
        else:
            for i in range(len(self._items_data)):
                if self._items_data[i]["name"] == item["name"]:
                    self._items_data[i]["count"] += add_count
                    break

    def add_monster_col(self, col_rect: pg.Rect):
        """Add Monster Col."""
        self.monster_col_rect = col_rect
        self.mon_slot_height = self.monster_col_rect.height // 6
        self.mon_slots = []
        for idx in range(6):
            mbg = Sprite(
                "UI/raw/UI_Flat_Frame03a.png",
                (self.monster_col_rect.width, self.mon_slot_height),
                nine_grid_margins=(45, 45, 45, 45),
            )
            mbg.image = color.recol(mbg.image, (120, 120, 120))
            self.mon_slots.append(
                pg.Rect(
                    self.monster_col_rect.left,
                    self.monster_col_rect.top + self.mon_slot_height * idx,
                    self.monster_col_rect.width,
                    crd(self.mon_slot_height).per(90),
                )
            )
            mbg.rect = self.mon_slots[idx]
            self.mbgs.append(mbg)
        self.monster_slot()

    def my_mon(self):
        """My Mon."""
        stat = "atk", "def", "spa", "spd", "spe"
        mod = 1
        self._monsters = []
        for i, mon in enumerate(self._monsters_data):
            if i == 6:
                break
            base = pokedex.data[mon["id"]]
            hp = (
                int(
                    (2 * base["hp"] + mon["IV"]["hp"] + mon["EV"]["hp"] / 4)
                    * mon["level"]
                    / 100
                )
                + mon["level"]
                + 10
            )
            stats = []
            for s in stat:
                stats.append(
                    (
                        int(
                            (2 * base[s] + mon["IV"][s] + mon["EV"][s] / 4)
                            * mon["level"]
                            / 100
                        )
                        + 5
                    )
                    * mod
                )
            atk, defen, spa, spd, spe = stats
            self._monsters.append(
                {
                    "idx": i,
                    "id": mon["id"],
                    "name": mon["name"],
                    "level": mon["level"],
                    "exp": 0,  # Battle experience to add
                    "chp": mon["hp"],
                    "hp": hp,
                    "atk": atk,
                    "def": defen,
                    "spa": spa,
                    "spd": spd,
                    "spe": spe,
                    "type": base["type"],
                    "move": mon["move"],
                    "IV": mon["IV"],
                    "EV": mon["EV"],  # Permanent EV values (for reference)
                    "EVA": {
                        "hp": 0,
                        "atk": 0,
                        "def": 0,
                        "spa": 0,
                        "spd": 0,
                        "spe": 0,
                    },  # EV Add (battle accumulator)
                }
            )

    def monster_slot(self):
        """Monster Slot."""
        self.monster_data.clear()
        self.monster_data.clear()
        if not hasattr(self, "mon_slot_height") or not hasattr(self, "mon_slots"):
            return

        for idx, monster in enumerate(self._monsters):
            # Icon BG
            icon_bg_size = int(self.mon_slot_height * 0.8)
            icon_bg = Sprite(
                "UI/raw/UI_Flat_Frame01a.png",
                (icon_bg_size, icon_bg_size),
                nine_grid_margins=(45, 45, 45, 45),
            )
            icon_bg.image = color.recol(icon_bg.image, (60, 60, 60))
            icon_bg.rect.left = self.mon_slots[idx].left + crd(
                self.mon_slots[idx].width
            ).per(2)
            icon_bg.rect.centery = self.mon_slots[idx].centery

            sprite = Sprite(pokedex.data[monster["id"]]["sprite_path"], (72, 72))
            sprite.rect.center = icon_bg.rect.center

            name = Text(monster["name"], 24, "azure")
            name.rect.topleft = (
                icon_bg.rect.right + crd(self.mon_slots[idx].width).per(2),
                self.mon_slots[idx].top + crd(self.mon_slot_height).per(5),
            )

            # Type Icons
            types = monster.get("type", [])
            type_sprites = []
            start_x = name.rect.right + 10
            for t_abbr in types:
                if not t_abbr:
                    continue
                t_name = TYPE_MAP.get(t_abbr)
                if t_name:
                    ts = Sprite(f"type/{t_name}.png", (24, 24))
                    ts.rect.midleft = (start_x, name.rect.centery)
                    start_x += 25
                    type_sprites.append(ts)

            hp = Text(f"HP: {monster['chp']}/{monster['hp']}", 24, "azure")
            hp = Text(f"HP: {monster['chp']}/{monster['hp']}", 24, "azure")
            hp.rect.topleft = (
                icon_bg.rect.right + crd(self.mon_slots[idx].width).per(2),
                self.mon_slots[idx].top + crd(self.mon_slot_height).per(35),
            )
            level = Text("Level: " + str(monster["level"]), 24, "azure")
            level.rect.topleft = (
                icon_bg.rect.right + crd(self.mon_slots[idx].width).per(2),
                self.mon_slots[idx].top + crd(self.mon_slot_height).per(65),
            )
            self.monster_data.append((sprite, name, hp, level, type_sprites, icon_bg))

    def add_item_col(self, col_rect: pg.Rect):
        """Add Item Col."""
        self.item_col_rect = col_rect
        self.item_slot_height = self.item_col_rect.height // 8
        self.item_slots = [
            pg.Rect(
                self.item_col_rect.left,
                self.item_col_rect.top + self.item_slot_height * idx,
                self.item_col_rect.width,
                self.item_slot_height,
            )
            for idx in range(8)
        ]
        self.item_slot()

    def item_slot(self):
        """Item Slot."""
        if not hasattr(self, "item_slots"):
            return

        from src.data.pokedex import PokeItems

        self.item_data.clear()
        for idx, item in enumerate(self._items_data):
            if idx < 8:
                if "sprite_path" not in item:
                    meta = PokeItems.items.get(item["name"])
                    if meta:
                        item["sprite_path"] = meta.get("sprite_path")
                    else:
                        item["sprite_path"] = "ingame_ui/ball.png"  # Safe fallback

                sprite = Sprite(item["sprite_path"], (64, 64))
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
        """Update."""
        pass

    def update_bag(self):
        """Update bag."""
        self.lvl_to_exp_check()
        self.my_mon()
        self.monster_slot()
        self.item_slot()

    def draw(self, screen: pg.Surface):
        """Draw."""
        self.draw_monsters(screen)
        self.draw_items(screen)

    def draw_monsters(self, screen):
        """Draw only monster column."""
        for bg in self.mbgs:
            bg.draw(screen)
        for mon in self.monster_data:
            sprite, name, hp, level, type_sprites, icon_bg = mon
            icon_bg.draw(screen)
            sprite.draw(screen)
            name.draw(screen)
            hp.draw(screen)
            level.draw(screen)
            for ts in type_sprites:
                ts.draw(screen)

    def draw_items(self, screen):
        """Draw only item column."""
        for item in self.item_data:
            for i in item:
                i.draw(screen)

    def remove_item(self, item_name, count=1):
        """Remove item."""
        for i in range(len(self._items_data)):
            if self._items_data[i]["name"] == item_name:
                self._items_data[i]["count"] -= count
                if self._items_data[i]["count"] <= 0:
                    self._items_data.pop(i)
                break

    def remove_monster(self, idx):
        """Remove monster by index (corresponding to _monsters list)."""
        if 0 <= idx < len(self._monsters):
            # _monsters contains 'idx' which points to the real index in _monsters_data
            real_idx = self._monsters[idx]["idx"]
            if 0 <= real_idx < len(self._monsters_data):
                self._monsters_data.pop(real_idx)
                # Rebuild monsters list to reflect changes
                self.my_mon()

    def to_dict(self) -> dict[str, object]:
        """To Dict."""
        return {
            "monsters": list(self._monsters_data),
            "items": list(self._items_data),
            "money": self.money,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Bag":
        """From Dict."""
        _monsters = data.get("monsters") or []
        items = data.get("items") or []
        money = data.get("money", 3000)
        bag = cls(_monsters, items, money)
        return bag
