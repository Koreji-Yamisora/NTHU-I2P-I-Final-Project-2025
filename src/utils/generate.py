import random


def generate_party(max_level: int, party_size: int=6):
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
    stat = 'atk', 'def', 'spa', 'spd', 'spe'
    mod = 1
    monsters = []
    for id in party:
        level = bias_gen(1, max_level)
        mon = {}
        mon['EV'] = new_ev(level)
        mon['IV'] = new_iv()
        base = pokedex.data[id]
        hp = int((2 * base['hp'] + mon['IV']['hp'] + mon['EV']['hp'] / 4) *
            level / 100) + level + 10
        stats = []
        for s in stat:
            stats.append((int((2 * base[s] + mon['IV'][s] + mon['EV'][s] / 
                4) * level / 100) + 5) * mod)
        atk, defen, spa, spd, spe = stats
        monsters.append({'id': id, 'name': pokedex.data[id]['name'],
            'level': level, 'chp': hp, 'hp': hp, 'atk': atk, 'def': defen,
            'spa': spa, 'spd': spd, 'spe': spe, 'type': base['type'], 'IV':
            mon['IV'], 'EV': mon['EV'], 'yield': pokedex.data[id]['yield'],
            'move': temp_move()})
    return monsters


def temp_move():
    """Temp Move."""
    return [{'name': 'Quick Attack', 'type': 'nor', 'cat': 'Normal Attack',
        'power': 60, 'acc': 95}]


def new_ev(level, exp=0.45) ->dict[str, int]:
    """New Ev."""
    STAT = 'hp', 'atk', 'def', 'spa', 'spd', 'spe'
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


def new_iv() ->dict[str, int]:
    """New Iv."""
    STAT = 'hp', 'atk', 'def', 'spa', 'spd', 'spe'
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
        for result in tqdm(pool.imap_unordered(worker, [exp] * runs), total
            =runs):
            results.append(result)
    avg = sum(results) / runs
    print('Average:', avg)
    return avg


if __name__ == '__main__':
    from tqdm import tqdm
    from multiprocessing import Pool
    import timeit
    r = []
    for n in range(10):
        r.append(run(n))
    print(*r)
