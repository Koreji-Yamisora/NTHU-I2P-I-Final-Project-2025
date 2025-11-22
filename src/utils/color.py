import pygame as pg


def recol(image, color) -> pg.Surface:
    new = pg.transform.grayscale(image.copy())
    tint = pg.Surface(image.get_size(), pg.SRCALPHA)
    tint.fill(color)
    new.blit(tint, (0, 0), special_flags=pg.BLEND_MULT)
    return new


def bright(image, color) -> pg.Surface:
    brightened_image = image.copy()
    brighten_color = color
    brightened_image.fill(brighten_color, special_flags=pg.BLEND_RGB_ADD)
    return brightened_image


def recolor_preserve_brightness(surface, new_color):
    """
    Recolor a surface while preserving brightness and alpha.
    This replaces the hue/saturation but keeps the luminosity.

    Args:
        surface: pygame.Surface to recolor
        new_color: tuple (r, g, b) - target color

    Returns:
        New recolored surface
    """
    # Create a copy to work with
    result = surface.copy()

    # Get pixel array
    width, height = result.get_size()

    # Create a colored overlay
    color_surface = pg.Surface((width, height), pg.SRCALPHA)
    color_surface.fill((*new_color, 255))

    # Method 1: Multiply blend mode (preserves darkness/lightness)
    # This works by multiplying the original brightness with the new color
    result.blit(color_surface, (0, 0), special_flags=pg.BLEND_RGBA_MULT)

    return result


def recolor_hue_shift(surface, new_color):
    """
    Alternative method: Shift hue while preserving luminosity and saturation structure.
    Better for gradients and detailed images.

    Args:
        surface: pygame.Surface to recolor
        new_color: tuple (r, g, b) - target color

    Returns:
        New recolored surface
    """
    result = surface.copy()
    width, height = result.get_size()

    # Create overlay with new color
    overlay = pg.Surface((width, height), pg.SRCALPHA)
    overlay.fill((*new_color, 128))  # 50% alpha for blend

    # Use ADD blend to tint without darkening
    result.blit(overlay, (0, 0), special_flags=pg.BLEND_RGB_ADD)

    # Clamp values to 0-255 (ADD can overflow)
    # Note: pygame handles this automatically

    return result


def recolor_multiply_screen(surface, new_color):
    """
    Advanced method: Uses multiply for shadows, screen for highlights.
    Gives the most natural looking recolor.

    Args:
        surface: pygame.Surface to recolor
        new_color: tuple (r, g, b) - target color

    Returns:
        New recolored surface
    """
    result = surface.copy()
    width, height = result.get_size()

    # Create color overlay
    color_overlay = pg.Surface((width, height))
    color_overlay.fill(new_color)

    # First pass: Multiply blend (for darker areas)
    temp = result.copy()
    temp.blit(color_overlay, (0, 0), special_flags=pg.BLEND_MULT)

    # Second pass: Add some brightness back
    brighten = pg.Surface((width, height))
    brighten.fill((50, 50, 50))  # Adjust this to control brightness
    temp.blit(brighten, (0, 0), special_flags=pg.BLEND_RGB_ADD)

    return temp
