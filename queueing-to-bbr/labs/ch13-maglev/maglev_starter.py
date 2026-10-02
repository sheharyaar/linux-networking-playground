#!/usr/bin/env python3
"""maglev_starter.py: starter for the Maglev chapter's Python lab (ch13.html, "Measure balance
and disruption at real sizes"). Fill in the two TODOs, then run:

    python3 maglev_starter.py

It checks your populate() against the paper's Table 1 (p. 6) first, then prints one line per
table size for N = 100 backends: entries per backend, and the share of the table that moves
between surviving backends when one backend leaves, for Maglev and for a plain mod-N table.
"""
import random

def populate(os_, M):
    """Pseudocode 1 (p. 6). os_ is a list of (offset, skip), one per backend.
    Return entry, a list of M backend indexes. Preference j of backend i is
    (offset + j * skip) % M. Backends take turns; each turn claims the first
    preference that is still empty."""
    # TODO: about ten lines
    raise NotImplementedError

def extra_moved(before, after, dead):
    """Percent of all M slots whose backend changed, counting only slots that did
    NOT belong to a removed backend (the paper's Fig. 12 metric, as the chapter
    reconstructs it)."""
    # TODO: one or two lines
    raise NotImplementedError

def one_trial(M, N, k, rng):
    os_ = [(rng.randrange(M), rng.randrange(M - 1) + 1) for _ in range(N)]
    before = populate(os_, M)
    dead = set(rng.sample(range(N), k))
    alive = [i for i in range(N) if i not in dead]
    after = [alive[x] for x in populate([os_[i] for i in alive], M)]   # back to original indexes
    counts = [before.count(i) for i in range(N)]
    modn_before = [j % N for j in range(M)]
    modn_after = [alive[j % len(alive)] for j in range(M)]
    return min(counts), max(counts), extra_moved(before, after, dead), extra_moved(modn_before, modn_after, dead)

if __name__ == '__main__':
    # Table 1: (offset, skip) for B0, B1, B2 and M = 7
    t1 = populate([(3, 4), (0, 2), (3, 1)], 7)
    assert t1 == [1, 0, 1, 0, 2, 2, 0], t1                       # B1 B0 B1 B0 B2 B2 B0
    t1_after = [[0, 2][x] for x in populate([(3, 4), (3, 1)], 7)]
    assert t1_after == [0, 0, 0, 0, 2, 2, 2], t1_after           # B0 B0 B0 B0 B2 B2 B2
    print('Table 1 matches p. 6')
    rng = random.Random(13)
    print('M      M/N   entries  maglev_moved%  modN_moved%')
    for M in (251, 1021, 4093, 16381, 65521):
        r = [one_trial(M, 100, 1, rng) for _ in range(10)]
        print(f'{M:<6} {M/100:5.0f}  {min(x[0] for x in r)}-{max(x[1] for x in r):<6} '
              f'{sum(x[2] for x in r)/10:8.2f}  {sum(x[3] for x in r)/10:12.1f}')
