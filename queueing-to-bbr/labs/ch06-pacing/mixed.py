#!/usr/bin/env python3
"""mixed.py: paced against unpaced flows in the same run, from chapter-6 flow.py CSVs.

  python3 mixed.py mix-k4-*-f.csv [--bulk] [--csv-out out.csv]

For fixed-size runs (flow.py --bytes) a flow's completion time is the first sample with done=1
(10 ms resolution). For bulk runs (flow.py --seconds) pass --bulk: it then uses each flow's
goodput instead.
It groups the files by condition (the file name up to "-N-f.csv") and prints, per condition:
the number of runs; the mean completion time (or Mbit/s) of the paced flows and of the unpaced
flows, each with its standard error; their ratio unpaced/paced (the paper's Fig. 15 plots
Latency(Reno)/Latency(Paced)); the loss events per flow (times a flow entered recovery or
loss), the retransmitted packets per flow, and the share of each group that lost in the run's
first congestion epoch (every recovery start within --window seconds of the first), for each group. The paced flows are the ones
with paced=1 in the CSV: the flows that set SO_MAX_PACING_RATE.
"""
import argparse, collections, csv, re

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('csv', nargs='+'); p.add_argument('--csv-out', dest='out')
p.add_argument('--bulk', action='store_true', help='the runs used --seconds: compare goodput per flow')
p.add_argument('--window', type=float, default=0.06, help='congestion epoch length, as in epochs.py')
a = p.parse_args()

def one(path):
    by = collections.defaultdict(list)
    for r in csv.DictReader(open(path)):
        by[int(r['flow'])].append(r)
    fixed = not a.bulk
    out = []
    firsts = {}
    for k, rs in by.items():
        prev = 'open'
        for r in rs:
            if r['ca_state'] in ('recovery', 'loss') and prev not in ('recovery', 'loss'):
                firsts[k] = float(r['t_s']); break
            prev = r['ca_state']
    t0 = min(firsts.values()) if firsts else 0
    for k, rs in sorted(by.items()):
        paced = rs[0]['paced'] == '1'
        prev, ev = 'open', 0
        for r in rs:
            if r['ca_state'] in ('recovery', 'loss') and prev not in ('recovery', 'loss'): ev += 1
            prev = r['ca_state']
        in_first = int(k in firsts and firsts[k] - t0 < a.window)
        if fixed:
            v = next((float(r['t_s']) for r in rs if r['done'] == '1'), float(rs[-1]['t_s']))
        else:
            v = int(rs[-1]['bytes_acked']) * 8 / float(rs[-1]['t_s']) / 1e6
        out.append((paced, v, ev, int(rs[-1]['total_retrans']), in_first))
    return fixed, out

def mean(v): return sum(v) / len(v) if v else float('nan')
def se(v):
    if len(v) < 2: return float('nan')
    m = mean(v); return (sum((x - m) ** 2 for x in v) / (len(v) - 1) / len(v)) ** 0.5

groups = collections.OrderedDict()
for f in a.csv:
    groups.setdefault(re.sub(r'-\d+-f\.csv$', '', f.split('/')[-1]), []).append(one(f))
rows = []
for g, runs in groups.items():
    fixed = runs[0][0]
    P = [x for _, o in runs for x in o if x[0]]; U = [x for _, o in runs for x in o if not x[0]]
    pv, uv = [x[1] for x in P], [x[1] for x in U]
    n_p, n_u = len(P) // len(runs), len(U) // len(runs)
    unit = 's' if fixed else 'Mbit/s'
    ratio = mean(uv) / mean(pv) if pv and uv else float('nan')
    print(f'{g}: {len(runs)} runs, {n_p} paced + {n_u} unpaced flows; '
          f'{"completion" if fixed else "goodput per flow"} paced {mean(pv):.3f}±{se(pv):.3f} {unit}, '
          f'unpaced {mean(uv):.3f}±{se(uv):.3f} {unit}, unpaced/paced {ratio:.2f}; '
          f'loss events per flow paced {mean([x[2] for x in P]):.2f}, unpaced {mean([x[2] for x in U]):.2f}; '
          f'retransmits per flow paced {mean([x[3] for x in P]):.1f}, unpaced {mean([x[3] for x in U]):.1f}; '
          f'lost in the first congestion epoch: paced {100 * mean([x[4] for x in P]):.0f}%, unpaced {100 * mean([x[4] for x in U]):.0f}%')
    rows.append(dict(condition=g, runs=len(runs), paced_flows=n_p, unpaced_flows=n_u, unit=unit,
                     paced=round(mean(pv), 3), paced_se=round(se(pv), 3),
                     unpaced=round(mean(uv), 3), unpaced_se=round(se(uv), 3), ratio=round(ratio, 3),
                     paced_events=round(mean([x[2] for x in P]), 2), unpaced_events=round(mean([x[2] for x in U]), 2),
                     paced_retrans=round(mean([x[3] for x in P]), 1), unpaced_retrans=round(mean([x[3] for x in U]), 1),
                     paced_first_epoch_pct=round(100 * mean([x[4] for x in P]), 1), unpaced_first_epoch_pct=round(100 * mean([x[4] for x in U]), 1)))
if a.out:
    with open(a.out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
