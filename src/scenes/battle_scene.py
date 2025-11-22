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
from src.utils import crd, Logger, color
from src.interface import overlay_battle as ob
import importlib
from src.data import poketype, pokedex
import random

from dataclasses import dataclass


class BattleScene(Scene):
    background: BackgroundSprite
    monster1: dict
    monster2: dict
    bg: Sprite

    def __init__(self):
        super().__init__()
        self.exit_cd = 0.0
        self.fainted = False

        self.win = False
        self.lose = False
        self.swapping = False
        self.background = BackgroundSprite("backgrounds/background2.png")
        self.cd = 0.0
        self.noti_cd = 0.6
        self.ntcon = False
        self.move = None
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        self.bg2 = Sprite("UI/raw/UI_Flat_Frame01a.png", (sw, sh.per(20)))
        self.bg2.rect.bottom = sh
        self.bg2.image = color.recol(self.bg2.image, (90, 90, 90))
        self.bg3 = Sprite("UI/raw/UI_Flat_Frame01a.png", (sw.per(55), sh.per(15)))
        self.bg3.rect.bottomleft = (sh.per(3), sh - sh.per(3))
        self.bg3.image = color.recol(self.bg3.image, (255, 255, 255))

        self.bg = Sprite("UI/raw/UI_Flat_Frame03a.png", (sw.per(40), sh.per(15)))
        self.bg.rect.bottomright = (sw - sh.per(3), sh - sh.per(3))
        self._init()

    def _init(self):
        self.item_overlay = ob.ItemOverlay()
        self.action_overlay = ob.ActionOverlay()
        self.move_overlay = ob.MoveOverlay()
        self.health_overlay = ob.HealthOverlay()
        self.victory = ob.Victory()

    def load_data(self):
        if not gh.gm:
            gh.load()
        elif not gh.gm.current_fight:
            self.exit()
        else:
            self._init()

            self.current = 4
            self.enemy = 0
            self.action_overlay.is_active = True
            self.action_overlay.is_passive = True

            self.player_turn = True
            self.waiting_for_action = True
            Logger.debug("BattleScene.load_data()")
            self.clear()
            self.monster1: dict = gh.gm.bag.monsters[self.current]
            self.monster2: dict = gh.gm.current_fight.monsters[self.enemy]
            self.img()

            self.items = gh.gm.bag.get_items()
            self.turn = True
            self.move_overlay.inmove(self.monster1["move"])
            self.health_overlay.load()
            sh = crd(GameSettings.SCREEN_HEIGHT)
            self.noti = Text(f"What will {self.monster1['name']} do?", 32, "Black")
            self.noti.rect.topleft = (
                self.bg3.rect.left + sh.per(3),
                self.bg3.rect.top + sh.per(2),
            )

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

    def notichange(self, text: str | list[str]):
        def _cooldown(text: list[str]):
            for t in text:
                yield t

        if isinstance(text, str):
            self.noti.change_text(text)
        else:
            self.run = _cooldown(text)
            self.ntcon = True

    def text_update(self, dt):
        self.noti_cd -= dt
        if self.ntcon:
            if self.noti_cd <= 0:
                self.noti_cd = 1
                try:
                    self.notichange(next(self.run))
                except StopIteration:
                    self.ntcon = False

    def save(self):
        if gh.gm:
            gh.gm.bag.monsters[self.current] = self.monster1

    def switch(self, n: int):
        self.save()
        self.current = n
        self.load_data()

    def switch_enemy(self, n: int):
        """Switch to a new enemy monster"""
        Logger.debug(f"Switching to enemy monster {n}")
        self.enemy = n
        self.monster2 = gh.gm.current_fight.monsters[n]

        # Reload the health overlay with new monster data
        self.health_overlay.load()

        # Update the enemy sprite if needed
        self.img()

        # Update notification
        self.notichange(f"Enemy sent out {self.monster2['name']}!")

    def attack(self, attacker, defender, move):
        """Calculate damage from attacker to defender using the given move"""
        dmg = 0

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

        if move["cat"] == "Normal Attack":
            dmg = (
                (2 * (attacker["level"] / 5) + 2)
                * move["power"]
                * (attacker["atk"] / defender["def"])
                / 50
                + 2
            ) * vai
            Logger.debug(f"{attacker['name']} dealt {dmg} damage to {defender['name']}")

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
        """Execute the attack based on whose turn it is"""
        self.health_overlay.health_ratio()

        if self.player_turn:
            # Player attacks enemy
            damage = self.attack(
                self.monster1, self.monster2, self.monster1["move"][self.move]
            )
            self.monster2["chp"] -= damage

            if self.monster2["chp"] <= 0:
                self.monster2["chp"] = 0
                self.health_overlay.health_update()
                self.enemy_fainted()
        else:
            enemy_move_index = 0
            Logger.debug(f"Enemy move: {self.monster2}")
            damage = self.attack(
                self.monster2, self.monster1, self.monster2["move"][enemy_move_index]
            )
            self.monster1["chp"] -= damage

            if self.monster1["chp"] <= 0:
                self.monster1["chp"] = 0

            self.health_overlay.health_update()

    def enemy_fainted(self):
        self.notichange(f"{self.monster2['name']} fainted!")

        enemy_monsters = gh.gm.current_fight.monsters

        self.fainted = True
        # Find next alive enemy monster
        self.next_enemy = None
        for i, mon in enumerate(enemy_monsters):
            if mon["chp"] > 0:  # Changed from == 0 to > 0
                next_enemy = i
                break

    def try_switching(self, dt):
        if not self.health_overlay.animating and self.fainted:
            if self.next_enemy is not None:
                # Switch to next enemy
                Logger.debug(f"Switching to next enemy: {self.next_enemy}")
                self.switch_enemy(self.next_enemy)
                self.player_turn = True
                self.waiting_for_action = True
            else:
                # All enemies defeated - Victory!
                self.win = True
                self.victory.open()
                Logger.debug("Victory!")
            self.fainted = False

    def wait_exit(self, dt):
        self.exit_cd += dt
        if self.exit_cd >= 3 and (self.win or self.lose):
            self.win = self.lose = False
            self.exit_cd = 0
            scene_manager.change_scene("game")

    @override
    def update(self, dt: float) -> None:
        self.try_switching(dt)
        if self.win or self.lose:
            if not self.health_overlay.animating:
                self.wait_exit(dt)
        else:
            if self.player_turn and not self.health_overlay.animating:
                if self.waiting_for_action:
                    self.action_overlay.open()
                    if self.action_overlay.is_move:
                        self.action_overlay.close()
                        self.move_overlay.open()
                        self.move_overlay.update(dt)

                        if self.move_overlay.selected:
                            self.waiting_for_action = False
                            self.doing_damage()
                            self.move_overlay.selected = False

                    elif self.action_overlay.is_item:
                        self.action_overlay.close()
                        self.item_overlay.open()
                        self.item_overlay.update(dt)
                    else:
                        self.action_overlay.open()
                        self.action_overlay.update(dt)
                else:
                    self.action_overlay.close()
                    self.move_overlay.close()
                    self.item_overlay.close()
                    self.player_turn = False
            elif not self.player_turn and not self.health_overlay.animating:
                self.cd += dt
                self.action_overlay.close()
                self.action_overlay.is_move = False
                self.action_overlay.is_item = False
                self.move_overlay.close()
                self.item_overlay.close()
                if self.cd >= 2:
                    self.doing_damage()
                    self.waiting_for_action = True
                    self.player_turn = True
                    self.cd = 0

        self.health_overlay.update(dt)
        self.text_update(dt)

    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)
        self.bg2.draw(screen)
        self.bg3.draw(screen)
        self.bg.draw(screen)
        self.m1_sprite.draw(screen)
        self.m2_sprite.draw(screen)
        self.action_overlay.draw(screen)
        self.health_overlay.draw(screen)
        self.noti.draw(screen)
        self.move_overlay.draw(screen)
        self.item_overlay.draw(screen)
        self.victory.draw(screen)


class TrainerAI:
    def __init__(self):
        pass
