import json
import sys
import os

sys.path.append(os.path.dirname(__file__))

# Validate if dicts remain identical after json roundtrip
def test_json_integrity():
    mon = {
        "atk": 55,
        "def": 40,
        "hp": 100,
        "type": ["Electric"],
        "level": 5
    }
    
    dumped = json.dumps(mon)
    loaded = json.loads(dumped)
    
    if mon == loaded:
        print("SUCCESS: JSON roundtrip preserves exact values.")
    else:
        print("FAILURE: JSON roundtrip altered values.")
        print(f"Original: {mon}")
        print(f"Loaded: {loaded}")

if __name__ == "__main__":
    test_json_integrity()
