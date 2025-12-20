from src.scenes.combat import CombatScene
from src.utils.combat import CombatType as ct
from src.utils.combat import OnlineCombatHandler
from src.utils import Logger
from src.core import gh


class PvPScene(CombatScene):
    """Player vs Player combat scene"""

    def __init__(self):
        super().__init__(combat_type=ct.PVP)

    def load_data(self):
        """Load PvP specific data"""
        if not gh.gm:
            gh.load()
        if not gh.gm.current_fight:
            self.exit()
            return

        # Player setup (same as others)
        self.ci1 = 0
        for i, mon in enumerate(gh.gm.bag.monsters):
            if mon["chp"] > 0:
                self.ci1 = i
                break

        self.ci2 = 0
        self.m1 = gh.gm.bag.monsters[self.ci1]
        self.m2 = gh.gm.current_fight.monsters[self.ci2]

        # PVP Handler Init
        opponent_id = getattr(gh.gm.current_fight, "opponent_id", None)
        if opponent_id is None:
            Logger.error("No opponent ID provided for PvP!")
            self.exit()
            return

        self.init_logic()
        self.handler = OnlineCombatHandler(self.logic, opponent_id)
        Logger.info(f"Initialized PVP Handler with opponent {opponent_id}")

        # Send my monsters data
        self.handler.send_battle_data({"monsters": gh.gm.bag.monsters})
        self.data_received = False

        self._img()
        self.health_overlay.load()
        self.switch_UI.init()
        self.item_overlay.init()
        self.move_refresh()
        self.move_overlay.inmove(self.m1["move"])

        self.common_ui_init()
        self.notichange("Waiting for opponent data...")
        self.waiting_for_action = False

        self.sync_timer = 0.0

    def update(self, dt):
        super().update(dt)

        # Check for opponent data
        if not self.data_received and self.handler:
            self.sync_timer += dt
            op_data = self.handler.opponent_data

            if op_data and "monsters" in op_data:
                # Update opponent monsters in the temporary fight context
                gh.gm.current_fight.monsters = op_data["monsters"]

                # Validate index
                if self.ci2 >= len(gh.gm.current_fight.monsters):
                    self.ci2 = 0

                self.m2 = gh.gm.current_fight.monsters[self.ci2]

                # Update logic with new monster
                if self.logic:
                    self.logic.pc2 = self.m2

                # Reload visuals
                self._img()
                self.health_overlay.load()
                self.notichange("Opponent data synced!")
                self.data_received = True
                self.waiting_for_action = True
            elif self.sync_timer > 5.0:
                Logger.warning("PvP Data Sync Timed Out!")
                self.notichange("Sync failed, using default data.")
                self.data_received = True
                self.waiting_for_action = True
