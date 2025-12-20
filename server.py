import asyncio
import json
import time
import threading
from typing import Set, Any
from server.playerHandler import PlayerHandler

from websockets.asyncio.server import serve

PORT = 8989

PLAYER_HANDLER = PlayerHandler()
PLAYER_HANDLER.start()


# ------------------------------
# Simple in-memory chat storage
# ------------------------------
class ChatStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._next_id = 1
        self._messages: list[dict] = []

    def add(self, sender_id: int, text: str) -> dict:
        # Sanitize
        t = (text or "").strip()
        if len(t) > 200:
            t = t[:200]
        if not t:
            raise ValueError("empty")
        with self._lock:
            msg = {
                "id": self._next_id,
                "from": sender_id,
                "text": t,
                "ts": time.time(),
            }
            self._messages.append(msg)
            self._next_id += 1
            # Keep only the last N to avoid unbounded growth
            if len(self._messages) > 1000:
                self._messages = self._messages[-800:]
            return msg

    def list_since(self, since_id: int) -> list[dict]:
        with self._lock:
            if since_id <= 0:
                return list(self._messages[-100:])  # cap response size
            # Find first index with id > since_id
            # Messages are appended in increasing id order
            out: list[dict] = []
            for m in self._messages:
                if int(m.get("id", 0)) > since_id:
                    out.append(m)
            # Cap size
            if len(out) > 200:
                out = out[-200:]
            return out


CHAT = ChatStore()

# Track connected clients
# Map websocket -> player_id for reverse lookup if needed, but primary is just set of sockets
# We actually need a way to target specific players for direct events (PvP)
CONNECTED_CLIENTS: Set[Any] = set()
PLAYER_SOCKETS: dict[int, Any] = {}  # Map player_id -> websocket
CLIENTS_LOCK = asyncio.Lock()


async def broadcast_player_update():
    """Broadcast player list to all connected clients periodically"""
    while True:
        await asyncio.sleep(0.0167)  # 60 updates per second
        players = PLAYER_HANDLER.list_players()
        message = {
            "type": "players_update",
            "players": players,
            "timestamp": time.time(),
        }
        msg_json = json.dumps(message)
        # Broadcast to all connected clients
        disconnected = set()
        async with CLIENTS_LOCK:
            for client in CONNECTED_CLIENTS:
                try:
                    await client.send(msg_json)
                except Exception:
                    disconnected.add(client)
            # Remove disconnected clients
            CONNECTED_CLIENTS.difference_update(disconnected)


async def handle_client(websocket: Any):
    """Handle a WebSocket client connection"""
    player_id = -1

    async with CLIENTS_LOCK:
        CONNECTED_CLIENTS.add(websocket)

    try:
        # Register player on connection - server assigns ID
        player_id = PLAYER_HANDLER.register()

        async with CLIENTS_LOCK:
            PLAYER_SOCKETS[player_id] = websocket

        await websocket.send(json.dumps({"type": "registered", "id": player_id}))

        # Send initial player list
        players = PLAYER_HANDLER.list_players()
        await websocket.send(
            json.dumps(
                {"type": "players_update", "players": players, "timestamp": time.time()}
            )
        )

        # Send recent chat messages
        recent_chat = CHAT.list_since(0)
        await websocket.send(
            json.dumps({"type": "chat_update", "messages": recent_chat})
        )

        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "player_update":
                    # Update player position - use server-assigned ID, ignore client ID
                    x = float(data.get("x", 0))
                    y = float(data.get("y", 0))
                    map_name = str(data.get("map", ""))
                    direction = str(data.get("direction", "DOWN"))
                    skin = int(data.get("skin", 0))
                    moving = bool(data.get("moving", False))

                    # Use the server-assigned player_id, not client-provided
                    PLAYER_HANDLER.update(
                        player_id, x, y, map_name, direction, skin, moving
                    )

                elif msg_type == "chat_send":
                    # Send chat message - use server-assigned ID
                    text = str(data.get("text", ""))
                    if text:
                        try:
                            msg = CHAT.add(player_id, text)  # Use server-assigned ID
                            # Broadcast to all clients
                            chat_msg = {"type": "chat_update", "messages": [msg]}
                            chat_json = json.dumps(chat_msg)
                            async with CLIENTS_LOCK:
                                disconnected = set()
                                for client in CONNECTED_CLIENTS:
                                    try:
                                        await client.send(chat_json)
                                    except Exception:
                                        disconnected.add(client)
                                CONNECTED_CLIENTS.difference_update(disconnected)
                        except ValueError:
                            await websocket.send(
                                json.dumps(
                                    {"type": "error", "message": "empty_message"}
                                )
                            )

                elif msg_type == "direct_event":
                    # Forward a direct event to another player (e.g. PvP action)
                    target_id = int(data.get("target_id", -1))
                    event_data = data.get("data", {})

                    if target_id != -1:
                        target_socket = None
                        async with CLIENTS_LOCK:
                            target_socket = PLAYER_SOCKETS.get(target_id)

                        if target_socket:
                            # Forward the event
                            forward_msg = {
                                "type": "direct_event",
                                "from": player_id,
                                "data": event_data,
                            }
                            try:
                                await target_socket.send(json.dumps(forward_msg))
                                # Ack to sender
                                await websocket.send(
                                    json.dumps(
                                        {
                                            "type": "event_sent",
                                            "success": True,
                                            "target": target_id,
                                        }
                                    )
                                )
                            except Exception:
                                await websocket.send(
                                    json.dumps(
                                        {
                                            "type": "event_sent",
                                            "success": False,
                                            "error": "send_failed",
                                        }
                                    )
                                )
                        else:
                            await websocket.send(
                                json.dumps(
                                    {
                                        "type": "event_sent",
                                        "success": False,
                                        "error": "target_not_found",
                                    }
                                )
                            )

            except json.JSONDecodeError:
                await websocket.send(
                    json.dumps({"type": "error", "message": "invalid_json"})
                )
            except Exception as e:
                await websocket.send(json.dumps({"type": "error", "message": str(e)}))

    except Exception as e:
        print(f"[Server] Client handler error: {e}")
    finally:
        # Unregister player on disconnect
        if player_id >= 0:
            PLAYER_HANDLER.unregister(player_id)
            async with CLIENTS_LOCK:
                if player_id in PLAYER_SOCKETS:
                    del PLAYER_SOCKETS[player_id]
        async with CLIENTS_LOCK:
            CONNECTED_CLIENTS.discard(websocket)


async def main():
    print(f"[Server] Running WebSocket server on ws://0.0.0.0:{PORT}")
    # Start broadcast task
    asyncio.create_task(broadcast_player_update())
    # Start server
    async with serve(handle_client, "0.0.0.0", PORT):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Server] Stopped by user")
