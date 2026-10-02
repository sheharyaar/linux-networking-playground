#!/usr/bin/env python3
"""summarise.py: medians per (family, size) from matrix.sh's JSON lines, and a CSV.

  python3 summarise.py data/veth-matrix.jsonl [--csv data/veth-summary.csv]

cpu_s_per_GB = busy seconds of the two pinned CPUs (from /proc/stat) per 10^9 bytes delivered.
"""
import json, statistics as st, sys, csv, argparse
p = argparse.ArgumentParser(); p.add_argument('jsonl'); p.add_argument('--csv'); a = p.parse_args()
rows = [json.loads(l) for l in open(a.jsonl)]
idle = [r['cpus_busy_s'] / r['seconds'] for r in rows if r.get('role') == 'idle']
print(f'idle baseline of the two pinned CPUs: {", ".join(f"{x:.2f}" for x in idle)} CPU-s per s')
out = []
for fam in (6, 4):
    for size in (65536, 185000):
        rs = [r for r in rows if r.get('role') == 'send' and r['family'] == fam and r['size'] == size]
        g = [r['gbps'] for r in rs]
        cpb = [r['cpus_busy_s'] / (r['bytes'] / 1e9) for r in rs]
        snd = [(r['utime_s'] + r['stime_s']) / (r['bytes'] / 1e9) for r in rs]
        rcv = [(r['recv_utime_s'] + r['recv_stime_s']) / (r['bytes'] / 1e9) for r in rs]
        hb = [r['host_busy_frac'] for r in rs]
        out.append(dict(family=fam, size=size, runs=len(rs), gbps_median=round(st.median(g), 1),
                        gbps_min=round(min(g), 1), gbps_max=round(max(g), 1),
                        cpu_s_per_GB_median=round(st.median(cpb), 4), cpu_s_per_GB_min=round(min(cpb), 4),
                        cpu_s_per_GB_max=round(max(cpb), 4),
                        sender_task_s_per_GB=round(st.median(snd), 4), sink_task_s_per_GB=round(st.median(rcv), 4),
                        host_busy_frac_median=round(st.median(hb), 3)))
for o in out:
    print(f"IPv{o['family']} {o['size']:>6}: {o['gbps_median']:5.1f} Gbit/s ({o['gbps_min']}-{o['gbps_max']}), "
          f"{o['cpu_s_per_GB_median']:.4f} CPU-s/GB ({o['cpu_s_per_GB_min']}-{o['cpu_s_per_GB_max']}); "
          f"tasks: sender {o['sender_task_s_per_GB']:.4f}, sink {o['sink_task_s_per_GB']:.4f}; host busy {o['host_busy_frac_median']}")
for fam in (6, 4):
    a_, b_ = [o for o in out if o['family'] == fam]
    print(f"IPv{fam}: throughput x{b_['gbps_median'] / a_['gbps_median']:.2f}, CPU per byte x{b_['cpu_s_per_GB_median'] / a_['cpu_s_per_GB_median']:.2f}")
if a.csv:
    w = csv.DictWriter(open(a.csv, 'w', newline=''), fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
