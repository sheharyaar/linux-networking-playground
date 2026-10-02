"""svgplot.py: small inline-SVG line charts for the dossier, no dependencies.

Follows the dataviz rules: 2px lines, hairline solid grid, text in ink tokens (never the
series colour), a legend whenever a panel has two or more series, direct end labels,
and a hover layer (one hit column per x bucket with a native <title> readout and a
crosshair line that CSS shows on hover). Panels stack vertically and share the x axis
(small multiples, never a second y axis).

Palette: the dataviz reference categorical slots, validated on white
(slot 3 aqua is below 3:1, so it always gets a direct label and the CSV table view).
"""
import html

SLOT = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']
INK, INK2, MUTED, GRID, AXIS = '#1b1f24', '#4a5560', '#898781', '#e8ebef', '#c3c2b7'

def esc(s): return html.escape(str(s), quote=True)

def nice(v):
    return f'{v:g}' if abs(v) < 1e5 else f'{v:,.0f}'

def plot(panels, x_range, x_ticks, x_label, width=720, label='chart', hover=None,
         left=58, right=150, top=30, gap=46, bottom=42, prefix='p'):
    """panels: list of dicts with keys
         height, y_range, y_ticks, y_label,
         series: [{name, xs, ys, color, step=False, width=2, dash=None, end_label=None}]
         dots:   [{name, xs, ys, color, r=3, marker='dot'|'x'}]
         refs:   [{y, text}]            horizontal reference lines (dashed: they are thresholds)
         notes:  [{x, y, text, anchor}] free annotations in data coordinates
       hover: list of (x, text) rows for the hit layer.
    """
    x0, x1 = x_range
    pw = width - left - right
    heights = [p['height'] for p in panels]
    H = top + sum(heights) + gap * (len(panels) - 1) + bottom
    out = [f'<svg viewBox="0 0 {width} {H}" role="img" aria-label="{esc(label)}" '
           f'xmlns="http://www.w3.org/2000/svg" font-size="12" '
           f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Inter,Roboto,sans-serif">']
    X = lambda x: left + (x - x0) / (x1 - x0) * pw
    y_off = top
    frames = []
    for pi, p in enumerate(panels):
        ph = p['height']; ya, yb = p['y_range']
        Y = (lambda yo, ph, ya, yb: (lambda y: yo + ph - (y - ya) / (yb - ya) * ph))(y_off, ph, ya, yb)
        frames.append((y_off, ph))
        # grid and y ticks
        for t in p['y_ticks']:
            yy = Y(t)
            out.append(f'<line x1="{left}" x2="{left + pw}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{GRID}" stroke-width="1"/>')
            out.append(f'<text x="{left - 8}" y="{yy + 4:.1f}" text-anchor="end" fill="{MUTED}">{nice(t)}</text>')
        out.append(f'<line x1="{left}" x2="{left + pw}" y1="{Y(ya):.1f}" y2="{Y(ya):.1f}" stroke="{AXIS}" stroke-width="1"/>')
        out.append(f'<text x="{left - 44}" y="{y_off + ph / 2:.1f}" fill="{INK2}" text-anchor="middle" '
                   f'transform="rotate(-90 {left - 44} {y_off + ph / 2:.1f})">{esc(p["y_label"])}</text>')
        for r in p.get('refs', []):
            yy = Y(r['y'])
            out.append(f'<line x1="{left}" x2="{left + pw}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{MUTED}" stroke-width="1" stroke-dasharray="4 4"/>')
            out.append(f'<text x="{left + pw + 6}" y="{yy + 4:.1f}" fill="{MUTED}">{esc(r["text"])}</text>')
        for s in p.get('series', []):
            pts = []
            prev = None
            for x, y in zip(s['xs'], s['ys']):
                if x < x0 or x > x1: continue
                if y is None or y == '': prev = None; continue
                if s.get('step') and prev is not None:
                    pts.append(f'{X(x):.1f},{Y(prev):.1f}')
                pts.append(f'{X(x):.1f},{Y(y):.1f}'); prev = y
            dash = f' stroke-dasharray="{s["dash"]}"' if s.get('dash') else ''
            out.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{s["color"]}" '
                       f'stroke-width="{s.get("width", 2)}" stroke-linejoin="round" stroke-linecap="round"{dash}/>')
            if s.get('end_label'):
                lx, ly, txt = s['end_label']
                out.append(f'<line x1="{left + pw + 4}" x2="{left + pw + 16}" y1="{Y(ly):.1f}" y2="{Y(ly):.1f}" stroke="{s["color"]}" stroke-width="2"/>')
                out.append(f'<text x="{left + pw + 20}" y="{Y(ly) + 4:.1f}" fill="{INK}">{esc(txt)}</text>')
        for d in p.get('dots', []):
            r = d.get('r', 3)
            for x, y in zip(d['xs'], d['ys']):
                if d.get('marker') == 'x':
                    cx, cy = X(x), Y(y)
                    out.append(f'<path d="M{cx - 4:.1f},{cy - 4:.1f}L{cx + 4:.1f},{cy + 4:.1f}M{cx - 4:.1f},{cy + 4:.1f}L{cx + 4:.1f},{cy - 4:.1f}" '
                               f'stroke="{d["color"]}" stroke-width="2" stroke-linecap="round"/>')
                else:
                    out.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{r}" fill="{d["color"]}" stroke="#fff" stroke-width="1.5"/>')
        for n in p.get('notes', []):
            out.append(f'<text x="{X(n["x"]):.1f}" y="{Y(n["y"]):.1f}" fill="{INK2}" text-anchor="{n.get("anchor", "start")}">{esc(n["text"])}</text>')
        if p.get('legend'):
            lx = left + 8
            for name, color, kind in p['legend']:
                ly = y_off - 8
                if kind == 'dot':
                    out.append(f'<circle cx="{lx + 6}" cy="{ly - 4}" r="4" fill="{color}"/>')
                elif kind == 'x':
                    out.append(f'<path d="M{lx + 2},{ly - 8}L{lx + 10},{ly}M{lx + 2},{ly}L{lx + 10},{ly - 8}" stroke="{color}" stroke-width="2"/>')
                else:
                    out.append(f'<line x1="{lx}" x2="{lx + 14}" y1="{ly - 4}" y2="{ly - 4}" stroke="{color}" stroke-width="2"/>')
                out.append(f'<text x="{lx + 19}" y="{ly}" fill="{INK}">{esc(name)}</text>')
                lx += 26 + 7 * len(name)
        y_off += ph + gap
    # x axis on the last panel
    yb = frames[-1][0] + frames[-1][1]
    for t in x_ticks:
        out.append(f'<text x="{X(t):.1f}" y="{yb + 16:.1f}" text-anchor="middle" fill="{MUTED}">{nice(t)}</text>')
    out.append(f'<text x="{left + pw / 2:.1f}" y="{yb + 34:.1f}" text-anchor="middle" fill="{INK2}">{esc(x_label)}</text>')
    # hover layer: one column per hover row
    if hover:
        xs = [h[0] for h in hover]
        for i, (x, text) in enumerate(hover):
            xa = X((xs[i - 1] + x) / 2) if i else X(x0)
            xb = X((x + xs[i + 1]) / 2) if i + 1 < len(xs) else X(x1)
            out.append(f'<g class="hit"><title>{esc(text)}</title><rect x="{xa:.1f}" y="{top}" width="{max(xb - xa, 1):.1f}" '
                       f'height="{yb - top:.1f}" fill="transparent"/><line x1="{X(x):.1f}" x2="{X(x):.1f}" y1="{top}" '
                       f'y2="{yb:.1f}" stroke="{MUTED}" stroke-width="1" opacity="0"/></g>')
    out.append('</svg>')
    return '\n'.join(out)
