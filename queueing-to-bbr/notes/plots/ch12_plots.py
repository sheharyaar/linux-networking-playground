"""ch12_plots.py: the plot in the pods chapter (ch12.html).

  python3 notes/plots/ch12_plots.py      (run from queueing-to-bbr/)

Writes notes/plots/ch12-overload.svg and splices it into ch12.html between
<!--PLOT:ch12-overload--> and <!--/PLOT:ch12-overload--> markers.
Data: labs/ch12-pods/data/edt-{over,bigfq,short,kept}-rx.csv (rxcount.py, 100 ms bins).
"""
import csv, re, sys
sys.path.insert(0, 'notes/plots')
from svgplot import plot, SLOT

D = 'labs/ch12-pods/data/'
def load(n):
    rows = list(csv.DictReader(open(D + f'edt-{n}-rx.csv')))
    xs = [float(r['t_s']) for r in rows]
    return xs, [float(r['mbit_wire']) for r in rows], [float(r['owd_ms_median']) for r in rows]

runs = {n: load(n) for n in ('over', 'bigfq', 'short', 'kept')}
# drop the last, partial 100 ms bin of each run (the sender stops inside it)
for n, (xs, r, d) in runs.items():
    runs[n] = (xs[:-1], r[:-1], d[:-1])
col = {'over': SLOT[1], 'bigfq': SLOT[3], 'short': SLOT[2], 'kept': SLOT[0]}
name = {'over': 'socket lost, 2 s horizon, flow_limit 100',
        'bigfq': 'socket lost, 2 s horizon, flow_limit 2000',
        'short': 'socket lost, 100 ms horizon, flow_limit 100',
        'kept': 'socket kept, 2 s horizon, flow_limit 100'}

def ser(n, k, **kw):
    xs, r, d = runs[n]
    return dict(name=name[n], xs=xs, ys=(r if k == 'rate' else d), color=col[n], **kw)

hover = []
for i in range(4, 80, 5):                          # every half second
    t = runs['short'][0][i]
    parts = []
    for n in ('over', 'kept', 'short', 'bigfq'):
        xs, r, d = runs[n]
        if i < len(xs): parts.append(f'{name[n]}: {r[i]:.2f} Mbit/s, {d[i]:.0f} ms')
    hover.append((t, f't = {t:.1f} s · ' + ' · '.join(parts)))

svg = plot(
    panels=[
        dict(height=170, y_range=(0, 12), y_ticks=[0, 2, 4, 6, 8, 10, 12], y_label='delivered (Mbit/s)',
             refs=[dict(y=10, text='limit "10M"')],
             series=[ser('kept', 'rate'), ser('short', 'rate'), ser('bigfq', 'rate', dash='6 4'),
                     ser('over', 'rate', end_label=(8, 0.6, '0.6 Mbit/s'))],
             notes=[dict(x=4.0, y=10.9, text='three runs on the limit, 10.0 Mbit/s')],
             legend=[('socket lost, 2 s horizon', SLOT[1], 'line'), ('same, flow_limit 2000', SLOT[3], 'line'),
                     ('100 ms horizon', SLOT[2], 'line'), ('socket kept', SLOT[0], 'line')]),
        dict(height=120, y_range=(0, 2200), y_ticks=[0, 500, 1000, 1500, 2000], y_label='delay (ms)',
             series=[ser('over', 'delay', end_label=(8, 2000, 'both 2 s')),
                     ser('bigfq', 'delay', dash='6 4')],
             notes=[dict(x=2.6, y=600, text='both reach the 2 s horizon')]),
        dict(height=90, y_range=(0, 150), y_ticks=[0, 50, 100, 150], y_label='delay (ms)',
             series=[ser('short', 'delay', end_label=(8, 112, '100 ms')),
                     ser('kept', 'delay', end_label=(8, 76, '86 ms'))]),
    ],
    x_range=(0, 8), x_ticks=[0, 1, 2, 3, 4, 5, 6, 7, 8], x_label='seconds since the first datagram arrived',
    label='Delivered rate and one-way delay of a UDP pod offering 20 Mbit/s against a 10 Mbit/s EDT limit, four settings',
    hover=hover)
open('notes/plots/ch12-overload.svg', 'w').write(svg)

page = 'ch12.html'
s = open(page).read()
s, n = re.subn(r'<!--PLOT:ch12-overload-->.*?<!--/PLOT:ch12-overload-->',
               lambda m: '<!--PLOT:ch12-overload-->\n%s\n<!--/PLOT:ch12-overload-->' % svg, s, flags=re.S)
print('ch12-overload', 'spliced' if n else 'marker not found')
open(page, 'w').write(s)
