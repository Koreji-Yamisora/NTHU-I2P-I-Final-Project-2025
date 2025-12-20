from __future__ import annotations
import pygame as pg
import math
from src.interface.components import Overlay, Button
from src.sprites import Sprite, Text, SequenceAnimation
from src.utils import GameSettings, crd, Logger, color
from src.core.services import resource_manager, input_manager
from src.data import PokeDex
from typing import Callable


class EvolutionOverlay(Overlay):
    """Evolution Overlay with sequence: Popup -> Evolve -> Animation -> Data Change."""

    # States
    STATE_IDLE = "IDLE"
    STATE_SLIDING_UP = "SLIDING_UP"
    STATE_WAITING = "WAITING"
    STATE_PULSING = "PULSING"
    STATE_LEVITATING = "LEVITATING"
    STATE_SLIDING_DOWN = "SLIDING_DOWN"
    STATE_EVOLVING = "EVOLVING"
    STATE_FADING = "FADING"
    STATE_SUCCESS = "SUCCESS"

    def __init__(self):
        super().__init__(overlay_alpha=180)  # Darker overlay for focus
        self.state = self.STATE_IDLE
        self.monster_data = None
        self.callback = None
        self._setup_properties()

    def _setup_properties(self):
        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        # Background Panel
        self.panel_img_path = "UI/raw/UI_Flat_Frame03a.png"  # Standard frame
        self.panel_w = sw.per(40)
        self.panel_h = sh.per(60)

        # We will create sprites dynamically in setup,
        # but pre-load star animation to be ready
        # Folder is 'star animation' in assets/images or graphics/other
        self.star_anim = SequenceAnimation(
            "star animation", duration=1.5, size=(256, 256)
        )

        # Tween trackers
        self.tween_time = 0.0
        self.tween_duration = 0.5
        self.flash_alpha = 0
        self.flash_surface = None
        self.original_poke_image = None

    def setup(self, monster_data: dict, evolve_callback: Callable):
        """Setup the overlay with a specific monster."""
        self.monster_data = monster_data
        self.real_callback = evolve_callback  # Called AFTER visual evolution

        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        self.clear()
        self.show_poke1_sprite = True
        self.show_poke2_sprite = False

        # 1. Background Panel (Initially off-screen bottom)
        self.bg = Sprite(
            self.panel_img_path,
            (self.panel_w, self.panel_h),
            nine_grid_margins=(45, 45, 45, 45),
        )
        self.bg.image = color.recol(self.bg.image, (120, 120, 120))
        self.bg_target_y = (sh - self.panel_h) // 2
        self.bg_start_y = sh  # Off screen
        self.bg.rect.centerx = sw // 2
        self.bg.rect.top = self.bg_start_y
        self.add_bg(self.bg)

        # 2. Pokemon Sprite (Current)
        if "sprite_path" in monster_data:
            sprite_path = monster_data["sprite_path"]
        elif "id" in monster_data:
            pid = monster_data["id"]
            if pid in PokeDex.data:
                sprite_path = PokeDex.data[pid]["sprite_path"]
            else:
                sprite_path = "pokemon/0.png"
        else:
            sprite_path = "pokemon/0.png"

        self.poke_sprite = Sprite(sprite_path, (128, 128))
        self.poke_sprite.rect.center = (sw // 2, self.bg.rect.top + self.panel_h // 3)
        self.original_poke_image = self.poke_sprite.image.copy()
        self.add_passive(self.poke_sprite)

        # Create evolved pokemon sprite (hidden initially)
        target_id = None
        pid = monster_data.get("id", 0)
        if pid in PokeDex.data:
            target_id = PokeDex.data[pid].get("evolution", {}).get("to")

        if target_id and target_id in PokeDex.data:
            evolved_sprite_path = PokeDex.data[target_id]["sprite_path"]
        else:
            evolved_sprite_path = "pokemon/0.png"

        self.poke_sprite2 = Sprite(evolved_sprite_path, (128, 128))
        self.poke_sprite2.rect.center = (sw // 2, sh // 2 - 50)
        self.original_poke2_image = self.poke_sprite2.image.copy()
        self.add_passive(self.poke_sprite2)

        # 3. Evolve Button
        self.evolve_btn = Button(
            "UI/raw/UI_Flat_Button01a_4.png",
            "UI/raw/UI_Flat_Button01a_3.png",
            sw // 2 - 100,
            self.bg_target_y + self.panel_h - 100,
            200,
            60,
            self._start_evolution_flow,
            nine_grid_margins=(14, 14, 14, 14),
        )
        self.evolve_btn.img_button_default.image = color.recol(
            self.evolve_btn.img_button_default.image, (120, 120, 120)
        )
        self.evolve_btn.img_button_hover.image = color.recol(
            self.evolve_btn.img_button_hover.image, (120, 120, 120)
        )
        self.btn_text = Text("EVOLVE", 24, "Black")
        self.btn_text.rect.center = self.evolve_btn.hitbox.center

        # 4. Message Text
        self.msg_name = monster_data.get("name", "Unknown")
        self.msg_text = Text(f"What? {self.msg_name} is evolving!", 28, "White")
        self.msg_text.rect.centerx = sw // 2
        self.msg_text.rect.bottom = sh - 50
        self.add_passive(self.msg_text)

        self._switched_form = False
        # Start State
        self.state = self.STATE_SLIDING_UP
        self.tween_time = 0.0
        self.open()

    def _start_evolution_flow(self):
        """User clicked Evolve."""
        Logger.info("User requested evolution!")
        # Start Pulsing
        self.state = self.STATE_PULSING
        self.tween_time = 0.0

        # Remove button and text
        if self.evolve_btn in self.active_components:
            self.active_components.remove(self.evolve_btn)
        if self.btn_text in self.components:
            self.components.remove(self.btn_text)

        # Hide arrow text if it exists
        if hasattr(self, "arrow_text") and self.arrow_text in self.components:
            self.components.remove(self.arrow_text)

    def update_content(self, dt: float):
        """Update logic for animations."""

        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        if self.state == self.STATE_SLIDING_UP:
            self.tween_time += dt
            t = min(1.0, self.tween_time / 0.5)
            # Ease out cubic (User likes this)
            ease = 1 - (1 - t) ** 3

            new_top = self.bg_start_y + (self.bg_target_y - self.bg_start_y) * ease
            self.bg.rect.top = int(new_top)

            # Sync element positions
            panel_center_y = self.bg.rect.top + self.panel_h // 3
            self.poke_sprite.rect.center = (sw // 2, panel_center_y)

            if t >= 1.0:
                self.state = self.STATE_WAITING
                self.add_active(self.evolve_btn)
                self.add_passive(self.btn_text)
                # Resync button pos
                self.evolve_btn.hitbox.centerx = sw // 2
                self.evolve_btn.hitbox.bottom = self.bg.rect.bottom - 50
                self.evolve_btn.img_button.rect.center = self.evolve_btn.hitbox.center
                self.btn_text.rect.center = self.evolve_btn.hitbox.center

        elif self.state == self.STATE_PULSING:
            self.tween_time += dt
            # Pulse + Levitate for 1.5 seconds simultaneously
            pulse_dur = 1.5
            t_pulse = min(1.0, self.tween_time / pulse_dur)

            # Levitation: Sprite moves UP while pulsing
            start_y = self.bg_target_y + self.panel_h // 3
            target_y = sh // 2 - 50
            ease = t_pulse * (2 - t_pulse)  # Ease out quad

            # Panel slides DOWN (out of the way)
            panel_start_y = self.bg_target_y
            panel_end_y = sh  # Off screen bottom
            self.bg.rect.top = int(panel_start_y + (panel_end_y - panel_start_y) * ease)

            if self.tween_time >= pulse_dur:
                self.state = self.STATE_EVOLVING
                self.tween_time = 0.0
                # Restore original image
                if self.original_poke_image:
                    self.poke_sprite.image = self.original_poke_image
                    self.poke_sprite.rect = self.poke_sprite.image.get_rect(
                        center=(sw // 2, target_y)
                    )
                self.star_anim.rect.center = self.poke_sprite.rect.center
                self.star_anim.play(self._on_animation_finish)
            else:
                # Sine wave pulsing: scale between 1.0 and 1.2
                pulse_phase = self.tween_time * 10
                scale_factor = 1.0 + 0.2 * abs(math.sin(pulse_phase))

                # White pulsing: oscillate white mix intensity
                white_intensity = int(128 + 127 * abs(math.sin(pulse_phase)))

                if self.original_poke_image:
                    w, h = self.original_poke_image.get_size()
                    new_size = (int(w * scale_factor), int(h * scale_factor))
                    scaled = pg.transform.scale(self.original_poke_image, new_size)

                    # Apply white tint overlay
                    white_overlay = pg.Surface(scaled.get_size(), pg.SRCALPHA)
                    white_overlay.fill((255, 255, 255, white_intensity))
                    scaled.blit(white_overlay, (0, 0), special_flags=pg.BLEND_RGBA_ADD)

                    self.poke_sprite.image = scaled
                    # Position sprite while levitating
                    current_y = int(start_y + (target_y - start_y) * ease)
                    self.poke_sprite.rect = self.poke_sprite.image.get_rect(
                        center=(sw // 2, current_y)
                    )

        elif self.state == self.STATE_EVOLVING:
            self.star_anim.rect.center = self.poke_sprite.rect.center
            self.star_anim.update(dt)
            self.poke_sprite.update(dt)  # For flash timer

            # Transformation and Mask Transition
            acc = self.star_anim.accumulator
            dur = self.star_anim.duration

            # No screen flash - removed

            # 1. Start Flash White (Mask) of Sprite
            if acc > dur * 0.1 and acc < dur * 0.2:
                if self.poke_sprite.flash_timer <= 0:
                    # Use full alpha for solid mask
                    self.poke_sprite.flash(
                        (255, 255, 255), duration=dur * 0.8, alpha=255
                    )

            # 2. Midpoint: Switch form!
            if acc > dur * 0.5 and not self._switched_form:
                self._switched_form = True
                # Switch to evolved sprite (but it's still masked white)
                target_id = None
                pid = self.monster_data.get("id", 0)
                if pid in PokeDex.data:
                    target_id = PokeDex.data[pid].get("evolution", {}).get("to")

                if target_id and target_id in PokeDex.data:
                    path = PokeDex.data[target_id]["sprite_path"]
                    img = resource_manager.get_image(path)
                    # Rescale
                    self.poke_sprite.image = pg.transform.scale(img, (128, 128))
                    self.original_poke_image = (
                        self.poke_sprite.image.copy()
                    )  # Update original for landing

            if acc > dur * 0.9:
                self.show_poke1_sprite = False
                # Transition to fading state with white wash
                self.state = self.STATE_FADING
                self.tween_time = 0.0
                self.flash_alpha = 255  # Start fully white
                # Position evolved sprite at center (same as where original was)
                sw = crd(GameSettings.SCREEN_WIDTH)
                sh = crd(GameSettings.SCREEN_HEIGHT)
                self.poke_sprite2.rect.center = (sw // 2, sh // 2 - 50)

        elif self.state == self.STATE_FADING:
            self.tween_time += dt
            fade_dur = 0.8  # Fade duration

            if self.tween_time >= fade_dur:
                # Fade complete, trigger callback and go to success
                self.flash_alpha = 0
                self._finish_evolution()
            else:
                # Fade out white wash to reveal evolved pokemon
                t = self.tween_time / fade_dur
                self.flash_alpha = int(255 * (1 - t))
                # Show the evolved sprite during fade
                self.show_poke2_sprite = True

        elif self.state == self.STATE_SUCCESS:
            self.tween_time += dt

            # Landing/Thud Effect (First 0.3s) for evolved sprite
            if self.tween_time < 0.3:
                # Scale from 2.0 down to 1.0
                t_land = self.tween_time / 0.3
                scale_land = 2.0 - 1.0 * t_land  # Linear 2 -> 1
                if self.original_poke2_image:
                    w, h = self.original_poke2_image.get_size()
                    new_size = (int(w * scale_land), int(h * scale_land))
                    self.poke_sprite2.image = pg.transform.scale(
                        self.original_poke2_image, new_size
                    )
                    self.poke_sprite2.rect = self.poke_sprite2.image.get_rect(
                        center=self.poke_sprite2.rect.center
                    )
            elif self.tween_time < 0.4 and self.tween_time >= 0.3:
                # Ensure resets to 1.0 exactly
                if self.original_poke2_image:
                    self.poke_sprite2.image = self.original_poke2_image
                    self.poke_sprite2.rect = self.poke_sprite2.image.get_rect(
                        center=self.poke_sprite2.rect.center
                    )

            # Auto close after 5 seconds, or click after 1.5 seconds default
            if self.tween_time >= 5.0:
                self.close()
            elif self.tween_time >= 1.5 and input_manager.mouse_pressed(1):
                self.close()

    def _finish_evolution(self):
        """Called after fade completes to finalize evolution."""
        Logger.info("Evolution animation finished.")
        # Trigger actual data change
        if self.real_callback:
            self.real_callback()

        sw = crd(GameSettings.SCREEN_WIDTH)
        sh = crd(GameSettings.SCREEN_HEIGHT)

        # Refetch evolved name for display
        new_name = self.monster_data.get("name", "Unknown")

        # Position evolved sprite at center
        self.poke_sprite2.rect.center = (sw // 2, sh // 2 - 50)

        # Background panel stays off-screen (don't slide back up)

        self.msg_text.change_text(
            f"Congratulations! {self.msg_name} evolved into {new_name}!", pos="center"
        )
        self.msg_text.rect.centerx = sw // 2
        self.msg_text.rect.bottom = sh - 50

        # Show evolved sprite, hide original
        self.show_poke1_sprite = False
        self.show_poke2_sprite = True
        self.state = self.STATE_SUCCESS
        self.tween_time = 0.0

    def _on_animation_finish(self):
        """Called when star animation ends - now just a passthrough."""
        # The actual finish is now handled by STATE_FADING
        pass

    def draw(self, screen: pg.Surface) -> None:
        """Draw."""
        if not self.is_open:
            return

        if self.overlay_alpha is not None:
            screen.blit(self._get_dark_overlay(), (0, 0))

        # Draw background elements (Panel)
        for b in self.backgrounds:
            b.draw(screen)

        # Draw interactive components
        for c in self.active_components:
            c.draw(screen)

        # Draw passive components (Sprites, Texts)
        for t in self.components:
            if t == self.poke_sprite:
                if getattr(self, "show_poke1_sprite", True):
                    t.draw(screen)
            elif t == self.poke_sprite2:
                if getattr(self, "show_poke2_sprite", False):
                    t.draw(screen)
            else:
                t.draw(screen)

        for t in self.components2:
            t.draw(screen)

        self.draw_content(screen)

        # Screen Flash Overlay
        if self.flash_alpha > 0:
            if (
                self.flash_surface is None
                or self.flash_surface.get_size() != screen.get_size()
            ):
                self.flash_surface = pg.Surface(screen.get_size())
                self.flash_surface.fill((255, 255, 255))

            self.flash_surface.set_alpha(self.flash_alpha)
            screen.blit(self.flash_surface, (0, 0))

    def draw_content(self, screen: pg.Surface):
        # Draw star animation if evolving
        if self.state == self.STATE_EVOLVING:
            self.star_anim.draw(screen)
