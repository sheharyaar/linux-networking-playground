"""ch07_plots.py: the two plots in the Carousel chapter (ch07.html).

  python3 notes/plots/ch07_plots.py      (run from queueing-to-bbr/)

Writes notes/plots/ch07-wheelwait.svg and notes/plots/ch07-occupancy.svg, then splices each one
into ch07.html between <!--PLOT:name--> and <!--/PLOT:name--> markers.

svgplot.py has linear axes only. The lateness plot needs log axes, so it plots log10 values and
then rewrites the tick labels of the finished SVG (ms instead of log10 ms). Nothing in svgplot.py
is changed.
"""
import csv, math, re, statistics, sys
sys.path.insert(0, 'notes/plots')
from svgplot import plot, SLOT, MUTED

D = 'labs/ch07-carousel/data/'
def rows(name): return list(csv.DictReader(open(D + name)))
L = math.log10

# ---- plot 1: how late the kernel's timer wheel fires, against an hrtimer -----------------
w = rows('wheelwait.csv')
wx = [L(int(r['requested_ms'])) for r in w if r['kind'] == 'wheel']
wy = [L(max(float(r['late_ms']), 0.02)) for r in w if r['kind'] == 'wheel']
hx = [L(int(r['requested_ms'])) for r in w if r['kind'] == 'hrtimer']
hy = [L(max(float(r['late_ms']), 0.02)) for r in w if r['kind'] == 'hrtimer']
# bucket width of the level each timeout falls in (HZ = 1000): 1 ms below 63, 8 below 504, 64 below 4032, 512 above
edges = [(14, 63, 1), (63, 504, 8), (504, 4032, 64), (4032, 14000, 512)]
sx, sy = [], []
for a, b, g in edges:
    sx += [L(a), L(b)]; sy += [L(g), L(g)]
req = sorted({int(r['requested_ms']) for r in w})
hover = []
for ms in req:
    lw = [float(r['late_ms']) for r in w if r['kind'] == 'wheel' and int(r['requested_ms']) == ms]
    lh = [float(r['late_ms']) for r in w if r['kind'] == 'hrtimer' and int(r['requested_ms']) == ms]
    g = next(g for a, b, g in edges if a <= ms < b)
    hover.append((L(ms), f'{ms} ms timeout · wheel bucket {g} ms · wheel late {min(lw):.2f} to {max(lw):.2f} ms '
                         f'(median {statistics.median(lw):.2f}) · hrtimer late median {statistics.median(lh):.3f} ms'))
XT = {L(v): lab for v, lab in ((20, '20 ms'), (50, '50'), (100, '100'), (200, '200'), (500, '500'), (1000, '1 s'),
                                 (2000, '2'), (5000, '5'), (10000, '10 s'))}
YT = {L(v): lab for v, lab in ((0.03, '0.03'), (0.1, '0.1'), (1, '1'), (10, '10'), (100, '100'), (1000, '1000'))}
svg1 = plot(
    panels=[dict(height=260, y_range=(L(0.02), L(1500)), y_ticks=list(YT), y_label='late (ms, log scale)',
                 series=[dict(name='bucket', xs=sx, ys=sy, color=SLOT[2], width=2, dash='5 4',
                              end_label=(L(14000), L(512), 'bucket width'))],
                 dots=[dict(name='wheel', xs=wx, ys=wy, color=SLOT[0], r=3),
                       dict(name='hrtimer', xs=hx, ys=hy, color=SLOT[1], r=3, marker='x')],
                 notes=[dict(x=L(22), y=L(3), text='level 0: 1 ms'), dict(x=L(110), y=L(20), text='level 1: 8 ms'),
                        dict(x=L(820), y=L(160), text='level 2: 64 ms'), dict(x=L(4300), y=L(1100), text='level 3: 512 ms')],
                 legend=[('timer wheel (SO_RCVTIMEO)', SLOT[0], 'dot'), ('hrtimer (time.sleep)', SLOT[1], 'x'),
                         ('bucket width', SLOT[2], 'line')])],
    x_range=(L(14), L(14000)), x_ticks=list(XT), x_label='requested timeout (log scale)',
    label='How late each timeout fired: timer-wheel waits stay under the bucket width of their wheel level; hrtimer sleeps are a tenth of a millisecond late',
    hover=hover)
# relabel the log ticks: x tick labels are centred, y tick labels are right-aligned
def relabel(svg, table, anchor):              # two passes, so a new label never matches an old one
    for i, v in enumerate(table):
        svg = svg.replace(f'text-anchor="{anchor}" fill="{MUTED}">{v:g}</text>', f'text-anchor="{anchor}" fill="{MUTED}">@@{i}@@</text>', 1)
    for i, lab in enumerate(table.values()):
        svg = svg.replace(f'>@@{i}@@<', f'>{lab}<')
    return svg
svg1 = relabel(relabel(svg1, XT, 'middle'), YT, 'end')
open('notes/plots/ch07-wheelwait.svg', 'w').write(svg1)

# ---- plot 2: bytes held by the shaper, with and without the sender seeing it ------------
def series(kind):
    q = rows(f'{kind}-qdisc.csv')
    return [float(r['t_s']) for r in q], [int(r['backlog_bytes']) for r in q]
rt, rb = series('htb-rtr'); ht, hb = series('htb-snd'); ft, fb = series('fq-snd')
def at(ts, vs, x):
    i = min(range(len(ts)), key=lambda k: abs(ts[k] - x)); return vs[i]
fl = {k: rows(f'{k}-flows.csv') for k in ('htb-rtr', 'htb-snd')}
def rtt_at(k, x):
    near = [float(r['rtt_ms']) for r in fl[k] if abs(float(r['t_s']) - x) < 0.06]
    return statistics.median(near) if near else float('nan')
hover2 = []
for i in range(0, 61):
    x = i * 0.5
    hover2.append((x, f't = {x:.1f} s · HTB on the router: {at(rt, rb, x) / 1e6:.2f} MB held, RTT {rtt_at("htb-rtr", x):.0f} ms · '
                      f'HTB on the sender: {at(ht, hb, x) / 1e3:.1f} KB, RTT {rtt_at("htb-snd", x):.0f} ms · fq on the sender: {at(ft, fb, x) / 1e3:.1f} KB'))
svg2 = plot(
    panels=[dict(height=170, y_range=(0, 2.5), y_ticks=[0, 0.5, 1, 1.5, 2, 2.5], y_label='held (MB)',
                 series=[dict(name='htb-rtr', xs=rt, ys=[b / 1e6 for b in rb], color=SLOT[1], width=1.5,
                              end_label=(30, 1.4, 'HTB on the router'))],
                 refs=[dict(y=2.4224, text='16 x 100-packet limit')],
                 notes=[dict(x=0.5, y=2.15, text='past the namespace boundary: no completion reaches TCP')],
                 legend=[('16 HTB classes on rtr:r1, no deferred completion', SLOT[1], 'line')]),
            dict(height=150, y_range=(0, 125), y_ticks=[0, 25, 50, 75, 100, 125], y_label='held (KB)',
                 series=[dict(name='htb-snd', xs=ht, ys=[b / 1e3 for b in hb], color=SLOT[0], width=1.5,
                              end_label=(30, 108, 'HTB on the sender')),
                         dict(name='fq-snd', xs=ft, ys=[b / 1e3 for b in fb], color=SLOT[2], width=1.5, dash='6 4',
                              end_label=(30, 84, 'fq on the sender'))],
                 notes=[dict(x=0.5, y=115, text='TCP small queues: 2 skbs per flow, 32 in all')],
                 legend=[('16 HTB classes on snd:s0', SLOT[0], 'line'), ('fq maxrate 500kbit on snd:s0', SLOT[2], 'line')])],
    x_range=(0, 30), x_ticks=[0, 5, 10, 15, 20, 25, 30], x_label='seconds since the 16 flows connected',
    label='Bytes held by a 16-flow shaper at 500 kbit/s per flow: megabytes on the router, where TCP gets no completion signal; 97 KB on the sender, where TCP small queues holds each flow to two skbs',
    hover=hover2)
open('notes/plots/ch07-occupancy.svg', 'w').write(svg2)

# ---- splice into the page -----------------------------------------------------------------
page = 'ch07.html'
try:
    s = open(page).read()
    for name, svg in (('ch07-wheelwait', svg1), ('ch07-occupancy', svg2)):
        s, n = re.subn(r'<!--PLOT:%s-->.*?<!--/PLOT:%s-->' % (name, name),
                       lambda m: '<!--PLOT:%s-->\n%s\n<!--/PLOT:%s-->' % (name, svg, name), s, flags=re.S)
        print(name, 'spliced' if n else 'marker not found')
    open(page, 'w').write(s)
except FileNotFoundError:
    print('ch07.html not written yet; SVGs saved only')
