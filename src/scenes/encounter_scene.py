from src.scenes.combat import CombatScene
from src.core import gh
from src.utils import Logger
from typing import override

class EncounterScene(CombatScene):
    """Wild Pokemon encounter scene"""
    
    def __init__(self):
        super().__init__(combat_type="wild")
    
    @override
    def load_data(self):
        """Load wild encounter data"""
        if not gh.gm:
            gh.load()
        elif not gh.gm.current_fight:
            self.exit()
        else:
            self._init()

            self.current = 4  # Wild encounters use index 4
            self.enemy = 0
            self.action_overlay.is_active = True
            self.action_overlay.is_passive = True
            self.next = None

            self.player_turn = True
            self.waiting_for_action = True
            self.clear()
            self.monster1 = gh.gm.bag.monsters[self.current]
            Logger.debug(f"{gh.gm.current_fight.monsters}")
            self.monster2 = gh.gm.current_fight.monsters[self.enemy]
            self.img()

            self.items = gh.gm.bag.get_items()
            self.turn = True
            self.move_overlay.inmove(self.monster1["move"])
            self.health_overlay.load()
            from src.utils import crd, GameSettings
            from src.sprites import Text
            sh = crd(GameSettings.SCREEN_HEIGHT)
            self.noti = Text(f"What will {self.monster1['name']} do?", 32, "Black")
            self.noti.rect.topleft = (
                self.bg3.rect.left + sh.per(3),
                self.bg3.rect.top + sh.per(2),
            )
            self.item_overlay.init()
            self.switch_UI.init()
            self.move_refresh()
            self.move_overlay.inmove(self.monster1["move"])

            # Combat State
            self.player_action = None
            self.enemy_action = None
            self.turn_queue = []
            self.executing_turn = False
            self.turn_timer = 0.0
