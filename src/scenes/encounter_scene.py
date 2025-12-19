from src.scenes.combat import CombatScene
from src.utils.combat import CombatType as ct


class EncounterScene(CombatScene):
    """Wild Pokemon encounter scene"""

    def __init__(self):
        super().__init__(combat_type=ct.WILD)

    def load_data(self):
        from src.core import gh

        if not gh.gm:
            gh.load()
        if not gh.gm.current_fight:
            self.exit()
            return

        self.ci1 = 0
        if not gh.gm.bag.monsters:
            from src.utils import Logger

            Logger.warning("No monsters in bag! Cannot start encounter.")
            self.exit()
            return

        found_alive = False
        for i, mon in enumerate(gh.gm.bag.monsters):
            if mon["chp"] > 0:
                self.ci1 = i
                found_alive = True
                break

        if not found_alive and gh.gm.bag.monsters:
            # Fallback if all dead (shouldn't happen ideally, but prevents crash if list not empty)
            # But if we fight with dead monster, it's weird.
            # For now, let's allow it but maybe warn? Or just let it be, as index 0 exists.
            pass

        self.ci2 = 0
        self.m1 = gh.gm.bag.monsters[self.ci1]
        self.m2 = gh.gm.current_fight.monsters[self.ci2]

        self.init_logic()
        self._img()

        self.health_overlay.load()
        self.switch_UI.init()
        self.item_overlay.init()
        self.move_refresh()
        self.move_overlay.inmove(self.m1["move"])

        self.common_ui_init()
