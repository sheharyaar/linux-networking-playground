"""ch13_plots.py: the two drawn figures in the Maglev chapter (ch13.html).

  python3 notes/plots/ch13_plots.py      (run from queueing-to-bbr/)

Writes
  notes/plots/ch13-table1.svg      the paper's Table 1 (p. 6) as a picture: the three preference
                                   lists, the order the slots were claimed in, the table before,
                                   and the table after B1 leaves (recomputed here, not copied)
  notes/plots/ch13-disruption.svg  the share of the table that changes owner when backends leave,
                                   against M/N: the lab's Python (labs/ch13-maglev/data/
                                   maglev-sweep-n100.csv) and Cilium's own Go code
                                   (labs/ch13-maglev/data/cilium-go-lab.txt)
and splices each one into ch13.html between <!--PLOT:name--> and <!--/PLOT:name--> markers.
"""
import csv, math, re, sys
sys.path.insert(0, 'notes/plots')
from svgplot import plot, SLOT, INK, INK2, MUTED, GRID, AXIS, esc

D = 'labs/ch13-maglev/data/'
FONT = '-apple-system,BlinkMacSystemFont,Segoe UI,Inter,Roboto,sans-serif'
RED = '#be123c'          # the page's --book colour, used for the one extra move

# ---- figure 1: Table 1, rebuilt -------------------------------------------------------
M = 7
NAMES = ['B0', 'B1', 'B2']
OS = {'B0': (3, 4), 'B1': (0, 2), 'B2': (3, 1)}
PERM = {b: [(o + j * s) % M for j in range(M)] for b, (o, s) in OS.items()}
COL = {'B0': SLOT[0], 'B1': SLOT[1], 'B2': SLOT[2]}

def populate(names):
    """Pseudocode 1, recording every probe: (backend, rank j, slot, round, claimed?)."""
    nxt = {b: 0 for b in names}; entry = [None] * M; n = 0; rnd = 0; probes = []
    while True:
        rnd += 1
        for b in names:
            c = PERM[b][nxt[b]]
            while entry[c] is not None:
                probes.append((b, nxt[b], c, rnd, False)); nxt[b] += 1; c = PERM[b][nxt[b]]
            probes.append((b, nxt[b], c, rnd, True)); entry[c] = b; nxt[b] += 1; n += 1
            if n == M: return entry, probes

before, probes = populate(NAMES)
after, _ = populate(['B0', 'B2'])
assert before == ['B1', 'B0', 'B1', 'B0', 'B2', 'B2', 'B0'], before      # p. 6, "Before"
assert after == ['B0', 'B0', 'B0', 'B0', 'B2', 'B2', 'B2'], after        # p. 6, "After"
extra = [j for j in range(M) if before[j] != 'B1' and before[j] != after[j]]
assert extra == [6], extra                                                # "row 6", p. 7
print('Table 1 rebuilt: before', before, 'after', after, 'extra moves', extra, 'probes', len(probes))

def table1_svg():
    W, H = 720, 344
    cw, ch, top = 54, 34, 92            # cell width and height, first row's y
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="The paper\'s Table 1 rebuilt: three preference '
         f'lists, the order slots were claimed, the table before and after backend B1 leaves" '
         f'xmlns="http://www.w3.org/2000/svg" font-size="13" font-family="{FONT}">']
    def text(x, y, s, fill=INK, anchor='middle', size=None, weight=None):
        a = f' font-size="{size}"' if size else ''
        a += f' font-weight="{weight}"' if weight else ''
        o.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" fill="{fill}"{a}>{esc(s)}</text>')
    # left block: preference lists, rank j down the side
    lx = 70
    text(lx + 1.5 * cw, 30, 'Preference lists: permutation[i][j]', INK, size=13, weight=600)
    text(lx + 1.5 * cw, 48, 'slot = (offset + j × skip) mod 7', INK2, size=12)
    for k, b in enumerate(NAMES):
        x = lx + k * cw
        text(x + cw / 2, 72, f'{b} {OS[b]}', COL[b] if False else INK, size=12, weight=600)
        o.append(f'<rect x="{x + 6}" y="76" width="{cw - 12}" height="3" fill="{COL[b]}"/>')
    for j in range(M):
        text(lx - 12, top + j * ch + 22, f'j={j}', MUTED, anchor='end', size=12)
    seen = {(b, j): (c, r, ok) for b, j, c, r, ok in probes}
    for k, b in enumerate(NAMES):
        x = lx + k * cw
        for j in range(M):
            y = top + j * ch; slot = PERM[b][j]
            pr = seen.get((b, j))
            if pr and pr[2]:
                o.append(f'<g class="hit"><title>{b} round {pr[1]}: claims slot {slot}</title>'
                         f'<rect x="{x + 3}" y="{y + 3}" width="{cw - 6}" height="{ch - 6}" rx="5" fill="{COL[b]}" fill-opacity="0.22" stroke="{COL[b]}" stroke-width="1.5"/></g>')
                text(x + cw / 2 - 6, y + 22, str(slot), INK, weight=700)
                text(x + cw - 9, y + 14, f'r{pr[1]}', INK2, anchor='end', size=10)
            elif pr:
                o.append(f'<g class="hit"><title>{b} round {pr[1]}: slot {slot} is taken, try the next preference</title>'
                         f'<rect x="{x + 3}" y="{y + 3}" width="{cw - 6}" height="{ch - 6}" rx="5" fill="#fff" stroke="{GRID}"/></g>')
                text(x + cw / 2, y + 22, str(slot), MUTED)
                o.append(f'<line x1="{x + cw / 2 - 9}" x2="{x + cw / 2 + 9}" y1="{y + 18}" y2="{y + 18}" stroke="{MUTED}" stroke-width="1.5"/>')
            else:
                o.append(f'<g class="hit"><title>{b}: never reached, the table filled first</title>'
                         f'<rect x="{x + 3}" y="{y + 3}" width="{cw - 6}" height="{ch - 6}" rx="5" fill="#fff" stroke="{GRID}" stroke-dasharray="3 3"/></g>')
                text(x + cw / 2, y + 22, str(slot), AXIS)
    # right blocks: the table before and after
    def column(x0, title, sub, owners, marks):
        text(x0 + 45, 30, title, INK, size=13, weight=600)
        text(x0 + 45, 48, sub, INK2, size=12)
        for s in range(M):
            y = top + s * ch; b = owners[s]
            if s in marks and marks[s][0] == 'extra':
                stroke, sw, dash = RED, 2.5, ''
            elif s in marks:
                stroke, sw, dash = COL['B1'], 2, ' stroke-dasharray="4 3"'
            else:
                stroke, sw, dash = COL[b], 1.5, ''
            tip = marks[s][1] if s in marks else f'slot {s}: {b}'
            o.append(f'<g class="hit"><title>{esc(tip)}</title><rect x="{x0}" y="{y + 3}" width="90" height="{ch - 6}" rx="5" '
                     f'fill="{COL[b]}" fill-opacity="0.22" stroke="{stroke}" stroke-width="{sw}"{dash}/></g>')
            text(x0 + 45, y + 22, b, INK, weight=700)
    tx = 330
    for s in range(M):
        text(tx - 14, top + s * ch + 22, f'slot {s}', MUTED, anchor='end', size=12)
    column(tx, 'Table before', 'B0: 3 slots, B1: 2, B2: 2', before, {})
    marks = {0: ('moved', 'slot 0: was B1, must move (B1 left)'), 2: ('moved', 'slot 2: was B1, must move (B1 left)'),
             6: ('extra', 'slot 6: was B0, now B2. The one extra move: B0 never left')}
    column(tx + 130, 'After B1 leaves', 'B0: 4 slots, B2: 3', after, marks)
    for s in range(M):
        if before[s] != after[s]:
            y = top + s * ch + ch / 2
            col = RED if s in extra else MUTED
            o.append(f'<line x1="{tx + 94}" x2="{tx + 126}" y1="{y:.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="1.5"/>')
            o.append(f'<path d="M{tx + 120},{y - 4:.1f}L{tx + 126},{y:.1f}L{tx + 120},{y + 4:.1f}" fill="none" stroke="{col}" stroke-width="1.5"/>')
    lx2 = tx + 236
    text(lx2, top + 0 * ch + 22, 'B1 left: must move', INK2, anchor='start', size=12)
    text(lx2, top + 2 * ch + 22, 'B1 left: must move', INK2, anchor='start', size=12)
    text(lx2, top + 6 * ch + 16, 'extra move:', RED, anchor='start', size=12, weight=700)
    text(lx2, top + 6 * ch + 31, 'B0 stayed, lost it', INK2, anchor='start', size=12)
    o.append('</svg>')
    return '\n'.join(o)

t1 = table1_svg()
open('notes/plots/ch13-table1.svg', 'w').write(t1)

# ---- figure 2: disruption against M/N ---------------------------------------------------
L = math.log10
rows = list(csv.DictReader(open(D + 'maglev-sweep-n100.csv')))
def sel(k): return [r for r in rows if int(r['k']) == k]
x1 = [L(float(r['M_over_N'])) for r in sel(1)]; y1 = [float(r['maglev_extra_pct']) for r in sel(1)]
x3 = [L(float(r['M_over_N'])) for r in sel(3)]; y3 = [float(r['maglev_extra_pct']) for r in sel(3)]
go = {}
for line in open(D + 'cilium-go-lab.txt'):
    m = re.match(r'^(\d+),([\d.]+),(\d+),(\d+),(\d+),(\d+),([\d.]+),([\d.]+)$', line.strip())
    if m and int(m.group(1)) in (100, 160):
        go[(int(m.group(1)), int(m.group(5)))] = (float(m.group(2)), float(m.group(7)))
print('cilium go points:', go)
gx1 = [L(go[(n, 1)][0]) for n in (100, 160)]; gy1 = [go[(n, 1)][1] for n in (100, 160)]
gx3 = [L(go[(n, 3)][0]) for n in (100, 160)]; gy3 = [go[(n, 3)][1] for n in (100, 160)]
hover = []
for a, b in zip(sel(1), sel(3)):
    hover.append((L(float(a['M_over_N'])),
                  f"M = {a['M']}, N = 100 (M/N = {float(a['M_over_N']):.0f}): one backend leaves → {float(a['maglev_extra_pct']):.2f}% of the table "
                  f"moves between backends that stayed; three leave → {float(b['maglev_extra_pct']):.2f}%; "
                  f"entries per backend {a['min_entries']}–{a['max_entries']}; plain mod-N moves {float(a['modn_extra_pct']):.0f}%"))
XT = [3, 10, 30, 100, 300, 1000]
svg = plot(
    panels=[dict(height=250, y_range=(0, 8), y_ticks=[0, 1, 2, 4, 6, 8], y_label='% of the table that moves',
                 series=[dict(name='one of 100 leaves', xs=x1, ys=y1, color=SLOT[0], end_label=(x1[-1], 0.25, 'one of 100 leaves')),
                         dict(name='three of 100 leave', xs=x3, ys=y3, color=SLOT[1], end_label=(x3[-1], 1.9, 'three of 100 leave'))],
                 dots=[dict(name='py1', xs=x1, ys=y1, color=SLOT[0], r=3), dict(name='py3', xs=x3, ys=y3, color=SLOT[1], r=3),
                       dict(name='go1', xs=gx1, ys=gy1, color=INK, marker='x'), dict(name='go3', xs=gx3, ys=gy3, color=INK, marker='x')],
                 refs=[dict(y=1, text="the docs' 1%")],
                 notes=[dict(x=L(125), y=6.2, text='plain mod-N moves about 98%'),
                        dict(x=L(125), y=5.7, text='at every size (off this scale)'),
                        dict(x=L(104), y=3.3, text='× Cilium’s Go code, M = 16381:'),
                        dict(x=L(104), y=2.8, text='N = 160 and N = 100')],
                 legend=[('one of 100 leaves', SLOT[0], 'line'), ('three of 100 leave', SLOT[1], 'line'),
                         ('Cilium pkg/maglev', INK, 'x')])],
    x_range=(L(2), L(1500)), x_ticks=[L(v) for v in XT],
    x_label='table size per backend, M/N (log scale)',
    label='Share of a Maglev table that changes owner among backends that stayed, when one or three of 100 backends leave, against M/N',
    hover=hover, right=170)
# x tick labels back to plain numbers (they are the only middle-anchored muted texts)
it = iter(str(v) for v in XT)
svg = re.sub(r'(<text x="[^"]+" y="[^"]+" text-anchor="middle" fill="%s">)[^<]*(</text>)' % MUTED,
             lambda m: m.group(1) + next(it) + m.group(2), svg)
# a dashed vertical rule at M = 100 N (the paper's rule, p. 6)
left, width, right = 58, 720, 170
pw = width - left - right
X = lambda x: left + (x - L(2)) / (L(1500) - L(2)) * pw
xv = X(L(100))
rule = (f'<line x1="{xv:.1f}" x2="{xv:.1f}" y1="30" y2="280" stroke="{MUTED}" stroke-width="1" stroke-dasharray="4 4"/>'
        f'<text x="{xv + 5:.1f}" y="44" text-anchor="start" fill="{INK2}">← M = 100 N, the paper’s rule</text>')
svg = svg.replace('</svg>', rule + '\n</svg>')
open('notes/plots/ch13-disruption.svg', 'w').write(svg)

# ---- splice into the page --------------------------------------------------------------
page = 'ch13.html'
try:
    s = open(page).read()
    for name, body in (('ch13-table1', t1), ('ch13-disruption', svg)):
        s, n = re.subn(r'<!--PLOT:%s-->.*?<!--/PLOT:%s-->' % (name, name),
                       lambda m: '<!--PLOT:%s-->\n%s\n<!--/PLOT:%s-->' % (name, body, name), s, flags=re.S)
        print(name, 'spliced' if n else 'marker not found')
    open(page, 'w').write(s)
except FileNotFoundError:
    print('ch13.html not written yet; SVGs saved only')
