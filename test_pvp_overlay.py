import sys
import os
import pygame as pg

# Add project root to path
sys.path.append(os.getcwd())

# Initialize Pygame mock/real
pg.init()
pg.font.init()

# Setup display for asset loading
screen = pg.display.set_mode((1710, 962))

from src.utils import GameSettings, Logger
from src.interface.overlay_battle_request import BattleRequestOverlay

def test_overlay():
    print("=== Testing BattleRequestOverlay ===")
    
    # Mock callbacks
    def on_accept(id):
        print(f"Accepted request from {id}")
        
    def on_decline():
        print("Declined request")
        
    try:
        print("Initializing overlay...")
        overlay = BattleRequestOverlay(999, on_accept, on_decline)
        print("✓ Overlay initialized successfully")
        
        print("Opening overlay...")
        overlay.open()
        print(f"✓ Overlay opened (is_open={overlay.is_open})")
        
        print("Updating overlay...")
        overlay.update(0.16)
        print("✓ Overlay updated")
        
        print("Drawing overlay...")
        overlay.draw(screen)
        pg.display.flip()
        print("✓ Overlay drawn")
        
        print("\nAll PvP Overlay tests passed!")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_overlay()
