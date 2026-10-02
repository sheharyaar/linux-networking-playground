#!/usr/bin/env python3
"""summarise.py: turn one poisson.py run into the numbers queueing theory talks about.

  python3 summarise.py rx.csv [--q q.csv] [--rate 10e6] [--skip 1.0] [--label fixed-0.80] [--out sweep.csv]

From the receiver's log (seq, send_ns, recv_ns, frame_bytes) it computes, after skipping the
first --skip seconds:
  lambda      measured arrival rate (packets/s)
  E[X], E[X^2] service time moments, X = frame_bytes * 8 / rate
  rho         lambda * E[X]
  Wq          waiting time in the queue: one-way delay - own service time - base path delay,
              where the base is the smallest (delay - service time) seen in the run
  T           Wq + X, the time in the bottleneck
and the Pollaczek-Khinchine prediction Wq = lambda E[X^2] / (2 (1 - rho)), which for 1514-byte
frames is the M/D/1 formula rho / (2 mu (1 - rho)).
With --q (a qwatch.py CSV of the bottleneck) it also checks Little's law: mean backlog N
against lambda * T.
"""
import argparse, csv, statistics as st, sys

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('rx'); p.add_argument('--q'); p.add_argument('--rate', type=float, default=10e6)
p.add_argument('--skip', type=float, default=1.0); p.add_argument('--label', default='')
p.add_argument('--out', help='append one summary row to this CSV')
a = p.parse_args()

rows = [(int(r['seq']), int(r['send_ns']), int(r['recv_ns']), int(r['frame_bytes']))
        for r in csv.DictReader(open(a.rx))]
t0 = rows[0][1]
rows = [r for r in rows if r[1] - t0 >= a.skip * 1e9]
n = len(rows); span = (rows[-1][1] - rows[0][1]) / 1e9
lam = (n - 1) / span
X = [fb * 8 / a.rate for _, _, _, fb in rows]
D = [(rx - tx) / 1e9 for _, tx, rx, _ in rows]
base = min(d - x for d, x in zip(D, X))
Wq = [max(0.0, d - x - base) for d, x in zip(D, X)]
EX, EX2 = st.mean(X), st.mean(x * x for x in X)
rho = lam * EX
pk = lam * EX2 / (2 * (1 - rho))
mm1 = rho * EX / (1 - rho)
T = [w + x for w, x in zip(Wq, X)]
seqs = [r[0] for r in rows]; lost = (max(seqs) - min(seqs) + 1) - n
Wq_s = sorted(Wq)
out = {'label': a.label, 'packets': n, 'lost': lost, 'lambda_pps': round(lam, 1),
       'mean_frame_B': round(st.mean(r[3] for r in rows), 1), 'EX_ms': round(EX * 1e3, 4),
       'cv2_service': round(EX2 / EX**2 - 1, 3), 'rho': round(rho, 4),
       'Wq_ms': round(st.mean(Wq) * 1e3, 3), 'Wq_p95_ms': round(Wq_s[int(0.95 * n)] * 1e3, 3),
       'pk_Wq_ms': round(pk * 1e3, 3), 'mm1_Wq_ms': round(mm1 * 1e3, 3),
       'T_ms': round(st.mean(T) * 1e3, 3), 'base_ms': round(base * 1e3, 3)}
if a.q:
    q = [(float(r['t_s']), int(r['backlog_pkts']), int(r['sent_pkts'])) for r in csv.DictReader(open(a.q))]
    # qwatch has its own clock: keep the samples between the first and the last packet it saw
    # leave, minus the same warm-up as above
    sent0, sent1 = q[0][2], q[-1][2]
    t_first = next(t for t, _, s in q if s > sent0)
    t_last = next(t for t, _, s in reversed(q) if s < sent1)
    N = st.mean(b for t, b, _ in q if t_first + a.skip <= t <= t_last)
    out['N_backlog'] = round(N, 3); out['lambda_T'] = round(lam * st.mean(T), 3)
print(' '.join(f'{k}={v}' for k, v in out.items()))
if a.out:
    new = False
    try: open(a.out).close()
    except FileNotFoundError: new = True
    with open(a.out, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(out));
        if new: w.writeheader()
        w.writerow(out)
