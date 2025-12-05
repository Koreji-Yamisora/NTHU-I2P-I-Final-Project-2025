from enum import FlagBoundary
import pygame as pg
from src import data
from src.utils import GameSettings
from src.sprites import Sprite, Text, BackgroundSprite
from src.scenes.combat import CombatScene
from src.interface.components import Button
from src.core.services import scene_manager, sound_manager, input_manager, resource_manager
from typing import override
from src.interface.components import Overlay
from src.core.managers import GameManager
from src.core import gh
from src.utils import crd, Logger, color
from src.interface import overlay_encounter as oe
import importlib
from src.data import poketype, pokedex
import random
from dataclasses import dataclass


class EncounterScene(CombatScene):
    """Encounter  scene."""
    background: BackgroundSprite
    monster1: dict
    monster2: dict
    bg: Sprite

    def __init__(self):
        super().__init__()
        self.exit_cd = 0.0
        self.pfainted = False
        self.efainted = False
        self.catching = False
        self.done = False
        self.win = False
        self.lose = False
        self.swapping = False
        self.background = BackgroundSprite('backgrounds/background2.png')
        self.cd = 0.0
        self.noti_cd = 0.6
        self.ntcon = False
        self.move = None
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)
        self.bg2 = Sprite('UI/raw/UI_Flat_Frame01a.png', (sw, sh.per(20)))
        self.bg2.rect.bottom = sh
        self.bg2.image = color.recol(self.bg2.image, (90, 90, 90))
        self.bg3 = Sprite('UI/raw/UI_Flat_Frame01a.png', (sw.per(55), sh.
            per(15)))
        self.bg3.rect.bottomleft = sh.per(3), sh - sh.per(3)
        self.bg3.image = color.recol(self.bg3.image, (255, 255, 255))
        self.bg = Sprite('UI/raw/UI_Flat_Frame03a.png', (sw.per(40), sh.per
            (15)))
        self.bg.rect.bottomright = sw - sh.per(3), sh - sh.per(3)
        self.victory = None
        self._init()

    def _init(self):
        self.item_overlay = oe.ItemOverlay()
        self.action_overlay = oe.ActionOverlay()
        self.health_overlay = oe.HealthOverlay()
        self.switch_UI = oe.SwitchOverlay()
        self.move_refresh()

    def move_refresh(self):
        """Move Refresh."""
        self.move_overlay = oe.MoveOverlay()

    def load_data(self):
        """Load data."""
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
            self.next = None
            self.player_turn = True
            self.waiting_for_action = True
            self.clear()
            self.monster1: dict = gh.gm.bag.monsters[self.current]
            Logger.debug(f'{gh.gm.current_fight.monsters}')
            self.monster2: dict = gh.gm.current_fight.monsters[self.enemy]
            self.img()
            self.items = gh.gm.bag.get_items()
            self.turn = True
            self.move_overlay.inmove(self.monster1['move'])
            self.health_overlay.load()
            sh = crd(GameSettings.SCREEN_HEIGHT)
            self.noti = Text(f"What will {self.monster1['name']} do?", 32,
                'Black')
            self.noti.rect.topleft = self.bg3.rect.left + sh.per(3
                ), self.bg3.rect.top + sh.per(2)
            self.item_overlay.init()
            self.switch_UI.init()
            self.move_refresh()
            self.move_overlay.inmove(self.monster1['move'])
            self.player_action = None
            self.enemy_action = None
            self.turn_queue = []
            self.executing_turn = False
            self.turn_timer = 0.0

    def img(self):
        """Img."""
        wid, hid = crd(GameSettings.SCREEN_WIDTH), crd(GameSettings.
            SCREEN_HEIGHT)
        self.m1_sprite = Sprite(pokedex.data[self.monster1['id']][
            'fight_path'], (wid, hid))
        w, h = self.m1_sprite.image.get_size()
        new = w // 2
        frame = self.m1_sprite.image.subsurface(pg.Rect(new, 0, new, h))
        self.m1_sprite.image = frame
        self.m1_sprite.rect.bottom = hid - hid.per(20)
        self.m2_sprite = Sprite(pokedex.data[self.monster2['id']][
            'fight_path'], (wid // 2, hid // 2))
        w, h = self.m2_sprite.image.get_size()
        new = w // 2
        frame = self.m2_sprite.image.subsurface(pg.Rect(0, 0, new, h))
        self.m2_sprite.image = frame
        self.m2_sprite.rect.centerx = wid

    def clear(self):
        """Clear."""
        self.monster1 = {}
        self.monster2 = {}
        self.items = []

    @override
    def enter(self) ->None:
        """Enter."""
        sound_manager.play_bgm('RBY 101 Opening (Part 1).ogg')
        self.clear()
        self.load_data()
        self.action_overlay.open()

    @override
    def exit(self) ->None:
        """Exit."""
        self.save()
        self.clear()

    def notichange(self, text: (str | list[str])):
        """Notichange."""

        def _cooldown(text: list[str]):
            for t in text:
                yield t
        if isinstance(text, str):
            self.noti.change_text(text)
        else:
            self.run = _cooldown(text)
            self.ntcon = True

    def text_update(self, dt):
        """Text Update."""
        self.noti_cd -= dt
        if self.ntcon:
            if self.noti_cd <= 0:
                self.noti_cd = 1
                try:
                    self.notichange(next(self.run))
                except StopIteration:
                    self.ntcon = False

    def save(self):
        """Save."""
        gh.gm.bag.monsters[self.current] = self.monster1
        gh.gm.bag.save_battle(gh.gm.bag.monsters)
        gh.gm.bag.update_bag()

    def switch_mon(self, idx):
        """Switch Mon."""
        self.save()
        for i, mon in enumerate(gh.gm.bag.monsters):
            if mon['idx'] == idx:
                self.current = i
                self.monster1 = mon
                break
        self.health_overlay.load()
        self.move_refresh()
        self.move_overlay.inmove(self.monster1['move'])
        self.img()
        self.notichange(f"You sent out {self.monster1['name']}!")

    def switch_enemy(self, n: int):
        """Switch to a new enemy monster"""
        Logger.debug(f'Switching to enemy monster {n}')
        self.enemy = n
        self.monster2 = gh.gm.current_fight.monsters[n]
        self.health_overlay.load()
        self.img()
        self.notichange(f"Enemy sent out {self.monster2['name']}!")

    def resolve_turn(self):
        """Calculate turn order and prepare execution queue"""
        actions = []
        if self.player_action:
            p_act = self.player_action
            if p_act['type'] == 'move':
                actions.append((0, self.monster1['spe'], self.monster1,
                    self.monster2, p_act['value'], True))
            else:
                actions.append((1, 999, self.monster1, self.monster2, p_act,
                    True))
        enemy_move = random.choice(self.monster2['move'])
        actions.append((0, self.monster2['spe'], self.monster2, self.
            monster1, enemy_move, False))
        actions.sort(key=lambda x: (x[0], x[1]), reverse=True)
        self.turn_queue = actions
        self.executing_turn = True
        self.turn_timer = 0.0
        self.current_action_idx = 0

    def execute_next_action(self):
        """Execute Next Action."""
        if self.current_action_idx >= len(self.turn_queue):
            self.executing_turn = False
            self.player_action = None
            self.waiting_for_action = True
            self.player_turn = True
            return
        priority, speed, attacker, defender, action, is_player = (self.
            turn_queue[self.current_action_idx])
        self.current_action_idx += 1
        if attacker['chp'] <= 0:
            Logger.debug(f"{attacker['name']} is fainted and cannot move.")
            return
        is_non_move_action = is_player and isinstance(action, dict
            ) and 'type' in action and action['type'] in ['switch', 'item',
            'catch', 'run']
        if is_non_move_action:
            if action['type'] == 'switch':
                self.switch_mon(action['value'])
            elif action['type'] == 'item':
                item = action['value']
                if item:
                    self.use_potion(self.monster1, item)
            elif action['type'] == 'catch':
                self.do_catching()
            elif action['type'] == 'run':
                self.run_attempt()
        else:
            self.notichange([f"{attacker['name']} used {action['name']}!", ''])
            damage = self.attack(attacker, defender, action)
            Logger.debug(
                f"Damage calculated: {damage}. Defender HP before: {defender['chp']}. Attacker: {attacker['name']}, Defender: {defender['name']}"
                )
            defender['chp'] -= damage
            if defender['chp'] < 0:
                defender['chp'] = 0
            Logger.debug(f"Defender HP after: {defender['chp']}")
            self.health_overlay.health_update()
            if defender['chp'] <= 0:
                if is_player:
                    self.enemy_fainted()
                else:
                    self.fainted()
        self.save()

    def run_attempt(self):
        """Run Attempt."""
        if 95 > random.randint(0, 100):
            scene_manager.change_scene('game')
        else:
            self.notichange('You fail to run away.')

    def doing_damage(self):
        """Doing Damage."""
        pass

    def check_health(self):
        """Check Health."""
        h = False
        monster = gh.gm.bag.monsters
        for i, mon in enumerate(monster):
            if mon['chp'] > 0:
                h = True
                break
        return h

    def enemy_fainted(self):
        """Enemy Fainted."""
        self.notichange(f"{self.monster2['name']} fainted!")
        enemy_monsters = gh.gm.current_fight.monsters
        self.efainted = True
        self.next_enemy = None
        for i, mon in enumerate(enemy_monsters):
            if mon['chp'] > 0:
                Logger.debug(f'Next enemy: {mon}')
                self.next_enemy = i
                break

    def try_team(self, dt):
        """Try Team."""
        if not self.health_overlay.animating:
            if self.check_health():
                if self.switch_UI.next is not None:
                    Logger.debug(
                        f'Switching to next pokemon: {self.switch_UI.next}')
                    self.switch_mon(self.switch_UI.next)
                    self.player_turn = False
                    self.waiting_for_action = False
                    self.switch_UI.next = None
                    self.pfainted = False
                    self.switch_UI.close()
            else:
                self.lose = True
                self.victory = ob.Victory(0)
                Logger.debug('Loses')
                self.pfainted = False

    def fainted(self):
        """Fainted."""
        self.pfainted = True
        self.switch_UI.forced = True
        self.switch_UI.init(forced=True)
        self.switch_UI.open()

    def try_switching(self, dt):
        """Try Switching."""
        if not self.health_overlay.animating and self.efainted:
            if self.next_enemy is not None:
                Logger.debug(f'Switching to next enemy: {self.next_enemy}')
                self.switch_enemy(self.next_enemy)
                self.player_turn = True
                self.waiting_for_action = True
            else:
                self.win = True
                self.victory = oe.Victory(1)
                Logger.debug('Victory!')
            self.efainted = False

    def wait_exit(self, dt):
        """Wait Exit."""
        self.exit_cd += dt
        self.action_overlay.close()
        self.move_overlay.close()
        self.item_overlay.close()
        self.switch_UI.close()
        if self.exit_cd >= 3 and (self.win or self.lose or self.done):
            self.win = self.lose = self.done = False
            self.exit_cd = 0
            scene_manager.change_scene('game')

    def do_catching(self):
        """Do Catching."""
        chance = 85
        c = random.randint(0, 100)
        if c < chance:
            self.notichange(['Catching...', 'Catched Succesfully'])
            self.catched()
        else:
            self.notichange(['Catching...', 'Fail to catch'])
            self.catching = False

    def catched(self):
        """Catched."""
        bag = getattr(gh, 'gm').bag._monsters_data
        m = self.monster2
        pokemon = {'id': m['id'], 'name': m['name'], 'level': m['level'],
            'hp': m['chp'], 'IV': m['IV'], 'EV': m['EV'], 'move': m['move']}
        bag.append(pokemon)
        Logger.debug(f'monster : {bag[-1]}')
        self.done = True
        self.catching = False

    @override
    def update(self, dt: float) ->None:
        """Update."""
        self.save()
        self.try_switching(dt)
        self.try_team(dt)
        if self.win or self.lose or self.done:
            if not self.health_overlay.animating:
                self.wait_exit(dt)
        elif self.pfainted:
            self.switch_UI.forced = True
            self.switch_UI.update(dt)
            if self.switch_UI.selected:
                self.switch_UI.selected = False
        elif self.executing_turn:
            self.action_overlay.close()
            self.move_overlay.close()
            self.item_overlay.close()
            self.switch_UI.close()
            if not self.ntcon and not self.health_overlay.animating:
                self.turn_timer += dt
                if self.turn_timer > 1.0:
                    self.execute_next_action()
                    self.turn_timer = 0.0
        elif self.player_turn and not self.health_overlay.animating:
            if self.waiting_for_action:
                self.move_overlay.close()
                self.item_overlay.close()
                self.switch_UI.close()
                self.action_overlay.open()
                if self.action_overlay.is_move:
                    self.action_overlay.close()
                    self.move_overlay.open()
                    self.move_overlay.update(dt)
                    if self.move_overlay.selected:
                        Logger.debug(
                            f'Move selected in Scene. Move index: {self.move}')
                        self.player_action = {'type': 'move', 'value': self
                            .monster1['move'][self.move]}
                        self.waiting_for_action = False
                        self.move_overlay.selected = False
                        self.action_overlay.is_move = False
                        self.resolve_turn()
                self.switch_UI.forced = False
                if self.action_overlay.is_switch:
                    self.switch_UI.open()
                    self.action_overlay.close()
                    self.switch_UI.update(dt)
                    if self.switch_UI.selected:
                        self.player_action = {'type': 'switch', 'value':
                            self.switch_UI.next}
                        self.waiting_for_action = False
                        self.switch_UI.selected = False
                        self.switch_UI.close()
                        self.action_overlay.is_switch = False
                        self.resolve_turn()
                elif self.action_overlay.is_item:
                    self.action_overlay.close()
                    self.item_overlay.open()
                    self.item_overlay.update(dt)
                    if self.item_overlay.selected:
                        selected_item = self.item_overlay.selected_item
                        if self.catching:
                            action_type = 'catch'
                        elif selected_item and 'healing' in selected_item:
                            action_type = 'item'
                        else:
                            action_type = 'item'
                        self.player_action = {'type': action_type, 'value':
                            selected_item}
                        self.waiting_for_action = False
                        self.item_overlay.selected = False
                        self.action_overlay.is_item = False
                        self.resolve_turn()
                elif self.action_overlay.is_run:
                    self.player_action = {'type': 'run', 'value': None}
                    self.waiting_for_action = False
                    self.action_overlay.is_run = False
                    self.resolve_turn()
                else:
                    self.action_overlay.open()
                    self.action_overlay.update(dt)
        self.health_overlay.update(dt)
        self.text_update(dt)

    @override
    def draw(self, screen: pg.Surface) ->None:
        """Draw."""
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
        self.switch_UI.draw(screen)
        if self.victory:
            self.victory.draw(screen)


class TrainerAI:
    """Trainer A I."""

    def __init__(self):
        pass
