import os
# Set dummy video driver before importing pygame
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame as pg
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

try:
    from utils.nine_grid import NineGrid
except ImportError:
    # Try assuming we are in root and simple import works if src is package but it is not
    # adjusting path again
    sys.path.append(os.getcwd())
    from src.utils.nine_grid import NineGrid

def main():
    pg.init()
    
    # Test Case 1: Standard 30x30 image with 10px borders
    print("Test Case 1: Standard 30x30 image")
    src_img = pg.Surface((30, 30))
    src_img.fill((0, 0, 255)) # Center blue
    pg.draw.rect(src_img, (255, 0, 0), (0, 0, 10, 10)) # TL
    
    grid = NineGrid(src_img, left=10, right=10, top=10, bottom=10)
    target_surface = pg.Surface((100, 50))
    grid.draw(target_surface, (0, 0, 100, 50))
    pg.image.save(target_surface, '/Users/wenxin/.gemini/antigravity/brain/44d1ef93-25c6-4f75-92a0-b40b4614992b/nine_grid_test_standard.png')
    
    # Test Case 2: Zero center (20x20 image, 10px borders)
    print("Test Case 2: Zero center 20x20 image")
    src_img_small = pg.Surface((20, 20))
    src_img_small.fill((255, 0, 0)) # Red corners entire thing basically
    
    grid_small = NineGrid(src_img_small, left=10, right=10, top=10, bottom=10)
    
    # Verify internal state
    if grid_small.parts['mid_center'] is None:
        print("PASS: mid_center is None")
    else:
        print("FAIL: mid_center should be None")
        
    target_surface_2 = pg.Surface((100, 50))
    grid_small.draw(target_surface_2, (0, 0, 100, 50))
    pg.image.save(target_surface_2, '/Users/wenxin/.gemini/antigravity/brain/44d1ef93-25c6-4f75-92a0-b40b4614992b/nine_grid_test_zero_center.png')

    print("Test images saved.")

if __name__ == "__main__":
    main()
