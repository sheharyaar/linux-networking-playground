"""ch10_plots.py: the two plots in the BBR chapter (ch10.html).

  python3 notes/plots/ch10_plots.py      (run from queueing-to-bbr/)

Writes notes/plots/ch10-fig1.svg and notes/plots/ch10-cycle.svg and splices each one into
ch10.html between <!--PLOT:name--> and <!--/PLOT:name--> markers. The Linux BBR series are drawn
only if labs/ch10-bbr/data/bbr-f.csv exists (it needs tcp_bbr loaded).
"""
import csv, os, re, sys
sys.path.insert(0, 'notes/plots')
from svgplot import plot, SLOT

D = 'labs/ch10-bbr/data/'
BTLBW = 10e6 * 1448 / 1514 / (1448 * 8)          # 825.6 segments/s of payload
RTPROP = 0.040 + 1514 * 8 / 10e6                  # 41.2 ms for a full-size packet
PAY = BTLBW * 1448 * 8 / 1e6                      # 9.56 Mbit/s
BDP, FULL = BTLBW * RTPROP, BTLBW * RTPROP + 50   # 34.0 and 84.0 segments
HAVE_BBR = os.path.exists(D + 'bbr-f.csv')

def load(name):
    return list(csv.DictReader(open(D + name))) if os.path.exists(D + name) else []

def every(rows, step, t_min=2.0):                 # one row per `step` seconds after t_min
    out, nxt = [], t_min
    for r in rows:
        t = float(r['t_s'])
        if t >= nxt: out.append(r); nxt = t + step
    return out

# ---- plot 1: Fig. 1 on the bench, model lines and measured dots -------------------------------
cub = every(load('cubic-f.csv'), 0.1)
bbr = every(load('bbr-f.csv'), 0.1) if HAVE_BBR else []
mx = [x / 2 for x in range(0, 2 * int(FULL) + 1)]
rtt_m = [max(RTPROP, x / BTLBW) * 1e3 for x in mx]
del_m = [min(x / RTPROP, BTLBW) * 1448 * 8 / 1e6 for x in mx]
def dots(rows, col):
    return [int(r['inflight']) for r in rows], [float(r[col]) for r in rows]
cx, cy = dots(cub, 'rtt_ms'); cdx, cdy = dots(cub, 'delivery_mbps')
dots_rtt = [dict(name='CUBIC', xs=cx, ys=cy, color=SLOT[1], r=2.5)]
dots_del = [dict(name='CUBIC', xs=cdx, ys=cdy, color=SLOT[1], r=2.5)]
legend1 = [('model', SLOT[0], 'line'), ('CUBIC, measured', SLOT[1], 'dot')]
if bbr:
    bx, by = dots(bbr, 'rtt_ms'); bdx, bdy = dots(bbr, 'delivery_mbps')
    dots_rtt.append(dict(name='BBR', xs=bx, ys=by, color=SLOT[2], r=2.5))
    dots_del.append(dict(name='BBR', xs=bdx, ys=bdy, color=SLOT[2], r=2.5))
    legend1.append(('BBR, measured', SLOT[2], 'dot'))
hover = []
for k in range(0, 101, 2):
    n_c = sum(1 for x in cx if abs(x - k) <= 1)
    n_b = sum(1 for x in (bx if bbr else []) if abs(x - k) <= 1)
    txt = (f'{k} segments in flight · model: RTT {max(RTPROP, k / BTLBW) * 1e3:.1f} ms, '
           f'delivery {min(k / RTPROP, BTLBW) * 1448 * 8 / 1e6:.2f} Mbit/s'
           + (' (beyond 84 the queue overflows)' if k > FULL else '') + f' · CUBIC samples here: {n_c}'
           + (f' · BBR samples here: {n_b}' if bbr else ''))
    hover.append((k, txt))
fig1 = plot(
    panels=[
        dict(height=210, y_range=(0, 120), y_ticks=[0, 20, 41.2, 60, 80, 101.7, 120], y_label='srtt (ms)',
             series=[dict(name='model', xs=mx, ys=rtt_m, color=SLOT[0], end_label=(FULL, 101.7, 'queue full'))],
             dots=dots_rtt, legend=legend1,
             notes=[dict(x=34, y=30, text='BDP = 34: the operating point', anchor='middle'),
                    dict(x=88, y=112, text='drops beyond 84', anchor='end')]),
        dict(height=130, y_range=(0, 12), y_ticks=[0, 4, 8, 9.56, 12], y_label='delivery (Mbit/s)',
             series=[dict(name='model', xs=mx, ys=del_m, color=SLOT[0], end_label=(FULL, 9.56, 'BtlBw 9.56'))],
             dots=dots_del,
             notes=[dict(x=18, y=4.0, text='slope 1/RTprop', anchor='start')]),
    ],
    x_range=(0, 100), x_ticks=[0, 20, 34, 50, 60, 84, 100], x_label='inflight (1448-byte segments)',
    label="The paper's Fig. 1 for the bench: RTT and delivery rate against inflight, model and measured flows",
    hover=hover)
open('notes/plots/ch10-fig1.svg', 'w').write(fig1)

# ---- plot 2: 700 ms of ProbeBW, model and (if loaded) Linux -----------------------------------
sim = load('sim-bench.csv')
def window(rows, t0, span=0.7):
    return [r for r in rows if t0 <= float(r['t_s']) <= t0 + span]
def start_of_probe(rows, after):                  # first 1 -> 1.25 change after `after` s, minus 150 ms
    prev = None
    for r in rows:
        t = float(r['t_s'])
        if t > after and r['state'] == 'probe_bw' and prev == '1.0' and r['pacing_gain'] in ('1.25',):
            return t - 0.15
        prev = r['pacing_gain'] if r['state'] == 'probe_bw' else None
    return after
t_s = start_of_probe(sim, 3.0)
sw = window(sim, t_s)
st = [(float(r['t_s']) - t_s) * 1e3 for r in sw]
series_g = [dict(name='model', xs=st, ys=[float(r['pacing_gain']) for r in sw], color=SLOT[1], step=True)]
series_i = [dict(name='model', xs=st, ys=[int(r['inflight']) for r in sw], color=SLOT[1])]
series_r = [dict(name='model', xs=st, ys=[float(r['srtt_ms']) for r in sw], color=SLOT[1])]
legend2 = [('model (gaincycle.py)', SLOT[1], 'line')]
lin = []
if HAVE_BBR:
    raw = load('bbr-f.csv')
    raw = [dict(r, pacing_gain=f"{float(r['pacing_gain']):.2f}".rstrip('0').rstrip('.') + ('.0' if float(r['pacing_gain']) == 1 else ''))
           if r['pacing_gain'] else r for r in raw]
    tb = start_of_probe([dict(r, pacing_gain=('1.25' if r['pacing_gain'] == '1.25' else r['pacing_gain'])) for r in raw], 3.0)
    lin = window(raw, tb)
    lt = [(float(r['t_s']) - tb) * 1e3 for r in lin]
    series_g.append(dict(name='Linux', xs=lt, ys=[float(r['pacing_gain']) for r in lin], color=SLOT[0], step=True))
    series_i.append(dict(name='Linux', xs=lt, ys=[int(r['inflight']) for r in lin], color=SLOT[0]))
    series_r.append(dict(name='Linux', xs=lt, ys=[float(r['rtt_ms']) for r in lin], color=SLOT[0]))
    legend2.insert(0, ('Linux tcp_bbr, TCP_CC_INFO', SLOT[0], 'line'))
hover2 = []
for r in sw[::4]:
    x = (float(r['t_s']) - t_s) * 1e3
    txt = f'{x:.0f} ms · model: gain {r["pacing_gain"]}, inflight {r["inflight"]}, queue {r["queue"]}, srtt {r["srtt_ms"]} ms'
    if lin:
        near = min(lin, key=lambda q: abs((float(q['t_s']) - tb) * 1e3 - x))
        txt += f' · Linux: gain {float(near["pacing_gain"]):g}, inflight {near["inflight"]}, srtt {near["rtt_ms"]} ms'
    hover2.append((x, txt))
fig2 = plot(
    panels=[
        dict(height=70, y_range=(0.6, 1.4), y_ticks=[0.75, 1, 1.25], y_label='pacing_gain',
             series=series_g, legend=legend2),
        dict(height=120, y_range=(25, 50), y_ticks=[25, 34, 42.5, 50], y_label='inflight (segs)',
             series=series_i, refs=[dict(y=34, text='BDP 34')]),
        dict(height=120, y_range=(40, 52), y_ticks=[41.2, 45, 50], y_label='srtt (ms)',
             series=series_r, refs=[dict(y=41.2, text='RTprop 41.2')]),
    ],
    x_range=(0, 700), x_ticks=[0, 100, 200, 300, 400, 500, 600, 700], x_label='time (ms)',
    label='700 ms of ProbeBW on the 10 Mbit/s, 40 ms bench: pacing gain, inflight and smoothed RTT',
    hover=hover2)
open('notes/plots/ch10-cycle.svg', 'w').write(fig2)

page = 'ch10.html'
s = open(page).read()
for name, svg in (('ch10-fig1', fig1), ('ch10-cycle', fig2)):
    s, n = re.subn(r'<!--PLOT:%s-->.*?<!--/PLOT:%s-->' % (name, name),
                   lambda m: '<!--PLOT:%s-->\n%s\n<!--/PLOT:%s-->' % (name, svg, name), s, flags=re.S)
    print(name, 'spliced' if n else 'marker not found', '(with Linux BBR)' if HAVE_BBR else '(model and CUBIC only)')
open(page, 'w').write(s)
