#!/usr/bin/env python3
"""wheel_starter.py: a timing wheel against a binary heap, for the Carousel chapter (ch07.html).

  python3 wheel_starter.py                      # heap only, until TimingWheel is written
  python3 wheel_starter.py --flows 100 1000 10000 100000
  python3 wheel_starter.py --literal --poll 3   # the paper's Algorithm 1, ported line by line

The workload is Carousel's (pp. 409-411): N paced flows share one shaper at a fixed total of
12 Gbit/s of 1500-byte packets, so about one packet is due per microsecond whatever N is.
Each flow keeps two packets in the shaper (a deferred completion: a flow stamps its next packet
only when one of its packets is released). A packet's release time is the flow's last release
time plus 1500 bytes over the flow's rate, the paper's LTS' = LTS + len/R (p. 410).

The driver is a busy poller: it moves the clock one granule (--poll slots of g) at a time and
takes every packet that is due. Your job is the TimingWheel class below: insert() and
extract_due(). The HeapScheduler next to it is complete and is the yardstick.

For each N it prints: packets released, the release error (poll time minus release time:
negative means released early, inside its slot; positive means late),
operations per packet (heap: comparisons; wheel: slot visits plus list operations), and
nanoseconds per packet. heapq is written in C and your wheel is Python, so compare how each
column changes with N, not the absolute numbers. The CPU is shared; time several runs.
"""
import argparse, heapq, random, time

PKT = 1500 * 8                      # bits per packet
TOTAL_BPS = 12e9                    # all flows together

class Counted:                       # a heap entry that counts its own comparisons
    n = 0
    __slots__ = ('t', 'item')
    def __init__(self, t, item): self.t, self.item = t, item
    def __lt__(self, other):
        Counted.n += 1
        return self.t < other.t

class HeapScheduler:
    """A binary heap keyed by release time: O(log n) insert and extract, like fq's throttled tree."""
    def __init__(self, g_ns, horizon_ns, count=False):
        self.h, self.count, self.ops, self.seq = [], count, 0, 0
    def insert(self, t_ns, item):
        self.seq += 1                                    # ties leave in arrival order
        heapq.heappush(self.h, Counted((t_ns, self.seq), item) if self.count else (t_ns, self.seq, item))
    def extract_due(self, now_ns):
        out, h = [], self.h
        while h and (h[0].t[0] if self.count else h[0][0]) <= now_ns:
            e = heapq.heappop(h)
            out.append(e.item if self.count else e[2])
        if self.count: self.ops = Counted.n
        return out

class TimingWheel:
    """An array of slots, each g_ns wide, covering horizon_ns ahead of the front (pp. 410-411).

    insert(t_ns, item): put item in the slot that covers t_ns. A time at or before the front
        goes into the front slot (send now); a time beyond the horizon goes into the last slot
        (the paper's first option, p. 411).
    extract_due(now_ns): return every item in every slot from the front up to the slot that
        covers now_ns, in slot order, oldest first within a slot, and move the front past them.
    Keep self.ops counting slot visits plus list operations, so the driver can print it.
    """
    def __init__(self, g_ns, horizon_ns, count=False):
        self.g = g_ns
        self.n = horizon_ns // g_ns          # number of slots
        self.slots = [None] * self.n         # a slot is None or a list of items
        self.front = 0                       # absolute slot number of the earliest slot not yet swept
        self.ops = 0
    def insert(self, t_ns, item):
        raise NotImplementedError('write TimingWheel.insert')
    def extract_due(self, now_ns):
        raise NotImplementedError('write TimingWheel.extract_due')

class Alg1Literal:
    """Algorithm 1 exactly as printed on p. 410, with times in ns and Granularity in ns."""
    def __init__(self, g_ns, horizon_ns, count=False):
        self.G, self.N = g_ns, horizon_ns // g_ns
        self.TW = [[] for _ in range(self.N)]
        self.FrontTimestamp, self.ops = 0, 0
    def insert(self, ts, packet):                                    # lines 1-9
        ts = ts // self.G
        if ts <= self.FrontTimestamp: ts = self.FrontTimestamp
        elif ts > self.FrontTimestamp + self.N - 1: ts = self.FrontTimestamp + self.N - 1
        self.TW[ts % self.N].append(packet)
    def extract(self, now):                                          # lines 10-20
        now = now // self.G
        while now >= self.FrontTimestamp:
            if not self.TW[now % self.N]:
                self.FrontTimestamp += self.G
            else:
                return self.TW[now % self.N].pop(0)
        return None
    def extract_due(self, now_ns):
        out = []
        while (p := self.extract(now_ns)) is not None: out.append(p)
        return out

def run(sched_cls, flows, releases, g_ns, poll, seed, count):
    rnd = random.Random(seed)
    rate = [TOTAL_BPS / flows * rnd.uniform(0.5, 1.5) for _ in range(flows)]
    gap = [int(PKT / r * 1e9) for r in rate]                         # ns between a flow's packets
    horizon = 4 * max(gap)                                           # room for two packets ahead
    s = sched_cls(g_ns, horizon, count)
    lts = [rnd.randrange(gap[f]) for f in range(flows)]              # each flow starts somewhere in its first gap
    for f in range(flows):
        for _ in range(2):
            s.insert(lts[f], (f, lts[f])); lts[f] += gap[f]
    s.ops = Counted.n = 0                                            # count the steady state only
    done, early, late, now, t0 = 0, 0, 0, 0, time.perf_counter()
    stop_at = 20 * releases * g_ns                                   # about one packet is due per microsecond
    while done < releases and now < stop_at:                         # a wheel that loses packets would loop forever
        now += g_ns * poll
        for f, due in s.extract_due(now):
            early, late = min(early, now - due), max(late, now - due); done += 1
            s.insert(lts[f], (f, lts[f])); lts[f] += gap[f]          # the completion lets the flow stamp its next packet
    dt = time.perf_counter() - t0
    return done, (early, late), s.ops / done if count else None, dt / done * 1e9, horizon

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--flows', type=int, nargs='+', default=[100, 1000, 10000])
    p.add_argument('--releases', type=int, default=200000)
    p.add_argument('--g-us', type=float, default=1.0, help='slot width in microseconds')
    p.add_argument('--poll', type=int, default=1, help='the poller visits every POLL-th slot')
    p.add_argument('--literal', action='store_true', help='run the printed Algorithm 1 instead of your wheel')
    p.add_argument('--seed', type=int, default=7)
    a = p.parse_args()
    g = int(a.g_us * 1000)
    kinds = [('heap', HeapScheduler), ('alg1-literal' if a.literal else 'wheel', Alg1Literal if a.literal else TimingWheel)]
    print(f'g = {a.g_us:g} us, poll every {a.poll} slot(s), {a.releases} releases per run, {TOTAL_BPS / 1e9:g} Gbit/s in total')
    print(f'{"scheduler":>12} {"flows":>7} {"queued":>7} {"horizon":>9} {"released":>9} {"error (us)":>17} {"ops/pkt":>8} {"ns/pkt":>7}')
    for n in a.flows:
        for name, cls in kinds:
            try:
                done, (e, l), _, _, hz = run(cls, n, a.releases, g, a.poll, a.seed, count=False)
                _, _, ops, _, _ = run(cls, n, a.releases, g, a.poll, a.seed, count=True)
                ns = min(run(cls, n, a.releases, g, a.poll, a.seed, count=False)[3] for _ in range(2))
            except NotImplementedError as e:
                print(f'{name:>12} {n:>7}  -- {e}'); continue
            err = f'{e / 1000:+.1f} .. {l / 1000:+.1f}'
            print(f'{name:>12} {n:>7} {2 * n:>7} {hz / 1e6:>7.1f}ms {done:>9} {err:>17} {ops:>8.1f} {ns:>7.0f}')
