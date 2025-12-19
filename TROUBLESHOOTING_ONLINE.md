# Troubleshooting: Players Not Seeing Each Other

## Quick Diagnostic Steps

### 1. Check Server is Running
```bash
# Start server in one terminal
cd /Users/wenxin/NTHU-I2P-I-Final-Project-2025
uv run server.py
```

You should see: `[Server] Running WebSocket server on ws://0.0.0.0:8989`

### 2. Test Connection
```bash
# In another terminal, run diagnostic
uv run diagnose_online.py
```

This will show:
- ✓ If connection works
- ✓ If you get registered
- ✓ If other players' data is received

### 3. Check Game Logs
When running the game (with DEBUG=True), look for these log messages:

**Good signs:**
```
[ONLINE] Found 1 online players
[ONLINE] Processing player 2 at (1024.0, 512.0) on map map.tmx
[ONLINE] Drawing 1 online player(s)
```

**Bad signs:**
```
[ONLINE] Skipping player X - different map
```
This means players are on different maps!

### 4. Common Issues & Fixes

#### Issue: "No players found"
- **Cause**: Server not running or not connected
- **Fix**: Make sure server.py is running first

#### Issue: "Skipping player - different map"
- **Cause**: Players spawned on different maps
- **Fix**: Make sure both game instances load the same map (check saves/game0.json)

#### Issue: "Players found but not drawing"
- **Cause**: Missing animation assets or camera issue
- **Fix**: Check that character/ow*.png files exist

#### Issue: "Connection failed"
- **Cause**: Wrong server URL
- **Fix**: Check `src/utils/settings.py` - IS_ONLINE should be True, ONLINE_SERVER_URL should be "http://localhost:8989"

### 5. Enable Debug Logging
In `src/utils/settings.py`:
```python
DEBUG: bool = True  # Make sure this is True!
```

### 6. Test with Two Game Instances
```bash
# Terminal 1: Server
uv run server.py

# Terminal 2: Game Instance 1
uv run main.py

# Terminal 3: Game Instance 2 (different save file)
# First, copy the save file
cp saves/game0.json saves/game1.json
# Then modify code to load game1.json or update gm_helper.py path

# Or just use the same save and both will spawn at same position
uv run main.py
```

Both instances should spawn on the same map at roughly same position initially.
