import asyncio
import threading
import time
import subprocess
import sys
import os

# Ensure we can import from src
sys.path.append(os.getcwd())

from src.core.managers.online_manager import OnlineManager

def run_server():
    """Run server in a separate process"""
    # Use 'uv run' to ensure dependencies are available
    cmd = ["uv", "run", "server.py"]
    return subprocess.Popen(cmd)

async def test_flow():
    print("--- Starting Online Flow Test ---")
    
    # 1. Start Server
    server_process = run_server()
    print("Server started...")
    time.sleep(2) # Give server time to start

    try:
        # 2. Start Client A
        client_a = OnlineManager()
        client_a.start()
        print("Client A started...")
        
        # 3. Start Client B
        client_b = OnlineManager()
        client_b.start()
        print("Client B started...")
        
        # Wait for registration
        timeout = 5
        start = time.time()
        while (client_a.player_id == -1 or client_b.player_id == -1):
            if time.time() - start > timeout:
                print("Timeout waiting for registration")
                return
            await asyncio.sleep(0.1)
            
        print(f"Client A ID: {client_a.player_id}")
        print(f"Client B ID: {client_b.player_id}")

        # 4. Setup Event Listener on Client B
        received_event = []
        def on_event(data):
            print(f"Client B received event: {data}")
            received_event.append(data)
        
        client_b.register_event_callback(on_event)

        # 5. Client A sends event to Client B
        event_payload = {"type": "attack", "damage": 10}
        print(f"Client A sending event to {client_b.player_id}...")
        success = client_a.send_event(client_b.player_id, event_payload)
        
        if not success:
            print("Failed to queue event from Client A")
        
        # 6. Wait for event
        start = time.time()
        while not received_event:
            if time.time() - start > timeout:
                print("Timeout waiting for event")
                break
            await asyncio.sleep(0.1)
        
        # Verify visual sync (Client A updated position, did Client B receive it?)
        # We need to expose internal list_players to verify
        print("Verifying visual sync...")
        players_b = client_b.get_list_players()
        a_in_b = next((p for p in players_b if p['id'] == client_a.player_id), None)
        
        if a_in_b:
             print(f"Client A found in Client B's list: {a_in_b}")
             if "direction" in a_in_b and "skin" in a_in_b:
                  print("SUCCESS: Visual fields present.")
             else:
                  print("FAILURE: Visual fields missing.")
        else:
             print("FAILURE: Client A not found in Client B.")
             
        if received_event:
            print("SUCCESS: Event received!")
        else:
            print("FAILURE: Event not received.")

        # 7. Test Chat
        print("Testing Chat...")
        client_a.send_chat("Hello from A")
        await asyncio.sleep(1)
        chats = client_b.get_recent_chat()
        if any(c['text'] == "Hello from A" for c in chats):
             print("SUCCESS: Chat received!")
        else:
             print("FAILURE: Chat not received.")

    finally:
        if 'client_a' in locals(): client_a.stop()
        if 'client_b' in locals(): client_b.stop()
        server_process.terminate()
        server_process.wait()
        print("Test finished.")

if __name__ == "__main__":
    asyncio.run(test_flow())
