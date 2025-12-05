import pygame as pg


def recol(image, color) ->pg.Surface:
    """Recol."""
    new = pg.transform.grayscale(image.copy())
    tint = pg.Surface(image.get_size(), pg.SRCALPHA)
    tint.fill(color)
    new.blit(tint, (0, 0), special_flags=pg.BLEND_MULT)
    return new


def bright(image, color) ->pg.Surface:
    """Bright."""
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
    result = surface.copy()
    width, height = result.get_size()
    color_surface = pg.Surface((width, height), pg.SRCALPHA)
    color_surface.fill((*new_color, 255))
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
    overlay = pg.Surface((width, height), pg.SRCALPHA)
    overlay.fill((*new_color, 128))
    result.blit(overlay, (0, 0), special_flags=pg.BLEND_RGB_ADD)
    return result


def recolor_multiply_screen(surface, new_color: (tuple[int, int, int] | str)):
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
    color_overlay = pg.Surface((width, height))
    color_overlay.fill(new_color)
    temp = result.copy()
    temp.blit(color_overlay, (0, 0), special_flags=pg.BLEND_MULT)
    brighten = pg.Surface((width, height))
    brighten.fill((50, 50, 50))
    temp.blit(brighten, (0, 0), special_flags=pg.BLEND_RGB_ADD)
    return temp
