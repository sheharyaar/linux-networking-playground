#!/usr/bin/env python3
"""wheelwait.py: watch the kernel's own timing wheel round your timeouts up.

  python3 wheelwait.py [--csv waits.csv] [--quick]

No sudo, no namespaces. A blocking recv() on an idle UDP socket with SO_RCVTIMEO sleeps in
schedule_timeout(), which arms a timer in the kernel's timer wheel (kernel/time/timer.c).
time.sleep() uses clock_nanosleep(), a high-resolution timer kept in a red-black tree.
For each requested timeout the script measures how late each one wakes up, and prints the
wheel level the timeout falls in and that level's bucket width (granularity). Before each pair
of waits it sleeps a random fraction of one bucket, so the start falls anywhere inside a bucket.

The level table comes from calc_wheel_index() in kernel/time/timer.c (v7.2): 64 buckets per
level, each level 8 times coarser than the one below, and a timer rounded UP to its bucket.
HZ is read from /proc/config.gz if it exists, else assumed to be 1000.
"""
import argparse, csv, gzip, random, socket, statistics, struct, sys, threading, time

def hz():
    try:
        for line in gzip.open('/proc/config.gz', 'rt'):
            if line.startswith('CONFIG_HZ='): return int(line.split('=')[1])
    except OSError:
        pass
    return 1000

HZ = hz()
LVL_START = [63 << (3 * (n - 1)) if n else 0 for n in range(9)]   # in jiffies: 0, 63, 504, 4032, ...

def level(ms):
    j = ms * HZ // 1000
    lvl = max(n for n in range(9) if j >= LVL_START[n])
    return lvl, (8 ** lvl) * 1000 / HZ                              # level, bucket width in ms

def wheel_wait(ms):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('127.0.0.1', 0))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, struct.pack('@ll', ms // 1000, (ms % 1000) * 1000))
    t0 = time.monotonic_ns()
    try:
        s.recv(1)
    except (BlockingIOError, TimeoutError, socket.timeout):
        pass
    t1 = time.monotonic_ns(); s.close()
    return (t1 - t0) / 1e6

def tree_wait(ms):
    t0 = time.monotonic_ns(); time.sleep(ms / 1000); return (time.monotonic_ns() - t0) / 1e6

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('--csv'); p.add_argument('--quick', action='store_true', help='fewer repeats, about 15 s')
a = p.parse_args()
PLAN = [(20, 20), (50, 20), (100, 20), (200, 20), (400, 15), (800, 10), (1500, 8), (3000, 6), (5000, 5), (10000, 3)]
if a.quick: PLAN = [(ms, max(2, n // 4)) for ms, n in PLAN if ms <= 5000]
rows, lock = [], threading.Lock()

def run(ms, n):                         # one thread per timeout value; each sleeps on its own
    g = level(ms)[1]
    for i in range(n):
        time.sleep(random.uniform(0, g / 1000))   # start at a random point inside a bucket
        for kind, f in (('wheel', wheel_wait), ('hrtimer', tree_wait)):
            got = f(ms)
            with lock: rows.append({'kind': kind, 'requested_ms': ms, 'elapsed_ms': round(got, 3), 'late_ms': round(got - ms, 3)})

ths = [threading.Thread(target=run, args=pl) for pl in PLAN]
[t.start() for t in ths]; [t.join() for t in ths]
print(f'HZ={HZ}; late = elapsed - requested, in ms')
print(f'{"timeout":>8} {"level":>5} {"bucket":>8} | {"wheel late: min":>15} {"median":>7} {"max":>7} | {"hrtimer median":>14}')
for ms, _ in PLAN:
    w = [r['late_ms'] for r in rows if r['kind'] == 'wheel' and r['requested_ms'] == ms]
    h = [r['late_ms'] for r in rows if r['kind'] == 'hrtimer' and r['requested_ms'] == ms]
    lvl, g = level(ms)
    print(f'{ms:>6} ms {lvl:>5} {g:>5g} ms | {min(w):>15.2f} {statistics.median(w):>7.2f} {max(w):>7.2f} | {statistics.median(h):>14.3f}')
if a.csv:
    w = csv.DictWriter(open(a.csv, 'w', newline=''), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
