#!/usr/bin/env python3
"""cwatch.py: sample every class of one classful qdisc (HTB, DRR) as CSV.

  ip netns exec rtr python3 cwatch.py --dev r1 [--every 0.25] [--seconds 40] [--csv classes.csv]

It runs `tc -s -j class show dev DEV` in a loop and writes one row per class per sample:
bytes and packets sent, drops, overlimits, backlog, and for HTB the lended/borrowed counters
and the two buckets (tokens, ctokens, in 64 ns ticks of sending time; negative means in debt).
Each row carries wall_s (time.time()) so it lines up with flow.py's CSVs.
"""
import argparse, csv, json, subprocess, sys, time

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('--dev', required=True); p.add_argument('--every', type=float, default=0.25)
p.add_argument('--seconds', type=float, default=40); p.add_argument('--csv')
a = p.parse_args()
KEYS = ('bytes', 'packets', 'drops', 'overlimits', 'backlog', 'qlen', 'lended', 'borrowed', 'tokens', 'ctokens')
rows, t0 = [], time.monotonic()
while (t := time.monotonic() - t0) < a.seconds:
    out = subprocess.run(['tc', '-s', '-j', 'class', 'show', 'dev', a.dev],
                         capture_output=True, text=True, check=True).stdout
    wall = time.time()
    for c in json.loads(out or '[]'):
        st = c.get('stats', {})
        rows.append({'t_s': f'{t:.3f}', 'wall_s': f'{wall:.3f}', 'class': c['handle'],
                     **{k: st.get(k, '') for k in KEYS}})
    time.sleep(a.every)
f = open(a.csv, 'w', newline='') if a.csv else sys.stdout
head = ['t_s', 'wall_s', 'class', *KEYS]          # the header is written even when DEV has no classes
w = csv.DictWriter(f, fieldnames=head); w.writeheader(); w.writerows(rows)
