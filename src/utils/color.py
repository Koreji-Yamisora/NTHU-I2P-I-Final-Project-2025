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
