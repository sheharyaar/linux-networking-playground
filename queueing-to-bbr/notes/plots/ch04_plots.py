"""ch04_plots.py: the three plots in the shapers chapter (ch04.html).

  python3 notes/plots/ch04_plots.py      (run from queueing-to-bbr/)

Writes notes/plots/ch04-tbf-queue.svg, ch04-borrow.svg and ch04-drr.svg, then splices each one into
ch04.html between <!--PLOT:name--> and <!--/PLOT:name--> markers.
"""
import csv, random, re, sys
from collections import deque
sys.path.insert(0, 'notes/plots')
from svgplot import plot, SLOT

D = 'labs/ch04-shapers/data/'

# ---- plot 1: the TBF's queue, measured (tbf rate 10mbit burst 32kb latency 50ms) -------------
q = list(csv.DictReader(open(D + 'tbf50-root-q.csv')))
qt = [float(r['t_s']) for r in q]
qd = [int(r['backlog_bytes']) * 8 / 10e6 * 1000 for r in q]          # ms of sending at 10 Mbit/s
hover1 = [(qt[i], f't = {qt[i]:.1f} s · backlog {q[i]["backlog_bytes"]} bytes, {q[i]["backlog_pkts"]} packets · '
                  f'{qd[i]:.1f} ms of sending') for i in range(0, len(q), 5)]
tbf = plot(
    panels=[dict(height=230, y_range=(0, 90), y_ticks=[0, 25, 50, 75], y_label='queue delay (ms)',
                 series=[dict(name='queue', xs=qt, ys=qd, color=SLOT[0], width=1.5,
                              end_label=(20, 30, 'TBF backlog'))],
                 refs=[dict(y=50, text='"latency 50ms"'), dict(y=76.2, text='limit / rate = 76 ms')],
                 notes=[dict(x=0.5, y=84, text='peak 93,868 bytes = 75 ms')])],
    x_range=(0, 21), x_ticks=[0, 5, 10, 15, 20], x_label='seconds since the qdisc was sampled',
    label='Measured backlog of a token bucket filter shaping one Reno flow, in milliseconds of sending',
    hover=hover1)
open('notes/plots/ch04-tbf-queue.svg', 'w').write(tbf)

# ---- plot 2: two customers on one HTB uplink, measured ------------------------------------------
g = list(csv.DictReader(open(D + 'eq-goodput.csv')))
gt = [float(r['t_s']) for r in g]
ga = [float(r['eq-a.csv']) for r in g]; gb = [float(r['eq-b.csv']) for r in g]
a0 = float(next(csv.DictReader(open(D + 'eq-a.csv')))['wall_s'])
cls = [r for r in csv.DictReader(open(D + 'eq-classes.csv')) if r['class'] == '1:10']
def per_second(rows, key):
    xs, ys = [], []
    by = {}
    for r in rows:
        by.setdefault(int(float(r['wall_s']) - a0), r)    # first sample in each whole second
    secs = sorted(k for k in by if k >= 0)
    for s0, s1 in zip(secs, secs[1:]):
        r0, r1 = by[s0], by[s1]
        dt = float(r1['wall_s']) - float(r0['wall_s'])
        xs.append(s0 + 0.5); ys.append((int(r1[key]) - int(r0[key])) / dt)
    return xs, ys
lx, ly = per_second(cls, 'lended'); bx, by_ = per_second(cls, 'borrowed')
def near(xs, ys, x):
    i = min(range(len(xs)), key=lambda k: abs(xs[k] - x)); return ys[i]
hover2 = [(x, f't = {x:.1f} s · A {near(gt, ga, x):.2f} Mbit/s · B {near(gt, gb, x):.2f} Mbit/s · '
              f'class A: {near(lx, ly, x):.0f} pkt/s on its own rate, {near(bx, by_, x):.0f} pkt/s borrowed')
          for x in gt]
bor = plot(
    panels=[dict(height=190, y_range=(0, 10), y_ticks=[0, 2.5, 5, 7.5, 10], y_label='goodput (Mbit/s)',
                 series=[dict(name='A', xs=gt, ys=ga, color=SLOT[0], end_label=(40, 8.6, 'customer A')),
                         dict(name='B', xs=gt, ys=gb, color=SLOT[1], end_label=(40, 1.0, 'customer B'))],
                 refs=[dict(y=4.78, text='rate 5, minus headers')],
                 legend=[('customer A', SLOT[0], 'line'), ('customer B', SLOT[1], 'line')]),
            dict(height=130, y_range=(0, 500), y_ticks=[0, 250, 500], y_label='class A pkt/s',
                 series=[dict(name='own', xs=lx, ys=ly, color=SLOT[2], end_label=(40, 430, 'own rate (lended)')),
                         dict(name='borrowed', xs=bx, ys=by_, color=SLOT[3], end_label=(40, 330, 'borrowed'))],
                 legend=[('own rate (lended)', SLOT[2], 'line'), ('borrowed from 1:1', SLOT[3], 'line')])],
    x_range=(0, 40), x_ticks=[0, 10, 20, 30, 40], x_label='seconds since customer A started',
    label='Measured goodput of two HTB customers and the packets class A sent on its own rate or borrowed',
    hover=hover2)
open('notes/plots/ch04-borrow.svg', 'w').write(bor)

# ---- plot 3: packet round robin against DRR, simulated (the lab's code) -------------------------
def flows(n=3000, seed=1):
    r = random.Random(seed)
    return {'bulk': [1500] * n, 'small': [64] * n, 'mixed': [r.randint(64, 1500) for _ in range(n)]}
def rr(queues, rounds):
    q = {f: deque(p) for f, p in queues.items()}; sent = {f: 0 for f in q}; tr = []
    for _ in range(rounds):
        for f in q:
            if q[f]: sent[f] += q[f].popleft()
        tr.append(dict(sent))
    return tr
def drr(queues, rounds, quantum):
    q = {f: deque(p) for f, p in queues.items()}; sent = {f: 0 for f in q}; dc = {f: 0 for f in q}; tr = []
    for _ in range(rounds):
        for f in q:
            if not q[f]: dc[f] = 0; continue
            dc[f] += quantum
            while q[f] and q[f][0] <= dc[f]:
                dc[f] -= q[f][0]; sent[f] += q[f].popleft()
            if not q[f]: dc[f] = 0
        tr.append(dict(sent))
    return tr
K = 40
t_rr, t_drr = rr(flows(), K), drr(flows(), K, 1500)
ks = list(range(1, K + 1))
def ser(tr, f): return [s[f] / 1000 for s in tr]
hover3 = [(k, f'round {k} · packet RR: bulk {t_rr[k-1]["bulk"]/1000:.1f}, mixed {t_rr[k-1]["mixed"]/1000:.1f}, '
              f'small {t_rr[k-1]["small"]/1000:.1f} KB · DRR: bulk {t_drr[k-1]["bulk"]/1000:.1f}, '
              f'mixed {t_drr[k-1]["mixed"]/1000:.1f}, small {t_drr[k-1]["small"]/1000:.1f} KB') for k in ks]
cols = {'bulk': SLOT[0], 'mixed': SLOT[2], 'small': SLOT[1]}
names = {'bulk': 'bulk, 1500 B', 'mixed': 'mixed, 64–1500 B', 'small': 'small, 64 B'}
def panel(tr, title, ends):
    return dict(height=170, y_range=(0, 60), y_ticks=[0, 20, 40, 60], y_label=title,
                series=[dict(name=f, xs=ks, ys=ser(tr, f), color=cols[f], end_label=(K, ends[f], names[f]))
                        for f in ('bulk', 'mixed', 'small')],
                legend=[(names[f], cols[f], 'line') for f in ('bulk', 'mixed', 'small')])
dr = plot(
    panels=[panel(t_rr, 'packet RR: KB sent', {'bulk': 60, 'mixed': 32, 'small': 4}),
            panel(t_drr, 'DRR: KB sent', {'bulk': 62, 'mixed': 55, 'small': 48})],
    x_range=(0, K), x_ticks=[0, 10, 20, 30, 40], x_label='rounds (quantum 1500 bytes, all three flows backlogged)',
    label='Simulated bytes sent by three flows under packet round robin and under deficit round robin',
    hover=hover3)
open('notes/plots/ch04-drr.svg', 'w').write(dr)
print('DRR at round 40:', t_drr[-1], ' RR:', t_rr[-1])

# ---- splice into the page ------------------------------------------------------------------------
page = 'ch04.html'
try:
    s = open(page).read()
    for name, svg in (('ch04-tbf-queue', tbf), ('ch04-borrow', bor), ('ch04-drr', dr)):
        s, n = re.subn(r'<!--PLOT:%s-->.*?<!--/PLOT:%s-->' % (name, name),
                       lambda m: '<!--PLOT:%s-->\n%s\n<!--/PLOT:%s-->' % (name, svg, name), s, flags=re.S)
        print(name, 'spliced' if n else 'marker not found')
    open(page, 'w').write(s)
except FileNotFoundError:
    print('ch04.html not written yet; SVGs saved only')
