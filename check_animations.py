import pytmx
import os


def check_animations():
    try:
        path = "assets/maps/map.tmx"
        print(f"Loading {path}...")
        tmxdata = pytmx.util_pygame.load_pygame(path)

        animated_tiles = []
        for gid, props in tmxdata.tile_properties.items():
            if "frames" in props:
                animated_tiles.append((gid, props["frames"]))

        print(f"Found {len(animated_tiles)} animated tiles.")
        for gid, frames in animated_tiles:
            print(f"GID: {gid}, Frames: {frames}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    check_animations()
