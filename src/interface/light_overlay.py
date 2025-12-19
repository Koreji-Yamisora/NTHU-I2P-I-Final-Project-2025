import pygame as pg
from src.utils import GameSettings, PositionCamera, Position
from src.core.gm_helper import gh

class LightOverlay:
    """Manages day/night cycle and light rendering."""
    
    def __init__(self):
        self.cycle_duration = 120.0  # 2 minutes full cycle
        self.timer = 0.0
        # Stages: (time_fraction, color_rgba)
        # Night -> Dawn -> Day -> Dusk -> Evening -> Night
        self.stages = [
            (0.0, (20, 20, 50, 210)),    # Night (Deep Blue/Black)
            (0.2, (50, 40, 60, 100)),    # Dawn (Purplish, fading darkness)
            (0.3, (255, 255, 255, 0)),   # Day (No darkness)
            (0.7, (255, 255, 255, 0)),   # Day continues
            (0.8, (200, 100, 50, 100)),  # Dusk (Orange/Red tint)
            (0.9, (40, 30, 60, 180)),    # Evening (Darkening)
        ]
        self.darkness = pg.Surface(
            (GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), 
            pg.SRCALPHA
        )

    def update(self, dt: float):
        """Update cycle timer."""
        self.timer = (self.timer + dt) % self.cycle_duration

    def get_current_color(self) -> tuple[int, int, int, int]:
        """Calculate current ambient color based on cycle time."""
        # Find current stage index
        current_time_frac = self.timer / self.cycle_duration
        
        idx = 0
        for i in range(len(self.stages) - 1):
            if self.stages[i][0] <= current_time_frac < self.stages[i+1][0]:
                idx = i
                break
        else:
            # Wrap around case (Evening -> Night)
            idx = len(self.stages) - 1
            
        start_frac, start_color = self.stages[idx]
        end_frac, end_color = self.stages[(idx + 1) % len(self.stages)]
        
        # Handle wrap around calculation
        if end_frac < start_frac:
            end_frac += 1.0
            
        if current_time_frac < start_frac:
            current_time_frac += 1.0

        # Lerp factor
        t = (current_time_frac - start_frac) / (end_frac - start_frac)
        t = max(0.0, min(1.0, t))

        # Linear interpolation
        r = int(start_color[0] + (end_color[0] - start_color[0]) * t)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * t)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * t)
        a = int(start_color[3] + (end_color[3] - start_color[3]) * t)
        
        return (r, g, b, a)

    def draw(self, screen: pg.Surface, camera: PositionCamera):
        """Draw darkness and lights."""
        # fill darkness
        try:
            color = self.get_current_color()
            if color[3] <= 5: # Optimization: Don't draw if fully bright
                 return

            self.darkness.fill(color)

            # Draw lights (subtract alpha from darkness)
            # 1. Player light
            if gh.gm and gh.gm.player:
                p_rect = camera.transform_rect(gh.gm.player.animation.rect)
                center = p_rect.center
                self._draw_light(self.darkness, center, 150)

            # 2. Map lights
            if gh.gm and gh.gm.current_map and hasattr(gh.gm.current_map, "lights"):
                 for light_pos in gh.gm.current_map.lights:
                    screen_pos = camera.transform_position(light_pos)
                    # Optimization: Only draw if on screen
                    if (0 <= screen_pos[0] <= GameSettings.SCREEN_WIDTH and 
                        0 <= screen_pos[1] <= GameSettings.SCREEN_HEIGHT):
                        self._draw_light(self.darkness, screen_pos, 120)

            screen.blit(self.darkness, (0, 0))
        except Exception as e:
            print(f"Error in LightOverlay: {e}")

    def _create_radial_gradient(self, radius: int) -> pg.Surface:
        """Create a smooth radial gradient surface for lighting."""
        # Create a surface twice the radius
        size = radius * 2
        surface = pg.Surface((size, size), pg.SRCALPHA)
        
        # Center of the surface
        cx, cy = radius, radius
        
        # We can simulate a gradient by iterating pixels? No, too slow for Python.
        # We can use large number of circles with float steps? Better.
        # Or generate a numpy array if numpy is available? Project doesn't seem to use numpy.
        # Best purely Pygame way: Draw many concentric circles with very small alpha steps.
        
        # To make it super smooth with pygame draw:
        # 1. Start from outside (radius) to inside (0)
        # 2. Each step increases alpha slightly
        
        # 100 steps is usually enough for a smooth look on a ~150px radius
        steps = 100
        for i in range(steps):
             # 0 to 1
            t = i / steps
            # Invert t: 1 at outside, 0 at inside
            # Gradient falloff: let's use quadratic or linear
            # r goes from radius down to 0
            current_radius = radius * (1 - t)
            
            # Alpha: We want to SUBTRACT darkness.
            # Center should subtract MAX (255). Edge subtracts 0.
            # We are drawing circles on top of each other.
            # If we just draw a solid color with specific alpha, they accumulate?
            # No, standard blit replaces or blends.
            
            # Better approach: Draw ONE circle with a special radial gradient texture created programmatically?
            # Actually, let's just make the "cookie" efficiently.
            pass

        # Since per-pixel manipulation in python is slow, we'll try a simpler stacked circle approach
        # with high step count, which is what the user asked to improve.
        # The key to "blend smoothly" is to just have enough steps and correct alpha math.
        
        # Let's try 255 steps for maximum smoothness (1 pixel radius decrement)
        # But for performance, let's limit to radius size.
        
        # Optimize: create purely additive gradient then use as SUB source
        for r in range(radius, 0, -2): # Step 2 pixels
            # Alpha calculation: standard linear falloff
            # Center (r=0) alpha should be 255. Edge (r=radius) alpha 0.
            # Wait, loop r is current radius.
            # r=radius -> alpha=0
            # r=0 -> alpha=255
            alpha_val = 255 * (1 - (r / radius))
            
            # Using a Quadratic falloff looks more "light-like" (inverse square law approximation)
            # alpha_val = 255 * ((1 - (r / radius)) ** 2)
            
            # We need to compute the *difference* in alpha from the previous larger circle
            # because we are painting over.
            # Actually, if we just draw concentric circles with increasing alpha (and solid color), 
            # painter's algorithm works if we go form outside in? No.
            
            # Correct Pygame "Gradient" hack:
            # Draw concentric circles where each inner circle has slightly higher alpha?
            # If we use SRCALPHA, they blend.
            
            # Let's use the method of drawing separate surfaces with low alpha and adding them?
            # Creating a "cookie" surface:
            # Just iterating pixels is actually fast enough for a ONCE-off texture generation (cached).
            pass
            
        # PIXEL ARRAY APPROACH (Best for smoothness, done ONCE)
        for x in range(size):
            for y in range(size):
                dx = x - cx
                dy = y - cy
                dist_sq = dx*dx + dy*dy
                if dist_sq <= radius*radius:
                    dist = dist_sq ** 0.5
                    norm_dist = dist / radius
                    # Smooth step or quadratic falloff
                    alpha = int(255 * (1 - norm_dist) ** 2)
                    # Set pixel (0,0,0, alpha)
                    # This surface will be used with BLEND_RGBA_SUB, so (0,0,0, alpha) works.
                    surface.set_at((x, y), (0, 0, 0, alpha))
        
        return surface

    def _draw_light(self, surface: pg.Surface, pos: tuple[int, int], radius: int):
        """Draw a weighted light mask."""
        # Check cache
        if not hasattr(self, "_light_cache"):
            self._light_cache = {}
            
        if radius not in self._light_cache:
            self._light_cache[radius] = self._create_radial_gradient(radius)
            
        light_surf = self._light_cache[radius]
        surface.blit(light_surf, (pos[0]-radius, pos[1]-radius), special_flags=pg.BLEND_RGBA_SUB)
