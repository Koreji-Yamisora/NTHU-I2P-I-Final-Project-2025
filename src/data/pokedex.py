class PokeDex:
    data = {
        1: {
            "sprite_path": "menu_sprites/menusprite1.png",
            "fight_path": "sprites/sprite1.png",
            "name": "Pikachu",
            "hp": 35,
            "atk": 55,
            "def": 40,
            "spa": 50,
            "spd": 50,
            "spe": 90,
            "type": ("ele", None),
            "abi": ("Static", None),
            "yield": {"spe": 2},
        },
        2: {
            "sprite_path": "menu_sprites/menusprite2.png",
            "fight_path": "sprites/sprite2.png",
            "name": "Charizard",
            "hp": 78,
            "atk": 84,
            "def": 78,
            "spa": 109,
            "spd": 85,
            "spe": 100,
            "type": ("fir", "fly"),
            "abi": ("Blaze", None),
            "yield": {"spa": 3},
        },
        3: {
            "sprite_path": "menu_sprites/menusprite3.png",
            "fight_path": "sprites/sprite3.png",
            "name": "Blastoise",
            "hp": 79,
            "atk": 83,
            "def": 100,
            "spa": 85,
            "spd": 105,
            "spe": 78,
            "type": ("fir", "fly"),
            "abi": ("Torrent", None),
            "yield": {"spd": 3},
        },
        4: {
            "sprite_path": "menu_sprites/menusprite4.png",
            "fight_path": "sprites/sprite4.png",
            "name": "Venusaur",
            "hp": 80,
            "atk": 82,
            "def": 83,
            "spa": 100,
            "spd": 100,
            "spe": 80,
            "type": ("gra", "poi"),
            "abi": ("Overgrow", None),
            "yield": {"spa": 2, "spd": 1},
        },
        5: {
            "sprite_path": "menu_sprites/menusprite5.png",
            "fight_path": "sprites/sprite5.png",
            "name": "Dragonite",
            "hp": 91,
            "atk": 134,
            "def": 95,
            "spa": 100,
            "spd": 100,
            "spe": 80,
            "type": ("dra", "fly"),
            "abi": ("Overgrow", None),
            "yield": {"atk": 3},
        },
    }


class LevelTable:
    pass


class PokeType:
    def __init__(self):
        self.type = [
            "nor",
            "fir",
            "wat",
            "ele",
            "gra",
            "ice",
            "fig",
            "poi",
            "gro",
            "fry",
            "psy",
            "bug",
            "roc",
            "gho",
            "dra",
            "dar",
            "ste",
            "fai",
        ]
        self.matrix = {
            "nor": (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 0, 1, 1, 3, 1),
            "fir": (0, 3, 3, 2, 1, 2, 1, 1, 1, 1, 1, 2, 3, 1, 3, 1, 2, 1),
            "wat": (1, 2, 3, 3, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 3, 1, 1, 1),
            "gra": (1, 3, 2, 3, 1, 1, 1, 3, 2, 3, 1, 3, 2, 1, 3, 1, 3, 1),
            "ele": (1, 1, 2, 3, 3, 1, 1, 1, 0, 2, 1, 1, 1, 1, 3, 1, 1, 1),
            "ice": (1, 3, 3, 2, 1, 3, 1, 1, 2, 2, 1, 1, 1, 1, 2, 1, 3, 1),
            "fig": (2, 1, 1, 1, 1, 2, 1, 3, 1, 3, 3, 3, 2, 0, 1, 2, 2, 3),
            "poi": (1, 1, 1, 2, 1, 1, 1, 3, 3, 1, 1, 1, 3, 3, 1, 1, 0, 2),
            "gro": (1, 2, 1, 3, 2, 1, 1, 2, 1, 0, 1, 3, 2, 1, 1, 1, 2, 1),
            "fly": (1, 1, 1, 2, 3, 1, 2, 1, 1, 1, 1, 2, 3, 1, 1, 1, 3, 1),
            "psy": (1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 3, 1, 1, 1, 1, 0, 3, 1),
            "bug": (1, 3, 1, 2, 1, 1, 3, 3, 1, 3, 2, 1, 1, 3, 1, 2, 3, 3),
            "roc": (1, 2, 1, 1, 1, 2, 3, 1, 3, 2, 1, 2, 1, 1, 1, 1, 3, 1),
            "gho": (0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 3, 1, 1),
            "dra": (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 3, 0),
            "dar": (1, 1, 1, 1, 1, 1, 3, 1, 1, 1, 2, 1, 1, 2, 1, 3, 1, 3),
            "ste": (1, 3, 3, 1, 3, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 3, 2),
            "fai": (1, 3, 1, 1, 1, 1, 2, 3, 1, 1, 1, 1, 1, 1, 2, 2, 3, 1),
        }

    def effective(self, your, target):
        def check(e1, e2=None) -> float:
            if e2:
                c = e1 + e2
            else:
                c = e1
            if e1 == 0 or e2 == 0:
                return 0
            else:
                match c:
                    case 1:
                        return 1
                    case 2:
                        if e2:
                            return 1
                        else:
                            return 2
                    case 3:
                        return 0.5
                    case 4:
                        return 4
                    case 5:
                        return 1
                    case 6:
                        return 0.25
                    case _:
                        return 1

        t1, t2 = 18, 18
        for idx, t in enumerate(self.type):
            if t == target[0]:
                t1 = idx
                if target[1] == "":
                    break
            elif t == target[1]:
                t2 = idx
                break

        e1 = self.matrix[your][t1]
        if t2 != 18:
            e2 = self.matrix[your][t2]
            result = check(e1, e2)
        else:
            result = check(e1)
        return result
