from src.utils import crd, GameSettings

print("hello")


sw = crd(GameSettings.SCREEN_WIDTH)
sh = crd(GameSettings.SCREEN_HEIGHT)

print(sw.per(50))
print(sh.per(50))
