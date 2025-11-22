import random


def new_ev(level, exp=0.45) -> dict[str, int]:
    STAT = ("hp", "atk", "def", "spa", "spd", "spe")
    ev = {}
    total_limit = 510
    stat_limit = 252

    def bias_gen(low, high):
        bias = random.random() ** exp
        return low + int((high - low + 1) * bias)

    max_ev = level * 2

    for stat in STAT:
        ev[stat] = bias_gen(0, max_ev)

    # Enforce total EV limit
    total = sum(ev.values())
    if total > total_limit:
        ratio = total_limit / total
        for stat in STAT:
            ev[stat] = int(ev[stat] * ratio)
    return ev


def new_iv() -> dict[str, int]:
    STAT = ("hp", "atk", "def", "spa", "spd", "spe")
    iv = {}
    stat_limit = 31

    for stat in STAT:
        iv[stat] = random.randint(0, stat_limit)
    return iv


def worker(exp):
    l = 100
    count = 1
    while l > exp:
        for i in new_ev(50).values():
            if i < l:
                l = i
        count += 1
    return count


def run(exp):
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
