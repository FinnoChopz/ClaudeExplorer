#!/usr/bin/env python3
"""Elementary cellular automaton explorer. No dependencies.

    python ca.py show 110            # draw a rule from a single seed
    python ca.py show 30 -w 79 -n 40 --random
    python ca.py survey              # rank the 88 distinct rules by complexity
    python ca.py equiv 110           # the rules that behave identically to 110
"""
import argparse
import random
import sys
import zlib


def rule_table(rule):
    """Map each 3-cell neighbourhood (0..7) to the next cell state."""
    if not 0 <= rule <= 255:
        raise ValueError("rule must be in 0..255")
    return [(rule >> i) & 1 for i in range(8)]


def step(cells, table):
    n = len(cells)
    return [
        table[(cells[i - 1] << 2) | (cells[i] << 1) | cells[(i + 1) % n]]
        for i in range(n)
    ]


def evolve(rule, width, steps, initial=None):
    """Return steps+1 rows on a ring of `width` cells. Default: one live cell."""
    table = rule_table(rule)
    row = list(initial) if initial is not None else [0] * width
    if initial is None:
        row[width // 2] = 1
    rows = [row]
    for _ in range(steps):
        row = step(row, table)
        rows.append(row)
    return rows


def mirror(rule):
    """Rule obtained by swapping left and right."""
    out = 0
    for n in range(8):
        m = ((n & 1) << 2) | (n & 2) | (n >> 2)
        out |= ((rule >> n) & 1) << m
    return out


def complement(rule):
    """Rule obtained by swapping the roles of 0 and 1."""
    out = 0
    for n in range(8):
        out |= (1 - ((rule >> (7 - n)) & 1)) << n
    return out


def equivalents(rule):
    return sorted({rule, mirror(rule), complement(rule), mirror(complement(rule))})


def canonical_rules():
    """One representative (the smallest) per equivalence class: 88 of them."""
    return sorted({equivalents(r)[0] for r in range(256)})


def compressibility(rows):
    """zlib ratio of the packed grid: near 0 = trivial, near 1 = incompressible."""
    raw = bytes(int("".join(map(str, r[i:i + 8])).ljust(8, "0"), 2)
                for r in rows for i in range(0, len(r), 8))
    return len(zlib.compress(raw, 9)) / max(1, len(raw))


def render(rows, on="█", off=" "):
    return "\n".join("".join(on if c else off for c in r) for r in rows)


def survey(width=101, steps=200, seed=1):
    """Score every canonical rule from a random start. Returns (score, rule) desc."""
    rng = random.Random(seed)
    init = [rng.getrandbits(1) for _ in range(width)]
    scored = [(compressibility(evolve(r, width, steps, init)), r)
              for r in canonical_rules()]
    return sorted(scored, reverse=True)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show")
    s.add_argument("rule", type=int)
    s.add_argument("-w", "--width", type=int, default=71)
    s.add_argument("-n", "--steps", type=int, default=35)
    s.add_argument("--random", action="store_true", help="random start, not a single seed")
    s.add_argument("--seed", type=int, default=1)
    sv = sub.add_parser("survey")
    sv.add_argument("--top", type=int, default=12)
    e = sub.add_parser("equiv")
    e.add_argument("rule", type=int)
    a = p.parse_args(argv)

    if a.cmd == "show":
        init = None
        if a.random:
            rng = random.Random(a.seed)
            init = [rng.getrandbits(1) for _ in range(a.width)]
        print(render(evolve(a.rule, a.width, a.steps, init)))
    elif a.cmd == "survey":
        ranked = survey()
        print("most incompressible (chaotic / rich):")
        for sc, r in ranked[:a.top]:
            print(f"  rule {r:3d}  {sc:.3f}")
        print("most compressible (dead / periodic):")
        for sc, r in ranked[-a.top:]:
            print(f"  rule {r:3d}  {sc:.3f}")
    else:
        print(f"rule {a.rule} ~ {equivalents(a.rule)}")


if __name__ == "__main__":
    sys.exit(main())
