import pygame as pg
import os
import sys

# Setup headless environment
os.environ["SDL_VIDEODRIVER"] = "dummy"

# Add project root to path
sys.path.append(os.getcwd())

# Mock resource manager before importing Sprite
from unittest.mock import MagicMock
sys.modules["src.core.services"] = MagicMock()
sys.modules["src.core.services"].resource_manager = MagicMock()

# Create a dummy image
dummy_surface = pg.Surface((100, 100))
dummy_surface.fill((255, 255, 255))
sys.modules["src.core.services"].resource_manager.get_image.return_value = dummy_surface

from src.sprites.sprite import Sprite

def test_nine_grid_sprite_integration():
    pg.init()
    screen = pg.Surface((800, 600))
    
    print("Testing Sprite with nine_grid_margins...")
    
    # 1. Initialize Sprite with margins
    s = Sprite("dummy_path", (200, 200), nine_grid_margins=(10, 10, 10, 10))
    
    # Check if NineGrid is initialized
    if s.nine_grid is None:
        print("FAIL: Sprite.nine_grid should be initialized when margins are provided.")
        return
    else:
        print("PASS: Sprite.nine_grid is initialized.")
        
    # Check rect size
    if s.rect.size != (200, 200):
        print(f"FAIL: Sprite.rect size mismatch. Expected (200, 200), got {s.rect.size}")
        return
    else:
        print("PASS: Sprite.rect size is correct.")
        
    # 2. Draw
    try:
        s.draw(screen)
        print("PASS: Sprite.draw() executed without error.")
    except Exception as e:
        print(f"FAIL: Sprite.draw() raised exception: {e}")
        return

    # 3. Initialize Sprite WITHOUT margins (regression test)
    print("\nTesting Sprite WITHOUT margins...")
    s_normal = Sprite("dummy_path", (50, 50))
    
    if s_normal.nine_grid is not None:
        print("FAIL: Sprite.nine_grid should be None when margins are NOT provided.")
        return
    else:
        print("PASS: Sprite.nine_grid is correctly None.")
        
    if s_normal.rect.size != (50, 50):
         print(f"FAIL: Normal Sprite rect size mismatch. Expected (50, 50), got {s_normal.rect.size}")
         return
    else:
        print("PASS: Normal Sprite rect size is correct.")

    print("\nALL TESTS PASSED!")

if __name__ == "__main__":
    test_nine_grid_sprite_integration()
