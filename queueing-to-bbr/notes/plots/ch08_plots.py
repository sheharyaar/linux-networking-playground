"""ch08_plots.py: the plot in the departure-times chapter (ch08.html).

  python3 notes/plots/ch08_plots.py      (run from queueing-to-bbr/)

Writes notes/plots/ch08-ratemodel.svg and splices it into ch08.html between
<!--PLOT:ch08-ratemodel--> and <!--/PLOT:ch08-ratemodel--> markers.
"""
import csv, re, sys
sys.path.insert(0, 'notes/plots')
from svgplot import plot, SLOT

D = 'labs/ch08-edt/data/'
rows = list(csv.DictReader(open(D + 'rate-model-sweep.csv')))
bef = [r for r in rows if r['mode'] == 'before']
edt = {r['cap_mbit']: r for r in rows if r['mode'] == 'edt'}

def segs(cap):       # TSO autosizing as in 2018: (rate >> 10) / MSS, at least 2 (tcp_output.c:2256-2271)
    return max(2, (int(cap * 1e6 / 8) >> 10) // 1448)
def model(cap):      # two TSQ skbs wait in fq, each segs * 1514 wire bytes at the cap (ms)
    return 2 * segs(cap) * 1514 * 8 / (cap * 1e6) * 1e3

mx = [x / 10 for x in range(55, 2001)]
my = [model(x) for x in mx]
bx = [float(r['cap_mbit']) for r in bef]; by = [float(r['rtt_med_ms']) for r in bef]
ex = [float(r['cap_mbit']) for r in edt.values()]; ey = [float(r['rtt_med_ms']) for r in edt.values()]
hover = []
for r in bef:
    c = float(r['cap_mbit']); e = edt[r['cap_mbit']]
    hover.append((c, f"{r['cap_mbit']} Mbit/s cap · rate model: RTT {float(r['rtt_med_ms']):.3f} ms measured, "
                     f"{model(c):.3f} ms model, {r['burst_pkts']}-segment skbs {r['burst_gap_us']} us apart · "
                     f"EDT: RTT {float(e['rtt_med_ms']):.3f} ms, {e['burst_pkts']}-segment skbs {e['burst_gap_us']} us apart"))
svg = plot(
    panels=[
        dict(height=210, y_range=(0, 9), y_ticks=[0, 2, 4, 6, 8], y_label='RTT, rate model (ms)',
             series=[dict(name='model', xs=mx, ys=my, color=SLOT[0], width=1.5, end_label=(200, 2.05, 'model: two gaps in fq'))],
             dots=[dict(name='bench', xs=bx, ys=by, color=SLOT[0], r=3.5),
                   dict(name='cover letter', xs=[24], ys=[2.195], color=SLOT[1], marker='x')],
             notes=[dict(x=27, y=3.1, text='cover letter, before: 2.195 ms'),
                    dict(x=28, y=0.75, text='34 Mbit/s: still 2-segment skbs, 0.71 ms apart')],
             legend=[('model', SLOT[0], 'line'), ('bench, fq maxrate plus the socket cap', SLOT[0], 'dot'),
                     ('cover letter', SLOT[1], 'x')]),
        dict(height=110, y_range=(0, 0.2), y_ticks=[0, 0.1, 0.2], y_label='RTT, EDT (ms)',
             dots=[dict(name='bench edt', xs=ex, ys=ey, color=SLOT[2], r=3.5),
                   dict(name='cover letter after', xs=[24], ys=[0.165], color=SLOT[1], marker='x')],
             notes=[dict(x=27, y=0.168, text='cover letter, after: 0.165 ms')],
             legend=[('bench, fq plus the socket cap', SLOT[2], 'dot'), ('cover letter', SLOT[1], 'x')]),
    ],
    x_range=(0, 200), x_ticks=[0, 24, 48, 96, 144, 192], x_label='pacing cap, SO_MAX_PACING_RATE (Mbit/s)',
    label='RTT TCP measures on a 0.03 ms path when fq derives each gap from the rate, against when TCP stamps each departure time',
    hover=hover)
open('notes/plots/ch08-ratemodel.svg', 'w').write(svg)

page = 'ch08.html'
try:
    s = open(page).read()
    s, n = re.subn(r'<!--PLOT:ch08-ratemodel-->.*?<!--/PLOT:ch08-ratemodel-->',
                   lambda m: '<!--PLOT:ch08-ratemodel-->\n%s\n<!--/PLOT:ch08-ratemodel-->' % svg, s, flags=re.S)
    print('ch08-ratemodel', 'spliced' if n else 'marker not found')
    open(page, 'w').write(s)
except FileNotFoundError:
    print('ch08.html not written yet; SVG saved only')
