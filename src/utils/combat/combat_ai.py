from src.utils.combat.combat_logic import CombatLogic
from src.utils import Logger
import random
from typing import Optional


class CombatAI:
    """Handles AI opponent logic for wild/trainer battles."""

    def __init__(self, combat_logic: CombatLogic, combat_type: str = "wild"):
        self.logic = combat_logic
        self.combat_type = str(combat_type) # Ensure string comparison works

    def get_enemy_action(self, enemy_monster: dict) -> dict:
        """AI selects an action for the enemy"""
        
        # 1. Check for running (Wild only)
        if self.combat_type == "wild":
            hp_percent = enemy_monster["chp"] / enemy_monster["hp"]
            if hp_percent < 0.5:
                # 50% chance to try running? Or always try?
                # User said: "wild will try to run if hp is less than half"
                # Let's make it attempt to run. In combat_new.py run_attempt has a chance.
                # But here we are returning an action. If we return "run", combat_new handles it.
                # However, usually enemies don't "run" using the standard run_attempt logic player uses?
                # The player run logic in combat_new.py calls scene_manager.change_scene("game").
                # Let's assume returning "run" action will be handled by combat_new.
                # Wait, combat_new.py execute_next_action handles "run" action:
                # elif action["type"] == "run": self.run_attempt()
                # run_attempt does: if random < 95: change_scene.
                # So if AI returns "run", it should work.
                
                # Let's add some randomness so it doesn't SPAM run if it fails?
                # Or maybe it should spam run if it wants to leave?
                # Let's say 2/3 chance it decides to run this turn if low hp.
                if random.random() < 0.66:
                     Logger.debug("AI decided to run away!")
                     return {"type": "run", "value": None}

        # 2. Choose best move
        best_move = None
        best_damage = -1.0
        
        # Shuffle moves to randomize tie-breaks
        moves = enemy_monster["move"][:] # Copy
        random.shuffle(moves)
        
        for move in moves:
            # We need the player's pokemon (defender)
            # CombatAI has self.logic, which has self.m1 (player) and self.m2 (enemy)
            # self.logic.m1 is player.
            estimated = self.logic.estimate_damage(enemy_monster, self.logic.m1, move)
            if estimated > best_damage:
                best_damage = estimated
                best_move = move
                
        if best_move:
             Logger.debug(f"AI selected best move: {best_move['name']} (Est. Dmg: {best_damage:.1f})")
             return {"type": "move", "value": best_move}

        # Fallback (shouldn't happen if moves exist)
        enemy_move = random.choice(enemy_monster["move"])
        Logger.debug(f"AI selected random move (fallback): {enemy_move['name']}")
        return {"type": "move", "value": enemy_move}
