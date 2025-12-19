class PokeDex:
    # Evolution format: "evolution": {"level": <level>, "to": <target_id>}
    data = {}

    @staticmethod
    def load_data():
        import json
        import os

        file_path = os.path.join(os.path.dirname(__file__), "pokedex.json")
        try:
            with open(file_path, "r") as f:
                raw_data = json.load(f)
                # Convert keys to integers
                PokeDex.data = {int(k): v for k, v in raw_data.items()}
        except FileNotFoundError:
            print(f"Error: {file_path} not found.")
            PokeDex.data = {}


class PokeItems:
    items = {}
    moves = {}

    @staticmethod
    def load_data():
        import json
        import os

        file_path = os.path.join(os.path.dirname(__file__), "pokeitems.json")
        try:
            with open(file_path, "r") as f:
                raw_data = json.load(f)
                PokeItems.items = raw_data.get("items", {})
                PokeItems.moves = raw_data.get("moves", {})
        except FileNotFoundError:
            print(f"Error: {file_path} not found.")
            PokeItems.moves = {}
            PokeItems.moves = {}


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
            "wat": (1, 3, 3, 3, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 3, 1, 1, 1),
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

PokeItems.load_data()


# Initialize data on import
PokeDex.load_data()
