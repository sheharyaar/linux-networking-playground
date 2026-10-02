#!/usr/bin/env python3
"""qwatch.py: sample one qdisc's backlog and drops, as CSV.

  ip netns exec rtr python3 qwatch.py --dev r1 [--every 0.02] [--seconds 20] [--csv q.csv]

It runs `tc -s -j qdisc show dev DEV` in a loop and keeps the root qdisc's
backlog (bytes, packets), drops and sent counters.
"""
import argparse, csv, json, subprocess, sys, time

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('--dev', required=True); p.add_argument('--every', type=float, default=0.02)
p.add_argument('--seconds', type=float, default=20); p.add_argument('--csv')
a = p.parse_args()
rows, t0 = [], time.monotonic()
while (t := time.monotonic() - t0) < a.seconds:
    q = json.loads(subprocess.run(['tc', '-s', '-j', 'qdisc', 'show', 'dev', a.dev],
                                  capture_output=True, text=True, check=True).stdout)
    root = next(x for x in q if x.get('root'))
    rows.append({'t_s': f'{t:.3f}', 'kind': root['kind'], 'backlog_bytes': root.get('backlog', 0),
                 'backlog_pkts': root.get('qlen', 0), 'drops': root.get('drops', 0),
                 'sent_pkts': root.get('packets', 0)})
    time.sleep(a.every)
out = open(a.csv, 'w', newline='') if a.csv else sys.stdout
w = csv.DictWriter(out, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
