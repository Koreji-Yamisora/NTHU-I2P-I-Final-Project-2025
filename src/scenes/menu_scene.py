import pygame as pg
from src.utils import GameSettings, Logger
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.interface.overlay_game import SettingOverlay
from src.core.services import (
    scene_manager,
    sound_manager,
    input_manager,
    resource_manager,
)
from typing import override


class MenuScene(Scene):
    """Menu  scene."""

    join_button: Button
    ip_input: str = "localhost"
    state: str = "MENU"  # MENU, JOIN
    font_ui: pg.font.Font

    def __init__(self):
        super().__init__()
        from src.core.gm_helper import gh

        self.background = BackgroundSprite("backgrounds/splash.png")
        self.setting_overlay = SettingOverlay()
        self.cursor_timer = 0.0

        # Layout configurations
        LEFT_OFFSET = 150
        BUTTON_HEIGHT = 100
        BUTTON_GAP = 10
        self.font = resource_manager.get_font("Pokemon solid.ttf", 82)
        self.ffont = resource_manager.get_font("dogicapixel.otf", 64)
        self.sub = resource_manager.get_font("dogicapixel.otf", 48)
        self.font_ui = resource_manager.get_font("dogicapixel.otf", 32)
        self.font_small = resource_manager.get_font("Pokemon solid.ttf", 24)

        # Title
        self.shadow = self.font.render("POKEMON???", True, (0, 0, 0))
        self.title = self.font.render("POKEMON???", True, (255, 128, 64))
        self.title_rect = self.title.get_rect(
            topleft=(150 + 50, (GameSettings.SCREEN_HEIGHT - 320) // 2 - 150)
        )  # Approx

        self.setup_buttons()

        # Slot Select State
        self.slot_buttons = []
        self.slot_mode = "LOAD"  # LOAD or NEW
        self.refresh_slot_buttons()

    def setup_buttons(self):
        from src.core.gm_helper import gh

        # Layout configurations
        LEFT_OFFSET = 150
        BUTTON_HEIGHT = 100
        BUTTON_GAP = 10
        BUTTON_SPACING = BUTTON_HEIGHT + BUTTON_GAP

        # Check save
        has_save = gh.has_save()  # Checks slots 0-2

        num_buttons = 3
        if has_save:
            num_buttons += 1

        total_height = num_buttons * BUTTON_SPACING - BUTTON_GAP
        start_y = (GameSettings.SCREEN_HEIGHT - total_height) // 2

        # Update title rect to match dynamic start_y
        self.title_rect.topleft = (LEFT_OFFSET + 50, start_y - 150)

        # Buttons
        self.btn_continue = None
        current_y = start_y

        if has_save:
            self.btn_continue = Button(
                "UI/button_play.png",
                "UI/button_play_hover.png",
                LEFT_OFFSET,
                current_y,
                100,
                100,
                lambda: self.enter_slot_select("LOAD"),
            )
            current_y += BUTTON_SPACING

        self.btn_new = Button(
            "UI/button_play.png",
            "UI/button_play_hover.png",
            LEFT_OFFSET,
            current_y,
            100,
            100,
            lambda: self.enter_slot_select("NEW"),
        )
        current_y += BUTTON_SPACING

        self.btn_join = Button(
            "UI/button_backpack.png",
            "UI/button_backpack_hover.png",
            LEFT_OFFSET,
            current_y,
            100,
            100,
            self.start_join,
        )
        current_y += BUTTON_SPACING

        self.settings_button = Button(
            "UI/button_setting.png",
            "UI/button_setting_hover.png",
            LEFT_OFFSET,
            current_y,
            100,
            100,
            self.enter_settings,
        )

    def refresh_slot_buttons(self):
        from src.core.gm_helper import gh
        import os

        self.slot_buttons = []

        start_y = 150
        gap = 80
        center_x = GameSettings.SCREEN_WIDTH // 2

        for i in range(3):
            path = gh.get_slot_path(i)
            exists = os.path.exists(path)

            # Slot Button
            btn = Button(
                "UI/button_backpack.png",
                "UI/button_backpack_hover.png",
                center_x - 250,
                start_y + i * gap,
                50,
                50,
                lambda idx=i: self.on_slot_click(idx),
            )
            # Label
            username = "Empty"
            if exists:
                import json

                try:
                    with open(path, "r") as f:
                        data = json.load(f)
                        username = data.get("username", "Player")
                except:
                    username = "???"

            if self.slot_mode == "NEW":
                if exists:
                    btn.label = f"Slot {i}: Overwrite ({username})"
                else:
                    btn.label = f"Slot {i}: Create New"
            elif self.slot_mode == "JOIN":
                if exists:
                    btn.label = f"Slot {i}: Join ({username})"
                else:
                    btn.label = f"Slot {i}: Join (New)"
            else:  # LOAD
                if exists:
                    btn.label = f"Slot {i}: Load ({username})"
                else:
                    btn.label = f"Slot {i}: Empty"

            self.slot_buttons.append(btn)

            # Delete Button (Only in LOAD mode and if exists)
            # Possibly allow deleting in NEW/JOIN? Probably safer only in LOAD for now.
            if self.slot_mode == "LOAD" and exists:
                del_btn = Button(
                    "UI/button_x.png",
                    "UI/button_x_hover.png",
                    center_x - 300,
                    start_y + i * gap,
                    40,
                    40,
                    lambda idx=i: self.delete_slot(idx),
                )
                self.slot_buttons.append(del_btn)

    def enter_slot_select(self, mode: str):
        self.state = "SLOT_SELECT"
        self.slot_mode = mode
        self.refresh_slot_buttons()

    def enter_username_entry(self, index: int):
        self.state = "USERNAME_ENTRY"
        self.target_slot_index = index
        self.username_input = ""
        input_manager.reset()  # clear inputs

    def on_slot_click(self, index: int):
        from src.core.gm_helper import gh
        import os

        path = gh.get_slot_path(index)
        exists = os.path.exists(path)

        if self.slot_mode == "LOAD":
            if exists:
                gh.set_save_path(path)
                if gh.load():
                    scene_manager.change_scene("game")
                else:
                    Logger.error(f"Failed to load slot {index}")
            else:
                pass

        elif self.slot_mode == "NEW":
            # Go to Username Entry instead of immediate create
            self.enter_username_entry(index)

        elif self.slot_mode == "JOIN":
            self.target_slot_index = index  # Store for logic

            # Configure OnlineManager
            target_ip = self.ip_input.strip() or "localhost"
            if gh.online_manager:
                base = target_ip
                if ":" not in base:
                    base += ":8989"
                gh.online_manager.ws_url = f"ws://{base}"

            # Load or New
            if exists:
                gh.set_save_path(path)
                if gh.load():
                    scene_manager.change_scene("game")
                else:
                    Logger.error(f"Failed to load slot {index} for join")
            else:
                # Create new game -> Go to username entry
                self.enter_username_entry(index)

    def finish_create_game(self):
        """Show starter selection before creating game."""
        from src.interface.overlay_starter import StarterOverlay

        # Open starter selection overlay
        self.starter_overlay = StarterOverlay(on_select=self.on_starter_selected)
        self.starter_overlay.open()
        self.state = "STARTER_SELECT"

    def on_starter_selected(self, starter_id: int):
        """Handle starter selection and create the game."""
        from src.core.gm_helper import gh
        from src.utils.generate import generate_monster

        name = self.username_input.strip() or "Player"
        if gh.new_game(self.target_slot_index, name):
            # Replace the auto-generated starter with the selected one
            selected_starter = generate_monster(starter_id, 5)
            gh.gm.bag._monsters_data = [selected_starter]
            gh.gm.bag.update_bag()
            gh.save()  # Save immediately with the chosen starter
            scene_manager.change_scene("game")

    def delete_slot(self, index: int):
        from src.core.gm_helper import gh

        gh.delete_save(index)
        # Refresh to remove the deleted slot from UI
        self.refresh_slot_buttons()
        # If no saves left, maybe return to menu or just stay?
        # Stay is better UX.

    def start_join(self):
        self.state = "JOIN"
        input_manager.reset()  # clear any old input

    def enter_settings(self):
        self.state = "SETTINGS"
        self.setting_overlay.open()

    @override
    def enter(self) -> None:
        """Enter."""
        sound_manager.play_bgm("01 - Genshin Impact Main Theme.mp3")
        input_manager.reset()
        self.state = "MENU"
        self.username_input = ""
        self.target_slot_index = -1
        self.setup_buttons()

    @override
    def exit(self) -> None:
        """Exit."""
        pass

    @override
    def update(self, dt: float) -> None:
        """Update."""
        self.cursor_timer += dt

        if self.state == "MENU":
            if self.btn_continue:
                self.btn_continue.update(dt)
            self.btn_new.update(dt)
            self.btn_join.update(dt)
            self.settings_button.update(dt)

        elif self.state == "JOIN":
            # Handle IP Input
            if input_manager.key_pressed(pg.K_ESCAPE):
                self.state = "MENU"
                input_manager.reset()
            elif input_manager.key_pressed(pg.K_RETURN):
                # Join logic
                self.join_game()
            elif input_manager.text_input:
                self.ip_input += input_manager.text_input
                input_manager.text_input = ""  # Consume

            # Handle Backspace
            if input_manager.key_pressed(pg.K_BACKSPACE):
                self.ip_input = self.ip_input[:-1]

        elif self.state == "SLOT_SELECT":
            if input_manager.key_pressed(pg.K_ESCAPE):
                self.state = "MENU"
                return

            for btn in self.slot_buttons:
                btn.update(dt)

        elif self.state == "USERNAME_ENTRY":
            if input_manager.key_pressed(pg.K_ESCAPE):
                # Go back to slot select
                self.state = "SLOT_SELECT"
                input_manager.reset()
                return
            elif input_manager.key_pressed(pg.K_RETURN):
                self.finish_create_game()
            elif input_manager.text_input:
                # Limit length
                if len(self.username_input) < 12:
                    self.username_input += input_manager.text_input
                input_manager.text_input = ""

            if input_manager.key_pressed(pg.K_BACKSPACE):
                self.username_input = self.username_input[:-1]

        elif self.state == "SETTINGS":
            self.setting_overlay.update(dt)
            if not self.setting_overlay.is_open:
                self.state = "MENU"

        elif self.state == "STARTER_SELECT":
            if hasattr(self, "starter_overlay"):
                self.starter_overlay.update(dt)
                if not self.starter_overlay.is_open:
                    # Selection made, state change handled in callback
                    pass

    def join_game(self):
        # We don't connect immediately. We go to slot select first.
        # But we need to update IP for when we do connect.
        # We can just store state and move on.
        self.enter_slot_select("JOIN")

    @override
    def draw(self, screen: pg.Surface) -> None:
        """Draw."""
        self.background.draw(screen)
        screen.blit(self.shadow, (self.title_rect.x + 2, self.title_rect.y + 2))
        screen.blit(self.title, self.title_rect)

        # Blink logic
        show_cursor = int(self.cursor_timer * 2) % 2 == 0
        cursor_char = "|" if show_cursor else ""

        if self.state == "MENU":
            if self.btn_continue:
                self.btn_continue.draw(screen)
                self.draw_label(screen, "Load Game", self.btn_continue.hitbox)

            self.btn_new.draw(screen)
            self.draw_label(screen, "New Game", self.btn_new.hitbox)

            self.btn_join.draw(screen)
            self.draw_label(screen, "Join Game", self.btn_join.hitbox)

            self.settings_button.draw(screen)
            self.draw_label(screen, "Settings", self.settings_button.hitbox)

        elif self.state == "JOIN":
            s = pg.Surface(
                (GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), pg.SRCALPHA
            )
            s.fill((0, 0, 0, 200))
            screen.blit(s, (0, 0))

            # Draw Prompt
            prompt = self.ffont.render("Enter Server IP:", True, (255, 255, 255))
            pr = prompt.get_rect(
                center=(
                    GameSettings.SCREEN_WIDTH // 2,
                    GameSettings.SCREEN_HEIGHT // 2 - 50,
                )
            )
            screen.blit(prompt, pr)

            # Draw Input
            inp = self.ffont.render(self.ip_input + cursor_char, True, (255, 255, 0))
            ir = inp.get_rect(
                center=(
                    GameSettings.SCREEN_WIDTH // 2,
                    GameSettings.SCREEN_HEIGHT // 2 + 50,
                )
            )
            screen.blit(inp, ir)

        elif self.state == "SLOT_SELECT":
            s = pg.Surface(
                (GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), pg.SRCALPHA
            )
            s.fill((0, 0, 0, 200))
            screen.blit(s, (0, 0))

            if self.slot_mode == "LOAD":
                txt = "Load Game"
            elif self.slot_mode == "JOIN":
                txt = "Select Profile to Join"
            else:
                txt = "New Game (Select Slot)"

            # Use smaller font if needed, or sub font
            if len(txt) > 20:
                title = self.sub.render(txt, True, (255, 255, 255))
            else:
                title = self.font.render(txt, True, (255, 255, 255))

            tr = title.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, 80))
            screen.blit(title, tr)

            for btn in self.slot_buttons:
                btn.draw(screen)
                if hasattr(btn, "label"):
                    self.draw_label(screen, btn.label, btn.hitbox)

        elif self.state == "USERNAME_ENTRY":
            s = pg.Surface(
                (GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), pg.SRCALPHA
            )
            s.fill((0, 0, 0, 200))
            screen.blit(s, (0, 0))

            prompt = self.ffont.render("Enter Name:", True, (255, 255, 255))
            pr = prompt.get_rect(
                center=(
                    GameSettings.SCREEN_WIDTH // 2,
                    GameSettings.SCREEN_HEIGHT // 2 - 50,
                )
            )
            screen.blit(prompt, pr)

            inp = self.ffont.render(
                self.username_input + cursor_char, True, (255, 255, 0)
            )
            ir = inp.get_rect(
                center=(
                    GameSettings.SCREEN_WIDTH // 2,
                    GameSettings.SCREEN_HEIGHT // 2 + 50,
                )
            )
            screen.blit(inp, ir)

        elif self.state == "SETTINGS":
            self.setting_overlay.draw(screen)

        elif self.state == "STARTER_SELECT":
            if hasattr(self, "starter_overlay"):
                self.starter_overlay.draw(screen)

    def draw_label(self, screen, text, rect):
        # Draw text to the right or centered?
        # Let's draw centered below or to the right
        # To right:
        lbl = self.font_ui.render(text, True, (0, 0, 0))  # Shadow
        lbl_w = self.font_ui.render(text, True, (255, 255, 255))

        pos = (rect.right + 20, rect.centery - lbl.get_height() // 2)
        screen.blit(lbl, (pos[0] + 2, pos[1] + 2))
        screen.blit(lbl_w, pos)
