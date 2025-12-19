from src.utils import GameSettings, crd, color
from src.interface.components import Overlay, Button
from src.sprites import Sprite, Text
import pygame as pg

class BattleRequestOverlay(Overlay):
    def __init__(self, sender_id: int, on_accept, on_decline):
        super().__init__()
        self.open()
        self.sender_id = sender_id
        
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)
        
        # Background
        bg_width = sw.per(40)
        bg_height = sh.per(30)
        bg = Sprite(
            "UI/raw/UI_Flat_Frame03a.png",
            (bg_width, bg_height),
            nine_grid_margins=(45, 45, 45, 45),
        )
        bg.image = color.recol(bg.image, (120, 120, 120))
        bg.rect.center = (sw // 2, sh // 2)
        self.add_bg(bg)
        
        # Text
        text = Text(f"Player {sender_id} wants to battle!", 32, "Black")
        text.rect.center = (bg.rect.centerx, bg.rect.top + bg_height // 4)
        self.add_passive(text)
        
        # Buttons
        button_width = bg_width // 3
        button_height = bg_height // 4
        
        accept_btn = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            bg.rect.left + bg_width // 6,
            bg.rect.bottom - bg_height // 3,
            button_width,
            button_height,
            on_accept,
            nine_grid_margins=(14, 14, 14, 14),
        )
        accept_btn.img_button_default.image = color.recol(accept_btn.img_button_default.image, (120, 120, 120))
        accept_btn.img_button_hover.image = color.recol(accept_btn.img_button_hover.image, (120, 120, 120))
        self.add_active(accept_btn)
        
        acc_label = Text("Accept", 28, "Black")
        acc_label.rect.center = accept_btn.hitbox.center
        acc_label.rect.bottom -= accept_btn.hitbox.height // 10
        self.add_passive(acc_label)
        
        decline_btn = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            bg.rect.right - bg_width // 6 - button_width,
            bg.rect.bottom - bg_height // 3,
            button_width,
            button_height,
            on_decline,
            nine_grid_margins=(14, 14, 14, 14),
        )
        decline_btn.img_button_default.image = color.recol(decline_btn.img_button_default.image, (120, 120, 120))
        decline_btn.img_button_hover.image = color.recol(decline_btn.img_button_hover.image, (120, 120, 120))
        self.add_active(decline_btn)
        
        dec_label = Text("Decline", 28, "Black")
        dec_label.rect.center = decline_btn.hitbox.center
        dec_label.rect.bottom -= decline_btn.hitbox.height // 10
        self.add_passive(dec_label)
