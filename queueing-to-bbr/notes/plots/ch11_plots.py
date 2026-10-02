"""ch11_plots.py: the plots in the where-BBR-loses chapter (ch11.html).

  python3 notes/plots/ch11_plots.py      (run from queueing-to-bbr/)

Writes notes/plots/ch11-ware.svg (a model) and notes/plots/ch11-loss.svg (bench measurements plus a
model panel), then splices each one into ch11.html between <!--PLOT:name--> and <!--/PLOT:name-->.
If labs/ch11-bbr-limits/data/ holds BBR runs (duel-bbr-*.txt summaries, sweep-bbr.csv), they are
drawn too; until tcp_bbr is loaded on the host they are absent and only the model and CUBIC/Reno show.
"""
import csv, math, os, re, sys
sys.path.insert(0, 'notes/plots')
import svgplot
from svgplot import plot, SLOT

D = 'labs/ch11-bbr-limits/data/'

# ---- plot 1: Ware et al.'s model of BBR's share against one CUBIC flow (pp. 140-142) -------------
C = 10e6 / 8 / 1514          # packets/s on the bench
L = 0.040                    # s
BDP = C * L                  # 33.0 packets

def ware(X, k=2.0, N=1, probe=True):
    q = X * BDP
    p = 1 / k - (k - 1) / (k * X) - 4 * N / q
    p = min(max(p, 0.0), 1.0)
    f = 1 - (q / C + 0.2 + L) / 10 if probe else 1.0
    return (1 - p) * f

OFF = 1000.0                 # x = OFF + log2(X); the tick labels are mapped back below
lx = [OFF + i / 20 for i in range(-40, 121)]          # X from 0.25 to 64
Xs = [2 ** (x - OFF) for x in lx]
full = [100 * ware(X) for X in Xs]
eq9 = [100 * ware(X, probe=False) for X in Xs]
cap4 = [100 * ware(X, k=4) for X in Xs]
_nice = svgplot.nice
TICKS = {OFF + e: (f'{2 ** e:g}') for e in range(-2, 7)}
svgplot.nice = lambda v: TICKS.get(v, _nice(v))

dots = []
if os.path.exists(D + 'duel-bbr-summary.csv'):          # measured BBR shares, once tcp_bbr is loaded
    rows = list(csv.DictReader(open(D + 'duel-bbr-summary.csv')))
    dots = [dict(name='measured', xs=[OFF + math.log2(float(r['bdp'])) for r in rows],
                 ys=[float(r['bbr_share_pct']) for r in rows], color=SLOT[1], r=4)]
hover = []
for X in (0.25, 0.5, 1, 1.24, 2, 4, 8, 10, 16, 32, 64):
    hover.append((OFF + math.log2(X), f'queue {X:g} BDP = {X * BDP:.0f} packets · BBR share: Eq. 9 alone '
                  f'{100 * ware(X, probe=False):.1f}%, with probe time {100 * ware(X):.1f}%, '
                  f'with a 4-BDP cap {100 * ware(X, k=4):.1f}%'))
legend = [('Eq. 9-11: cap 2 BDP, with probe time', SLOT[0], 'line'), ('Eq. 9 alone', SLOT[2], 'line'),
          ('the paper\'s 4-BDP cap', SLOT[3], 'line')]
if dots: legend.append(('measured on the bench', SLOT[1], 'dot'))
ware_svg = plot(
    panels=[dict(height=250, y_range=(0, 100), y_ticks=[0, 25, 50, 75, 100], y_label='BBR share of the link (%)',
                 series=[dict(name='eq9', xs=lx, ys=eq9, color=SLOT[2], width=2, dash='6 4',
                              end_label=(lx[-1], 50, 'Eq. 9 alone')),
                         dict(name='cap4', xs=lx, ys=cap4, color=SLOT[3], width=2,
                              end_label=(lx[-1], 59, '4-BDP cap')),
                         dict(name='full', xs=lx, ys=full, color=SLOT[0], width=2.5,
                              end_label=(lx[-1], 36, 'cap 2 BDP + probe')),
                         dict(name='m05', xs=[OFF - 1, OFF - 1], ys=[0, 100], color='#c3c2b7', width=1, dash='3 3'),
                         dict(name='m10', xs=[OFF + math.log2(10)] * 2, ys=[0, 100], color='#c3c2b7', width=1, dash='3 3')],
                 dots=dots,
                 refs=[dict(y=50, text='')],
                 notes=[dict(x=OFF - 1.95, y=52, text='simple model: 50%'), dict(x=OFF - 0.95, y=8, text='spine: 0.5 BDP'), dict(x=OFF + math.log2(10) + 0.05, y=8, text='10 BDP')],
                 legend=legend)],
    x_range=(OFF - 2, OFF + 6), x_ticks=[OFF + e for e in range(-2, 7)],
    x_label='bottleneck queue, in BDPs (log scale; the bench: 1 BDP = 33 packets)',
    label='Ware et al.\'s model of one BBRv1 flow\'s share of a 10 Mbit/s, 40 ms link against CUBIC, against queue size in BDPs',
    hover=hover, right=150)
svgplot.nice = _nice
open('notes/plots/ch11-ware.svg', 'w').write(ware_svg)

# ---- plot 2: goodput against random loss (bench), and Cao et al.'s probe ratio (model) ------------
def sweep(name):
    out = {}
    if not os.path.exists(D + name): return out
    for r in csv.DictReader(open(D + name)):
        out.setdefault(r['cc'], []).append((float(r['loss_pct']), float(r['goodput_mbps']), r))
    return {k: sorted(v) for k, v in out.items()}
S = sweep('sweep-cubic-reno.csv')
S.update(sweep('sweep-bbr.csv'))
col = {'cubic': SLOT[0], 'reno': SLOT[2], 'bbr': SLOT[1]}
series, sdots, leg = [], [], []
ends = {'cubic': 1.0, 'reno': 0.15, 'bbr': 8.5}
for cc in ('bbr', 'cubic', 'reno'):
    if cc not in S: continue
    xs = [x for x, y, r in S[cc]]; ys = [y for x, y, r in S[cc]]
    series.append(dict(name=cc, xs=xs, ys=ys, color=col[cc], width=2, end_label=(35, ends[cc], cc.upper() if cc == 'bbr' else cc.capitalize())))
    sdots.append(dict(name=cc, xs=xs, ys=ys, color=col[cc], r=3))
    leg.append((('BBR' if cc == 'bbr' else cc.capitalize()) + ' (bench)', col[cc], 'dot'))
mx = [0.25 + i * 0.25 for i in range(140)]
mathis = [min(9.56, 1448 * 8 / 0.045 * 1.22 / math.sqrt(p / 100) / 1e6) for p in mx]
series.append(dict(name='mathis', xs=mx, ys=mathis, color='#898781', width=1.5, dash='5 4'))
leg.append(('Mathis formula, RTT 45 ms', '#898781', 'line'))
gx = [i * 0.25 for i in range(141)]
ratio = {g: [g * (1 - p / 100) for p in gx] for g in (1.1, 1.25, 1.5)}
det = 100 * (50 / 256) / (1 + 50 / 256)
hover2 = []
for p in (0, 0.1, 0.5, 1, 2, 5, 8.2, 9.1, 10, 15, 16.3, 18, 19.2, 20, 22, 25, 30, 33.3):
    parts = [f'random loss {p:g}%']
    for cc in ('bbr', 'cubic', 'reno'):
        hit = [y for x, y, r in S.get(cc, []) if abs(x - p) < 1e-9]
        if hit: parts.append(f'{cc}: {hit[0]:.2f} Mbit/s')
    parts.append('probe ratio g(1-p): ' + ', '.join(f'{g:g} -> {g * (1 - p / 100):.3f}' for g in (1.1, 1.25, 1.5)))
    hover2.append((p, ' · '.join(parts)))
loss_svg = plot(
    panels=[dict(height=200, y_range=(0, 10), y_ticks=[0, 2, 4, 6, 8, 10], y_label='goodput (Mbit/s)',
                 series=series, dots=sdots, legend=leg,
                 refs=[dict(y=9.56, text='link 9.56')]),
            dict(height=170, y_range=(0.7, 1.55), y_ticks=[0.8, 1.0, 1.2, 1.4], y_label='g(1-p), a model',
                 series=[dict(name='g11', xs=gx, ys=ratio[1.1], color=SLOT[3], width=2, end_label=(35, ratio[1.1][-1], 'gain 1.1')),
                         dict(name='g125', xs=gx, ys=ratio[1.25], color=SLOT[1], width=2.5, end_label=(35, ratio[1.25][-1], 'gain 1.25')),
                         dict(name='g15', xs=gx, ys=ratio[1.5], color=SLOT[0], width=2, end_label=(35, ratio[1.5][-1] + 0.03, 'gain 1.5')),
                         dict(name='d1', xs=[det, det], ys=[0.7, 1.55], color='#898781', width=1.5, dash='4 3')],
                 refs=[dict(y=1.0, text='')],
                 notes=[dict(x=0.5, y=0.74, text='dashed line at 1: the probe delivers the estimate'), dict(x=det - 0.3, y=1.535, text='policer detector:', anchor='end'),
                        dict(x=det - 0.3, y=1.485, text='16.3% of packets sent', anchor='end'), dict(x=det - 0.3, y=1.435, text='(lost/delivered 19.5%)', anchor='end')],
                 legend=[('the probe phase delivers g(1-p) of the estimate (Cao Eq. 3)', SLOT[1], 'line')])],
    x_range=(0, 35), x_ticks=[0, 5, 10, 15, 20, 25, 30, 35], x_label='random loss on the bottleneck (%)',
    label='Goodput against random loss for CUBIC and Reno on the bench, with the Mathis formula; below, the probe ratio g(1-p) for three pacing gains and the BBRv1 policer detector threshold',
    hover=hover2, right=150)
open('notes/plots/ch11-loss.svg', 'w').write(loss_svg)

# ---- splice into the page ----------------------------------------------------------------------
page = 'ch11.html'
s = open(page).read()
for name, svg in (('ch11-ware', ware_svg), ('ch11-loss', loss_svg)):
    pat = re.compile(r'(<!--PLOT:%s-->).*?(<!--/PLOT:%s-->)' % (name, name), re.S)
    if pat.search(s):
        s = pat.sub(lambda m: m.group(1) + '\n' + svg + '\n' + m.group(2), s)
    else:
        print('no marker for', name)
open(page, 'w').write(s)
print('wrote ch11-ware.svg, ch11-loss.svg')
