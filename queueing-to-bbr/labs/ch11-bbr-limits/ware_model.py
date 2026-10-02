#!/usr/bin/env python3
"""ware_model.py: Ware et al.'s model of BBRv1's share against loss-based flows (IMC 2019, pp. 140-142),
and the loss-cliff arithmetic of Cao et al. (IMC 2019, p. 134). Runs anywhere; needs no BBR.

  python3 ware_model.py                       the bench: 10 Mbit/s, 40 ms, 1514-byte frames, 1 BBR flow
  python3 ware_model.py --mbps 1000 --rtt 20  Cao et al.'s Fig. 8 path
  python3 ware_model.py --cap 4               the paper's modified BBR with a 4-BDP inflight cap

Model (the paper's notation): c = link rate in packets/s, l = RTT with no queue, q = queue in packets,
X = q / (c l), N = BBR flows, k = cwnd_gain (2 in BBRv1). The loss-based flows' share p solves
   k (1 - p) c ((p q + 4 N) / c + l) = (1 - p)(q + c l)                     (Eq. 9 with k = 2)
   p = 1/k - (k - 1) / (k X) - 4 N / q,   and p < 0 means BBR takes the whole link (p. 142)
ProbeRTT costs Probe_time / d = (q / c + 0.2 + l) / 10 of the time (Eq. 11), so
   BBR_frac = (1 - p) (1 - (q / c + 0.2 + l) / 10)                           (Eq. 10)
The simple model (p. 140: one BBR flow, q >> c l) gives p = 1/k: half the link for k = 2.
"""
import argparse

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('--mbps', type=float, default=10); p.add_argument('--rtt', type=float, default=40, help='ms')
p.add_argument('--frame', type=int, default=1514, help='bytes on the wire per packet')
p.add_argument('--flows', type=int, default=1, help='N, BBR flows'); p.add_argument('--cap', type=float, default=2, help='k, cwnd_gain')
p.add_argument('--x', default='0.25 0.5 1 2 4 8 10 16 32 64', help='queue sizes in BDPs')
a = p.parse_args()

c = a.mbps * 1e6 / 8 / a.frame
l = a.rtt / 1000
bdp = c * l
k, N = a.cap, a.flows

def share(X):
    q = X * bdp
    pl = 1 / k - (k - 1) / (k * X) - 4 * N / q
    pl = min(max(pl, 0.0), 1.0)
    probe = (q / c + 0.2 + l) / 10
    return pl, 1 - pl, (1 - pl) * (1 - probe), probe

print(f'path: {a.mbps:g} Mbit/s, {a.rtt:g} ms, {a.frame}-byte frames: c = {c:.1f} packets/s, BDP = {bdp:.1f} packets')
print(f'BBR flows N = {N}, inflight cap k = {k:g} BDP; simple model (deep buffer, one flow): BBR share {1 - 1 / k:.0%}')
print(f'{"X (BDP)":>8} {"q (pkts)":>9} {"p loss-based":>13} {"BBR, Eq. 9":>11} {"ProbeRTT time":>14} {"BBR_frac":>9} {"Jain, 2 flows":>14}')
for X in [float(x) for x in a.x.split()]:
    pl, b9, b10, probe = share(X)
    jain = 1 / (2 * (b10 ** 2 + (1 - b10) ** 2))
    print(f'{X:8g} {X * bdp:9.0f} {pl:13.3f} {b9:11.3f} {probe:13.1%} {b10:9.3f} {jain:14.3f}')

print('\nCao et al.\'s cliff (Eq. 3, p. 134): the probe delivers g (1 - p) of the estimate; below 1 the estimate decays')
for g in (1.1, 1.25, 1.5):
    print(f'  pacing gain {g:<4}: cliff p = 1 - 1/g = {1 - 1 / g:6.1%};  with v7.2\'s 1% pacing margin, 1 - 1/(0.99 g) = {1 - 1 / (0.99 * g):6.1%}')
t = 50 / 256
print(f'BBRv1 policer detector (tcp_bbr.c:188, 743): lost/delivered >= 50/256 = {t:.2%}; with uniform random loss p,')
print(f'  lost/delivered = p / (1 - p), so it is crossed at p = 50/306 = {t / (1 + t):.2%} of the packets sent')
