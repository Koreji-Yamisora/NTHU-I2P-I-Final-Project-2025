import xml.etree.ElementTree as ET
import sys

map_path = "assets/maps/data/maps/world.tmx"
try:
    tree = ET.parse(map_path)
    root = tree.getroot()
except Exception as e:
    print(f"Error parsing {map_path}: {e}")
    sys.exit(1)

print(f"Parsed {map_path}")

objects = []
for group in root.findall(".//objectgroup"):
    for obj in group.findall("object"):
        name = obj.get("name", "Unnamed")
        x = float(obj.get("x", 0))
        y = float(obj.get("y", 0))
        objects.append({"name": name, "x": x, "y": y})

# Sort by X + Y desc
objects.sort(key=lambda o: o["x"] + o["y"], reverse=True)

print("Top 10 objects by lower-right position:")
for o in objects[:10]:
    print(f"Name: {o['name']}, X: {o['x']}, Y: {o['y']}")

# Also search for 'spawn' explicitly
spawns = [o for o in objects if "spawn" in o["name"].lower()]
if spawns:
    print("\nFound explicit 'spawn' objects:")
    for s in spawns:
        print(f"Name: {s['name']}, X: {s['x']}, Y: {s['y']}")
else:
    print("\nNo objects with 'spawn' in name found.")
