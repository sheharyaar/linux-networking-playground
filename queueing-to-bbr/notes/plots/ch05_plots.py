"""ch05_plots.py: the two plots in the small-queues chapter (ch05.html).

  python3 notes/plots/ch05_plots.py      (run from queueing-to-bbr/)

Writes notes/plots/ch05-tsq.svg and notes/plots/ch05-spacing.svg, then splices each one into
ch05.html between <!--PLOT:name--> and <!--/PLOT:name--> markers.
"""
import csv, re, sys
sys.path.insert(0, 'notes/plots')
from svgplot import plot, SLOT

D = 'labs/ch05-small-queues/data/'

def rows(name): return list(csv.DictReader(open(D + name)))
def col(rs, k, f=float): return [f(r[k]) for r in rs]

# ---- plot 1: the sender's own qdisc, with and without TSQ seeing it ------------------
net = rows('orphan-netem-qdisc.csv'); tbf = rows('tsq-tbf-default-qdisc.csv'); t4k = rows('tsq-tbf-lob4k-qdisc.csv')
nf = rows('orphan-netem-flow.csv'); tf = rows('tsq-tbf-default-flow.csv')
nt, nb = col(net, 't_s'), [b / 1e6 for b in col(net, 'backlog_bytes')]
tt, tb = col(tbf, 't_s'), [b / 1e3 for b in col(tbf, 'backlog_bytes')]
kt, kb = col(t4k, 't_s'), [b / 1e3 for b in col(t4k, 'backlog_bytes')]
def at(ts, vs, x):
    i = min(range(len(ts)), key=lambda k: abs(ts[k] - x)); return vs[i]
nft, nfr = col(nf, 't_s'), col(nf, 'rtt_ms'); tft, tfr = col(tf, 't_s'), col(tf, 'rtt_ms')
hover = []
for k in range(0, 201):
    x = k * 0.1
    hover.append((x, f't = {x:.1f} s · netem on s0: {at(nt, nb, x):.2f} MB queued, RTT {at(nft, nfr, x):.0f} ms · '
                     f'tbf on s0: {at(tt, tb, x):.1f} KB queued, RTT {at(tft, tfr, x):.1f} ms · '
                     f'tbf, 4 KB limit: {at(kt, kb, x):.1f} KB'))
tsq = plot(
    panels=[
        dict(height=170, y_range=(0, 16), y_ticks=[0, 4, 8, 12, 16], y_label='queued (MB)',
             series=[dict(name='netem', xs=nt, ys=nb, color=SLOT[1], width=1.5, end_label=(20, 7.2, 'netem rate 10mbit'))],
             notes=[dict(x=0.3, y=14.6, text='netem frees each skb at enqueue, so TSQ never sees this queue')],
             legend=[('netem on s0: socket charge dropped at enqueue', SLOT[1], 'line')]),
        dict(height=150, y_range=(0, 12), y_ticks=[0, 4, 8, 12], y_label='queued (KB)',
             series=[dict(name='tbf default', xs=tt, ys=tb, color=SLOT[0], width=1.5, end_label=(20, 9.1, 'tbf, default limit')),
                     dict(name='tbf 4k', xs=kt, ys=kb, color=SLOT[2], width=1.5, end_label=(20, 4.5, 'tbf, 4 KB limit'))],
             refs=[],
             legend=[('tbf on s0, default (4 MB)', SLOT[0], 'line'), ('tbf on s0, 4 KB limit', SLOT[2], 'line')]),
    ],
    x_range=(0, 20), x_ticks=[0, 5, 10, 15, 20], x_label='seconds since connect',
    label='Bytes queued in the sender\'s own qdisc for one Reno flow at 10 Mbit/s: megabytes when netem orphans the skb, kilobytes when TSQ can see it',
    hover=hover)
open('notes/plots/ch05-tsq.svg', 'w').write(tsq)

# ---- plot 2: packets per 5 ms leaving the sender, first 250 ms ----------------------
def bins(name, width=5, span=250):
    t = [float(r['t_s']) * 1000 for r in rows(name)]
    xs = list(range(0, span + 1, width))
    return xs, [sum(1 for v in t if b <= v < b + width) for b in xs]
px, py = bins('pace-pfifo-nocap-packets.csv')
fx, fy = bins('pace-fq-nocap-packets.csv')
cx, cy = bins('pace-fq-cap5-packets.csv')
hover2 = [(x, f'{x}-{x + 5} ms · pfifo: {a} packets · fq: {b} · fq, 5 Mbit/s cap: {c}')
          for x, a, b, c in zip(px, py, fy, cy)]
spacing = plot(
    panels=[dict(height=150, y_range=(0, 12), y_ticks=[0, 4, 8, 12], y_label='pfifo (pkts/5 ms)',
                 series=[dict(name='pfifo', xs=px, ys=py, color=SLOT[1], step=True, width=1.5, end_label=(250, 8, 'pfifo: no pacing'))],
                 notes=[dict(x=44, y=10.6, text='bursts at 2x the bottleneck, then silence')],
                 legend=[('pfifo on s0, no pacing', SLOT[1], 'line')]),
            dict(height=150, y_range=(0, 12), y_ticks=[0, 4, 8, 12], y_label='fq (pkts/5 ms)',
                 series=[dict(name='fq', xs=fx, ys=fy, color=SLOT[0], step=True, width=1.5, end_label=(250, 8, 'fq: rate TCP computes')),
                         dict(name='fq cap', xs=cx, ys=cy, color=SLOT[2], step=True, width=1.5, end_label=(250, 2, 'fq: 5 Mbit/s cap'))],
                 notes=[dict(x=44, y=10.6, text='the same rounds spread over the RTT')],
                 legend=[('fq, pacing at the computed rate', SLOT[0], 'line'), ('fq, SO_MAX_PACING_RATE 5 Mbit/s', SLOT[2], 'line')])],
    x_range=(0, 250), x_ticks=[0, 50, 100, 150, 200, 250], x_label='ms since the first data packet (seen at rtr:r0, before the 10 Mbit/s bottleneck)',
    label='Packets per 5 ms leaving the sender during slow start, with pfifo and with fq', hover=hover2)
open('notes/plots/ch05-spacing.svg', 'w').write(spacing)

# ---- splice into the page -----------------------------------------------------------
page = 'ch05.html'
try:
    s = open(page).read()
    for name, svg in (('ch05-tsq', tsq), ('ch05-spacing', spacing)):
        s, n = re.subn(r'<!--PLOT:%s-->.*?<!--/PLOT:%s-->' % (name, name),
                       lambda m: '<!--PLOT:%s-->\n%s\n<!--/PLOT:%s-->' % (name, svg, name), s, flags=re.S)
        print(name, 'spliced' if n else 'marker not found')
    open(page, 'w').write(s)
except FileNotFoundError:
    print('ch05.html not written yet; SVGs saved only')
