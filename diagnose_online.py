#!/usr/bin/env python3
"""
Quick diagnostic to check if online manager is receiving player data.
Run this while the game is running to see what data is being received.
"""

import sys
import os
sys.path.append(os.getcwd())

from src.core.managers.online_manager import OnlineManager
from src.utils.settings import GameSettings
import time
import asyncio

async def diagnose():
    print("=== Online Player Diagnostic ===")
    print(f"Server URL: {GameSettings.ONLINE_SERVER_URL}")
    print()
    
    # Create manager
    try:
        manager = OnlineManager()
        print("✓ OnlineManager created")
    except Exception as e:
        print(f"✗ Failed to create OnlineManager: {e}")
        return
    
    # Start connection
    try:
        manager.start()
        print("✓ Connection started")
    except Exception as e:
        print(f"✗ Failed to start connection: {e}")
        return
    
    # Wait for registration
    print("\nWaiting for registration...")
    for i in range(10):
        await asyncio.sleep(0.5)
        if manager.player_id != -1:
            print(f"✓ Registered with ID: {manager.player_id}")
            break
    else:
        print("✗ Failed to register (timeout)")
        manager.stop()
        return
    
    # Monitor for 10 seconds
    print("\nMonitoring for other players (10 seconds)...")
    for i in range(20):
        await asyncio.sleep(0.5)
        players = manager.get_list_players()
        if players:
            print(f"\n[{i * 0.5:.1f}s] Found {len(players)} player(s):")
            for p in players:
                print(f"  - Player {p['id']}: pos=({p['x']:.1f}, {p['y']:.1f}), map='{p['map']}', dir={p.get('direction', '?')}, skin={p.get('skin', '?')}, moving={p.get('moving', '?')}")
        elif i % 4 == 0:
            print(f"[{i * 0.5:.1f}s] No other players yet...")
    
    print("\nStopping...")
    manager.stop()
    print("✓ Diagnostic complete")

if __name__ == "__main__":
    asyncio.run(diagnose())
