from enum import FlagBoundary
import pygame as pg

from src import data
from src.utils import GameSettings
from src.sprites import Sprite, Text, BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.core.services import (
    scene_manager,
    sound_manager,
    input_manager,
    resource_manager,
)
from typing import override

from src.interface.components import Overlay
from src.core.managers import GameManager
from src.core import gh
from src.utils import crd, Logger
from src.interface import overlay_battle as ob
import importlib
from src.data import poketype, pokedex
import random

from dataclasses import dataclass


class BattleScene(Scene):
    background: BackgroundSprite
    monster1: dict
    monster2: dict

    def __init__(self):
        super().__init__()
        self.background = BackgroundSprite("backgrounds/background2.png")
        self._init()
        self.cd = 5

    def _init(self):
        self.item_overlay = ob.ItemOverlay()
        self.action_overlay = ob.ActionOverlay()
        self.move_overlay = ob.MoveOverlay()
        self.health_overlay = ob.HealthOverlay()
        self.pair = [4, 1]
        self.action_overlay.is_active = True
        self.action_overlay.is_passive = True

    def load_data(self):
        if not gh.gm:
            gh.load()
        else:
            self.clear()
            self.monster1: dict = gh.gm.bag.monsters[self.pair[0]]
            self.monster2: dict = gh.gm.bag.monsters[self.pair[1]]
            self.img()
            self.action_overlay.msg_srt.change_text(
                f"What will {self.monster1['name']} do?"
            )

            self.items = gh.gm.bag.get_items()
            self.turn = True
            self.move_overlay.inmove(self.monster1["move"])
            self.health_overlay.load()

    def img(self):
        wid, hid = crd(GameSettings.SCREEN_WIDTH), crd(GameSettings.SCREEN_HEIGHT)
        self.m1_sprite = Sprite("sprites/sprite1.png", (wid, hid))
        w, h = self.m1_sprite.image.get_size()
        new = w // 2
        frame = self.m1_sprite.image.subsurface(pg.Rect(new, 0, new, h))
        self.m1_sprite.image = frame
        self.m1_sprite.rect.bottom = hid - hid.per(20)
        self.m2_sprite = Sprite("sprites/sprite2.png", (wid // 2, hid // 2))
        w, h = self.m2_sprite.image.get_size()
        new = w // 2
        frame = self.m2_sprite.image.subsurface(pg.Rect(0, 0, new, h))
        self.m2_sprite.image = frame
        self.m2_sprite.rect.centerx = wid

    def clear(self):
        self.monster1 = {}
        self.monster2 = {}
        self.items = []

    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 101 Opening (Part 1).ogg")
        self.clear()
        self.load_data()
        self.action_overlay.open()

    @override
    def exit(self) -> None:
        self.save()
        self.clear()

    def save(self):
        if gh.gm:
            gh.gm.bag.monsters[self.pair[0]] = self.monster1
            gh.gm.bag.monsters[self.pair[1]] = self.monster2

    def switch(self, n: int, m: int):
        self.save()
        self.pairs = [n, m]
        self.load_data()

    def attack(self, move):
        dmg = 0

        target = 1
        weather = 1
        critical = 1
        ran = random.randint(85, 100) / 100
        acu = 1 if random.randint(0, 100) < move["acc"] else 0
        stab = 1.5 if self.monster1["type"] == move["type"] else 1
        ty: float = poketype.effective(move["type"], self.monster2["type"])
        vai = target * weather * critical * ran * stab * ty * acu

        self.move_overlay.notichange(
            [f"{self.monster1['name']} used {move['name']}!", self.eff_mes(ty, acu), ""]
        )
        if move["cat"] == "Normal Attack":
            dmg = (
                (2 * (self.monster1["level"] / 5) + 2)
                * move["power"]
                * (self.monster1["atk"] / self.monster2["def"])
                / 50
                + 2
            ) * vai
            Logger.debug("dmg: " + str(dmg))
        return int(dmg)

    def eff_mes(self, type: float, acu: int):
        if type > 1:
            return "It's super effective!"
        elif type < 1:
            return "It's not very effective..."
        elif type == 0:
            return f"It doesn't affect {self.monster2['name']}..."
        elif acu == 0:
            return "It missed..."
        else:
            return ""

    def heal_all(self):
        self.monster1["chp"] = self.monster1["hp"]
        self.monster2["chp"] = self.monster2["hp"]

    def doing_damage(self):
        Logger.debug(self.monster2["chp"])

        self.monster2["chp"] -= self.attack(
            self.monster1["move"][self.move_overlay.result()]
        )
        Logger.debug(self.monster2["chp"])

        if self.monster2["chp"] < 0:
            self.monster2["chp"] = 0
        self.health_overlay.load()

    @override
    def update(self, dt: float) -> None:
        if input_manager.key_pressed(pg.K_t) and self.cd <= 0:
            importlib.reload(ob)
            self._init()
            self.load_data()
            self.action_overlay.open()
        if input_manager.key_pressed(pg.K_h):
            self.heal_all()
            self.health_overlay.load()

            self.cd = 3
        self.cd -= dt

        if self.action_overlay.Turn:
            self.action_overlay.is_active = True
            self.action_overlay.is_passive = True

            if self.action_overlay.is_move:
                self.move_overlay.open()
                self.action_overlay.is_active = False
                self.action_overlay.is_passive = False
                if self.move_overlay.selected:
                    self.doing_damage()
                    self.move_overlay.update(dt)
                    self.move_overlay.selected = False
                else:
                    self.move_overlay.update(dt)
            elif self.action_overlay.is_item:
                self.item_overlay.open()
                self.action_overlay.is_active = False
                self.action_overlay.is_passive = True
                self.item_overlay.update(dt)
            else:
                self.move_overlay.close()
                self.item_overlay.close()
                self.action_overlay.update(dt)
        else:
            self.action_overlay.is_active = False
            self.action_overlay.is_passive = False
            self.move_overlay.close()
            self.item_overlay.close()
            self.action_overlay.update(dt)
        self.health_overlay.update(dt)

    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)
        self.m1_sprite.draw(screen)
        self.m2_sprite.draw(screen)
        self.health_overlay.draw(screen)
        self.action_overlay.draw(screen)
        self.move_overlay.draw(screen)
        self.item_overlay.draw(screen)
