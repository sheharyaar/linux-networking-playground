"""ch03_plots.py: the three plots in the queue-delay chapter (ch03.html).

  python3 notes/plots/ch03_plots.py      (run from queueing-to-bbr/)

Writes notes/plots/ch03-bench.svg, ch03-ctl.svg and ch03-step.svg, then splices each one into
ch03.html between <!--PLOT:name--> and <!--/PLOT:name--> markers.
Data: labs/ch03-codel/data/ (the author's runs, 2 October 2026).
"""
import csv, math, re, sys
sys.path.insert(0, 'notes/plots')
from svgplot import plot, SLOT

D = 'labs/ch03-codel/data/'

def tcp(name):
    r = list(csv.DictReader(open(D + name + '-tcp.csv')))
    return [float(x['t_s']) for x in r], [float(x['rtt_ms']) for x in r]

def ping(name):
    xs, ys = [], []
    for line in open(D + name + '-ping.txt'):
        m = re.search(r'icmp_seq=(\d+).*time=([\d.]+) ms', line)
        if m:
            xs.append(int(m.group(1)) * 0.1); ys.append(float(m.group(2)))
    return xs, ys

def near(xs, ys, x):
    if not xs: return None
    i = min(range(len(xs)), key=lambda k: abs(xs[k] - x))
    return ys[i] if abs(xs[i] - x) < 0.3 else None

def thin(xs, ys, step):
    """keep every point whose x moved by at least `step` since the last kept one, plus local extremes"""
    ox, oy, last = [], [], -1e9
    for i, (x, y) in enumerate(zip(xs, ys)):
        if x - last >= step or (0 < i < len(ys) - 1 and (y > ys[i - 1] and y > ys[i + 1])):
            ox.append(x); oy.append(y); last = x
    return ox, oy

# ---- plot 1: the bench, pfifo vs codel vs fq_codel ------------------------------------------
runs = [('pfifo', 'pfifo, limit 1000', (0, 1400), [0, 400, 800, 1200]),
        ('codel', 'codel', (35, 60), [40, 50, 60]),
        ('fq_codel', 'fq_codel', (35, 60), [40, 50, 60])]
panels, hover_src = [], {}
for i, (name, label, yr, yt) in enumerate(runs):
    tx, ty = thin(*tcp(name), 0.05)
    px, py = ping(name)
    hover_src[name] = (tx, ty, px, py)
    py_c = [min(max(v, yr[0]), yr[1]) for v in py]
    p = dict(height=150 if i == 0 else 110, y_range=yr, y_ticks=yt, y_label=label + ' (ms)',
             series=[dict(name='ping', xs=px, ys=py_c, color=SLOT[1], width=1.5),
                     dict(name='TCP srtt', xs=tx, ys=[min(max(v, yr[0]), yr[1]) for v in ty], color=SLOT[0])],
             refs=[dict(y=40, text='empty path 40')] if i else [dict(y=655, text='median 655')])
    if i == 0:
        p['legend'] = [('TCP smoothed RTT (Reno flow)', SLOT[0], 'line'), ('ping, a second flow', SLOT[1], 'line')]
        p['notes'] = [dict(x=16, y=1250, text='slow start fills all 1000 slots, then ~513 packets stand')]
    elif name == 'codel':
        p['notes'] = [dict(x=1, y=56.5, text='ping shares the one queue: up to 52 ms')]
    else:
        p['notes'] = [dict(x=1, y=56.5, text='ping has its own queue: 40.4 ms, max 41.3')]
    panels.append(p)
hover = []
for k in range(0, 80):
    x = k * 0.5
    parts = [f't = {x:.1f} s']
    for name, *_ in runs:
        tx, ty, px, py = hover_src[name]
        a, b = near(tx, ty, x), near(px, py, x)
        parts.append(f'{name}: srtt {a:.0f}' + (f', ping {b:.0f}' if b else ''))
    hover.append((x, ' · '.join(parts) + ' ms'))
bench = plot(panels=panels, x_range=(0, 40), x_ticks=[0, 10, 20, 30, 40], x_label='seconds since connect',
             label='Round-trip times through a 10 Mbit/s bottleneck with pfifo, codel and fq_codel holding the queue',
             hover=hover, right=110)
open('notes/plots/ch03-bench.svg', 'w').write(bench)

# ---- plot 2: the control law, model and measured ----------------------------------------------
I = 100.0
paper_t, paper_k = [0.0], [1]
t = 0.0
for k in range(2, 320):
    t += I / math.sqrt(k - 1); paper_t.append(t / 1000); paper_k.append(k)
q = list(csv.DictReader(open(D + 'udp-codel-q.csv')))
t_first = next(float(r['t_s']) for r in q if r['dropping'] == '1')
t_exit = next(float(r['t_s']) for r in q if float(r['t_s']) > t_first and r['dropping'] == '0')
ep = [r for r in q if t_first - 0.2 <= float(r['t_s']) <= t_exit + 0.15]
mx = [float(r['t_s']) - t_first for r in ep]
mk = [int(r['count']) if r['dropping'] == '1' or float(r['t_s']) <= t_exit else None for r in ep]
mk = [int(r['count']) if float(r['t_s']) >= t_first and float(r['t_s']) < t_exit else None for r in ep]
ml = [float(r['ldelay']) / 1000 for r in ep]
mb = [int(r['backlog_pkts']) for r in ep]
approx_t = [i / 100 for i in range(0, 341)]
approx_k = [(x / (2 * I / 1000)) ** 2 for x in approx_t]
hover2 = []
for i in range(0, 35):
    x = i * 0.1
    k_model = max(k for tt, k in zip(paper_t, paper_k) if tt <= x)
    k_meas = near(mx, [v if v is not None else 0 for v in mk], x)
    hover2.append((x, f'{x:.1f} s after the first drop · model: {k_model} drops, next gap {I / math.sqrt(k_model):.1f} ms · '
                      f'measured count {k_meas} · sojourn {near(mx, ml, x):.1f} ms'))
ctl = plot(
    panels=[
        dict(height=220, y_range=(0, 300), y_ticks=[0, 100, 200, 300], y_label='drops so far',
             series=[dict(name='approx', xs=approx_t, ys=approx_k, color=SLOT[3], width=1.5, dash='5 4',
                          end_label=(3.4, 262, '(t/2I)²')),
                     dict(name='model', xs=paper_t, ys=paper_k, color=SLOT[0], end_label=(3.4, 230, 'model')),
                     dict(name='measured', xs=mx, ys=mk, color=SLOT[1], width=2.5, end_label=(3.4, 198, 'measured'))],
             notes=[dict(x=0.05, y=270, text='after 1 s: 33 drops, now 17 ms apart'),
                    dict(x=0.05, y=245, text='the measured line sits on the model')],
             legend=[('model: interval/√count', SLOT[0], 'line'), ('measured codel count', SLOT[1], 'line'),
                     ('(t/2I)² shape', SLOT[3], 'line')]),
        dict(height=130, y_range=(0, 100), y_ticks=[0, 25, 50, 75, 100], y_label='sojourn (ms)',
             series=[dict(name='sojourn', xs=mx, ys=ml, color=SLOT[2], width=1.5, end_label=(3.4, 30, 'ldelay'))],
             refs=[dict(y=5, text='target 5 ms')],
             notes=[dict(x=1.6, y=88, text='drop rate passes the 83/s excess near 1.5 s'),
                    dict(x=2.2, y=60, text='queue drains; exit at 3.2 s')]),
    ],
    x_range=(0, 3.4), x_ticks=[0, 0.5, 1, 1.5, 2, 2.5, 3], x_label='seconds since CoDel entered its dropping state',
    label='CoDel drop count against time: the interval over square-root-of-count model and a measured run',
    hover=hover2, right=130)
open('notes/plots/ch03-ctl.svg', 'w').write(ctl)
print('udp episode', round(t_first, 3), '->', round(t_exit, 3), '=', round(t_exit - t_first, 3), 's; count at exit',
      next(r['count'] for r in q if float(r['t_s']) >= t_exit))

# ---- plot 3: the rate step, 10 -> 1 Mbit/s at 20 s ----------------------------------------------
steps = [('step-pfifo', 'pfifo (ms)', (0, 7000), [0, 2000, 4000, 6000]),
         ('step-codel', 'codel (ms)', (0, 400), [0, 100, 200, 300, 400])]
panels3, src3 = [], {}
for i, (name, label, yr, yt) in enumerate(steps):
    tx, ty = thin(*tcp(name), 0.05)
    px, py = ping(name)
    src3[name] = (tx, ty, px, py)
    p = dict(height=150, y_range=yr, y_ticks=yt, y_label=label,
             series=[dict(name='ping', xs=px, ys=[min(v, yr[1]) for v in py], color=SLOT[1], width=1.5),
                     dict(name='TCP srtt', xs=tx, ys=[min(v, yr[1]) for v in ty], color=SLOT[0])])
    if i == 0:
        p['legend'] = [('TCP smoothed RTT (Reno flow)', SLOT[0], 'line'), ('ping, a second flow', SLOT[1], 'line')]
        p['refs'] = [dict(y=6400, text='530 × 12.1 ms')]
        p['notes'] = [dict(x=21, y=4300, text='← the same 530 packets, now 6.4 s deep')]
    else:
        p['refs'] = [dict(y=65, text='ping ≈ 65')]
        p["notes"] = [dict(x=21.5, y=330, text="← 360 ms spike; count reaches 29; under 100 ms within 2 s")]
    panels3.append(p)
hover3 = []
for k in range(20, 90):
    x = k * 0.5
    parts = [f't = {x:.1f} s ({"10" if x < 20 else "1"} Mbit/s)']
    for name, *_ in steps:
        tx, ty, px, py = src3[name]
        a, b = near(tx, ty, x), near(px, py, x)
        parts.append(f'{name[5:]}: srtt {a:.0f}' + (f', ping {b:.0f}' if b else ''))
    hover3.append((x, ' · '.join(parts) + ' ms'))
step = plot(panels=panels3, x_range=(10, 45), x_ticks=[10, 20, 30, 40],
            x_label='seconds since connect (bottleneck drops from 10 to 1 Mbit/s at 20 s)',
            label='Round-trip time before and after the bottleneck rate falls tenfold, pfifo against codel',
            hover=hover3, right=110)
open('notes/plots/ch03-step.svg', 'w').write(step)

# ---- splice into the page --------------------------------------------------------
page = 'ch03.html'
try:
    s = open(page).read()
    for name, svg in (('ch03-bench', bench), ('ch03-ctl', ctl), ('ch03-step', step)):
        s, n = re.subn(r'<!--PLOT:%s-->.*?<!--/PLOT:%s-->' % (name, name),
                       lambda m: '<!--PLOT:%s-->\n%s\n<!--/PLOT:%s-->' % (name, svg, name), s, flags=re.S)
        print(name, 'spliced' if n else 'marker not found')
    open(page, 'w').write(s)
except FileNotFoundError:
    print('ch03.html not written yet; SVGs saved only')
