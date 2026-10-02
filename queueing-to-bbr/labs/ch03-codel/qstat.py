#!/usr/bin/env python3
"""qstat.py: sample one qdisc's backlog, drops and CoDel state, as CSV.

  ip netns exec rtr python3 qstat.py --dev r1 [--handle 2:] [--every 0.01] [--seconds 40] [--csv q.csv]

A copy of labs/common/qwatch.py, extended for the queue-delay chapter. It runs
`tc -s -j qdisc show dev DEV` in a loop and keeps one qdisc (by handle; default:
the first qdisc that is not the root, else the root). Besides backlog and drops it
records the CoDel fields that `tc -s` prints:

  codel:    count, lastcount, ldelay (us), drop_next (us from now), dropping
  fq_codel: new_flows_len, old_flows_len, new_flow_count, drop_overlimit, ecn_mark

Fields a qdisc does not have are left empty.
"""
import argparse, csv, json, subprocess, sys, time

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('--dev', required=True); p.add_argument('--handle')
p.add_argument('--every', type=float, default=0.01)
p.add_argument('--seconds', type=float, default=40); p.add_argument('--csv')
a = p.parse_args()

XS = ('count', 'lastcount', 'ldelay', 'drop_next', 'dropping', 'ecn_mark', 'drop_overlimit',
      'new_flows_len', 'old_flows_len', 'new_flow_count', 'maxpacket')
rows, t0 = [], time.monotonic()
while (t := time.monotonic() - t0) < a.seconds:
    q = json.loads(subprocess.run(['tc', '-s', '-j', 'qdisc', 'show', 'dev', a.dev],
                                  capture_output=True, text=True, check=True).stdout)
    if a.handle:
        x = next(x for x in q if x.get('handle') == a.handle)
    else:
        x = next((x for x in q if not x.get('root')), q[0])
    row = {'t_s': f'{t:.3f}', 'kind': x['kind'], 'backlog_bytes': x.get('backlog', 0),
           'backlog_pkts': x.get('qlen', 0), 'drops': x.get('drops', 0), 'sent_pkts': x.get('packets', 0)}
    for k in XS:
        v = x.get(k, '')
        row[k] = int(v) if isinstance(v, bool) else v
    if x['kind'] == 'codel' and row['dropping'] == '':
        row['dropping'] = 0            # tc prints "dropping" only while it is set
    rows.append(row)
    time.sleep(a.every)
out = open(a.csv, 'w', newline='') if a.csv else sys.stdout
w = csv.DictWriter(out, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
