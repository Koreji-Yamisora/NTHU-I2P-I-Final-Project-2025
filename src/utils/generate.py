import random

# Default moves per type (first move is the primary/STAB move)
TYPE_DEFAULT_MOVES = {
    "nor": ["Quick Attack", "Tackle", "Scratch"],
    "fir": ["Ember", "Flamethrower"],
    "wat": ["Water Gun", "Hydropun"],
    "ele": ["Thunder Shock", "Thunderbolt"],
    "gra": ["Vine Attack", "Razor Leaf", "Solar Beam"],
    "ice": ["Ice Beam", "Blizzard"],
    "fig": ["Karate Chop", "Low Kick"],
    "poi": ["Poison Sting", "Sludge Bomb"],
    "gro": ["Earthquake", "Mud Shot"],
    "fly": ["Wing Attack", "Air Slash", "fly"],
    "psy": ["Confusion", "Psychic"],
    "bug": ["Bug Bite", "X-Scissor"],
    "roc": ["Rock Throw", "Rock Slide"],
    "gho": ["Shadow Ball", "Night Shade", "lick"],
    "dra": ["Dragon Breath", "Dragon Claw"],
    "dar": ["Crunch", "Dark Pulse", "Bite"],
    "ste": ["Metal Claw", "Iron Tail"],
    "fai": ["Moonblast", "Dazzling Gleam"],
}

# Pool of generic moves that can be added to any Pokémon
GENERIC_MOVES = ["Quick Attack", "Tackle", "Scratch", "Bite", "Peck"]


def generate_party(max_level: int, party_size: int = 6):
    """Generate Party."""
    from src.data import pokedex
    import random

    def bias_gen(low, high):
        """Bias Gen."""
        bias = random.random() ** 0.3
        return low + int((high - low + 1) * bias)

    party = []
    for i in range(random.randint(1, party_size)):
        pokemon = random.choice(list(pokedex.data.keys()))
        party.append(pokemon)
    stat = "atk", "def", "spa", "spd", "spe"
    mod = 1
    monsters = []
    for id in party:
        level = bias_gen(1, max_level)
        mon = {}
        mon["EV"] = new_ev(level)
        mon["IV"] = new_iv()
        base = pokedex.data[id]
        hp = (
            int((2 * base["hp"] + mon["IV"]["hp"] + mon["EV"]["hp"] / 4) * level / 100)
            + level
            + 10
        )
        stats = []
        for s in stat:
            stats.append(
                (int((2 * base[s] + mon["IV"][s] + mon["EV"][s] / 4) * level / 100) + 5)
                * mod
            )
        atk, defen, spa, spd, spe = stats

        # Generate moves based on type
        poke_types = base.get("type", ["nor", None])
        moves = generate_moves(poke_types)

        monsters.append(
            {
                "id": id,
                "name": pokedex.data[id]["name"],
                "level": level,
                "chp": hp,
                "hp": hp,
                "atk": atk,
                "def": defen,
                "spa": spa,
                "spd": spd,
                "spe": spe,
                "type": base["type"],
                "IV": mon["IV"],
                "EV": mon["EV"],
                "yield": pokedex.data[id]["yield"],
                "move": moves,
            }
        )
    return monsters


def generate_moves(poke_types: list, max_moves: int = 4) -> list:
    """Generate a moveset based on the Pokémon's type(s).

    Args:
        poke_types: List of 1-2 type strings (e.g., ['fir', 'fly'])
        max_moves: Maximum number of moves to generate (default 4)

    Returns:
        List of move dictionaries
    """
    from src.data.pokedex import PokeItems

    selected_move_names = []

    # 1. Add primary type's default move
    primary_type = poke_types[0] if poke_types[0] else "nor"
    if primary_type in TYPE_DEFAULT_MOVES:
        selected_move_names.append(TYPE_DEFAULT_MOVES[primary_type][0])

    # 2. Add secondary type's default move (if exists)
    if len(poke_types) > 1 and poke_types[1]:
        secondary_type = poke_types[1]
        if secondary_type in TYPE_DEFAULT_MOVES:
            move = TYPE_DEFAULT_MOVES[secondary_type][0]
            if move not in selected_move_names:
                selected_move_names.append(move)

    # 3. Fill remaining slots with random moves
    all_moves = list(PokeItems.moves.keys())
    attempts = 0
    while len(selected_move_names) < max_moves and attempts < 20:
        random_move = random.choice(all_moves)
        if random_move not in selected_move_names:
            selected_move_names.append(random_move)
        attempts += 1

    # 4. Convert move names to move data
    moves = []
    for name in selected_move_names:
        if name in PokeItems.moves:
            move_data = PokeItems.moves[name].copy()
            move_data["name"] = name
            # Initialize current PP to max PP
            move_data["cpp"] = move_data.get("pp", 10)
            moves.append(move_data)

    return moves


def new_ev(level, exp=0.45) -> dict[str, int]:
    """New Ev."""
    STAT = "hp", "atk", "def", "spa", "spd", "spe"
    ev = {}
    total_limit = 510
    stat_limit = 252

    def bias_gen(low, high):
        """Bias Gen."""
        bias = random.random() ** exp
        return low + int((high - low + 1) * bias)

    max_ev = level * 2
    for stat in STAT:
        ev[stat] = bias_gen(0, max_ev)
    total = sum(ev.values())
    if total > total_limit:
        ratio = total_limit / total
        for stat in STAT:
            ev[stat] = int(ev[stat] * ratio)
    return ev


def new_iv() -> dict[str, int]:
    """New Iv."""
    STAT = "hp", "atk", "def", "spa", "spd", "spe"
    iv = {}
    stat_limit = 31
    for stat in STAT:
        iv[stat] = random.randint(0, stat_limit)
    return iv


def worker(exp):
    """Worker."""
    l = 100
    count = 1
    while l > exp:
        for i in new_ev(50).values():
            if i < l:
                l = i
        count += 1
    return count


def run(exp):
    """Run."""
    runs = 1000
    workers = 12
    results = []
    with Pool(workers) as pool:
        for result in tqdm(pool.imap_unordered(worker, [exp] * runs), total=runs):
            results.append(result)
    avg = sum(results) / runs
    print("Average:", avg)
    return avg


if __name__ == "__main__":
    from tqdm import tqdm
    from multiprocessing import Pool
    import timeit

    r = []
    for n in range(10):
        r.append(run(n))
    print(*r)
