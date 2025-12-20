import pygame as pg
import math


class StatsHexagon:
    """
    Hexagon graph that displays base stats.
    Stats are scaled relative to the highest stat (highest = 100%).
    """

    def __init__(self, rect, color=(100, 200, 255)):
        self.rect = rect
        self.color = color
        self.stats = {}
        self.max_stat = 1
        self.animation_progress = 0.0
        self.animating = False

        # Stat Labels
        self.labels = ["HP", "Atk", "Def", "Spe", "SpD", "SpA"]

    def set_stats(self, mon):
        """Set statistics data from a monster dict."""
        # Order: HP (Top), Atk, Def, Spe, SpD, SpA (Clockwise)
        self.stats = {
            "HP": mon.get("hp", 0),
            "Atk": mon.get("atk", 0),
            "Def": mon.get("def", 0),
            "Spe": mon.get("spe", 0),
            "SpD": mon.get("spd", 0),
            "SpA": mon.get("spa", 0),
        }

        # Find the highest stat value for relative scaling
        self.max_stat = max(self.stats.values()) if self.stats.values() else 1
        self.max_stat = max(1, self.max_stat)  # Prevent division by zero

        self.animation_progress = 0.0
        self.animating = True

    def update(self, dt):
        if self.animating:
            self.animation_progress += dt * 3.0  # Fast animation (0.33s)
            if self.animation_progress >= 1.0:
                self.animation_progress = 1.0
                self.animating = False

    def draw(self, surface):
        center = self.rect.center
        radius = min(self.rect.width, self.rect.height) / 2 * 0.8

        # Background Hexagon (webs)
        for scale in [1.0, 0.75, 0.5, 0.25]:
            points = []
            for i in range(6):
                angle = math.radians(60 * i - 90)
                r = radius * scale
                x = center[0] + r * math.cos(angle)
                y = center[1] + r * math.sin(angle)
                points.append((x, y))
            color = (80, 80, 80) if scale == 1.0 else (60, 60, 60)
            pg.draw.polygon(surface, color, points, 1)

        # Draw Labels
        font = pg.font.SysFont("Arial", 16, bold=True)
        for i, label in enumerate(self.labels):
            angle = math.radians(60 * i - 90)
            r = radius * 1.15
            x = center[0] + r * math.cos(angle)
            y = center[1] + r * math.sin(angle)

            txt = font.render(label, True, (200, 200, 200))
            txt_rect = txt.get_rect(center=(x, y))
            surface.blit(txt, txt_rect)

        if not self.stats:
            return

        # Draw Stat Polygon - scaled relative to highest stat
        stat_points = []
        for i, label in enumerate(self.labels):
            val = self.stats.get(label, 0)
            # Scale relative to highest stat (highest = 100%)
            ratio = (val / self.max_stat) * self.animation_progress
            ratio = min(1.0, max(0.05, ratio))  # Clamp with minimum visibility

            angle = math.radians(60 * i - 90)
            r = radius * ratio
            x = center[0] + r * math.cos(angle)
            y = center[1] + r * math.sin(angle)
            stat_points.append((x, y))

        # Draw filled polygon with alpha
        temp_surf = pg.Surface(self.rect.size, pg.SRCALPHA)
        local_points = [
            (p[0] - self.rect.left, p[1] - self.rect.top) for p in stat_points
        ]

        fill_color = (*self.color, 100)
        pg.draw.polygon(temp_surf, fill_color, local_points)
        pg.draw.polygon(temp_surf, self.color, local_points, 2)

        surface.blit(temp_surf, self.rect.topleft)
