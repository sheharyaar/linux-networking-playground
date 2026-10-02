#!/usr/bin/env python3
"""drr_starter.py: the build-a-tiny-one lab of the shapers chapter.

  python3 drr_starter.py

Three always-backlogged flows share one output link:
  bulk  - 1500-byte packets
  small - 64-byte packets
  mixed - sizes uniform between 64 and 1500 bytes
Write rr() and drr() below. Each returns a trace: after every round, a dict {flow: bytes sent so far}.
main() then prints each flow's share after K rounds, Jain's index, and for DRR the worst
|K*Q - sent| over every round and flow, which Theorem 4.2 (p. 236) bounds by Max.
"""
import random
from collections import deque

def flows(n_pkts=30000, seed=1):
    r = random.Random(seed)
    return {'bulk':  [1500] * n_pkts,
            'small': [64] * n_pkts,
            'mixed': [r.randint(64, 1500) for _ in range(n_pkts)]}

def rr(queues, rounds):
    """Packet round robin: one packet per backlogged flow per round."""
    raise NotImplementedError('TODO: write rr()')

def drr(queues, rounds, quantum):
    """Deficit round robin after Fig. 4 of Shreedhar and Varghese (p. 236)."""
    raise NotImplementedError('TODO: write drr()')

def jain(xs): return sum(xs) ** 2 / (len(xs) * sum(x * x for x in xs))

def main(Q=1500, K=1000, MAX=1500):
    t_rr, t_drr = rr(flows(), K), drr(flows(), K, Q)
    for name, t in (('packet RR', t_rr), ('DRR', t_drr)):
        s = t[-1]; tot = sum(s.values())
        print(f'{name:9s} after {K} rounds: ' + '  '.join(f'{f} {v / tot:6.1%}' for f, v in s.items())
              + f'   Jain {jain(list(s.values())):.3f}')
    worst = max(abs(k * Q - s[f]) for k, s in enumerate(t_drr, 1) for f in s)
    print(f'DRR: worst |K*Q - sent| over all rounds and flows = {worst} bytes (bound: Max = {MAX})')

if __name__ == '__main__':
    try:
        main()
    except NotImplementedError as e:
        print(e)
