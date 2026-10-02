"""ch14_plots.py: the plot in the BIG TCP chapter (ch14.html).

  python3 notes/plots/ch14_plots.py      (run from queueing-to-bbr/)

Writes notes/plots/ch14-cpu.svg (CPU per GB and throughput against skb size: the measured runs on
the rootless veth pair, and the two-term model fitted through the medians), then splices it into
ch14.html between <!--PLOT:ch14-cpu--> and <!--/PLOT:ch14-cpu--> markers.
"""
import json, re, statistics as st, sys
sys.path.insert(0, 'notes/plots')
from svgplot import plot, SLOT

D = 'labs/ch14-big-tcp/data/'
rows = [json.loads(l) for l in open(D + 'veth-matrix.jsonl')]
send = [r for r in rows if r.get('role') == 'send']
MSS = {6: 1428, 4: 1448}
def payload(fam, size):                       # bytes of TCP payload per skb: (size - 321) // MSS * MSS
    return (size - 321) // MSS[fam] * MSS[fam]

pts = {}                                      # (fam, size) -> (payload KB, [cpu/GB], [Gbit/s])
for fam in (6, 4):
    for size in (65536, 185000):
        rs = [r for r in send if r['family'] == fam and r['size'] == size]
        pts[fam, size] = (payload(fam, size) / 1000,
                          [r['cpus_busy_s'] / (r['bytes'] / 1e9) for r in rs], [r['gbps'] for r in rs])

def fit(fam):                                 # CPU per skb = F + b * bytes, through the two medians
    (s1, c1, _), (s2, c2, _) = pts[fam, 65536], pts[fam, 185000]
    s1, s2 = s1 * 1000, s2 * 1000
    k1, k2 = st.median(c1) * s1, st.median(c2) * s2      # CPU-s per GB x bytes = ns per skb
    b = (k2 - k1) / (s2 - s1); F = k1 - b * s1
    return F, b                                # F in ns per skb, b in CPU-s per GB (= ns per byte)
F6, b6 = fit(6); F4, b4 = fit(4)
xs = [k for k in range(44, 541, 4)]
model6 = [F6 / (x * 1000) + b6 for x in xs]
ceiling = payload(6, 524280) / 1000

hover = []
for x in xs[::2]:
    hover.append((x, f'{x} KB of payload per skb · model (IPv6 fit): {F6 / (x * 1000) + b6:.3f} CPU-s per GB, '
                     f'of which {F6 / (x * 1000):.3f} per-skb and {b6:.3f} per-byte'))
for (fam, size), (x, c, g) in pts.items():
    hover.append((x, f'IPv{fam}, knobs {size}: {x * 1000:,.0f} B per skb · CPU {st.median(c):.4f} CPU-s per GB '
                     f'(runs {min(c):.3f}-{max(c):.3f}) · {st.median(g):.1f} Gbit/s (runs {min(g):.1f}-{max(g):.1f})'))
hover.sort()

svg = plot(
    panels=[
        dict(height=200, y_range=(0.1, 0.3), y_ticks=[0.1, 0.15, 0.2, 0.25, 0.3], y_label='CPU-s per GB',
             series=[dict(name='model', xs=xs, ys=model6, color=SLOT[2], end_label=(540, model6[-1] + 0.014, 'model: 6.2 µs per skb'))],
             dots=[dict(name='IPv4', xs=[pts[4, s][0]] * 5, ys=pts[4, s][1], color=SLOT[1], marker='x') for s in (65536, 185000)] +
                  [dict(name='IPv6', xs=[pts[6, s][0]] * 5, ys=pts[6, s][1], color=SLOT[0], r=4.5) for s in (65536, 185000)] +
                  [dict(name='ceiling', xs=[ceiling], ys=[F6 / (ceiling * 1000) + b6], color=SLOT[2], r=4.5)],
             refs=[dict(y=b6, text='per-byte floor 0.12')],
             notes=[dict(x=74, y=0.262, text='knobs at 65,536'), dict(x=194, y=0.185, text='knobs at 185,000'),
                    dict(x=ceiling, y=0.152, text='ceiling 524,280: 0.134', anchor='end')],
             legend=[('IPv6 runs', SLOT[0], 'dot'), ('IPv4 runs', SLOT[1], 'x'), ('model through the IPv6 medians', SLOT[2], 'line')]),
        dict(height=130, y_range=(40, 80), y_ticks=[40, 60, 80], y_label='Gbit/s',
             dots=[dict(name='IPv4', xs=[pts[4, s][0]] * 5, ys=pts[4, s][2], color=SLOT[1], marker='x') for s in (65536, 185000)] +
                  [dict(name='IPv6', xs=[pts[6, s][0]] * 5, ys=pts[6, s][2], color=SLOT[0], r=4.5) for s in (65536, 185000)],
             series=[dict(name='v6', xs=[pts[6, 65536][0], pts[6, 185000][0]], ys=[st.median(pts[6, s][2]) for s in (65536, 185000)],
                          color=SLOT[0], width=1.5, dash='3 3', end_label=(pts[6, 185000][0], 69.1, 'IPv6 median 69'))],
             legend=[('IPv6 runs', SLOT[0], 'dot'), ('IPv4 runs', SLOT[1], 'x')]),
    ],
    x_range=(0, 540), x_ticks=[0, 64, 128, 185, 256, 384, 512], x_label='TCP payload per skb (KB)',
    label='CPU seconds per gigabyte and throughput of one bulk TCP flow over a veth pair, at 64 KB and 185,000-byte skbs, with a two-term model',
    hover=hover)
open('notes/plots/ch14-cpu.svg', 'w').write(svg)

page = open('ch14.html').read()
new = re.sub(r'<!--PLOT:ch14-cpu-->.*?<!--/PLOT:ch14-cpu-->',
             lambda m: '<!--PLOT:ch14-cpu-->\n' + svg + '\n<!--/PLOT:ch14-cpu-->', page, flags=re.S)
if new != page:
    open('ch14.html', 'w').write(new)
print(f'IPv6 fit: F = {F6 / 1000:.2f} us per skb, b = {b6:.4f} CPU-s/GB; IPv4 fit: F = {F4 / 1000:.2f} us, b = {b4:.4f}')
print(f'model at the ceiling ({ceiling:.1f} KB): {F6 / (ceiling * 1000) + b6:.4f} CPU-s per GB')
