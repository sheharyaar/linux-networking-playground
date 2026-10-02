#!/usr/bin/env python3
"""share.py: each flow's goodput over a time window, its share of the total, and Jain's index.

  python3 share.py --from 30 --to 120 bbr.csv cubic.csv

Goodput is the growth of bytes_acked (from flow.py's TCP_INFO samples) between the first sample at
or after --from and the last sample at or before --to. Jain's fairness index over n flows with
rates x_i is (sum x)^2 / (n * sum x^2): 1 when the rates are equal, 1/n when one flow has them all.
It also prints each flow's retransmissions in the window, and its mean RTT.
"""
import argparse, csv

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('--from', dest='t0', type=float, default=0.0)
p.add_argument('--to', dest='t1', type=float, default=1e9)
p.add_argument('csv', nargs='+')
a = p.parse_args()

flows = []
for f in a.csv:
    rows = [r for r in csv.DictReader(open(f)) if a.t0 <= float(r['t_s']) <= a.t1]
    if len(rows) < 2:
        raise SystemExit(f'share.py: {f} has fewer than two samples in [{a.t0}, {a.t1}]')
    first, last = rows[0], rows[-1]
    dt = float(last['t_s']) - float(first['t_s'])
    mbps = (int(last['bytes_acked']) - int(first['bytes_acked'])) * 8 / dt / 1e6
    retr = int(last['total_retrans']) - int(first['total_retrans'])
    rtt = sum(float(r['rtt_ms']) for r in rows) / len(rows)
    flows.append((last.get('label') or f, mbps, retr, rtt, dt))

tot = sum(x[1] for x in flows)
jain = tot ** 2 / (len(flows) * sum(x[1] ** 2 for x in flows)) if tot else 0
for label, mbps, retr, rtt, dt in flows:
    print(f'{label:>8}: {mbps:6.2f} Mbit/s  share {100 * mbps / tot:5.1f}%  retrans {retr:6d}  mean rtt {rtt:6.1f} ms  ({dt:.0f} s window)')
print(f'   total: {tot:6.2f} Mbit/s  Jain index {jain:.3f}')
