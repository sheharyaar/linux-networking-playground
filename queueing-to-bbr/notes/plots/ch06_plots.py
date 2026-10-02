"""ch06_plots.py: the plots in the TCP pacing chapter (ch06.html).

  python3 notes/plots/ch06_plots.py      (run from queueing-to-bbr/)

Writes notes/plots/ch06-sync.svg and notes/plots/ch06-mixed.svg, then splices each one into
ch06.html between <!--PLOT:name--> and <!--/PLOT:name--> markers.
"""
import csv, re, sys
sys.path.insert(0, 'notes/plots')
from svgplot import plot, SLOT, INK2

D = 'labs/ch06-pacing/data/'

def rows(name): return list(csv.DictReader(open(D + name)))

# ---- plot 1: eight flows started together, unpaced and fq-paced ----------------------
def loss_events(name):
    by = {}
    for r in rows(name):
        by.setdefault(int(r['flow']), []).append(r)
    ev = []
    for k, rs in by.items():
        prev = 'open'
        for r in rs:
            if r['ca_state'] in ('recovery', 'loss') and prev not in ('recovery', 'loss'):
                ev.append((float(r['t_s']), k))
            prev = r['ca_state']
    return ev
na, fa = rows('none-1-agg.csv'), rows('fq-1-agg.csv')
SPAN = 6.0
nt = [float(r['t_s']) for r in na]; nc = [int(r['agg_cwnd']) for r in na]
ft = [float(r['t_s']) for r in fa]; fc = [int(r['agg_cwnd']) for r in fa]
ne = [e for e in loss_events('none-1-f.csv') if e[0] <= SPAN]
fe = [e for e in loss_events('fq-1-f.csv') if e[0] <= SPAN]
def at(ts, vs, x):
    i = min(range(len(ts)), key=lambda k: abs(ts[k] - x)); return vs[i]
hover = []
for k in range(0, int(SPAN * 20) + 1):
    x = k * 0.05
    nl = sorted({f for t, f in ne if x - 0.025 <= t < x + 0.025})
    fl = sorted({f for t, f in fe if x - 0.025 <= t < x + 0.025})
    hover.append((x, f't = {x:.2f} s · sum of windows: unpaced {at(nt, nc, x)}, fq-paced {at(ft, fc, x)} packets'
                     f' · flows entering recovery: unpaced {len(nl)}, fq-paced {len(fl)}'))
sync = plot(
    panels=[
        dict(height=190, y_range=(0, 200), y_ticks=[0, 50, 100, 150, 200], y_label='sum of 8 windows (pkts)',
             series=[dict(name='unpaced', xs=nt, ys=nc, color=SLOT[1], width=1.5, end_label=(SPAN, 62, 'unpaced (pfifo)')),
                     dict(name='fq', xs=ft, ys=fc, color=SLOT[0], width=1.5, end_label=(SPAN, 128, 'paced by fq'))],
             refs=[dict(y=85, text='pipe 85'), dict(y=106, text='pipe + buffer 106')],
             notes=[dict(x=0.3, y=190, text='fq-paced peak 188'), dict(x=0.42, y=150, text='unpaced peak 157')],
             legend=[('unpaced: pfifo on s0, nothing paces', SLOT[1], 'line'), ('paced: fq on s0', SLOT[0], 'line')]),
        dict(height=92, y_range=(-0.8, 7.8), y_ticks=[0, 7], y_label='unpaced: flow',
             dots=[dict(name='unpaced losses', xs=[t for t, f in ne], ys=[f for t, f in ne], color=SLOT[1], r=2.6)],
             legend=[('a flow enters recovery (unpaced)', SLOT[1], 'dot')]),
        dict(height=92, y_range=(-0.8, 7.8), y_ticks=[0, 7], y_label='fq-paced: flow',
             dots=[dict(name='fq losses', xs=[t for t, f in fe], ys=[f for t, f in fe], color=SLOT[0], r=2.6)],
             legend=[('a flow enters recovery (fq-paced)', SLOT[0], 'dot')]),
    ],
    x_range=(0, SPAN), x_ticks=[0, 1, 2, 3, 4, 5, 6], x_label='seconds since the eight flows started together',
    label='Eight Reno flows started together through a 10 Mbit/s bottleneck with a 21-packet buffer: the sum of their windows, and when each flow entered recovery, unpaced and paced by fq',
    hover=hover)
open('notes/plots/ch06-sync.svg', 'w').write(sync)

# ---- plot 2: paced and unpaced flows in the same run (the bench's Figs 14-15) -----------
import os
mixed = None
if os.path.exists(D + 'mixed-300-runs.csv') and os.path.exists(D + 'mixed-bulk-runs.csv'):
    def pts(name, prefix):
        out = []
        for r in rows(name):
            if not r['condition'].startswith(prefix): continue
            out.append((int(r['paced_flows']), r))
        return sorted(out, key=lambda x: x[0])
    def ok(v): return v not in ('', 'nan')
    short = pts('mixed-300-runs.csv', 'mix300-k')
    long_ = pts('mixed-bulk-runs.csv', 'mixbulk-k')
    # all-unpaced and all-paced bulk points come from the eight-flow runs (pfifo; TCP's timer)
    bulk = {r['run'].rsplit('-', 1)[0]: [] for r in rows('bulk-runs-b21.csv')}
    for r in rows('bulk-runs-b21.csv'): bulk[r['run'].rsplit('-', 1)[0]].append(float(r['gp_all']) / 8)
    l_px = [0.0] * 0; l_py = []; l_ux = []; l_uy = []
    for k, r in long_:
        if ok(r['paced']): l_px.append(k); l_py.append(float(r['paced']))
        if ok(r['unpaced']): l_ux.append(k); l_uy.append(float(r['unpaced']))
    l_ux = [0] + l_ux; l_uy = [sum(bulk['none']) / len(bulk['none'])] + l_uy
    l_px = l_px + [8]; l_py = l_py + [sum(bulk['timer']) / len(bulk['timer'])]
    s_px = [k for k, r in short if ok(r['paced'])]; s_py = [float(r['paced']) for k, r in short if ok(r['paced'])]
    s_ux = [k for k, r in short if ok(r['unpaced'])]; s_uy = [float(r['unpaced']) for k, r in short if ok(r['unpaced'])]
    hover2 = []
    sd = {k: r for k, r in short}; ld = {k: r for k, r in long_}
    for k in range(0, 9):
        parts = [f'{k} of 8 flows paced by TCP\'s timer']
        if k in sd:
            r = sd[k]
            parts.append('300-packet flows, mean completion: paced ' + (f"{float(r['paced']):.3f} s" if ok(r['paced']) else '-') +
                         ', unpaced ' + (f"{float(r['unpaced']):.3f} s" if ok(r['unpaced']) else '-') + f" ({r['runs']} runs)")
        if k in ld:
            r = ld[k]
            parts.append('15 s flows, Mbit/s per flow: paced ' + (f"{float(r['paced']):.2f}" if ok(r['paced']) else '-') +
                         ', unpaced ' + (f"{float(r['unpaced']):.2f}" if ok(r['unpaced']) else '-') + f" ({r['runs']} runs)")
        if len(parts) > 1: hover2.append((k, ' · '.join(parts)))
    mixed = plot(
        panels=[dict(height=170, y_range=(1.0, 1.5), y_ticks=[1.0, 1.1, 1.2, 1.3, 1.4, 1.5], y_label='300 pkts: completion (s)',
                     series=[dict(name='paced', xs=s_px, ys=s_py, color=SLOT[0], width=2, end_label=(8.3, s_py[-1], 'paced flows')),
                             dict(name='unpaced', xs=s_ux, ys=s_uy, color=SLOT[1], width=2, end_label=(8.3, s_uy[-1], 'unpaced flows'))],
                     dots=[dict(name='p', xs=s_px, ys=s_py, color=SLOT[0]), dict(name='u', xs=s_ux, ys=s_uy, color=SLOT[1])],
                     legend=[('flows paced by TCP\'s own timer', SLOT[0], 'dot'), ('unpaced flows (pfifo)', SLOT[1], 'dot')]),
                dict(height=170, y_range=(0.8, 1.3), y_ticks=[0.8, 0.9, 1.0, 1.1, 1.2, 1.3], y_label='15 s flows: Mbit/s each',
                     series=[dict(name='paced', xs=l_px, ys=l_py, color=SLOT[0], width=2, end_label=(8.3, l_py[-1], 'paced flows')),
                             dict(name='unpaced', xs=l_ux, ys=l_uy, color=SLOT[1], width=2, end_label=(8.3, l_uy[-1], 'unpaced flows'))],
                     dots=[dict(name='p', xs=l_px, ys=l_py, color=SLOT[0]), dict(name='u', xs=l_ux, ys=l_uy, color=SLOT[1])],
                     refs=[dict(y=8.88 / 8, text='fair share 1.11')],
                     legend=[('paced flows', SLOT[0], 'dot'), ('unpaced flows', SLOT[1], 'dot')])],
        x_range=(-0.3, 8.3), x_ticks=[0, 1, 2, 4, 6, 7, 8], x_label='how many of the eight flows are paced',
        label='Paced and unpaced flows in the same run: completion time of 300-packet flows, and goodput of 15-second flows, against the number of paced flows',
        hover=hover2, right=110)
    open('notes/plots/ch06-mixed.svg', 'w').write(mixed)

# ---- splice into the page -----------------------------------------------------------
page = 'ch06.html'
s = open(page).read()
for name, svg in (('ch06-sync', sync), ('ch06-mixed', mixed)):
    if svg is None: print(name, 'no data yet'); continue
    s, n = re.subn(r'<!--PLOT:%s-->.*?<!--/PLOT:%s-->' % (name, name),
                   lambda m: '<!--PLOT:%s-->\n%s\n<!--/PLOT:%s-->' % (name, svg, name), s, flags=re.S)
    print(name, 'spliced' if n else 'marker not found')
open(page, 'w').write(s)
