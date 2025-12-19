from __future__ import annotations
import pygame as pg
from typing import Optional, Callable, List, Dict
from src.interface.components.component import UIComponent
from src.core.services import input_manager
from src.utils import Logger, color


class ChatOverlay(UIComponent):
    """Lightweight chat UI similar to Minecraft: toggle with a key, type, press Enter to send."""

    is_open: bool
    _input_text: str
    _cursor_timer: float
    _cursor_visible: bool
    _just_opened: bool
    _send_callback: Callable[[str], bool] | None
    _get_messages: Callable[[int], list[dict]] | None
    _font_msg: pg.font.Font
    _font_input: pg.font.Font
    _error_msg: str = ""
    _error_timer: float = 0.0

    def __init__(
        self,
        send_callback: Callable[[str], bool] | None = None,
        get_messages: Callable[[int], list[dict]] | None = None,
        *,
        font_path: str = None,
    ) -> None:
        self.is_open = False
        self._input_text = ""
        self._cursor_timer = 0.0
        self._cursor_visible = True
        self._just_opened = False
        self._send_callback = send_callback
        self._get_messages = get_messages

        try:
            self._font_msg = pg.font.Font(font_path, 16)
            self._font_input = pg.font.Font(font_path, 20)
        except Exception:
            Logger.warning(f"Failed to load font {font_path}, using default SysFont.")
            self._font_msg = pg.font.SysFont("arial", 16)
            self._font_input = pg.font.SysFont("arial", 20)

    def open(self, initial_text: str = "") -> None:
        if not self.is_open:
            self.is_open = True
            self._cursor_timer = 0.0
            self._cursor_visible = True
            self._just_opened = True
            self._input_text = initial_text

    def close(self) -> None:
        self.is_open = False

    def _handle_typing(self) -> None:
        """
        Turn keyboard keys into characters that appear inside the chat box.
        """
        shift = input_manager.key_down(pg.K_LSHIFT) or input_manager.key_down(
            pg.K_RSHIFT
        )

        # Letters A-Z
        for k in range(pg.K_a, pg.K_z + 1):
            if input_manager.key_pressed(k):
                ch = chr(ord("a") + (k - pg.K_a))
                self._input_text += ch.upper() if shift else ch

        # Numbers 0-9
        for k in range(pg.K_0, pg.K_9 + 1):
            if input_manager.key_pressed(k):
                ch = str(k - pg.K_0)
                # Simple shift logic for standard US layout (approximate)
                if shift:
                    symbols = {
                        pg.K_1: "!",
                        pg.K_2: "@",
                        pg.K_3: "#",
                        pg.K_4: "$",
                        pg.K_5: "%",
                        pg.K_6: "^",
                        pg.K_7: "&",
                        pg.K_8: "*",
                        pg.K_9: "(",
                        pg.K_0: ")",
                    }
                    ch = symbols.get(k, ch)
                self._input_text += ch

        # Space
        if input_manager.key_pressed(pg.K_SPACE):
            self._input_text += " "

        # Punctuation
        # Map key -> (normal, shifted)
        punctuation_map = {
            pg.K_SLASH: ("/", "?"),
            pg.K_PERIOD: (".", ">"),
            pg.K_COMMA: (",", "<"),
            pg.K_SEMICOLON: (";", ":"),
            pg.K_QUOTE: ("'", '"'),
            pg.K_LEFTBRACKET: ("[", "{"),
            pg.K_RIGHTBRACKET: ("]", "}"),
            pg.K_BACKSLASH: ("\\", "|"),
            pg.K_MINUS: ("-", "_"),
            pg.K_EQUALS: ("=", "+"),
            pg.K_BACKQUOTE: ("`", "~"),
        }
        for k, (normal, shifted) in punctuation_map.items():
            if input_manager.key_pressed(k):
                self._input_text += shifted if shift else normal

        # Backspace
        if input_manager.key_pressed(pg.K_BACKSPACE):
            if len(self._input_text) > 0:
                self._input_text = self._input_text[:-1]

        # Enter to send
        if input_manager.key_pressed(pg.K_RETURN) or input_manager.key_pressed(
            pg.K_KP_ENTER
        ):
            txt = self._input_text.strip()
            if txt and self._send_callback:
                ok = False
                try:
                    ok = self._send_callback(txt)
                except Exception as e:
                    Logger.error(f"Chat send error: {e}")
                    ok = False

                if ok:
                    self._input_text = ""
                    self.close()
                else:
                    self._error_msg = "Send Failed (Not Connected?)"
                    self._error_timer = 3.0
                    Logger.warning("Chat send failed")

    def update(self, dt: float) -> None:
        if not self.is_open:
            return

        # Close on Escape
        if input_manager.key_pressed(pg.K_ESCAPE):
            self.close()
            return

        # Typing
        if self._just_opened:
            self._just_opened = False
        else:
            self._handle_typing()

        # Cursor blink
        self._cursor_timer += dt
        if self._cursor_timer >= 0.5:
            self._cursor_timer = 0.0
            self._cursor_visible = not self._cursor_visible

        # Error timer
        if self._error_timer > 0:
            self._error_timer -= dt
            if self._error_timer < 0:
                self._error_timer = 0.0

    def draw(self, screen: pg.Surface) -> None:
        # Always draw recent messages faintly, even when closed
        msgs = self._get_messages(8) if self._get_messages else []
        sw, sh = screen.get_size()
        x = 10
        y = sh - 100

        # Draw background for messages if there are any
        if msgs:
            container_w = max(100, int((sw - 20) * 0.6))
            # Calculate height based on number of messages?
            # Original code hardcoded 90 height for ~8 messages?
            # 8 messages * (~20px) = 160px. 90 seems small for 8 lines.
            # Let's trust logic provided or adapt dynamic height?
            # Provided: "bg = pg.Surface((container_w, 90), pg.SRCALPHA)"
            # Let's keep specific logic from prompt but maybe safely adjust if needed.
            # Actually, let's stick to the prompt's intended logic.

            bg = pg.Surface((container_w, 90), pg.SRCALPHA)
            bg.fill((0, 0, 0, 90 if self.is_open else 60))
            _ = screen.blit(bg, (x, y))

            # Render last messages
            # Logic: lines = list(msgs)[-8:] means take last 8.
            lines = list(msgs)[-8:]
            draw_y = y + 8
            for m in lines:
                sender = str(m.get("from", ""))
                text = str(m.get("text", ""))
                # Render text
                try:
                    surf = self._font_msg.render(
                        f"{sender}: {text}", True, (255, 255, 255)
                    )
                    _ = screen.blit(surf, (x + 10, draw_y))
                    draw_y += surf.get_height() + 4
                except Exception:
                    pass

        # If not open, skip input field
        if not self.is_open:
            return

        # Input box
        box_h = 28
        box_w = max(100, int((sw - 20) * 0.6))
        # Place it below messages? Or overlay?
        # Prompt: "y = sh - 100" (message top). Messages draw down.
        # "box_y = sh - box_h - 6" -> This puts input box at very bottom.
        box_y = sh - box_h - 6

        # Background box
        bg2 = pg.Surface((box_w, box_h), pg.SRCALPHA)
        bg2.fill((0, 0, 0, 160))
        _ = screen.blit(bg2, (x, box_y))

        # Text
        txt_to_render = self._input_text
        text_surf = self._font_input.render(txt_to_render, True, (255, 255, 255))
        _ = screen.blit(text_surf, (x + 8, box_y + 4))

        # Caret
        if self._cursor_visible:
            cx = x + 8 + text_surf.get_width() + 2
            cy = box_y + 6
            pg.draw.rect(screen, (255, 255, 255), pg.Rect(cx, cy, 2, box_h - 12))

        # Error Message
        if self._error_timer > 0:
            err_surf = self._font_msg.render(self._error_msg, True, (255, 50, 50))
            screen.blit(err_surf, (x, box_y - 20))
