#!/usr/bin/env python3
"""ffsq_starter.py: the build-it lab of the Eiffel chapter.

  python3 ffsq_starter.py --buckets 20000 --packets 1000

Write FFSQueue.push() and FFSQueue.pop_min() below: a bucketed priority queue over the
ranks 0..N-1, one FIFO per bucket, and a tree of 64-bit bitmap words over the buckets
(Eiffel, p. 21, Fig. 3). Level 0 has one bit per bucket; each level above has one bit per
word of the level below, set when that word is non-zero; the top level is one word.

main() fills the queue with random ranks, drains it, checks that the ranks come out in
order, and prints what each pop cost: words of bitmap touched by your queue, and
comparisons made by Python's heapq for the same packets. Then it times both.
Find first set on a Python int: (w & -w).bit_length() - 1 is the index of the lowest set bit.
"""
import argparse, heapq, random, time
from collections import deque

W = 64

class FFSQueue:
    def __init__(self, nbuckets):
        self.levels = []                  # levels[0]: one bit per bucket ... levels[-1]: [root word]
        bits = nbuckets
        while True:
            words = (bits + W - 1) // W
            self.levels.append([0] * words)
            if words == 1:
                break
            bits = words
        self.buckets = [None] * nbuckets  # a deque per bucket, made on first use
        self.touched = 0                  # add 1 for every bitmap word you read or write

    def push(self, rank, item):
        """Append item to bucket `rank`; set its bit, and each parent bit that was clear."""
        raise NotImplementedError('TODO: write push()')

    def pop_min(self):
        """Return (rank, item) from the first non-empty bucket: one find-first-set per level,
        root first. If the bucket empties, clear its bit, and each parent whose word becomes 0."""
        raise NotImplementedError('TODO: write pop_min()')


class Count:                              # a heap key that counts its comparisons
    n = 0
    __slots__ = ('k',)
    def __init__(self, k): self.k = k
    def __lt__(self, o): Count.n += 1; return self.k < o.k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--buckets', type=int, default=20000)
    ap.add_argument('--packets', type=int, default=1000)
    ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args()
    r = random.Random(a.seed)
    ranks = [r.randrange(a.buckets) for _ in range(a.packets)]

    q = FFSQueue(a.buckets)
    for i, k in enumerate(ranks):
        q.push(k, i)
    pushed = q.touched
    out = [q.pop_min()[0] for _ in ranks]
    assert out == sorted(ranks), 'ranks came out of order'
    h = []
    for i, k in enumerate(ranks):
        heapq.heappush(h, (Count(k), i))
    hpush = Count.n
    while h:
        heapq.heappop(h)
    n = a.packets
    print(f'{a.buckets} buckets, {len(q.levels)} levels, {n} packets')
    print(f'ffs queue: {pushed / n:.2f} words per push, {(q.touched - pushed) / n:.2f} words per pop')
    print(f'heapq:     {hpush / n:.2f} comparisons per push, {(Count.n - hpush) / n:.2f} per pop')

    for name, make, push, pop in (
            ('ffs queue', lambda: FFSQueue(a.buckets), lambda s, k, i: s.push(k, i), lambda s: s.pop_min()),
            ('heapq', list, lambda s, k, i: heapq.heappush(s, (k, i)), heapq.heappop)):
        best = 1e9
        for _ in range(3):
            s = make()
            t0 = time.perf_counter()
            for i, k in enumerate(ranks):
                push(s, k, i)
            for _ in ranks:
                pop(s)
            best = min(best, time.perf_counter() - t0)
        print(f'{name:9s}  {best / n * 1e9:7.0f} ns per push+pop (fastest of 3)')


if __name__ == '__main__':
    try:
        main()
    except NotImplementedError as e:
        print(e)
