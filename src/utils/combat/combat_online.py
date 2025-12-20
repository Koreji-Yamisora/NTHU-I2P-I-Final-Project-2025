from src.utils.combat.combat_logic import CombatLogic
from src.utils import Logger
from src.core.gm_helper import gh
from src.utils.settings import GameSettings
from typing import Optional


class OnlineCombatHandler:
    """Handles PvP combat logic with network synchronization"""

    def __init__(self, combat_logic: CombatLogic, opponent_id: int):
        self.logic = combat_logic
        self.opponent_id = opponent_id

        # PvP state
        self.opponent_action_received = False
        self.opponent_action: Optional[dict] = None
        self.waiting_for_opponent = False
        self.opponent_data = None

        # Register callback
        if gh.online_manager:
            gh.online_manager.register_event_callback(self.handle_event)

    def send_action(self, action: dict, seed: Optional[int] = None) -> bool:
        """Send player's action to opponent"""
        if not gh.online_manager:
            Logger.warning("Online manager not available")
            return False

        action_data = {"type": "battle_action", "action": action}
        if seed is not None:
            action_data["seed"] = seed

        success = gh.online_manager.send_event(self.opponent_id, action_data)

        if success:
            if GameSettings.ONLINE_LOGGING:
                Logger.info(f"Sent action to opponent {self.opponent_id}: {action}")
            self.waiting_for_opponent = True
        else:
            Logger.warning("Failed to send action to opponent")

        return success

    def handle_event(self, event: dict) -> None:
        """Handle incoming PvP event"""
        event_type = event.get("type")

        if event_type == "battle_action":
            self.opponent_action = event.get("action")
            # Inject seed into action if present
            if self.opponent_action and "seed" in event:
                self.opponent_action["seed"] = event["seed"]

            self.opponent_action_received = True
            self.waiting_for_opponent = False
            if GameSettings.ONLINE_LOGGING:
                Logger.info(f"Received opponent action: {self.opponent_action}")

        elif event_type == "forfeit":
            if GameSettings.ONLINE_LOGGING:
                Logger.info("Opponent forfeited!")
            # This will be handled by the combat scene

        elif event_type == "battle_end":
            result = event.get("result")
            if GameSettings.ONLINE_LOGGING:
                Logger.info(f"Battle ended - opponent {result}")

        elif event_type == "battle_data":
            self.opponent_data = event.get("data")
            if GameSettings.ONLINE_LOGGING:
                Logger.info(f"Received opponent data: {self.opponent_data}")

    def send_battle_data(self, data: dict) -> bool:
        """Send initialization data (e.g. monster info)"""
        if not gh.online_manager:
            return False

        return gh.online_manager.send_event(
            self.opponent_id, {"type": "battle_data", "data": data}
        )

    def is_ready_to_resolve(self) -> bool:
        """Check if both actions are ready"""
        return self.opponent_action_received and self.opponent_action is not None

    def get_opponent_action(self) -> Optional[dict]:
        """Get the opponent's action"""
        return self.opponent_action

    def reset_turn(self) -> None:
        """Reset for next turn"""
        self.opponent_action = None
        self.opponent_action_received = False
        self.waiting_for_opponent = False

    def send_battle_end(self, won: bool) -> bool:
        """Send battle end signal"""
        if not gh.online_manager:
            return False

        return gh.online_manager.send_event(
            self.opponent_id, {"type": "battle_end", "result": "win" if won else "lose"}
        )
