#!/usr/bin/env python3
"""goodput.py: per-flow goodput over time from flow.py CSVs, on one shared time axis.

  python3 goodput.py a.csv b.csv [--bin 1.0] [--csv goodput.csv]

Each input is a flow.py (chapter 4 copy) sender CSV with wall_s and bytes_acked columns.
Time zero is the earliest wall_s across all files. For every bin it prints the Mbit/s each
flow got (bytes_acked difference / bin), then a summary line per phase you pass with
--phase NAME:START:END (seconds on the shared axis), e.g. --phase both:12:28.
"""
import argparse, csv, sys

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('files', nargs='+'); p.add_argument('--bin', type=float, default=1.0)
p.add_argument('--csv'); p.add_argument('--phase', action='append', default=[])
a = p.parse_args()
flows = {f: [(float(r['wall_s']), int(r['bytes_acked'])) for r in csv.DictReader(open(f))] for f in a.files}
t0 = min(rows[0][0] for rows in flows.values())
end = max(rows[-1][0] for rows in flows.values()) - t0

def acked_at(rows, t):                 # bytes acked by shared time t (0 before start, last after end)
    v = 0
    for w, b in rows:
        if w - t0 > t: break
        v = b
    return v

out = []
t = 0.0
while t + a.bin <= end + 1e-9:
    row = {'t_s': f'{t + a.bin / 2:.2f}'}
    for f, rows in flows.items():
        row[f] = round((acked_at(rows, t + a.bin) - acked_at(rows, t)) * 8 / a.bin / 1e6, 3)
    out.append(row); t += a.bin
w = csv.DictWriter(open(a.csv, 'w', newline='') if a.csv else sys.stdout, fieldnames=list(out[0]))
w.writeheader(); w.writerows(out)
for ph in a.phase:
    name, s, e = ph.split(':'); s, e = float(s), float(e)
    rates = {f: (acked_at(r, e) - acked_at(r, s)) * 8 / (e - s) / 1e6 for f, r in flows.items()}
    print(f'phase {name} {s:g}-{e:g} s: ' + '  '.join(f'{f} {v:.2f} Mbit/s' for f, v in rates.items())
          + f'  total {sum(rates.values()):.2f}', file=sys.stderr)
