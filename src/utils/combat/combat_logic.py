from enum import Enum
import pygame as pg
from src.utils import GameSettings, crd, Logger, color
from src.sprites import Sprite, Text, BackgroundSprite
from src.scenes.scene import Scene
from src.interface import overlay_combat as oc
from src.core import gh
from src.data import poketype, pokedex
import random
from typing import Optional


class CombatType(Enum):
    """Combat type enumeration"""

    WILD = "wild"
    TRAINER = "trainer"
    PVP = "pvp"


class CombatLogic:
    """Base combat logic that handles damage calculation, stat stages, etc."""

    def __init__(self, m1: dict, m2: dict):
        self.m1 = m1
        self.m2 = m2
        self.rng = random.Random()  # Instance-based RNG

        # Stat stages for both Pokemon (range: -6 to +6)
        self.stat_stages = {
            "player": {"atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0},
            "enemy": {"atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0},
        }

    def set_seed(self, seed: int):
        """Set the seed for RNG to ensure deterministic results"""
        self.rng.seed(seed)
        Logger.debug(f"CombatLogic seed set to: {seed}")

    def get_stat_multiplier(self, stage: int) -> float:
        """Get the multiplier for a given stat stage (-6 to +6)"""
        multipliers = {
            -6: 0.25,
            -5: 0.28,
            -4: 0.33,
            -3: 0.4,
            -2: 0.5,
            -1: 0.66,
            0: 1.0,
            1: 1.5,
            2: 2.0,
            3: 2.5,
            4: 3.0,
            5: 3.5,
            6: 4.0,
        }
        return multipliers.get(stage, 1.0)

    def attack(
        self, attacker: dict, defender: dict, move: dict
    ) -> tuple[int, float, bool]:
        """Calculate damage from attacker to defender using the given move.

        Returns:
            tuple: (damage, type_effectiveness, hit_success)
        """
        target = 1
        weather = 1
        critical = 1
        ran = self.rng.randint(85, 100) / 100
        acu = 1 if self.rng.randint(0, 100) < move["acc"] else 0
        hit_success = acu == 1
        stab = 1.5 if move["type"] in attacker["type"] else 1
        ty: float = poketype.effective(move["type"], defender["type"])
        vai = target * weather * critical * ran * stab * ty * acu
        dmg = 0

        is_player_attacker = attacker == self.m1
        is_player_defender = defender == self.m1
        attacker_stages = self.stat_stages["player" if is_player_attacker else "enemy"]
        defender_stages = self.stat_stages["player" if is_player_defender else "enemy"]

        if move["cat"] == "Normal Attack":
            atk_multiplier = self.get_stat_multiplier(attacker_stages["atk"])
            def_multiplier = self.get_stat_multiplier(defender_stages["def"])
            dmg = (
                (2 * (attacker["level"] / 5) + 2)
                * move["power"]
                * (
                    attacker["atk"]
                    * atk_multiplier
                    / (defender["def"] * def_multiplier)
                )
                / 50
                + 2
            ) * vai
        elif move["cat"] == "Special Attack":
            spa_multiplier = self.get_stat_multiplier(attacker_stages["spa"])
            spd_multiplier = self.get_stat_multiplier(defender_stages["spd"])
            dmg = (
                (2 * (attacker["level"] / 5) + 2)
                * move["power"]
                * (
                    attacker["spa"]
                    * spa_multiplier
                    / (defender["spd"] * spd_multiplier)
                )
                / 50
                + 2
            ) * vai

        Logger.debug(
            f"DEBUG: Attack {move['name']} | Seed: {self.rng.getstate()[1][0] if hasattr(self.rng, 'getstate') else '?'}"
        )
        Logger.debug(
            f"DEBUG: Attacker {attacker['name']}: Atk={attacker.get('atk')} Def={attacker.get('def')} Lvl={attacker.get('level')}"
        )
        Logger.debug(
            f"DEBUG: Defender {defender['name']}: Atk={defender.get('atk')} Def={defender.get('def')} Lvl={defender.get('level')}"
        )
        Logger.debug(
            f"DEBUG: Modifiers: Ran={ran}, Crit={critical}, Stab={stab}, Type={ty}"
        )
        Logger.debug(
            f"{attacker['name']} dealt {int(dmg)} damage to {defender['name']} (Effectiveness: {ty}x)"
        )
        return (int(dmg), ty, hit_success)

    def estimate_damage(self, attacker: dict, defender: dict, move: dict) -> float:
        """Estimate damage for AI decision making (ignores RNG/Crit/Miss potential for simplicity)"""
        target = 1
        weather = 1
        critical = 1  # Assume no crit
        ran = 1.0  # Average random roll? Or max? Let's use max (1.0) or avg (0.925). Let's use 1.0 for "potential"
        # We can penalize low accuracy moves if we want:
        # expected_value = damage * (accuracy / 100)
        acu = move["acc"] / 100
        stab = 1.5 if move["type"] in attacker["type"] else 1
        ty: float = poketype.effective(move["type"], defender["type"])
        vai = target * weather * critical * ran * stab * ty

        # Stat calculation
        is_player_attacker = attacker == self.m1
        is_player_defender = defender == self.m1
        attacker_stages = self.stat_stages["player" if is_player_attacker else "enemy"]
        defender_stages = self.stat_stages["player" if is_player_defender else "enemy"]

        dmg = 0
        if move["cat"] == "Normal Attack":
            atk_multiplier = self.get_stat_multiplier(attacker_stages["atk"])
            def_multiplier = self.get_stat_multiplier(defender_stages["def"])
            dmg = (
                (2 * (attacker["level"] / 5) + 2)
                * move["power"]
                * (
                    attacker["atk"]
                    * atk_multiplier
                    / (defender["def"] * def_multiplier)
                )
                / 50
                + 2
            ) * vai
        elif move["cat"] == "Special Attack":
            spa_multiplier = self.get_stat_multiplier(attacker_stages["spa"])
            spd_multiplier = self.get_stat_multiplier(defender_stages["spd"])
            dmg = (
                (2 * (attacker["level"] / 5) + 2)
                * move["power"]
                * (
                    attacker["spa"]
                    * spa_multiplier
                    / (defender["spd"] * spd_multiplier)
                )
                / 50
                + 2
            ) * vai

        return dmg * acu  # Return expected value

    def eff_mes(self, type_effectiveness: float, accuracy: int) -> str:
        """Generate effectiveness message"""
        if type_effectiveness > 1:
            return "It's super effective!"
        elif type_effectiveness < 1:
            return "It's not very effective..."
        elif type_effectiveness == 0:
            return "It doesn't affect the target..."
        elif accuracy == 0:
            return "It missed..."
        else:
            return ""

    def use_potion(self, monster: dict, item: dict) -> tuple[bool, str]:
        """Apply potion healing to a monster. Returns (success, message)."""
        if monster["chp"] >= monster["hp"]:
            return False, f"{monster['name']} is already at full HP!"

        healing = item.get("healing", 20)
        old_hp = monster["chp"]
        monster["chp"] = min(monster["chp"] + healing, monster["hp"])
        actual_healing = monster["chp"] - old_hp

        Logger.debug(f"Potion used: {item['name']} healed {actual_healing} HP")
        return True, f"{monster['name']} restored {actual_healing} HP!"

    def use_stat_boost(
        self, monster: dict, item: dict, is_player: bool
    ) -> tuple[bool, str]:
        """Apply stat boost to a monster. Returns (success, message)."""
        stat = item.get("stat_boost")
        boost_amount = item.get("boost_amount", 1)

        if not stat:
            return False, "Can't use that item!"

        stages = self.stat_stages["player" if is_player else "enemy"]

        if stages[stat] >= 6:
            return False, f"{monster['name']}'s {stat.upper()} won't go higher!"

        stages[stat] = min(6, stages[stat] + boost_amount)

        stat_names = {
            "atk": "Attack",
            "def": "Defense",
            "spa": "Sp. Attack",
            "spd": "Sp. Defense",
            "spe": "Speed",
        }
        boost_text = "greatly " if boost_amount >= 2 else ""

        Logger.debug(
            f"Stat boost: {monster['name']} {stat} +{boost_amount} (now at stage {stages[stat]})"
        )
        return True, f"{monster['name']}'s {stat_names[stat]} {boost_text}rose!"

    def add_yield(self, fainted: dict, target: dict) -> None:
        """Add EVs from fainted Pokemon to target"""
        base = pokedex.data[fainted["id"]]
        if "yield" in base:
            for stat, amount in base["yield"].items():
                if stat in target["EV"]:
                    target["EV"][stat] = min(252, target["EV"][stat] + amount)

    def get_required_exp(self, level: int) -> int:
        """Calculate required EXP for next level"""
        return (level + 1) ** 3

    def recalculate_stats(self, mon: dict) -> None:
        """Recalculate stats based on level, IVs, and EVs"""
        base = pokedex.data[mon["id"]]
        level = mon["level"]

        # Capture old Max HP
        old_max_hp = mon["hp"]

        # New HP Calculation
        new_max_hp = (
            int((2 * base["hp"] + mon["IV"]["hp"] + mon["EV"]["hp"] / 4) * level / 100)
            + level
            + 10
        )
        mon["hp"] = new_max_hp

        # Increase current HP by the max HP gain
        hp_gain = new_max_hp - old_max_hp
        if hp_gain > 0:
            mon["chp"] += hp_gain

        # Cap chp just in case
        mon["chp"] = min(mon["chp"], mon["hp"])

        # Other Stats
        stats = ["atk", "def", "spa", "spd", "spe"]
        for s in stats:
            mon[s] = (
                int((2 * base[s] + mon["IV"][s] + mon["EV"][s] / 4) * level / 100) + 5
            )

    def add_exp(
        self, fainted: dict, target: dict, is_trainer_battle: bool
    ) -> tuple[int, bool]:
        """Add experience from fainted Pokemon to target. Returns (exp_gained, leveled_up)."""
        if target["level"] >= 100:  # Cap at 100
            return 0, False

        # Calculate Gain
        # Simplified formula: (BaseExp * Level * TrainerBonus) / 7
        # We don't have BaseExp in pokedex explicitly used in old code, it used rng * level
        # Let's keep it somewhat similar but boost it slightly
        gain = (self.rng.randint(25, 50) * target["level"]) // 5
        if is_trainer_battle:
            gain = int(gain * 1.5)

        target["exp"] += gain
        leveled_up = False

        # Level Up Check
        req = self.get_required_exp(target["level"])
        while target["exp"] >= req:
            target["exp"] -= req
            target["level"] += 1
            self.recalculate_stats(target)
            leveled_up = True

            # Heal fully on level up? Standard pokemon doesn't, but let's do small heal
            # Actually standard practice is stats increase current HP by delta.
            # `recalculate_stats` caps chp. Let's add delta match.
            # Simplified: Level up restores 10% HP? No, let's stick to standard:
            # Stats update, current HP stays same ratio? or same value?
            # Same value + delta max HP is correct.
            # My recalculate_stats implementation capped chp which is safe.

            if target["level"] >= 100:
                target["exp"] = 0
                break
            req = self.get_required_exp(target["level"])

        return gain, leveled_up
