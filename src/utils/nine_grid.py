import pygame as pg

class NineGrid:
    def __init__(self, image: pg.Surface, left: int = 0, right: int = 0, top: int = 0, bottom: int = 0):
        """
        Initialize the NineGrid with a source image and slice margins.
        
        Args:
            image (pg.Surface): The source image.
            left (int): Left margin width.
            right (int): Right margin width.
            top (int): Top margin height.
            bottom (int): Bottom margin height.
        """
        self.image = image
        self.width = image.get_width()
        self.height = image.get_height()
        
        # If no margins are provided, assume 1/3 split for all sides
        if left == 0 and right == 0 and top == 0 and bottom == 0:
            self.left = self.width // 3
            self.right = self.width // 3
            self.top = self.height // 3
            self.bottom = self.height // 3
        else:
            self.left = left
            self.right = right
            self.top = top
            self.bottom = bottom
            
        self.center_width = max(0, self.width - self.left - self.right)
        self.center_height = max(0, self.height - self.top - self.bottom)
        
        # Pre-slice the image into 9 parts
        self.parts = {
            'top_left': None, 'top_center': None, 'top_right': None,
            'mid_left': None, 'mid_center': None, 'mid_right': None,
            'bottom_left': None, 'bottom_center': None, 'bottom_right': None
        }
        
        # Helper to safely get subsurface
        def get_sub(x, y, w, h):
            if w > 0 and h > 0:
                return image.subsurface((x, y, w, h))
            return None

        # Row 1 (Top)
        if self.top > 0:
            self.parts['top_left'] = get_sub(0, 0, self.left, self.top)
            self.parts['top_center'] = get_sub(self.left, 0, self.center_width, self.top)
            self.parts['top_right'] = get_sub(self.width - self.right, 0, self.right, self.top)
        
        # Row 2 (Middle)
        if self.center_height > 0:
            self.parts['mid_left'] = get_sub(0, self.top, self.left, self.center_height)
            self.parts['mid_center'] = get_sub(self.left, self.top, self.center_width, self.center_height)
            self.parts['mid_right'] = get_sub(self.width - self.right, self.top, self.right, self.center_height)
        
        # Row 3 (Bottom)
        if self.bottom > 0:
            self.parts['bottom_left'] = get_sub(0, self.height - self.bottom, self.left, self.bottom)
            self.parts['bottom_center'] = get_sub(self.left, self.height - self.bottom, self.center_width, self.bottom)
            self.parts['bottom_right'] = get_sub(self.width - self.right, self.height - self.bottom, self.right, self.bottom)

    def draw(self, surface: pg.Surface, rect: pg.Rect | tuple | list):
        """
        Draw the 9-sliced image onto the target surface at the given rect.
        
        Args:
            surface (pg.Surface): Destination surface.
            rect (pg.Rect | tuple | list): Destination rectangle (x, y, width, height).
        """
        if isinstance(rect, (tuple, list)):
            x, y, w, h = rect
        else:
            x, y, w, h = rect.x, rect.y, rect.width, rect.height
            
        # Determine effective margin sizes (scaling down if target is too small)
        scale_x = 1.0
        if w < self.left + self.right:
            scale_x = w / (self.left + self.right)
            
        scale_y = 1.0
        if h < self.top + self.bottom:
            scale_y = h / (self.top + self.bottom)
            
        eff_left = int(self.left * scale_x)
        eff_right = int(self.right * scale_x)
        eff_top = int(self.top * scale_y)
        eff_bottom = int(self.bottom * scale_y)
        
        # Ensure we don't exceed width/height due to rounding
        if eff_left + eff_right > w:
            eff_right = w - eff_left
        if eff_top + eff_bottom > h:
            eff_bottom = h - eff_top

        # Calculate dimensions for the center and edges
        target_center_w = max(0, w - eff_left - eff_right)
        target_center_h = max(0, h - eff_top - eff_bottom)
        
        # Draw corners
        # Top Left
        if self.parts['top_left']:
            img = self.parts['top_left']
            if scale_x < 1.0 or scale_y < 1.0:
                img = pg.transform.scale(img, (eff_left, eff_top))
            surface.blit(img, (x, y))
            
        # Top Right
        if self.parts['top_right']:
            img = self.parts['top_right']
            if scale_x < 1.0 or scale_y < 1.0:
                img = pg.transform.scale(img, (eff_right, eff_top))
            surface.blit(img, (x + w - eff_right, y))
            
        # Bottom Left
        if self.parts['bottom_left']:
            img = self.parts['bottom_left']
            if scale_x < 1.0 or scale_y < 1.0:
                img = pg.transform.scale(img, (eff_left, eff_bottom))
            surface.blit(img, (x, y + h - eff_bottom))
            
        # Bottom Right
        if self.parts['bottom_right']:
            img = self.parts['bottom_right']
            if scale_x < 1.0 or scale_y < 1.0:
                img = pg.transform.scale(img, (eff_right, eff_bottom))
            surface.blit(img, (x + w - eff_right, y + h - eff_bottom))
        
        # Draw top and bottom edges (scale horizontally)
        if target_center_w > 0:
            if self.parts['top_center']:
                top_edge = pg.transform.scale(self.parts['top_center'], (target_center_w, eff_top))
                surface.blit(top_edge, (x + eff_left, y))
            if self.parts['bottom_center']:
                bottom_edge = pg.transform.scale(self.parts['bottom_center'], (target_center_w, eff_bottom))
                surface.blit(bottom_edge, (x + eff_left, y + h - eff_bottom))
            
        # Draw left and right edges (scale vertically)
        if target_center_h > 0:
            if self.parts['mid_left']:
                left_edge = pg.transform.scale(self.parts['mid_left'], (eff_left, target_center_h))
                surface.blit(left_edge, (x, y + eff_top))
            if self.parts['mid_right']:
                right_edge = pg.transform.scale(self.parts['mid_right'], (eff_right, target_center_h))
                surface.blit(right_edge, (x + w - eff_right, y + eff_top))
            
        # Draw center (scale both ways)
        if target_center_w > 0 and target_center_h > 0:
            if self.parts['mid_center']:
                center = pg.transform.scale(self.parts['mid_center'], (target_center_w, target_center_h))
                surface.blit(center, (x + eff_left, y + eff_top))
