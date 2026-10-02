"""ch09_plots.py: the plot in the Eiffel chapter (ch09.html).

  python3 notes/plots/ch09_plots.py      (run from queueing-to-bbr/)

Writes notes/plots/ch09-race.svg from labs/ch09-eiffel/data/race-vs-packets.csv and splices it
into ch09.html between <!--PLOT:ch09-race--> and <!--/PLOT:ch09-race-->. Both axes are log10:
the values are plotted as logarithms and the tick labels are formatted back to plain numbers.
"""
import csv, math, re, sys
sys.path.insert(0, 'notes/plots')
import svgplot
from svgplot import plot, SLOT

def fmt(v):                       # tick labels: the axes carry log10 values
    x = float(f'{10 ** v:.2g}')
    if x >= 1e6: return f'{x / 1e6:g}M'
    if x >= 1e3: return f'{x / 1e3:g}k'
    return f'{x:g}'
svgplot.nice = fmt

rows = list(csv.DictReader(open('labs/ch09-eiffel/data/race-vs-packets.csv')))
Ns = sorted({int(r['n']) for r in rows})     # packets queued; the window is 20,000 buckets
get = {(int(r['n']), r['queue']): (float(r['ns_per_op']), float(r['touched_per_op'])) for r in rows}
L = math.log10
names = [('cffs', 'cFFS (two FFS trees)', SLOT[0]), ('heap', 'binary heap', SLOT[1]),
         ('scan', 'wheel + one bit per slot', SLOT[2]), ('wheel', 'wheel, slot by slot', SLOT[3])]
series, dots = [], []
end_y = {'wheel': L(9.6), 'heap': L(122), 'scan': L(15.5), 'cffs': L(25)}   # end labels, nudged apart
for q, label, color in names:
    xs = [L(N) for N in Ns]; ys = [L(get[(N, q)][0]) for N in Ns]
    series.append(dict(name=label, xs=xs, ys=ys, color=color, end_label=(xs[-1], end_y[q], label)))
    dots.append(dict(name=label, xs=xs, ys=ys, color=color, r=3))
hover = []
for N in Ns:
    c, h, s, w = (get[(N, q)] for q in ('cffs', 'heap', 'scan', 'wheel'))
    hover.append((L(N), f'{N:,} packets queued in 20,000 buckets · cFFS {c[0]:.1f} ns ({c[1]:.1f} words) · '
                        f'heap {h[0]:.1f} ns ({h[1]:.1f} comparisons) · one-bit scan {s[0]:.1f} ns ({s[1]:.1f} words) · '
                        f'slot-by-slot wheel {w[0]:.0f} ns ({w[1]:.0f} slots)'))
svg = plot(
    panels=[dict(height=250, y_range=(L(5), L(6000)), y_ticks=[L(v) for v in (10, 30, 100, 300, 1000, 3000)],
                 y_label='ns per pop + push', series=series, dots=dots,
                 notes=[dict(x=L(40), y=L(2000), text='20,000 buckets, as in the paper\'s kernel queue; the window moves forward')],
                 legend=[(lab, col, 'line') for _, lab, col in names])],
    x_range=(L(2.5), L(1.2e6)), x_ticks=[L(v) for v in (3, 10, 100, 1e3, 1e4, 1e5, 1e6)],
    x_label='packets kept in the queue (log scale)', label='Time per pop and push for four priority queues over 20,000 buckets as the number of queued packets grows, measured',
    hover=hover, right=180)
open('notes/plots/ch09-race.svg', 'w').write(svg)

page = 'ch09.html'
try:
    s = open(page).read()
    s, n = re.subn(r'<!--PLOT:ch09-race-->.*?<!--/PLOT:ch09-race-->',
                   lambda m: '<!--PLOT:ch09-race-->\n%s\n<!--/PLOT:ch09-race-->' % svg, s, flags=re.S)
    print('ch09-race', 'spliced' if n else 'marker not found')
    open(page, 'w').write(s)
except FileNotFoundError:
    print('ch09.html not written yet; SVG saved only')
