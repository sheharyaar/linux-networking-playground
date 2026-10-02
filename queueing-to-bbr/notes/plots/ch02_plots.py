"""ch02_plots.py: the two plots in the queueing chapter (ch02.html).

  python3 notes/plots/ch02_plots.py      (run from queueing-to-bbr/)

Writes notes/plots/ch02-md1.svg (measured queueing delay against the M/D/1, P-K and M/M/1
formulas) and notes/plots/ch02-power.svg (the window sweep: throughput, RTT and Kleinrock's
power against a fixed window), then splices each into ch02.html between <!--PLOT:name--> and
<!--/PLOT:name--> markers. Data: labs/ch02-queues/data/.
"""
import csv, re, sys
sys.path.insert(0, 'notes/plots')
from svgplot import plot, SLOT

D = 'labs/ch02-queues/data/'
X = 1514 * 8 / 10e6                     # service time of one full frame at 10 Mbit/s, seconds

# ---- plot 1: wait in queue against utilisation ---------------------------------
fx = list(csv.DictReader(open(D + 'sweep-fixed.csv')))
mx = list(csv.DictReader(open(D + 'sweep-exp.csv')))
cv2_mix = sum(float(r['cv2_service']) for r in mx) / len(mx)
rhos = [i / 200 for i in range(0, 193)]                 # 0 .. 0.96
cap = lambda ys, top: [y if y <= top else None for y in ys]     # svgplot does not clip: stop lines at the frame
md1 = cap([r * X / (2 * (1 - r)) * 1e3 for r in rhos], 24)
mm1 = cap([r * X / (1 - r) * 1e3 for r in rhos], 24)
n_md1 = cap([r / (2 * (1 - r)) for r in rhos], 20)
n_mm1 = cap([r / (1 - r) for r in rhos], 20)
n_mix = cap([(1 + cv2_mix) / 2 * r / (1 - r) for r in rhos], 20)
f_rho = [float(r['rho']) for r in fx]; f_wq = [float(r['Wq_ms']) for r in fx]
m_rho = [float(r['rho']) for r in mx]; m_wq = [float(r['Wq_ms']) / float(r['EX_ms']) for r in mx]
f_norm = [w / (X * 1e3) for w in f_wq]
hover = []
for r in [x / 100 for x in range(5, 97, 1)]:
    hover.append((r, f'utilisation {r:.2f} · M/D/1 wait {r * X / (2 * (1 - r)) * 1e3:.2f} ms · '
                     f'M/M/1 wait {r * X / (1 - r) * 1e3:.2f} ms · in packet times: M/D/1 {r / (2 * (1 - r)):.2f}, '
                     f'mixed sizes {(1 + cv2_mix) / 2 * r / (1 - r):.2f}, M/M/1 {r / (1 - r):.2f}'))
notes1 = [dict(x=fr - 0.012, y=fw + 0.9, text=f'{fw:.1f}', anchor='end') for fr, fw in zip(f_rho, f_wq) if fr > 0.85]
md1_svg = plot(
    panels=[
        dict(height=220, y_range=(0, 24), y_ticks=[0, 6, 12, 18, 24], y_label='wait in queue (ms)',
             series=[dict(name='M/M/1', xs=rhos, ys=mm1, color=SLOT[1], end_label=(0.96, 23.5, 'M/M/1')),
                     dict(name='M/D/1', xs=rhos, ys=md1, color=SLOT[0], end_label=(0.96, 13.5, 'M/D/1'))],
             dots=[dict(name='measured', xs=f_rho, ys=f_wq, color=SLOT[0], r=4)],
             notes=notes1 + [dict(x=0.02, y=21, text='1514-byte frames, 10 Mbit/s: one packet time = 1.21 ms')],
             legend=[('M/D/1', SLOT[0], 'line'), ('M/M/1', SLOT[1], 'line'), ('measured, fixed size', SLOT[0], 'dot')]),
        dict(height=200, y_range=(0, 20), y_ticks=[0, 5, 10, 15, 20], y_label='wait ÷ mean service time',
             series=[dict(name='M/M/1', xs=rhos, ys=n_mm1, color=SLOT[1], end_label=(0.96, 19.5, 'M/M/1, c² = 1')),
                     dict(name='P-K mix', xs=rhos, ys=n_mix, color=SLOT[2], end_label=(0.96, 15.2, f'P-K, c² = {cv2_mix:.2f}')),
                     dict(name='M/D/1', xs=rhos, ys=n_md1, color=SLOT[0], end_label=(0.96, 11.0, 'M/D/1, c² = 0'))],
             dots=[dict(name='fixed', xs=f_rho, ys=f_norm, color=SLOT[0], r=4),
                   dict(name='mixed', xs=m_rho, ys=m_wq, color=SLOT[2], marker='x')],
             legend=[('measured, fixed size', SLOT[0], 'dot'), ('measured, mixed sizes', SLOT[2], 'x')]),
    ],
    x_range=(0, 1), x_ticks=[0, 0.2, 0.4, 0.6, 0.8, 1], x_label='utilisation ρ of the 10 Mbit/s bottleneck (Poisson arrivals)',
    label='Measured mean queueing delay of Poisson packets in netem rate 10mbit, against the M/D/1, P-K and M/M/1 formulas',
    hover=hover)
open('notes/plots/ch02-md1.svg', 'w').write(md1_svg)

# ---- plot 2: the window sweep and Kleinrock's power ----------------------------------
ws = list(csv.DictReader(open(D + 'wsweep.csv')))
fixed = [r for r in ws if r['W'] != 'none']
reno = [r for r in ws if r['W'] == 'none'][0]
RTT0 = 41.3                     # ms: 40 ms of netem delay + one 1.21 ms frame + the stack
PPS = 1e7 / (1514 * 8)          # packets per second the link drains
CG = PPS * 1448 * 8 / 1e6       # Mbit/s of TCP payload at full link
PIPE = PPS * RTT0 / 1000
Wm = [w / 2 for w in range(2, 181)]   # 1 .. 90
thr_m = [min(w * 1448 * 8 / (RTT0 / 1000) / 1e6, CG) for w in Wm]
rtt_m = [max(RTT0, w / PPS * 1000) for w in Wm]
pow_m = [(t / CG) / (r / RTT0) for t, r in zip(thr_m, rtt_m)]
W = [int(r['W']) for r in fixed]
thr = [float(r['goodput_mbps']) for r in fixed]
rtt = [float(r['rtt_ms']) for r in fixed]
pw = [(t / CG) / (r / RTT0) for t, r in zip(thr, rtt)]
rw = float(reno['cwnd_mean']); rt = float(reno['goodput_mbps']); rr = float(reno['rtt_ms'])
rp = (rt / CG) / (rr / RTT0)
hover2 = [(w, f'window {w} packets · measured {t:.2f} Mbit/s, RTT {r:.1f} ms, power {p:.2f} '
              f'· model {min(w * 1448 * 8 / (RTT0 / 1000) / 1e6, CG):.2f} Mbit/s, {max(RTT0, w / PPS * 1000):.1f} ms')
          for w, t, r, p in zip(W, thr, rtt, pw)]
vline = lambda top: dict(name='pipe', xs=[PIPE, PIPE], ys=[0, top], color='#898781', width=1, dash='4 4')
power_svg = plot(
    panels=[
        dict(height=130, y_range=(0, 12), y_ticks=[0, 4, 8, 12], y_label='goodput (Mbit/s)',
             series=[vline(12), dict(name='model', xs=Wm, ys=thr_m, color=SLOT[0], end_label=(90, 9.6, 'throughput'))],
             dots=[dict(name='measured', xs=W, ys=thr, color=SLOT[0], r=4),
                   dict(name='reno', xs=[rw], ys=[rt], color=SLOT[1], marker='x')],
             notes=[dict(x=PIPE + 1.5, y=1.2, text=f'pipe ≈ {PIPE:.0f} packets')],
             legend=[('model', SLOT[0], 'line'), ('measured, window held fixed', SLOT[0], 'dot'), ('Reno, no cap', SLOT[1], 'x')]),
        dict(height=130, y_range=(0, 120), y_ticks=[0, 40, 80, 120], y_label='RTT (ms)',
             series=[vline(120), dict(name='model', xs=Wm, ys=rtt_m, color=SLOT[2], end_label=(90, 109, 'RTT'))],
             dots=[dict(name='measured', xs=W, ys=rtt, color=SLOT[2], r=4),
                   dict(name='reno', xs=[rw], ys=[rr], color=SLOT[1], marker='x')]),
        dict(height=150, y_range=(0, 1.1), y_ticks=[0, 0.25, 0.5, 0.75, 1], y_label='power (1 = peak)',
             series=[vline(1.1), dict(name='model', xs=Wm, ys=pow_m, color=SLOT[3], end_label=(90, pow_m[-1], 'power'))],
             dots=[dict(name='measured', xs=W, ys=pw, color=SLOT[3], r=4),
                   dict(name='reno', xs=[rw], ys=[rp], color=SLOT[1], marker='x')],
             notes=[dict(x=rw + 2, y=rp + 0.08, text=f'Reno: {rp:.2f}')]),
    ],
    x_range=(0, 90), x_ticks=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90], x_label='window held fixed (packets), one flow, 10 Mbit/s, 40 ms',
    label='Goodput, RTT and normalised Kleinrock power of one TCP flow whose window is held fixed, measured on the bench',
    hover=hover2)
open('notes/plots/ch02-power.svg', 'w').write(power_svg)
print('pipe %.1f packets, link goodput %.2f Mbit/s, Reno power %.2f, mixed c2 %.3f' % (PIPE, CG, rp, cv2_mix))
for w, t, r, p in zip(W, thr, rtt, pw): print('  W=%d %.2f Mbit/s %.1f ms power %.2f' % (w, t, r, p))

# ---- splice into the page --------------------------------------------------------
page = 'ch02.html'
s = open(page).read()
for name, svg in (('ch02-md1', md1_svg), ('ch02-power', power_svg)):
    s, n = re.subn(r'<!--PLOT:%s-->.*?<!--/PLOT:%s-->' % (name, name),
                   lambda m: '<!--PLOT:%s-->\n%s\n<!--/PLOT:%s-->' % (name, svg, name), s, flags=re.S)
    print(name, 'spliced' if n else 'marker not found')
open(page, 'w').write(s)
