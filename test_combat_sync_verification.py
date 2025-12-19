import random
import sys

# Mock Logger
class Logger:
    @staticmethod
    def debug(msg):
        pass

# Mock poketype
class poketype:
    @staticmethod
    def effective(t1, t2):
        return 1.0

# Extracted and Simplified CombatLogic to verify RNG logic
class CombatLogic:
    def __init__(self, m1: dict, m2: dict):
        self.m1 = m1
        self.m2 = m2
        self.rng = random.Random() # Instance-based RNG
        self.stat_stages = {
            "player": {"atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0},
            "enemy": {"atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0},
        }

    def set_seed(self, seed: int):
        self.rng.seed(seed)

    def get_stat_multiplier(self, stage: int) -> float:
        return 1.0

    def attack(self, attacker: dict, defender: dict, move: dict) -> int:
        target = 1
        weather = 1
        critical = 1
        # The key logic change we are testing
        ran = self.rng.randint(85, 100) / 100
        acu = 1 if self.rng.randint(0, 100) < move["acc"] else 0
        stab = 1.5 if move["type"] in attacker["type"] else 1
        ty = 1.0
        vai = target * weather * critical * ran * stab * ty * acu
        
        # Simplified damage calc for verification
        dmg = (
                (2 * (attacker["level"] / 5) + 2)
                * move["power"]
                * (attacker["atk"] / defender["def"])
                / 50
                + 2
            ) * vai
        return int(dmg)

def test_deterministic_combat():
    # Mock Data
    m1 = {"name": "Charizard", "level": 50, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100, "type": ["Fire", "Flying"], "chp": 100, "hp": 100}
    m2 = {"name": "Blastoise", "level": 50, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100, "type": ["Water"], "chp": 100, "hp": 100}
    move = {"name": "Flamethrower", "type": "Fire", "cat": "Special Attack", "power": 90, "acc": 100}

    # Instance 1
    logic1 = CombatLogic(m1.copy(), m2.copy())
    logic1.set_seed(12345)
    dmg1 = logic1.attack(m1, m2, move)

    # Instance 2
    logic2 = CombatLogic(m1.copy(), m2.copy())
    logic2.set_seed(12345)
    dmg2 = logic2.attack(m1, m2, move)

    print(f"Logic 1 Damage: {dmg1}")
    print(f"Logic 2 Damage: {dmg2}")

    if dmg1 == dmg2:
        print("SUCCESS: Damage is identical with same seed.")
    else:
        print("FAILURE: Damage differs despite same seed.")
        sys.exit(1)

    # Test differnt seeds
    logic3 = CombatLogic(m1.copy(), m2.copy())
    logic3.set_seed(67890)
    dmg3 = logic3.attack(m1, m2, move)
    print(f"Logic 3 Damage (Diff Seed): {dmg3}")
    
    if dmg1 != dmg3:
         print("SUCCESS: Damage differs with different seed.")
    else:
         print("WARNING: Damage happened to be same with different seed.")

if __name__ == "__main__":
    test_deterministic_combat()
