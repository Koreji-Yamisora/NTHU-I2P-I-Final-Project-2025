import pytmx
import os


def check_coast(path="assets/maps/map.tmx"):
    try:
        if not os.path.exists(path):
            print(f"File not found: {path}")
            return

        print(f"Loading {path}...")
        tmxdata = pytmx.util_pygame.load_pygame(path)

        found_coast = False
        for layer in tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledObjectGroup):
                print(f"Checking Object Layer: {layer.name}")
                for obj in layer:
                    if "side" in obj.properties:
                        print(
                            f"Found object with 'side': {obj.name} - Side: {obj.properties['side']} at ({obj.x}, {obj.y})"
                        )
                        found_coast = True
                    # Also check if name contains 'coast' just in case
                    if obj.name and "coast" in obj.name.lower():
                        print(
                            f"Found object with name 'coast': {obj.name} at ({obj.x}, {obj.y})"
                        )
                        found_coast = True

        if not found_coast:
            print("No objects with 'side' property or 'coast' name found.")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    check_coast()
