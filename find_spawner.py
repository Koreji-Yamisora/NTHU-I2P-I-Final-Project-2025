import pytmx
import os

map_path = "assets/maps/data/maps/world.tmx"

if not os.path.exists(map_path):
    print(f"Error: {map_path} not found")
    exit(1)

tmxdata = pytmx.load_pygame(map_path)
print(f"Loaded {map_path} ({tmxdata.width}x{tmxdata.height} tiles)")

spawners = []

for layer in tmxdata.visible_layers:
    if isinstance(layer, pytmx.TiledObjectGroup):
        for obj in layer:
            if obj.name and "spawn" in obj.name.lower():
                print(
                    f"Found '{obj.name}' at ({obj.x}, {obj.y}) in layer '{layer.name}'"
                )
                spawners.append(obj)

if not spawners:
    print("No objects found with 'spawn' in name.")
else:
    # Sort by X + Y to find "lower right" roughly
    # Or just X and Y
    spawners.sort(key=lambda o: o.x + o.y, reverse=True)
    best = spawners[0]
    print(f"Lower-right-most spawner: '{best.name}' at ({best.x}, {best.y})")
