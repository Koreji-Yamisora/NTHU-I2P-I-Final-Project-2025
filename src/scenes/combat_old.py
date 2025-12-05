from abc import ABC, abstractmethod
import pygame as pg
import random
from typing import override

from src.scenes.scene import Scene
from src.sprites import Sprite, Text, BackgroundSprite
from src.utils import GameSettings, crd, Logger, color
from src.core import gh
from src.data import poketype, pokedex
from src.core.services import scene_manager


class CombatScene(Scene, ABC):
    """Base class for combat scenes (encounters, battles, etc.)"""

    def __init__(self):
        super().__init__()
        # Combat state
        self.monster1: dict = {}
        self.monster2: dict = {}
        self.current: int = 0  # Player's current monster index
        self.enemy: int = 0  # Enemy's current monster index
        
        # Faint tracking
        self.pfainted = False  # Player fainted this turn
        self.efainted = False  # Enemy fainted this turn
        
        # Turn management
        self.player_turn = True
        self.waiting_for_action = True
        
        # Text notifications
        self.noti_cd = 0.6
        self.ntcon = False
        self.run = None
        
        # Items
        self.items = []

    def attack(self, attacker: dict, defender: dict, move: dict) -> int:
        """Calculate damage from attacker to defender using the given move"""
        target = 1
        weather = 1
        critical = 1
        ran = random.randint(85, 100) / 100
        acu = 1 if random.randint(0, 100) < move["acc"] else 0
        stab = 1.5 if attacker["type"] == move["type"] else 1
        ty: float = poketype.effective(move["type"], defender["type"])
        vai = target * weather * critical * ran * stab * ty * acu

        self.notichange(
            [f"{attacker['name']} used {move['name']}!", self.eff_mes(ty, acu), ""]
        )

        dmg = 0
        if move["cat"] == "Normal Attack":
            dmg = (
                (2 * (attacker["level"] / 5) + 2)
                * move["power"]
                * (attacker["atk"] / defender["def"])
                / 50
                + 2
            ) * vai
        elif move["cat"] == "Special Attack":
            dmg = (
                (2 * (attacker["level"] / 5) + 2)
                * move["power"]
                * (attacker["spa"] / defender["spd"])
                / 50
                + 2
            ) * vai

        Logger.debug(f"{attacker['name']} dealt {int(dmg)} damage to {defender['name']}")
        return int(dmg)

    def eff_mes(self, type_effectiveness: float, accuracy: int) -> str:
        """Generate effectiveness message"""
        if type_effectiveness > 1:
            return "It's super effective!"
        elif type_effectiveness < 1:
            return "It's not very effective..."
        elif type_effectiveness == 0:
            return f"It doesn't affect {self.monster2['name']}..."
        elif accuracy == 0:
            return "It missed..."
        else:
            return ""

    def use_potion(self, monster: dict, item: dict) -> bool:
        """Apply potion healing to a monster. Returns True if healing was applied."""
        if monster["chp"] >= monster["hp"]:
            self.notichange(f"{monster['name']} is already at full HP!")
            return False
        
        # Get healing amount from item
        healing = item.get("healing", 20)  # Default 20 if not specified
        
        old_hp = monster["chp"]
        monster["chp"] = min(monster["chp"] + healing, monster["hp"])
        actual_healing = monster["chp"] - old_hp
        
        self.notichange(f"{monster['name']} restored {actual_healing} HP!")
        Logger.debug(f"Potion used: {item['name']} healed {actual_healing} HP")
        
        # Update health overlay
        if hasattr(self, 'health_overlay'):
            self.health_overlay.health_update()
        
        return True

    def heal_all(self):
        """Heal both monsters to full HP"""
        self.monster1["chp"] = self.monster1["hp"]
        self.monster2["chp"] = self.monster2["hp"]

    def check_health(self) -> bool:
        """Check if player has any alive monsters"""
        if not gh.gm or not gh.gm.bag:
            return False
        
        for mon in gh.gm.bag.monsters:
            if mon["chp"] > 0:
                return True
        return False

    def save(self):
        """Save current monster state"""
        if gh.gm and gh.gm.bag and self.current < len(gh.gm.bag.monsters):
            gh.gm.bag.monsters[self.current] = self.monster1
            gh.gm.bag.save_battle(gh.gm.bag.monsters)
            gh.gm.bag.update_bag()

    def switch_mon(self, idx: int):
        """Switch player's current monster"""
        self.save()
        for i, mon in enumerate(gh.gm.bag.monsters):
            if mon["idx"] == idx:
                self.current = i
                self.monster1 = mon
                break
        
        if hasattr(self, 'health_overlay'):
            self.health_overlay.load()
        if hasattr(self, 'move_overlay'):
            self.move_overlay.inmove(self.monster1["move"])
        
        self.img()
        self.notichange(f"You sent out {self.monster1['name']}!")

    def switch_enemy(self, n: int):
        """Switch to a new enemy monster"""
        Logger.debug(f"Switching to enemy monster {n}")
        self.enemy = n
        
        if gh.gm and gh.gm.current_fight:
            self.monster2 = gh.gm.current_fight.monsters[n]
        
        if hasattr(self, 'health_overlay'):
            self.health_overlay.load()
        
        self.img()
        self.notichange(f"Enemy sent out {self.monster2['name']}!")

    def img(self):
        """Load combat sprite images"""
        wid, hid = crd(GameSettings.SCREEN_WIDTH), crd(GameSettings.SCREEN_HEIGHT)
        
        # Player sprite (right half, bottom)
        self.m1_sprite = Sprite(
            pokedex.data[self.monster1["id"]]["fight_path"], (wid, hid)
        )
        w, h = self.m1_sprite.image.get_size()
        new = w // 2
        frame = self.m1_sprite.image.subsurface(pg.Rect(new, 0, new, h))
        self.m1_sprite.image = frame
        self.m1_sprite.rect.bottom = hid - hid.per(20)
        
        # Enemy sprite (left half, centered)
        self.m2_sprite = Sprite(
            pokedex.data[self.monster2["id"]]["fight_path"], (wid // 2, hid // 2)
        )
        w, h = self.m2_sprite.image.get_size()
        new = w // 2
        frame = self.m2_sprite.image.subsurface(pg.Rect(0, 0, new, h))
        self.m2_sprite.image = frame
        self.m2_sprite.rect.centerx = wid

    def clear(self):
        """Clear monster data"""
        self.monster1 = {}
        self.monster2 = {}
        self.items = []

    def notichange(self, text: str | list[str]):
        """Update notification text (can be single string or list for animation)"""
        def _cooldown(text: list[str]):
            for t in text:
                yield t

        if isinstance(text, str):
            if hasattr(self, 'noti'):
                self.noti.change_text(text)
        else:
            self.run = _cooldown(text)
            self.ntcon = True

    def text_update(self, dt: float):
        """Handle text animation updates"""
        self.noti_cd -= dt
        if self.ntcon:
            if self.noti_cd <= 0:
                self.noti_cd = 1
                try:
                    self.notichange(next(self.run))
                except StopIteration:
                    self.ntcon = False

    @abstractmethod
    def load_data(self):
        """Load combat data - must be implemented by subclasses"""
        pass

    @abstractmethod
    def enemy_fainted(self):
        """Handle enemy fainting - must be implemented by subclasses"""
        pass

    @abstractmethod
    def fainted(self):
        """Handle player fainting - must be implemented by subclasses"""
        pass
