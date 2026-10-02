"""ch01_plots.py: the two plots in the congestion-avoidance chapter (ch01.html).

  python3 notes/plots/ch01_plots.py      (run from queueing-to-bbr/)

Writes notes/plots/ch01-sawtooth.svg and notes/plots/ch01-rto.svg, then splices each one into
ch01.html between <!--PLOT:name--> and <!--/PLOT:name--> markers.
"""
import csv, math, random, re, sys
sys.path.insert(0, 'notes/plots')
from svgplot import plot, SLOT, INK, MUTED

D = 'labs/ch01-aimd/data/'

# ---- plot 1: the measured Reno sawtooth and the bottleneck queue ----------------
rows = list(csv.DictReader(open(D + 'reno-sawtooth.csv')))
rows = rows[::2]
t = [float(r['t_s']) for r in rows]
cw = [int(r['cwnd']) for r in rows]
ss = [int(r['ssthresh']) if r['ssthresh'] else None for r in rows]
q = list(csv.DictReader(open(D + 'reno-bottleneck-queue.csv')))
qt = [float(r['t_s']) for r in q]; qp = [int(r['backlog_pkts']) for r in q]

def at(ts, vs, x):
    i = min(range(len(ts)), key=lambda k: abs(ts[k] - x)); return vs[i]
hover = []
for k in range(0, 300):
    x = k * 0.1
    hover.append((x, f't = {x:.1f} s · cwnd {at(t, cw, x)} packets · ssthresh {at(t, ss, x) or "not set"} · '
                     f'queue {at(qt, qp, x)} packets'))
saw = plot(
    panels=[
        dict(height=230, y_range=(0, 180), y_ticks=[0, 40, 80, 120, 160], y_label='packets',
             series=[dict(name='cwnd', xs=t, ys=cw, color=SLOT[0], end_label=(30, 64, 'cwnd')),
                     dict(name='ssthresh', xs=t, ys=ss, color=SLOT[1], step=True, end_label=(30, 48, 'ssthresh'))],
             refs=[dict(y=33, text='pipe ≈ 33'), dict(y=83, text='pipe + queue = 83')],
             notes=[dict(x=1.0, y=163, text='← slow start overshoots to 166, 86 packets lost')],
             legend=[('cwnd', SLOT[0], 'line'), ('ssthresh', SLOT[1], 'line')]),
        dict(height=110, y_range=(0, 50), y_ticks=[0, 25, 50], y_label='queue (pkts)',
             series=[dict(name='queue', xs=qt, ys=qp, color=SLOT[2], width=1.5, end_label=(30, 20, 'bottleneck queue'))],
             refs=[dict(y=8, text='never below 8')]),
    ],
    x_range=(0, 30), x_ticks=[0, 5, 10, 15, 20, 25, 30], x_label='seconds since connect',
    label='Measured Reno congestion window, slow-start threshold and bottleneck queue over 30 seconds',
    hover=hover)
open('notes/plots/ch01-sawtooth.svg', 'w').write(saw)

# ---- plot 2: how often each retransmit timer fires before the ack, as load rises ----
# Model: RTT = b + Q, with Q exponential of mean m = s*rho/(1-rho) (b = 100 ms path, s = 100 ms).
# 2R      is late when Q > b + 2m          -> exp(-2 - b/m)
# A + kD  is late when Q > m + k*(2m/e)     -> exp(-(1 + 2k/e))   (E|Q - m| = 2m/e for an exponential)
b, s_ = 100.0, 100.0
rhos = [i / 100 for i in range(1, 96)]
def late_2r(r):
    m = s_ * r / (1 - r); return 100 * math.exp(-2 - b / m)
def late_kd(k): return 100 * math.exp(-(1 + 2 * k / math.e))
l2r = [late_2r(r) for r in rhos]; l2d = [late_kd(2)] * len(rhos); l4d = [late_kd(4)] * len(rhos)
hover2 = [(r, f'load {r:.2f} · 2R late {late_2r(r):.1f}% · A+2D late {late_kd(2):.1f}% · A+4D late {late_kd(4):.1f}%')
          for r in rhos[::2]]
rto = plot(
    panels=[dict(height=240, y_range=(0, 15), y_ticks=[0, 5, 10, 15], y_label='% of acks later than the timer',
                 series=[dict(name='2R', xs=rhos, ys=l2r, color=SLOT[1], end_label=(0.95, l2r[-1] + 0.6, 'RFC 793: 2R')),
                         dict(name='A+2D', xs=rhos, ys=l2d, color=SLOT[0], end_label=(0.95, l2d[-1] - 0.6, 'A+2D (the paper)')),
                         dict(name='A+4D', xs=rhos, ys=l4d, color=SLOT[2], end_label=(0.95, l4d[-1], 'A+4D (Linux)'))],
                 refs=[],
                 notes=[dict(x=0.02, y=13.6, text='2R heads for e⁻² = 13.5% once queueing swamps the 100 ms path')],
                 legend=[('RFC 793: 2R', SLOT[1], 'line'), ('A+2D', SLOT[0], 'line'), ('A+4D', SLOT[2], 'line')])],
    x_range=(0, 1), x_ticks=[0, 0.25, 0.5, 0.75, 1], x_label='load ρ on the bottleneck (100 ms path, exponential queueing delay)',
    label='Fraction of acks that arrive after the retransmit timer, for three timers, as load rises', hover=hover2)
open('notes/plots/ch01-rto.svg', 'w').write(rto)
print('2R late at rho .3 .5 .75 .9:', [round(late_2r(r), 1) for r in (.3, .5, .75, .9)], 'A+2D', round(late_kd(2), 2), 'A+4D', round(late_kd(4), 2))

# ---- splice into the page --------------------------------------------------------
page = 'ch01.html'
try:
    s = open(page).read()
    for name, svg in (('ch01-sawtooth', saw), ('ch01-rto', rto)):
        s, n = re.subn(r'<!--PLOT:%s-->.*?<!--/PLOT:%s-->' % (name, name),
                       lambda m: '<!--PLOT:%s-->\n%s\n<!--/PLOT:%s-->' % (name, svg, name), s, flags=re.S)
        print(name, 'spliced' if n else 'marker not found')
    open(page, 'w').write(s)
except FileNotFoundError:
    print('ch01.html not written yet; SVGs saved only')
