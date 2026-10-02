#!/usr/bin/env python3
"""qwatch.py (chapter 7 copy of the chapter 5 copy): sample one qdisc's backlog, as CSV.

  ip netns exec snd python3 qwatch.py --dev s0 [--every 0.02] [--seconds 20] [--csv q.csv]

It runs `tc -s -j qdisc show dev DEV` in a loop. Columns:
  backlog_bytes, backlog_pkts, drops, sent_pkts   from the root qdisc, as in the common copy
  sent_bytes                                      added here
  fq_flows, fq_inactive, fq_throttled_now,         only when the root is fq. tc prints two fields
  fq_throttled_events                              called "throttled": the first is the number of
                                                   flows waiting right now (q->throttled_flows), the
                                                   second counts every time a flow had to wait
                                                   (q->stat_throttled). json.loads would keep only
                                                   the last, so this copy keeps both, in order.
"""
import argparse, csv, json, subprocess, sys, time

def pairs(kv):                       # keep repeated keys: [('throttled', 0), ..., ('throttled', 7)]
    return kv

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('--dev', required=True); p.add_argument('--every', type=float, default=0.02)
p.add_argument('--seconds', type=float, default=20); p.add_argument('--csv')
a = p.parse_args()
rows, t0 = [], time.monotonic()
while (t := time.monotonic() - t0) < a.seconds:
    out = subprocess.run(['tc', '-s', '-j', 'qdisc', 'show', 'dev', a.dev],
                         capture_output=True, text=True, check=True).stdout
    qd = json.loads(out, object_pairs_hook=pairs)
    root = next(x for x in qd if dict(x).get('root'))
    d = dict(root)
    row = {'t_s': f'{t:.3f}', 'kind': d['kind'], 'backlog_bytes': d.get('backlog', 0),
           'backlog_pkts': d.get('qlen', 0), 'drops': d.get('drops', 0),
           'sent_pkts': d.get('packets', 0), 'sent_bytes': d.get('bytes', 0)}
    if d['kind'] == 'fq':
        thr = [v for k, v in root if k == 'throttled']
        row.update(fq_flows=d.get('flows', 0), fq_inactive=d.get('inactive', 0),
                   fq_throttled_now=thr[0] if thr else 0, fq_throttled_events=thr[-1] if thr else 0)
    rows.append(row)
    time.sleep(a.every)
out = open(a.csv, 'w', newline='') if a.csv else sys.stdout
w = csv.DictWriter(out, fieldnames=list(rows[-1])); w.writeheader(); w.writerows(rows)
