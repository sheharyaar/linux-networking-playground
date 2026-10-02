#!/usr/bin/env python3
"""eyeq_loop.py: EyeQ's rate rule (p. 302) on one link, counted in 200 us steps.

  python3 eyeq_loop.py

R <- R * (1 - alpha * (y - C) / C), with y = N * R (N senders at the advertised rate) and C = 1.
"Taking care to keep R_i positive" (p. 302) is done here as a floor of 1 Mb/s on a 10 Gb/s link
(1e-4), the floor EyeQ's limiters fall to without feedback (p. 302). A run ends when R is within
0.01% of R* = 1/N, the paper's criterion (p. 303). No third-party modules.
"""
import math
def steps(N, a, R0, floor=1e-4, tol=1e-4, nmax=1000):
    R, Rs = R0, 1.0 / N
    for n in range(1, nmax + 1):
        R = max(R * (1 - a * (N * R - 1)), floor)
        if abs(R - Rs) / Rs < tol: return n
    return None
print('alpha 0.5, all senders starting at line rate (the test on p. 305 starts there):')
for N in (2, 4, 14, 100):
    n = steps(N, 0.5, 1.0)
    print(f'  N = {N:>3}: {n} steps = {n * 0.2:.1f} ms at 200 us per step')
print(f'linear part alone, error 1 down to 1e-4 at factor 0.5: {math.log(1e-4) / math.log(0.5):.1f} steps')
print('N = 14, start at 1.5 R*, other gains:')
for a in (0.25, 0.5, 1.0, 1.5, 1.9, 2.1):
    n = steps(14, a, 1.5 / 14)
    print(f'  alpha {a}: ' + (f'{n} steps' if n else 'never settles (diverges or oscillates)'))
