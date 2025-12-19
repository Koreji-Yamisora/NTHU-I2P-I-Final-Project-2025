import pygame as pg
from src.interface.components import Overlay, Button
from src.utils import crd, GameSettings, Logger, color
from src.sprites import Text, Sprite

class BattleRequestOverlay(Overlay):
    def __init__(self, requester_id: int, on_accept, on_decline):
        super().__init__(overlay_alpha=150) # Use built-in dimming
        self.requester_id = requester_id
        self.on_accept_cb = on_accept
        self.on_decline_cb = on_decline
        
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)
        
        # Background Panel
        panel_w, panel_h = 400, 250
        panel = Sprite(
            "UI/raw/UI_Flat_Frame01a.png",
            (panel_w, panel_h),
            nine_grid_margins=(45, 45, 45, 45),
        )
        panel.image = color.recol(panel.image, (120, 120, 120))
        panel.rect.center = (sw // 2, sh // 2)
        self.add_bg(panel)
        
        # Title Text
        self.title = Text(
            f"Battle Request\nfrom Player {requester_id}!", 
            32, 
            "White"
        )
        self.title.rect.center = (sw // 2, sh // 2 - 50)
        self.add_passive(self.title)
        
        self.btn_accept = Button(
            "UI/button_play.png", 
            "UI/button_play_hover.png",
            sw // 2 - 60,
            sh // 2 + 40,
            100, 50,
            self.accept
        )
        self.add_active(self.btn_accept)
        
        self.btn_decline = Button(
            "UI/button_x.png",
            "UI/button_x_hover.png",
            sw // 2 + 60,
            sh // 2 + 40,
            50, 50,
            self.decline
        )
        self.add_active(self.btn_decline)
        
    def accept(self):
        Logger.info("Accepted battle request")
        self.close()
        if self.on_accept_cb:
            self.on_accept_cb(self.requester_id)
            
    def decline(self):
        Logger.info("Declined battle request")
        self.close()
        if self.on_decline_cb:
            self.on_decline_cb()
