from src.scenes.combat import CombatScene
from src.utils.combat import CombatType as ct
from typing import override

class BattleScene(CombatScene):
    """Trainer battle scene"""

    def __init__(self):
        super().__init__(combat_type=ct.TRAINER)

    def load_data(self):
        from src.core import gh
        if not gh.gm:
            gh.load()
        if not gh.gm.current_fight:
            self.exit()
            return

        self.ci1 = 0
        for i, mon in enumerate(gh.gm.bag.monsters):
            if mon["chp"] > 0:
                self.ci1 = i
                break
        
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
