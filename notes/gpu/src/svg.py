"""Hand-drawn SVG figures for gpu-programming-dossier.html.

Each function returns one <svg class="hand"> string. Coordinates are computed,
never typed, so a change of grid size moves every label with it. Palette is the
dossier's own (see base.css :root).
"""

INK, SOFT, LINE = "#1b1f24", "#4a5560", "#dfe4ea"
ACC, ACC_SOFT = "#0b6bcb", "#e8f1fb"
GOOD, GOOD_SOFT = "#0f7b6c", "#e6f4f1"
WARM, WARM_SOFT = "#b45309", "#fdf3e3"
RED, RED_SOFT = "#be123c", "#fde8ec"
FONT = 'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Inter,Roboto,sans-serif"'


def _svg(w, h, body, label):
    return (f'<svg class="hand" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{label}" xmlns="http://www.w3.org/2000/svg" {FONT}>'
            f'<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            f'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{SOFT}"/>'
            f'</marker></defs>{body}</svg>')


def _rect(x, y, w, h, fill="#fff", stroke=LINE, sw=1, rx=0, extra=""):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}" {extra}/>')


def _text(x, y, s, size=12, fill=INK, anchor="start", weight="normal", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}" {extra}>{s}</text>')


def _line(x1, y1, x2, y2, stroke=SOFT, sw=1, dash=None, arrow=False):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    a = ' marker-end="url(#ah)"' if arrow else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{d}{a}/>'


def matvec_picture():
    """Diagram 0.1: y = W·x, x drawn on its side above W, one row highlighted."""
    rows, cols, c = 6, 10, 30          # grid size and cell size
    gx, gy = 70, 96                    # top-left of W
    xy = 44                            # top of the x strip
    hi = 2                             # highlighted row
    yx = gx + cols * c + 80            # left of the y column
    b = []
    b.append(_text(gx, xy - 12, "x: n numbers, drawn on its side", 14, GOOD, weight="600"))
    for j in range(cols):
        b.append(_rect(gx + j * c, xy, c, 22, GOOD_SOFT, GOOD))
    b.append(_text(gx - 14, gy + rows * c / 2, "W", 20, INK, "end", "700"))
    b.append(_text(gx - 14, gy + rows * c / 2 + 18, "d rows", 12, SOFT, "end"))
    b.append(_text(gx + cols * c / 2, gy + rows * c + 20, "n columns", 12, SOFT, "middle"))
    for i in range(rows):
        for j in range(cols):
            fill, stroke = (ACC_SOFT, ACC) if i == hi else ("#fff", LINE)
            b.append(_rect(gx + j * c, gy + i * c, c, c, fill, stroke))
    for j in range(cols):
        cx = gx + j * c + c / 2
        b.append(_line(cx, xy + 22, cx, gy + hi * c, GOOD, 1.2, "2 3"))
    b.append(_text(yx + c / 2, gy - 12, "y", 20, INK, "middle", "700"))
    b.append(_text(yx + c / 2, gy + rows * c + 20, "d numbers", 12, SOFT, "middle"))
    for i in range(rows):
        fill, stroke = (ACC_SOFT, ACC) if i == hi else ("#fff", LINE)
        b.append(_rect(yx, gy + i * c, c, c, fill, stroke, 2 if i == hi else 1))
    ry = gy + hi * c + c / 2
    b.append(_line(gx + cols * c + 6, ry, yx - 6, ry, ACC, 2.2, arrow=True))
    b.append(_text((gx + cols * c + yx) / 2, ry - 10, "dot product", 13, ACC, "middle", "700"))
    ny = gy + rows * c + 56
    notes = [
        ("One row of W, multiplied pair by pair with x and added up, gives one number of y.", INK, "600"),
        ("Every number in W is read once, used in one multiply and one add, then never touched again.", SOFT, "normal"),
        ("Our matvec: d = n = 4096, 4 bytes per number.", WARM, "600"),
        ("W is 64 MiB, and the work is 16.8 million multiply-adds.", WARM, "600"),
    ]
    for k, (s_, col, wt) in enumerate(notes):
        b.append(_text(gx - 40, ny + k * 22, s_, 14, col, weight=wt))
    w = yx + c + 60
    h = ny + 3 * 22 + 16
    return _svg(max(w, 640), h, "".join(b), "A matrix W times a vector x gives a vector y; one row of W dotted with x gives one element of y")


def flynn():
    """Diagram 1.1: Flynn's taxonomy as a 2x2, with SIMT on the SIMD/MIMD line."""
    x0, y0, bw, bh, gap = 150, 60, 230, 120, 14
    b = []
    b.append(_text(x0 + bw + gap / 2, 24, "instruction streams", 14, SOFT, "middle", "600"))
    b.append(_text(x0 + bw / 2, 46, "one", 13, SOFT, "middle"))
    b.append(_text(x0 + bw + gap + bw / 2, 46, "many", 13, SOFT, "middle"))
    b.append(_text(30, y0 + bh + gap / 2, "data", 14, SOFT, "start", "600"))
    b.append(_text(30, y0 + bh + gap / 2 + 18, "streams", 14, SOFT, "start", "600"))
    b.append(_text(x0 - 14, y0 + bh / 2 + 4, "one", 13, SOFT, "end"))
    b.append(_text(x0 - 14, y0 + bh + gap + bh / 2 + 4, "many", 13, SOFT, "end"))
    cells = [
        (0, 0, "SISD", ["one plain CPU core", "running scalar code:", "one multiply-add at a time"], "#fff", LINE, INK),
        (1, 0, "MISD", ["many instruction streams,", "one data stream:", "almost never built"], "#f6f7f9", LINE, SOFT),
        (0, 1, "SIMD", ["one instruction, many lanes:", "AVX-512 on the laptop's CPU,", "16 floats per instruction"], GOOD_SOFT, GOOD, INK),
        (1, 1, "MIMD", ["many cores, each with its", "own program: a multicore CPU,", "or a GPU counted warp by warp"], WARM_SOFT, WARM, INK),
    ]
    for cx, cy, title, lines, fill, stroke, col in cells:
        x = x0 + cx * (bw + gap); y = y0 + cy * (bh + gap)
        b.append(_rect(x, y, bw, bh, fill, stroke, 1.5, 10))
        b.append(_text(x + 16, y + 30, title, 20, col, weight="700"))
        for k, ln in enumerate(lines):
            b.append(_text(x + 16, y + 58 + k * 19, ln, 13, col))
    # SIMT box below the bottom row, joined to both SIMD and MIMD
    sw_, sh_ = 260, 54
    sx = x0 + bw + gap / 2 - sw_ / 2; sy = y0 + 2 * bh + gap + 30
    b.append(_line(x0 + bw / 2 + 40, y0 + 2 * bh + gap, sx + 30, sy, ACC, 1.5, "4 3"))
    b.append(_line(x0 + bw + gap + bw / 2 - 40, y0 + 2 * bh + gap, sx + sw_ - 30, sy, ACC, 1.5, "4 3"))
    b.append(_rect(sx, sy, sw_, sh_, ACC_SOFT, ACC, 2, 10))
    b.append(_text(sx + sw_ / 2, sy + 23, "SIMT", 17, ACC, "middle", "700"))
    b.append(_text(sx + sw_ / 2, sy + 42, "SIMD inside a warp, MIMD across warps", 12, ACC, "middle"))
    h = sy + sh_ + 14
    return _svg(x0 + 2 * bw + gap + 20, h, "".join(b), "Flynn's taxonomy: SISD, SIMD, MISD, MIMD, with SIMT straddling SIMD and MIMD")


def divergence():
    """Diagram 1.3: one warp through if (lane < 20) A (10 cycles) else B (20 cycles)."""
    lanes, cw = 32, 15
    x0, y0, k = 150, 40, 5          # k = pixels per cycle
    rows = [("test the condition", 4, range(0, 32), GOOD),
            ("path A, lanes 0 to 19", 10, range(0, 20), ACC),
            ("path B, lanes 20 to 31", 20, range(20, 32), WARM),
            ("after the if: reconverged", 6, range(0, 32), GOOD)]
    b = []
    for i in range(0, lanes, 4):
        b.append(_text(x0 + i * cw + cw / 2, y0 - 10, str(i), 11, SOFT, "middle"))
    b.append(_text(x0 + lanes * cw / 2, y0 - 26, "lane", 12, SOFT, "middle", "600"))
    y = y0
    for label, cyc, active, col in rows:
        h = cyc * k
        b.append(_text(x0 - 12, y + h / 2 + 4, label, 12, INK, "end", "600"))
        for ln in range(lanes):
            on = ln in active
            fill = {ACC: ACC_SOFT, WARM: WARM_SOFT, GOOD: GOOD_SOFT}[col] if on else "#f2f3f5"
            stroke = col if on else LINE
            b.append(_rect(x0 + ln * cw, y, cw, h, fill, stroke, 0.8))
            if not on:
                b.append(_line(x0 + ln * cw + 2, y + h - 2, x0 + ln * cw + cw - 2, y + 2, "#c7ccd3", 0.8))
        b.append(_text(x0 + lanes * cw + 10, y + h / 2 + 4, f"{cyc} cycles", 12, SOFT))
        y += h + 6
    # time arrow
    b.append(_line(x0 + lanes * cw + 86, y0, x0 + lanes * cw + 86, y - 6, SOFT, 1.2, arrow=True))
    b.append(_text(x0 + lanes * cw + 94, y0 + 12, "time", 12, SOFT))
    b.append(_text(x0, y + 16, "Hatched lanes are masked off: they hold their registers and do nothing.", 12, SOFT))
    b.append(_text(x0, y + 34, "The warp pays 10 + 20 cycles for the if, though no lane needed more than 20.", 12, INK, weight="600"))
    return _svg(x0 + lanes * cw + 150, y + 46, "".join(b), "A warp executing both sides of a divergent branch one after the other, with inactive lanes masked")


def sm_floorplan():
    """Diagram 2.1: one Ada SM, four sub-partitions over a shared L1/shared-memory block."""
    W, pad = 680, 16
    pw = (W - 2 * pad - 3 * 10) / 4
    b = []
    b.append(_rect(4, 4, W - 8, 470, "#fbfcfd", SOFT, 1.5, 12))
    b.append(_text(pad + 4, 28, "One SM (Ada, compute capability 8.9)", 15, INK, weight="700"))
    b.append(_text(W - pad - 4, 28, "×20 on the laptop · ×132 on an H100", 13, WARM, "end", "600"))
    b.append(_rect(pad, 40, W - 2 * pad, 28, "#f2f3f5", LINE, 1, 6))
    b.append(_text(W / 2, 59, "instruction cache, shared by the four sub-partitions", 12, SOFT, "middle"))
    blocks = [
        ("warp scheduler", "one ready warp per cycle", ACC_SOFT, ACC, 46),
        ("register file", "16,384 × 32-bit = 64 KB", GOOD_SOFT, GOOD, 46),
        ("32 FP32 lanes", "16 of them also do integers", "#fff", SOFT, 46),
        ("tensor core", "small matrix multiplies", WARM_SOFT, WARM, 40),
        ("load/store · SFU", "memory requests · exp, sin", "#fff", SOFT, 40),
    ]
    for p_ in range(4):
        x = pad + p_ * (pw + 10)
        b.append(_rect(x, 78, pw, 268, "#fff", LINE, 1, 8))
        b.append(_text(x + pw / 2, 96, f"sub-partition {p_}", 12, SOFT, "middle", "600"))
        y = 104
        for title, sub, fill, stroke, h in blocks:
            b.append(_rect(x + 8, y, pw - 16, h, fill, stroke, 1.2, 6))
            b.append(_text(x + pw / 2, y + 18, title, 12.5, INK, "middle", "700"))
            b.append(_text(x + pw / 2, y + 34, sub, 10.5, SOFT, "middle"))
            y += h + 4
    b.append(_rect(pad, 356, W - 2 * pad, 52, ACC_SOFT, ACC, 1.5, 8))
    b.append(_text(W / 2, 378, "L1 data cache and shared memory: 128 KB, one pool, split as the kernel asks", 13, INK, "middle", "700"))
    b.append(_text(W / 2, 397, "up to 100 KB of it usable as shared memory", 11.5, SOFT, "middle"))
    b.append(_text(W / 2, 432, "Whole SM: 65,536 registers (256 KB), at most 48 resident warps,", 12.5, INK, "middle", "600"))
    b.append(_text(W / 2, 452, "and up to 4 warp-instructions issued per cycle, one per sub-partition.", 12.5, INK, "middle", "600"))
    return _svg(W, 480, "".join(b), "Block diagram of one Ada streaming multiprocessor with four sub-partitions")


def _simulate(n_warps, prog, lat, cycles):
    """Tiny warp-scheduler model: one issue per cycle, loose round-robin over ready warps."""
    pc = [0] * n_warps
    ready_at = [0] * n_warps
    issued, last = [], -1
    for t in range(cycles):
        pick = None
        for k in range(1, n_warps + 1):
            w = (last + k) % n_warps
            if pc[w] < len(prog) and ready_at[w] <= t:
                pick = w
                break
        if pick is None:
            issued.append(None)
            continue
        op = prog[pc[pick]]
        issued.append((pick, op))
        pc[pick] += 1
        # a 'L' (load) makes the next instruction wait for lat cycles
        ready_at[pick] = t + (lat if op == "L" else 1)
        last = pick
    return issued


def latency_hiding():
    """Diagram 2.2: one scheduler, 1 / 2 / 4 warps, each looping over A A L U U."""
    prog = list("AALUU") * 30
    lat, cycles, cw = 14, 44, 12
    colors = [ACC, WARM, GOOD, "#7c3aed", "#be123c", "#475569", "#0e7490", "#65a30d"]
    softs = [ACC_SOFT, WARM_SOFT, GOOD_SOFT, "#f1eafd", "#fde8ec", "#eef1f4", "#e0f4f8", "#eef7e1"]
    x0, y = 150, 40
    b = [_text(x0, 22, "issue slots of one warp scheduler, one box per cycle", 12.5, SOFT, weight="600")]
    for n in (1, 2, 4, 8):
        iss = _simulate(n, prog, lat, cycles)
        idle = sum(1 for v in iss if v is None)
        b.append(_text(x0 - 12, y + 15, f"{n} warp{'s' if n > 1 else ''}", 13, INK, "end", "700"))
        for t, v in enumerate(iss):
            if v is None:
                b.append(_rect(x0 + t * cw, y, cw, 22, "#f6f7f9", "#e3e6ea", 0.8))
            else:
                w, op = v
                b.append(_rect(x0 + t * cw, y, cw, 22, softs[w], colors[w], 0.9))
                b.append(_text(x0 + t * cw + cw / 2, y + 15, op, 9.5, colors[w], "middle", "700"))
        b.append(_text(x0 + cycles * cw + 10, y + 15, f"{idle} idle", 12, "#be123c" if idle else GOOD, weight="600"))
        y += 40
    leg = y + 8
    b.append(_text(x0, leg, "A = independent arithmetic   L = load from memory   U = use the loaded value", 12, SOFT))
    b.append(_text(x0, leg + 18, f"A load's result arrives {lat} cycles after it issues (real DRAM: hundreds). Grey = no warp was ready.", 12, SOFT))
    b.append(_text(x0, leg + 36, "Colours are warps. Switching costs nothing: every warp's registers are already in the register file.", 12, INK, weight="600"))
    return _svg(x0 + cycles * cw + 70, leg + 50, "".join(b), "Warp scheduler issue slots with one, two and four warps, showing idle cycles shrink as warps are added")


def mem_hierarchy():
    """Diagram 3.1: the memory ladder of the laptop GPU, widest = biggest and slowest."""
    rows = [
        ("registers", "one thread's own", "256 KB per SM", "no wait at all", GOOD_SOFT, GOOD, 0.56),
        ("L1 cache and shared memory", "one SM", "128 KB per SM", "tens of cycles", ACC_SOFT, ACC, 0.66),
        ("L2 cache", "the whole chip", "a few tens of MB", "a couple of hundred cycles", "#f1eafd", "#7c3aed", 0.76),
        ("global memory (GDDR6 on the laptop)", "every thread, every SM", "6 GB", "several hundred cycles · 216 GB/s peak", WARM_SOFT, WARM, 0.88),
        ("host memory, across PCIe", "host and device", "the laptop's RAM", "much slower again", "#f2f3f5", SOFT, 0.97),
    ]
    W, rh, gap, y0 = 720, 54, 8, 34
    b = [_text(16, 20, "faster and smaller at the top; bigger and slower at the bottom", 12.5, SOFT, weight="600")]
    for k, (name, who, size, lat, fill, stroke, frac) in enumerate(rows):
        w = W * frac; x = (W - w) / 2; y = y0 + k * (rh + gap)
        b.append(_rect(x, y, w, rh, fill, stroke, 1.5, 8))
        b.append(_text(W / 2, y + 22, name, 14, INK, "middle", "700"))
        b.append(_text(W / 2, y + 41, f"seen by: {who} · {size} · {lat}", 11.5, SOFT, "middle"))
    return _svg(W, y0 + len(rows) * (rh + gap) + 6, "".join(b), "GPU memory hierarchy from registers to host memory")


def coalescing():
    """Diagram 3.2: what one warp-wide load touches, warp-per-row vs thread-per-row."""
    b = []
    sx, sw = 40, 20                      # one float = 20 px; a 32-byte sector = 8 floats
    def sectors_row(y, label, used_runs, n_floats=64, note=""):
        b.append(_text(sx, y - 8, label, 13, INK, weight="700"))
        for f in range(n_floats):
            sec = f // 8
            used = any(a <= f < a2 for a, a2 in used_runs)
            fetched = any(a // 8 <= sec <= (a2 - 1) // 8 for a, a2 in used_runs)
            fill = ACC if used else (ACC_SOFT if fetched else "#fff")
            b.append(_rect(sx + (f % 32) * sw, y + (f // 32) * 18, sw, 16, fill, LINE if not fetched else ACC, 0.7))
        if note:
            b.append(_text(sx, y + 2 * 18 + 18, note, 12, SOFT))
    # warp per row: lanes read 32 consecutive floats = 4 sectors
    sectors_row(34, "warp per row: lane i reads W[row][j + i]", [(0, 32)], 32,
                "")
    for k in range(5):
        b.append(_line(sx + k * 8 * sw, 30, sx + k * 8 * sw, 54, INK, 2))
    for k in range(4):
        b.append(_text(sx + k * 8 * sw + 4 * sw, 47, f"sector {k}", 10.5, "#fff", "middle", "700"))
    b.append(_text(sx, 34 + 34, "32 neighbouring floats = 128 bytes = 4 sectors of 32 bytes. Every fetched byte is used.", 12, SOFT))
    # thread per row: 32 lanes, each in a different row, each hits its own sector
    y = 112
    b.append(_text(sx, y - 8, "thread per row: lane i reads W[row + i][j]  (rows are 16 KiB apart)", 13, INK, weight="700"))
    for lane in range(8):
        yy = y + lane * 20
        b.append(_text(sx - 6, yy + 12, f"lane {lane}", 10.5, SOFT, "end"))
        for f in range(8):
            fill = ACC if f == 0 else ACC_SOFT
            b.append(_rect(sx + 40 + f * sw, yy, sw, 16, fill, ACC, 0.7))
        b.append(_text(sx + 40 + 8 * sw + 10, yy + 12, "one sector, 4 of its 32 bytes used now", 10.5, SOFT))
    b.append(_text(sx + 40, y + 8 * 20 + 12, "… and so on for lanes 8 to 31: 32 sectors, 1,024 bytes fetched to deliver 128.", 12, SOFT))
    b.append(_text(sx + 40, y + 8 * 20 + 30, "The other 28 bytes of each sector are useful only if they are still in a cache when the lane wants them.", 12, INK, weight="600"))
    # legend
    ly = y + 8 * 20 + 56
    b.append(_rect(sx, ly - 11, 14, 12, ACC, ACC)); b.append(_text(sx + 20, ly, "bytes a lane asked for", 11.5, SOFT))
    b.append(_rect(sx + 190, ly - 11, 14, 12, ACC_SOFT, ACC)); b.append(_text(sx + 210, ly, "bytes fetched with them, in the same sector", 11.5, SOFT))
    return _svg(sx + 32 * sw + 30, ly + 14, "".join(b), "Coalesced versus uncoalesced loads for one warp")


def roofline(machines=None, points=None, title=None):
    """Diagram 3.3 (and later the three-generation roofline): log-log roofline."""
    import math
    machines = machines or [("RTX 4050 Laptop, FP32", 216.0, 12000.0, ACC)]
    points = points or [("our matvec, FP32: 0.5 FLOP/byte", 0.5, WARM), ("a matmul over 64 vectors: 32 FLOP/byte", 32.0, GOOD)]
    W, H = 700, 420
    L, R, T, B = 80, 30, 30, 60
    xmin, xmax, ymin, ymax = 0.0625, 1024.0, 10.0, 100000.0
    def X(v): return L + (math.log10(v) - math.log10(xmin)) / (math.log10(xmax) - math.log10(xmin)) * (W - L - R)
    def Y(v): return H - B - (math.log10(v) - math.log10(ymin)) / (math.log10(ymax) - math.log10(ymin)) * (H - T - B)
    b = [_rect(L, T, W - L - R, H - T - B, "#fff", LINE, 1)]
    for e in range(-4, 11):
        v = 2.0 ** e
        if xmin <= v <= xmax:
            b.append(_line(X(v), T, X(v), H - B, "#eef1f4", 1))
            lab = f"{v:g}" if v >= 1 else f"1/{int(1/v)}"
            b.append(_text(X(v), H - B + 16, lab, 10.5, SOFT, "middle"))
    for v in (10, 100, 1000, 10000, 100000):
        b.append(_line(L, Y(v), W - R, Y(v), "#eef1f4", 1))
        b.append(_text(L - 8, Y(v) + 4, f"{v:,}", 10.5, SOFT, "end"))
    b.append(_text((L + W - R) / 2, H - 18, "arithmetic intensity: FLOP per byte moved from memory (log scale)", 12, SOFT, "middle", "600"))
    b.append(_text(18, (T + H - B) / 2, "attainable GFLOPS", 12, SOFT, "middle", "600", f'transform="rotate(-90 18 {(T + H - B) / 2})"'))
    for name, bw, peak, col in machines:
        ridge = peak / bw
        b.append(f'<polyline points="{X(xmin):.1f},{Y(max(ymin, bw * xmin)):.1f} {X(ridge):.1f},{Y(peak):.1f} {X(xmax):.1f},{Y(peak):.1f}" fill="none" stroke="{col}" stroke-width="2.5"/>')
        b.append(_text(X(ridge) + 6, Y(peak) - 8, f"{name}: {peak/1000:g} TFLOPS", 11.5, col, weight="700"))
        b.append(_line(X(ridge), Y(peak), X(ridge), H - B, col, 1, "3 3"))
        b.append(_text(X(ridge) + 4, H - B - 6, f"ridge {ridge:.0f}", 10.5, col))
        bx = 0.25
        b.append(_text(X(bx) + 4, Y(bw * bx) - 10, f"{bw:g} GB/s", 11, col, weight="600",
                       extra=f'transform="rotate(-{math.degrees(math.atan2(Y(bw*bx)-Y(bw*bx*4), X(bx*4)-X(bx))):.1f} {X(bx)+4:.1f} {Y(bw*bx)-10:.1f})"'))
    for label, ai, col in points:
        bw, peak = machines[0][1], machines[0][2]
        att = min(peak, bw * ai)
        b.append(f'<circle cx="{X(ai):.1f}" cy="{Y(att):.1f}" r="6" fill="{col}" stroke="#fff" stroke-width="1.5"/>')
        if ai > 4:
            b.append(_text(X(ai) - 10, Y(att) + 20, f"{label} → {att:,.0f} GFLOPS", 11.5, col, "end", "700"))
        else:
            b.append(_text(X(ai) + 10, Y(att) + 18, f"{label} → {att:,.0f} GFLOPS", 11.5, col, weight="700"))
    if title:
        b.append(_text(L, T - 10, title, 12.5, INK, weight="700"))
    return _svg(W, H, "".join(b), "Roofline chart")


def shuffle_tree():
    """Diagram 4.2: warp_sum — five __shfl_down_sync steps fold 32 partial sums into lane 0."""
    lanes, cw, x0, y0, rh = 32, 19, 110, 46, 52
    b = []
    for i in range(0, lanes, 4):
        b.append(_text(x0 + i * cw + cw / 2, y0 - 14, str(i), 10.5, SOFT, "middle"))
    b.append(_text(x0 + lanes * cw / 2, y0 - 30, "lane", 12, SOFT, "middle", "600"))
    steps = [None, 16, 8, 4, 2, 1]
    live = lanes
    for r, off in enumerate(steps):
        y = y0 + r * rh
        label = "partial sums" if off is None else f"offset {off}"
        b.append(_text(x0 - 12, y + 14, label, 12, INK, "end", "600"))
        if off is not None:
            live = off
            for i in range(off):
                sx = x0 + (i + off) * cw + cw / 2; dx = x0 + i * cw + cw / 2
                b.append(_line(sx, y - rh + 20, dx, y - 1, ACC, 1, None, True))
        for i in range(lanes):
            useful = i < live
            fill = ACC_SOFT if useful else "#f6f7f9"
            stroke = ACC if useful else LINE
            if r == len(steps) - 1 and i == 0:
                fill, stroke = WARM_SOFT, WARM
            b.append(_rect(x0 + i * cw + 1, y, cw - 2, 18, fill, stroke, 1, 3))
    yb = y0 + len(steps) * rh
    b.append(_text(x0, yb, "Each step: every lane adds the value held by the lane offset places to its right (__shfl_down_sync).", 12, SOFT))
    b.append(_text(x0, yb + 18, "All 32 lanes run every step; only the blue ones still hold a useful partial sum. After 5 steps lane 0 has the total.", 12, SOFT))
    b.append(_text(x0, yb + 36, "No memory is touched: values move between registers of the same warp.", 12, INK, weight="600"))
    return _svg(x0 + lanes * cw + 20, yb + 48, "".join(b), "Warp shuffle reduction tree folding 32 values into lane 0 in five steps")


def reg_occupancy():
    """Diagram 7.3: registers per thread -> resident warps per SM (Ada cap 48, Pascal/Hopper cap 64)."""
    import math
    def warps(r, cap):
        per_warp = math.ceil(r * 32 / 256) * 256
        return min(cap, 65536 // per_warp)
    W, H, L, R, T, B = 700, 360, 70, 30, 30, 70
    rmin, rmax = 16, 128
    def X(r): return L + (r - rmin) / (rmax - rmin) * (W - L - R)
    def Y(w): return H - B - w / 64 * (H - T - B)
    b = [_rect(L, T, W - L - R, H - T - B, "#fff", LINE)]
    for w in (0, 16, 32, 48, 64):
        b.append(_line(L, Y(w), W - R, Y(w), "#eef1f4"))
        b.append(_text(L - 8, Y(w) + 4, str(w), 11, SOFT, "end"))
    for r in range(16, 129, 16):
        b.append(_text(X(r), H - B + 16, str(r), 11, SOFT, "middle"))
    b.append(_text((L + W - R) / 2, H - B + 36, "registers per thread", 12, SOFT, "middle", "600"))
    b.append(_text(18, (T + H - B) / 2, "resident warps per SM", 12, SOFT, "middle", "600", f'transform="rotate(-90 18 {(T + H - B) / 2})"'))
    for cap, col, name in ((64, GOOD, "Pascal and Hopper (cap 64)"), (48, ACC, "Ada (cap 48)")):
        pts = []
        for r in range(rmin, rmax + 1):
            pts.append(f"{X(r):.1f},{Y(warps(r, cap)):.1f}")
        b.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" stroke-width="2.4"/>')
        b.append(_text(X(96), Y(warps(96, cap)) - 8, name, 11.5, col, weight="700"))
    for r, name in ((38, "naive 38"), (40, "warp 40"), (53, "warp4 53")):
        w = warps(r, 48)
        b.append(f'<circle cx="{X(r):.1f}" cy="{Y(w):.1f}" r="5.5" fill="{WARM}" stroke="#fff" stroke-width="1.5"/>')
        b.append(_text(X(r) + 8, Y(w) + (16 if r == 53 else -10), f"{name} regs → {w} warps on Ada", 11, WARM, weight="700"))
    b.append(_text(L, H - 14, "Rule: a warp's registers are rounded up to a multiple of 256; 65,536 per SM; then the SM's warp cap applies.", 11.5, SOFT))
    return _svg(W, H, "".join(b), "Staircase of resident warps per SM against registers per thread")


def streams_graphs():
    """Diagram 8.3: one stream vs three (copy/compute overlap), and per-kernel launches vs one graph launch."""
    u, lx, w = 34, 190, 900            # px per time unit, left edge of timelines, width
    lane_h, gap = 26, 8
    b = []

    def lane(y, label):
        b.append(_text(lx - 10, y + lane_h / 2 + 4, label, 12, SOFT, "end"))
        b.append(_line(lx, y + lane_h, lx + 18 * u, y + lane_h, LINE))

    def box(y, t0, t1, txt, fill, stroke):
        b.append(_rect(lx + t0 * u + 1, y + 2, (t1 - t0) * u - 2, lane_h - 4, fill, stroke, 1, 3))
        b.append(_text(lx + (t0 + t1) / 2 * u, y + lane_h / 2 + 4, txt, 11, INK, "middle"))

    def endmark(y0, y1, t, txt, colour):
        x = lx + t * u
        b.append(_line(x, y0, x, y1, colour, 1.5, "4 3"))
        b.append(_text(x + 6, y0 + 10, txt, 12, colour, weight="600"))

    # --- top: copy in / kernel / copy out, 3 chunks of 2 time units each step
    y = 34
    b.append(_text(20, y - 12, "Copies and kernels: one stream against three (pinned host memory)", 14, INK, weight="600"))
    names = ["copy engine, host to GPU", "SMs, the kernel", "copy engine, GPU to host"]
    kinds = [("in", GOOD_SOFT, GOOD), ("K", ACC_SOFT, ACC), ("out", WARM_SOFT, WARM)]
    b.append(_text(20, y + 10, "one stream, all of W at once", 12, ACC, weight="600"))
    y += 18
    for r in range(3):
        ly = y + r * (lane_h + gap)
        lane(ly, names[r])
        box(ly, 6 * r, 6 * r + 6, kinds[r][0] + " (all of W)", kinds[r][1], kinds[r][2])
    endmark(y - 2, y + 3 * (lane_h + gap) + 4, 18, "done at 18", RED)
    y2 = y + 3 * (lane_h + gap) + 14
    b.append(_text(20, y2 + 10, "three streams, W in three chunks, one chunk per stream", 12, ACC, weight="600"))
    y2 += 18
    for r in range(3):
        ly = y2 + r * (lane_h + gap)
        lane(ly, names[r])
        for c in range(3):
            t0 = 2 * (c + r)
            box(ly, t0, t0 + 2, f"{kinds[r][0]} {c + 1}", kinds[r][1], kinds[r][2])
    endmark(y2 - 2, y2 + 3 * (lane_h + gap) + 4, 10, "done at 10", GOOD)

    # --- bottom: five small kernels, launch work 3 units each vs one graph launch
    y3 = y2 + 3 * (lane_h + gap) + 54
    b.append(_text(20, y3 - 12, "Five short kernels: five launches against one graph launch", 14, INK, weight="600"))
    a, k, n = 3, 2, 5
    lane(y3, "CPU, five launches")
    for i in range(n):
        box(y3, a * i, a * i + a, f"launch {i + 1}", "#fff", SOFT)
    yg = y3 + lane_h + gap
    lane(yg, "GPU")
    end = 0
    for i in range(n):
        t0 = max(a * i + a, end)
        if t0 > end and i > 0:
            b.append(_rect(lx + end * u + 1, yg + 8, (t0 - end) * u - 2, lane_h - 16, RED_SOFT, RED_SOFT))
        box(yg, t0, t0 + k, f"k{i + 1}", ACC_SOFT, ACC)
        end = t0 + k
    endmark(y3 - 2, yg + lane_h + 4, end, f"done at {end}", RED)
    b.append(_text(lx + 5.5 * u, yg + lane_h + 18, "pink: GPU idle, waiting for the CPU to queue the next kernel", 11, RED, "middle"))
    y4 = yg + lane_h + 34
    lane(y4, "CPU, one graph launch")
    box(y4, 0, a, "graph launch", "#fff", SOFT)
    yg2 = y4 + lane_h + gap
    lane(yg2, "GPU")
    for i in range(n):
        box(yg2, a + k * i, a + k * i + k, f"k{i + 1}", ACC_SOFT, ACC)
    endmark(y4 - 2, yg2 + lane_h + 4, a + k * n, f"done at {a + k * n}", GOOD)
    h = yg2 + lane_h + 22
    b.append(_text(lx + 9 * u, h - 4, "time, in arbitrary units", 11, SOFT, "middle"))
    return _svg(w, h + 6, "".join(b), "Copy and kernel overlap with three streams, and kernel launches against a CUDA graph launch")


def waves():
    """Diagram 9.2: matvec_warp's 512 blocks as waves, laptop (20 SMs x 6 slots) vs H100 (132 SMs x 8)."""
    w, lx = 900, 90
    b = []
    # --- laptop: 20 SMs, 6 block slots each, 512 blocks -> 4 full waves + 32 blocks
    sms, slots, blocks = 20, 6, 512
    cw, cg, sh, sg = 30, 4, 6, 1        # column width/gap, slot height/gap
    y = 34
    b.append(_text(20, y - 8, "Laptop, RTX 4050: 20 SMs × 6 block slots = 120 blocks per wave", 17, INK, weight="600"))
    per_wave = sms * slots
    nwaves = -(-blocks // per_wave)
    row_h = slots * (sh + sg) + 10
    for wv in range(nwaves):
        left = blocks - wv * per_wave
        used = min(left, per_wave)
        ry = y + 8 + wv * row_h
        b.append(_text(lx - 12, ry + row_h / 2, f"wave {wv + 1}", 14, SOFT, "end"))
        for sm in range(sms):
            # spread a partial wave the way the work distributor would: one per SM, then a second
            n = slots if used == per_wave else used // sms + (1 if sm < used % sms else 0)
            for k in range(slots):
                on = k < n
                b.append(_rect(lx + sm * (cw + cg), ry + (slots - 1 - k) * (sh + sg), cw, sh,
                               ACC if on else "#fff", ACC if on else LINE))
        b.append(_text(lx + sms * (cw + cg) + 8, ry + row_h / 2, f"{used} of {per_wave}",
                       15, RED if used < per_wave else SOFT, weight="600" if used < per_wave else "normal"))
    yb = y + 8 + nwaves * row_h
    b.append(_text(lx, yb + 10, "one column per SM, one box per block slot; blue = a block of 8 warps", 13, SOFT))
    # --- H100: 132 SMs, 8 slots each
    y2 = yb + 56
    sms2, slots2 = 132, 8
    per2 = sms2 * slots2
    b.append(_text(20, y2 - 8, f"H100 SXM: 132 SMs × 8 block slots = {per2:,} blocks per wave", 17, INK, weight="600"))
    cw2 = 5
    ry = y2 + 8
    b.append(_text(lx - 12, ry + slots2 * (sh + sg) / 2 + 4, "wave 1", 14, SOFT, "end"))
    for sm in range(sms2):
        n = blocks // sms2 + (1 if sm < blocks % sms2 else 0)
        for k in range(slots2):
            on = k < n
            b.append(_rect(lx + sm * cw2, ry + (slots2 - 1 - k) * (sh + sg), cw2 - 1, sh,
                           ACC if on else "#fff", ACC if on else LINE, 0.5))
    b.append(_text(lx + sms2 * cw2 + 8, ry + slots2 * (sh + sg) / 2 + 4,
                   f"{blocks} of {per2:,}", 15, RED, weight="600"))
    h = ry + slots2 * (sh + sg) + 22
    b.append(_text(lx, h - 4, "the same grid, 512 blocks: less than half of one wave", 13, SOFT))
    return _svg(w, h + 6, "".join(b), "matvec_warp's 512 blocks as waves on the laptop and on an H100")


def tool_tower():
    """Diagram 10.1: which tool sees which layer. Full dot = sees it, ring = sees part of it."""
    rows = ["your program and its framework, NVTX ranges",
            "CUDA API calls, runtime and driver",
            "host kernel driver: ioctls, page faults",
            "GPU timeline: each kernel and copy, start to end",
            "one kernel's hardware counters",
            "inside a kernel: per instruction, per thread",
            "the whole device, sampled"]
    cols = [("NVML,", "DCGM"), ("Nsight", "Systems"), ("Nsight", "Compute"), ("Sanitizer,", "NVBit"),
            ("host eBPF:", "uprobe, kprobe"), ("bpftime", "GPU probe")]
    F, P = "F", "P"
    marks = {  # (row, col): mark
        (6, 0): F, (4, 0): P,
        (0, 1): F, (1, 1): F, (2, 1): P, (3, 1): F, (6, 1): P,
        (3, 2): P, (4, 2): F, (5, 2): P,
        (5, 3): F,
        (0, 4): P, (1, 4): F, (2, 4): F,
        (1, 5): F, (3, 5): P, (5, 5): P,
    }
    lw, cw, rh, top = 360, 104, 40, 64
    w = lw + cw * len(cols) + 20
    b = []
    for j, (a, c) in enumerate(cols):
        x = lw + j * cw + cw / 2
        colour = ACC if j == 5 else INK
        b.append(_text(x, 26, a, 14, colour, "middle", "600"))
        b.append(_text(x, 44, c, 14, colour, "middle", "600"))
    for i, r in enumerate(rows):
        y = top + i * rh
        if i % 2 == 0:
            b.append(_rect(10, y, w - 20, rh, "#f6f8fa", "none"))
        b.append(_text(20, y + rh / 2 + 5, r, 14, INK))
        for j in range(len(cols)):
            m = marks.get((i, j))
            cx, cy = lw + j * cw + cw / 2, y + rh / 2
            colour = ACC if j == 5 else GOOD
            if m == F:
                b.append(f'<circle cx="{cx}" cy="{cy}" r="9" fill="{colour}"/>')
            elif m == P:
                b.append(f'<circle cx="{cx}" cy="{cy}" r="8" fill="#fff" stroke="{colour}" stroke-width="2.5"/>')
    yl = top + len(rows) * rh + 26
    b.append(f'<circle cx="28" cy="{yl - 5}" r="7" fill="{GOOD}"/>')
    b.append(_text(42, yl, "sees this layer", 13, SOFT))
    b.append(f'<circle cx="178" cy="{yl - 5}" r="6" fill="#fff" stroke="{GOOD}" stroke-width="2.5"/>')
    b.append(_text(192, yl, "sees part of it (the chapter text says which part)", 13, SOFT))
    return _svg(w, yl + 14, "".join(b), "Which GPU tool sees which layer, from the program down to inside a kernel")


def tool_taps():
    """Diagram 10.3: three lanes (host, load-time code, GPU) and where each tool taps in."""
    w, lx, bw, bh, gap = 920, 190, 200, 46, 50
    lanes = [
        ("host", [("program,", "framework"), ("CUDA API:", "libcudart, libcuda"), ("host kernel driver:", "nvidia.ko")],
         {1: ("uprobes, CUPTI callbacks,", "Nsight Systems", GOOD), 2: ("kprobes", "", GOOD)}),
        ("the kernel's code,", [("PTX", ""), ("ptxas", ""), ("SASS", "")],
         {0: ("bpftime rewrites", "the PTX here", ACC), 2: ("NVBit rewrites", "the SASS here", WARM)}),
        ("GPU", [("kernel runs", ""), ("hardware counters", "")],
         {0: ("bpftime's probe code", "runs inside it", ACC), 1: ("Nsight Compute,", "CUPTI profiling, DCGM", GOOD)}),
    ]
    lane_h = 150
    b = []
    for i, (name, boxes, taps) in enumerate(lanes):
        y = 14 + i * lane_h
        b.append(_rect(10, y, w - 20, lane_h - 12, "#f6f8fa" if i % 2 == 0 else "#fff", LINE, 1, 8))
        b.append(_text(24, y + 30, name, 15, INK, weight="600"))
        if i == 1:
            b.append(_text(24, y + 50, "at load time", 15, INK, weight="600"))
        for j, (a, c) in enumerate(boxes):
            x = lx + j * (bw + gap)
            by = y + 16
            b.append(_rect(x, by, bw, bh, "#fff", SOFT, 1.2, 4))
            if c:
                b.append(_text(x + bw / 2, by + 19, a, 14, INK, "middle"))
                b.append(_text(x + bw / 2, by + 37, c, 14, INK, "middle"))
            else:
                b.append(_text(x + bw / 2, by + 28, a, 14, INK, "middle"))
            if j + 1 < len(boxes):
                b.append(_line(x + bw, by + bh / 2, x + bw + gap - 2, by + bh / 2, SOFT, 1.4, arrow=True))
            if j in taps:
                t1, t2, colour = taps[j]
                ty = by + bh + 28
                b.append(_line(x + bw / 2, ty - 12, x + bw / 2, by + bh + 2, colour, 1.6, "3 3", arrow=True))
                b.append(_text(x + bw / 2, ty + 4, t1, 14, colour, "middle", "600"))
                if t2:
                    b.append(_text(x + bw / 2, ty + 22, t2, 14, colour, "middle", "600"))
    h = 14 + len(lanes) * lane_h
    return _svg(w, h, "".join(b), "Where each GPU tool taps in: host API and driver, PTX and SASS at load time, and the GPU")


def roofline3():
    """Diagram 11.1: rooflines of the three benches, plus the H100's FP16 tensor-core roof."""
    import math
    W, H = 780, 480
    L, R, T, B = 86, 24, 34, 62
    xmin, xmax, ymin, ymax = 0.0625, 1024.0, 10.0, 2000000.0
    def X(v): return L + (math.log10(v) - math.log10(xmin)) / (math.log10(xmax) - math.log10(xmin)) * (W - L - R)
    def Y(v): return H - B - (math.log10(v) - math.log10(ymin)) / (math.log10(ymax) - math.log10(ymin)) * (H - T - B)
    b = [_rect(L, T, W - L - R, H - T - B, "#fff", LINE, 1)]
    for e in range(-4, 11):
        v = 2.0 ** e
        b.append(_line(X(v), T, X(v), H - B, "#eef1f4", 1))
        b.append(_text(X(v), H - B + 16, f"{v:g}" if v >= 1 else f"1/{int(1/v)}", 11, SOFT, "middle"))
    for v in (10, 100, 1000, 10000, 100000, 1000000):
        b.append(_line(L, Y(v), W - R, Y(v), "#eef1f4", 1))
        b.append(_text(L - 8, Y(v) + 4, f"{v:,}", 11, SOFT, "end"))
    b.append(_text((L + W - R) / 2, H - 18, "arithmetic intensity: FLOP per byte from memory (log scale)", 13, SOFT, "middle", "600"))
    b.append(_text(20, (T + H - B) / 2, "attainable GFLOPS", 13, SOFT, "middle", "600", f'transform="rotate(-90 20 {(T + H - B) / 2})"'))
    machines = [  # name, GB/s, GFLOPS, colour, label dy, ridge label y
        ("H100 SXM, FP16 tensor cores, dense", 3352.0, 1000000.0, RED, -8, 0),
        ("H100 SXM, FP32", 3352.0, 66900.0, GOOD, -8, 1),
        ("RTX 4050 Laptop, FP32", 216.0, 12000.0, ACC, -8, 2),
        ("P5000, FP32", 288.0, 8900.0, WARM, 17, 3),
    ]
    for name, bw, peak, col, dy, k in machines:
        ridge = peak / bw
        b.append(f'<polyline points="{X(xmin):.1f},{Y(max(ymin, bw * xmin)):.1f} {X(ridge):.1f},{Y(peak):.1f} {X(xmax):.1f},{Y(peak):.1f}" fill="none" stroke="{col}" stroke-width="2.5"/>')
        b.append(_text(X(xmax) - 6, Y(peak) + dy, f"{name}: {peak / 1000:,.4g} TFLOPS", 12.5, col, "end", "700"))
        b.append(_line(X(ridge), Y(peak), X(ridge), H - B, col, 1, "3 3"))
        b.append(_text(X(ridge) + 4, H - B - 8 - 16 * k, f"ridge {ridge:.0f}", 11.5, col, weight="600"))
    # bandwidth labels on the two families of slopes
    for bw, txt, col, bx in ((3352.0, "3,352 GB/s", GOOD, 0.09), (250.0, "216 and 288 GB/s", ACC, 0.0625)):
        ang = math.degrees(math.atan2(Y(bw * bx) - Y(bw * bx * 4), X(bx * 4) - X(bx)))
        b.append(_text(X(bx) + 4, Y(bw * bx) - 10, txt, 12, col, weight="600",
                       extra=f'transform="rotate(-{ang:.1f} {X(bx) + 4:.1f} {Y(bw * bx) - 10:.1f})"'))
    # our matvec on each machine
    for bw, col in ((3352.0, GOOD), (216.0, ACC), (288.0, WARM)):
        b.append(f'<circle cx="{X(0.5):.1f}" cy="{Y(bw * 0.5):.1f}" r="6" fill="{col}" stroke="#fff" stroke-width="1.5"/>')
    b.append(_text(X(0.5) + 14, Y(40), "our matvec, 0.5 FLOP/byte:", 12.5, INK, weight="700"))
    b.append(_text(X(0.5) + 14, Y(40) + 17, "108, 144 and 1,676 GFLOPS", 12.5, INK, weight="700"))
    # batch-64 FP16 decode on the H100 tensor roof
    ai = 64.0
    att = min(1000000.0, 3352.0 * ai)
    b.append(f'<circle cx="{X(ai):.1f}" cy="{Y(att):.1f}" r="7" fill="{RED}" stroke="#fff" stroke-width="1.5"/>')
    b.append(_text(X(ai) - 12, Y(att) + 4, f"64 sequences decoding at once, FP16 weights:", 12.5, RED, "end", "700"))
    b.append(_text(X(ai) - 12, Y(att) + 21, f"64 FLOP/byte → {att / 1000:,.0f} TFLOPS, still under the slope", 12.5, RED, "end", "700"))
    return _svg(W, H, "".join(b), "Rooflines of the P5000, the RTX 4050 Laptop and the H100")


def _box(b, x, y, w, h, lines, fill="#fff", stroke=SOFT, size=14, colour=INK, weight="normal", sw=1.2):
    """A rounded box with centred lines of text."""
    b.append(_rect(x, y, w, h, fill, stroke, sw, 5))
    n = len(lines)
    for i, t in enumerate(lines):
        ty = y + h / 2 + (i - (n - 1) / 2) * (size + 4) + size * 0.35
        b.append(_text(x + w / 2, ty, t, size, colour, "middle", weight))


def _panel(b, x, y, w, h, title, fill="#f6f8fa"):
    b.append(_rect(x, y, w, h, fill, LINE, 1, 8))
    b.append(_text(x + 12, y + 20, title, 14, SOFT, weight="600"))


def _arrow(b, x1, y1, x2, y2, colour=SOFT, sw=1.6, dash=None, label=None, lx=None, ly=None, anchor="middle"):
    b.append(_line(x1, y1, x2, y2, colour, sw, dash, arrow=True))
    if label:
        for i, t in enumerate(label if isinstance(label, list) else [label]):
            b.append(_text(lx if lx is not None else (x1 + x2) / 2, (ly if ly is not None else (y1 + y2) / 2 - 6) + i * 16,
                           t, 13, colour, anchor, "600"))


def bpftime_session():
    """Diagram 12.1: loader process, shared segment, target process."""
    W, H = 920, 380
    b = []
    _panel(b, 10, 10, 260, 360, "loader process")
    _box(b, 30, 50, 220, 60, ["libbpf program,", "for example cuda_probe"])
    _box(b, 30, 200, 220, 74, ["libbpftime-syscall-server.so:", "answers instead", "of the kernel"])
    _arrow(b, 140, 110, 140, 198, label=["bpf(),", "perf_event_open()"], lx=150, ly=145, anchor="start")
    _panel(b, 320, 10, 270, 360, "shared-memory segment")
    _box(b, 340, 50, 230, 50, ["programs: eBPF bytecode"])
    _box(b, 340, 130, 230, 50, ["maps: host maps live here"])
    _box(b, 340, 210, 230, 74, ["handlers: kprobe on", "_Z11matvec_warpPKfS0_Pfii,", "…"], size=13)
    b.append(_text(455, 330, "named by BPFTIME_GLOBAL_SHM_NAME", 12, SOFT, "middle"))
    _panel(b, 640, 10, 270, 360, "target process: the CUDA program")
    _box(b, 660, 50, 230, 60, ["libbpftime-agent.so: reads", "handlers, compiles programs"])
    _box(b, 660, 170, 230, 56, ["Frida attach:", "uprobes on host functions"])
    _box(b, 660, 270, 230, 56, ["nv_attach_impl:", "probes inside GPU kernels"], ACC_SOFT, ACC, sw=2)
    _arrow(b, 775, 110, 775, 168)
    _arrow(b, 700, 110, 700, 268)
    _arrow(b, 250, 237, 338, 237, label="writes", ly=228)
    _arrow(b, 572, 75, 658, 75, label="reads", ly=66)
    _arrow(b, 250, 80, 338, 155, GOOD, 1.6, "5 4", label="reads maps", lx=300, ly=104)
    return _svg(W, H, "".join(b), "A bpftime session: loader process, shared segment, target process")


def map_costs():
    """Diagram 12.2: GPU map lookup is address arithmetic; ordinary map lookup is a host round trip."""
    W, H = 960, 410
    b = []
    _panel(b, 10, 130, 200, 150, "inside the patched kernel")
    _box(b, 30, 175, 160, 70, ["probe code,", "one copy per thread"])
    _panel(b, 370, 10, 250, 110, "device memory", GOOD_SOFT)
    _box(b, 390, 45, 210, 56, ["per-thread array map:", "one slot per thread"], "#fff", GOOD, sw=2)
    _panel(b, 370, 250, 320, 150, "host memory: the segment, pinned", WARM_SOFT)
    _box(b, 390, 290, 120, 56, ["request", "area"], "#fff", WARM, sw=2)
    _box(b, 530, 290, 140, 56, ["hash map,", "array map, …"])
    _panel(b, 740, 250, 210, 150, "target process, host side")
    _box(b, 755, 290, 180, 56, ["agent's watcher", "thread: runs the", "real lookup"], size=13)
    _panel(b, 740, 10, 210, 110, "loader process")
    _box(b, 755, 45, 180, 56, ["libbpf:", "bpf_map_lookup_elem"], size=13)
    _arrow(b, 190, 190, 388, 78, GOOD, 2, label=["address arithmetic,", "no host involved"], lx=200, ly=44, anchor="start")
    _arrow(b, 190, 230, 388, 312, WARM, 2, label=["write a request,", "wait for the answer"], lx=200, ly=352, anchor="start")
    _arrow(b, 753, 318, 672, 318, SOFT, 1.4)
    b.append(f'<polyline points="845,346 845,372 450,372 450,348" fill="none" stroke="{WARM}" stroke-width="1.4" stroke-dasharray="4 3" marker-end="url(#ah)"/>')
    b.append(_text(648, 390, "polls the request area", 12, WARM, "middle", "600"))
    _arrow(b, 753, 73, 602, 73, GOOD, 1.4, label=["copies every", "thread's slot"], lx=612, ly=94, anchor="start")
    _arrow(b, 845, 101, 640, 288, SOFT, 1.2, "4 3")
    return _svg(W, H, "".join(b), "Two kinds of bpftime map and what a lookup from the GPU costs")

def attach_pipeline():
    """Diagram 13.2: from fatbin to patched launch, as a numbered snake of boxes."""
    W, bw, bh, gx, gy = 940, 270, 78, 45, 50
    x0, y0 = 20, 40
    b = []
    steps = [
        ("1  registration hooked", ["__cudaRegisterFatBinary:", "fatbin bytes copied"], "#fff", SOFT),
        ("2  PTX extracted", ["only the PTX entries;", "the SASS is not used"], "#fff", SOFT),
        ("3  passes patch the PTX", ["call __probe_func__… at entry,", "__retprobe_func__… before ret"], ACC_SOFT, ACC),
        ("4  trampoline added", ["helpers, map_info, constData", "prepended as PTX"], "#fff", SOFT),
        ("5  compiled for this GPU", [".target rewritten; nvPTXCompiler", "--gpu-name=sm_89 -O3"], "#fff", SOFT),
        ("6  loaded as a new module", ["cuModuleLoadDataEx; constData", "and map_info filled in"], "#fff", SOFT),
        ("7  launch intercepted", ["cudaLaunchKernel, _ptsz,", "cuLaunchKernel, graph nodes"], "#fff", SOFT),
        ("8  CUfunction swapped", ["same name, same arguments,", "the patched module's copy"], ACC_SOFT, ACC),
        ("9  patched kernel runs", ["every thread calls the probe", "at entry and at exit"], GOOD_SOFT, GOOD),
    ]
    pos = []
    for i in range(9):
        r, c = divmod(i, 3)
        if r == 1:
            c = 2 - c
        pos.append((x0 + c * (bw + gx), y0 + r * (bh + gy + 22)))
    rows_title = ["at registration, before main", "", "at every launch"]
    b.append(_text(x0, 24, "at registration, before main (or after attach, by scanning loaded fatbins)", 14, SOFT, weight="600"))
    b.append(_text(x0, y0 + 2 * (bh + gy + 22) - 16, "at every launch", 14, SOFT, weight="600"))
    for i, ((title, lines, fill, stroke), (x, y)) in enumerate(zip(steps, pos)):
        b.append(_rect(x, y, bw, bh + 22, fill, stroke, 1.6 if stroke != SOFT else 1.2, 6))
        b.append(_text(x + 12, y + 22, title, 14, stroke if stroke != SOFT else INK, weight="700"))
        for j, t in enumerate(lines):
            b.append(_text(x + 12, y + 50 + j * 19, t, 13, INK))
    for i in range(8):
        (xa, ya), (xb, yb) = pos[i], pos[i + 1]
        if ya == yb:
            if xb > xa:
                _arrow(b, xa + bw, ya + 50, xb - 2, yb + 50)
            else:
                _arrow(b, xa, ya + 50, xb + bw + 2, yb + 50)
        elif i == 5:
            continue
        else:
            _arrow(b, xa + bw / 2, ya + bh + 22, xb + bw / 2, yb - 2)
    H = pos[-1][1] + bh + 22 + 16
    return _svg(W, H, "".join(b), "bpftime's GPU attach pipeline from fatbin registration to the patched launch")


def host_calls():
    """Diagram 14.2: host-call helpers served one at a time, one per watcher wake-up."""
    W, lx, u = 860, 150, 110        # u = px per millisecond
    rows = ["warp 0 lane 0", "warp 0 lane 1", "warp 3 lane 0", "warp 9 lane 0", "warp 9 lane 1"]
    rh, top = 38, 72
    b = []
    b.append(_text(lx - 10, 46, "watcher", 15, INK, "end", "600"))
    for k in range(6):
        x = lx + 0.35 * u + k * u
        b.append(_line(x, 34, x, 58, WARM, 2))
        b.append(_text(x, 28, "checks", 13, WARM, "middle"))
    b.append(_line(lx, 58, lx + 6.4 * u, 58, LINE))
    for i, r in enumerate(rows):
        y = top + i * rh
        b.append(_text(lx - 10, y + rh / 2 + 5, r, 15, INK, "end"))
        t_req = 0.05 + 0.02 * i                  # every lane asks almost at once
        t_srv = 0.35 + i                         # served at successive checks
        b.append(_rect(lx + t_req * u, y + 8, (t_srv - t_req) * u, rh - 16, RED_SOFT, RED_SOFT, 1, 3))
        b.append(_rect(lx + t_srv * u, y + 6, 0.12 * u, rh - 12, GOOD, GOOD, 1, 2))
        b.append(_line(lx + t_srv * u, 58, lx + t_srv * u + 0.06 * u, y + 6, GOOD, 1, "3 3"))
    yb = top + len(rows) * rh + 14
    for k in range(7):
        x = lx + k * u
        b.append(_line(x, yb - 6, x, yb, SOFT))
        b.append(_text(x, yb + 14, f"{k} ms", 13, SOFT, "middle"))
    b.append(_rect(lx, yb + 30, 14, 12, RED_SOFT, RED_SOFT))
    b.append(_text(lx + 20, yb + 41, "waiting: spinning on the GPU-wide lock, or on the answer flag", 14, SOFT))
    b.append(_rect(lx, yb + 50, 14, 12, GOOD, GOOD))
    b.append(_text(lx + 20, yb + 61, "served: the watcher saw the request and answered", 14, SOFT))
    return _svg(W, yb + 72, "".join(b), "Host-call helpers are served one at a time, one per watcher wake-up")


def attention_toy():
    """Diagram 15.2: one head, one new token. Scores q·k, softmax, weighted sum of v. Toy numbers."""
    import math, random
    rnd = random.Random(7)
    toks = ["The", "cat", "sat", "on", "the", "mat"]
    scores = [0.3, 2.1, 0.8, -0.5, 0.4, 1.6]
    e = [math.exp(x) for x in scores]
    p = [x / sum(e) for x in e]
    W, c, rh = 900, 18, 30
    xt, xk, xs, xb, xv = 20, 120, 300, 430, 640
    top = 96
    b = []
    def cells(x, y, n, colour, alpha_list, h=rh - 8):
        for j in range(n):
            a = alpha_list[j]
            b.append(f'<rect x="{x + j * c}" y="{y}" width="{c - 2}" height="{h}" fill="{colour}" fill-opacity="{a:.2f}" stroke="{colour}" stroke-width="0.6"/>')
    # query
    b.append(_text(xk, 30, "q: the query of the new token, from Wq · x", 13, ACC, weight="600"))
    cells(xk, 40, 8, ACC, [rnd.uniform(0.2, 0.9) for _ in range(8)])
    b.append(_text(xk, top - 12, "K: one key per token", 13, ACC, weight="600"))
    b.append(_text(xs, top - 12, "score: q·k / √64", 13, INK, weight="600"))
    b.append(_text(xb, top - 12, "softmax: sums to 1", 13, WARM, weight="600"))
    b.append(_text(xv, top - 12, "V: one value per token", 13, GOOD, weight="600"))
    vals = []
    for i, t in enumerate(toks):
        y = top + i * rh
        cur = i == len(toks) - 1
        b.append(_text(xt, y + 16, t + ("  (new)" if cur else ""), 14, INK, weight="700" if cur else "normal"))
        cells(xk, y, 8, ACC, [rnd.uniform(0.15, 0.9) for _ in range(8)])
        b.append(_text(xs + 40, y + 16, f"{scores[i]:+.1f}", 14, INK, "middle"))
        bw = p[i] * 220
        b.append(_rect(xb, y + 3, bw, rh - 10, WARM, WARM, 1, 2))
        b.append(_text(xb + bw + 6, y + 16, f"{p[i]:.2f}", 13, WARM))
        row = [rnd.uniform(0.15, 0.95) for _ in range(8)]
        vals.append(row)
        cells(xv, y, 8, GOOD, [0.12 + 0.88 * p[i] * v / max(p) for v in row])
    yo = top + len(toks) * rh + 34
    out = [sum(p[i] * vals[i][j] for i in range(len(toks))) for j in range(8)]
    m = max(out)
    b.append(_text(xv, yo - 8, "output = Σ weight × v", 13, GOOD, weight="600"))
    cells(xv, yo, 8, GOOD, [0.15 + 0.85 * o / m for o in out])
    b.append(_line(xv + 72, top + len(toks) * rh - 4, xv + 72, yo - 22, GOOD, 1.4, arrow=True))
    b.append(_text(xt, yo + 18, "Toy numbers: 8 of the head's 64 dimensions drawn; the scores are invented.", 12, SOFT))
    b.append(_text(xt, yo + 36, "The new token attends to itself and to every earlier token, never to later ones.", 12, SOFT))
    return _svg(W, yo + 46, "".join(b), "Attention for one head and one new token, with toy numbers")


def request_timeline():
    """Diagram 16.1: one request: queue, prefill, then decode steps; TTFT and ITL marked."""
    W, lx = 900, 40
    b = []
    y = 70
    segs = [("queue", 0, 60, "#eef1f4", SOFT), ("prefill: the whole prompt in one pass", 60, 360, ACC_SOFT, ACC)]
    for name, x0, x1, fill, stroke in segs:
        b.append(_rect(lx + x0, y, x1 - x0, 40, fill, stroke, 1.4, 4))
        b.append(_text(lx + (x0 + x1) / 2, y + 25, name, 14, INK, "middle"))
    x = 360
    for k in range(10):
        b.append(_rect(lx + x + 2, y, 40, 40, GOOD_SOFT, GOOD, 1.4, 4))
        b.append(_text(lx + x + 22, y + 25, "d", 13, GOOD, "middle", "600"))
        b.append(_line(lx + x + 42, y - 6, lx + x + 42, y + 46, GOOD, 1, "2 2"))
        x += 44
    b.append(_text(lx + x + 8, y + 25, "…", 16, GOOD))
    # markers
    def mark(xv, label, ly, colour):
        b.append(_line(lx + xv, y - 30, lx + xv, y + 70, colour, 1.6))
        b.append(_text(lx + xv + 4, ly, label, 13, colour, weight="600"))
    mark(0, "request arrives", y - 36, INK)
    mark(360, "first token, from prefill", y - 36, ACC)
    # TTFT bracket
    yb = y + 64
    b.append(_line(lx, yb, lx + 360, yb, ACC, 2))
    b.append(_text(lx + 180, yb + 20, "time to first token (TTFT): queue + prefill + the first sampling", 13, ACC, "middle", "600"))
    b.append(_line(lx + 362, y + 50, lx + 402, y + 50, GOOD, 2))
    b.append(_text(lx + 430, y + 130, "inter-token latency (ITL): one decode step, d, per further token", 13, GOOD, "start", "600"))
    b.append(_line(lx + 382, y + 52, lx + 430, y + 118, GOOD, 1, "3 3"))
    b.append(_text(lx, y + 170, "Prefill is matrix-matrix work, usually compute-bound. Each decode step is matrix-vector work for every", 13, SOFT))
    b.append(_text(lx, y + 188, "sequence in the batch, memory-bound, and produces one token per sequence. Drawn to no scale.", 13, SOFT))
    return _svg(W, y + 200, "".join(b), "One request's life: queue, prefill, decode steps, with TTFT and ITL")


def kv_grid():
    """Diagram 16.2: the KV cache as layers x tokens; prefill fills a block, each decode step adds a column."""
    W = 900
    layers, prompt, steps = 6, 10, 4
    c, r = 30, 24
    x0, y0 = 150, 60
    b = []
    b.append(_text(x0, 30, "prompt tokens: written by prefill, all at once", 13, ACC, weight="600"))
    b.append(_text(x0 + prompt * c + 10, 30, "decode steps: one column each", 13, GOOD, weight="600"))
    for i in range(layers):
        y = y0 + i * r
        lab = ["layer 1", "layer 2", "layer 3", "layer 4", "⋮", "layer 24"][i]
        b.append(_text(x0 - 12, y + 16, lab, 13, INK, "end"))
        for t in range(prompt + steps):
            if t < prompt:
                fill, stroke = ACC_SOFT, ACC
            elif t < prompt + steps - 1:
                fill, stroke = GOOD_SOFT, GOOD
            else:
                fill, stroke = GOOD, GOOD
            b.append(_rect(x0 + t * c, y, c - 3, r - 4, fill, stroke, 1, 2))
    xn = x0 + (prompt + steps - 1) * c
    b.append(_text(xn + c + 10, y0 + 14, "the new token writes", 13, GOOD, weight="600"))
    b.append(_text(xn + c + 10, y0 + 31, "its k and v in every layer", 13, GOOD, weight="600"))
    yb = y0 + layers * r + 18
    b.append(_line(x0, yb, xn + c - 3, yb, WARM, 2.5, arrow=True))
    b.append(_text(x0, yb + 22, "and its attention, layer by layer, reads every column so far: the read grows with context", 13, WARM, weight="600"))
    b.append(_text(x0, yb + 44, "Each cell is one token's k and v for one layer: 512 bytes for Qwen2.5-0.5B in 16-bit, 4,096 for Llama-3.1-8B.", 12, SOFT))
    return _svg(W, yb + 56, "".join(b), "The KV cache: layers by tokens, filled by prefill and extended by decode")


def roofline_llm():
    """Diagram 16.3: prefill and decode on the H100's FP16 tensor-core roofline."""
    import math
    W, H = 720, 440
    L, R, T, B = 86, 24, 30, 62
    xmin, xmax, ymin, ymax = 0.5, 8192.0, 1000.0, 2000000.0
    def X(v): return L + (math.log10(v) - math.log10(xmin)) / (math.log10(xmax) - math.log10(xmin)) * (W - L - R)
    def Y(v): return H - B - (math.log10(v) - math.log10(ymin)) / (math.log10(ymax) - math.log10(ymin)) * (H - T - B)
    b = [_rect(L, T, W - L - R, H - T - B, "#fff", LINE, 1)]
    for e in range(-1, 14):
        v = 2.0 ** e
        if xmin <= v <= xmax:
            b.append(_line(X(v), T, X(v), H - B, "#eef1f4", 1))
            if e % 2 == 0 or e < 2:
                b.append(_text(X(v), H - B + 16, f"{v:g}", 13, SOFT, "middle"))
    for v in (1000, 10000, 100000, 1000000):
        b.append(_line(L, Y(v), W - R, Y(v), "#eef1f4", 1))
        b.append(_text(L - 8, Y(v) + 4, f"{v:,}", 13, SOFT, "end"))
    b.append(_text((L + W - R) / 2, H - 18, "FLOP per byte (log scale): about the batch B, or the prompt length P", 14, SOFT, "middle", "600"))
    b.append(_text(20, (T + H - B) / 2, "attainable GFLOPS", 14, SOFT, "middle", "600", f'transform="rotate(-90 20 {(T + H - B) / 2})"'))
    bw, peak = 3352.0, 1000000.0
    ridge = peak / bw
    b.append(f'<polyline points="{X(xmin):.1f},{Y(bw * xmin):.1f} {X(ridge):.1f},{Y(peak):.1f} {X(xmax):.1f},{Y(peak):.1f}" fill="none" stroke="{RED}" stroke-width="2.5"/>')
    b.append(_text(X(xmax) - 6, Y(peak) - 8, "H100, FP16 tensor cores: 1,000 TFLOPS", 15, RED, "end", "700"))
    b.append(_line(X(ridge), Y(peak), X(ridge), H - B, RED, 1, "3 3"))
    b.append(_text(X(ridge) + 4, H - B - 8, "ridge ≈ 300", 14, RED, weight="600"))
    pts = [("decode, B = 1", 1.0, GOOD, 10, 18, "start"), ("decode, B = 64", 64.0, GOOD, -12, 4, "end"),
           ("prefill, P = 4,096", 4096.0, ACC, -12, 30, "end")]
    for label, ai, col, dx, dy, anchor in pts:
        att = min(peak, bw * ai)
        b.append(f'<circle cx="{X(ai):.1f}" cy="{Y(att):.1f}" r="7" fill="{col}" stroke="#fff" stroke-width="1.5"/>')
        b.append(_text(X(ai) + dx, Y(att) + dy, f"{label}: ≤ {att / 1000:,.0f} TFLOPS", 15, col, anchor, "700"))
    return _svg(W, H, "".join(b), "Prefill and decode on the H100 roofline")


def token_budget():
    """Diagram 17.2: six scheduler steps under a 2,048-token budget: decodes, a chunked long prompt, a short prompt."""
    W, lx, bw, rh = 920, 120, 700, 40
    budget = 2048
    sc = bw / budget
    steps = [
        [("dec", 40)],
        [("dec", 40), ("A", 2008)],
        [("dec", 40), ("A", 2008)],
        [("dec", 40), ("A", 984), ("B", 300)],
        [("dec", 42)],
        [("dec", 42)],
    ]
    colours = {"dec": (GOOD, GOOD), "A": (ACC_SOFT, ACC), "B": (WARM_SOFT, WARM)}
    b = []
    b.append(_text(lx, 22, "each row is one step; its width is the 2,048-token budget", 13, SOFT, weight="600"))
    for i, row in enumerate(steps):
        y = 36 + i * (rh + 10)
        b.append(_text(lx - 12, y + rh / 2 + 5, f"step {i + 1}", 14, INK, "end"))
        b.append(_rect(lx, y, bw, rh, "#fff", LINE, 1, 3))
        x = lx
        for kind, n in row:
            w = n * sc
            fill, stroke = colours[kind]
            b.append(_rect(x, y + 2, max(w, 3), rh - 4, fill, stroke, 1, 2))
            if kind == "A":
                b.append(_text(x + w / 2, y + rh / 2 + 5, f"prompt A, chunk of {n:,} tokens", 13, ACC, "middle", "600"))
            elif kind == "B" :
                b.append(_text(x + w / 2, y + rh / 2 + 5, f"B: {n}", 13, WARM, "middle", "600"))
            x += w
        used = sum(n for _, n in row)
        b.append(_text(lx + bw + 10, y + rh / 2 + 5, f"{used:,}", 13, SOFT))
    y = 36 + len(steps) * (rh + 10) + 6
    b.append(_rect(lx, y, 14, 12, GOOD, GOOD))
    b.append(_text(lx + 20, y + 11, "one token for each of 40 running requests: their decode steps never stop", 13, SOFT))
    b.append(_text(lx, y + 32, "Prompt A, 5,000 tokens, arrives before step 2 and is prefilled in three chunks; B, 300 tokens, fits in step 4.", 13, SOFT))
    b.append(_text(lx, y + 52, "Both have joined the decodes by step 5: 42 requests now produce one token each per step.", 13, SOFT))
    return _svg(W, y + 62, "".join(b), "Scheduler steps filling a token budget with decodes and prefill chunks")


def block_table():
    """Diagram 17.3: two requests' block tables pointing into one pool of 16-token blocks, sharing a prefix block."""
    W = 900
    b = []
    pool_x, pool_y, cw, ch = 440, 70, 46, 40
    cols, rows = 8, 3
    owner = {2: ("A0 B0", "shared"), 9: ("A1", "A"), 5: ("A2", "A"), 14: ("A3", "A"), 11: ("B1", "B"), 0: ("B2", "B")}
    col = {"shared": (GOOD_SOFT, GOOD), "A": (ACC_SOFT, ACC), "B": (WARM_SOFT, WARM)}
    b.append(_text(pool_x, 50, "physical blocks in GPU memory, 16 tokens each", 13, INK, weight="600"))
    centres = {}
    for k in range(cols * rows):
        r, c = divmod(k, cols)
        x, y = pool_x + c * cw, pool_y + r * ch
        fill, stroke = col[owner[k][1]] if k in owner else ("#fff", LINE)
        b.append(_rect(x, y, cw - 4, ch - 4, fill, stroke, 1.2, 3))
        b.append(_text(x + 4, y + 13, str(k), 10, SOFT))
        if k in owner:
            b.append(_text(x + (cw - 4) / 2, y + 27, owner[k][0], 11.5, stroke, "middle", "700"))
        centres[k] = (x, y + (ch - 4) / 2)
    def table(x, y, name, entries, colour):
        b.append(_text(x, y - 10, name, 13, colour, weight="700"))
        for i, phys in enumerate(entries):
            b.append(_rect(x, y + i * 34, 150, 28, "#fff", colour, 1.2, 3))
            b.append(_text(x + 8, y + i * 34 + 19, f"logical {i}  →  block {phys}", 13, INK))
            px, py = centres[phys]
            b.append(_line(x + 150, y + i * 34 + 14, px - 2, py, colour, 1, "3 3", arrow=True))
    table(40, 80, "request A: 60 tokens, 4 blocks", [2, 9, 5, 14], ACC)
    table(40, 250, "request B: 40 tokens, 3 blocks", [2, 11, 0], WARM)
    notes = [("Block 2 holds the same 16-token prefix for A and B:", GOOD), ("computed once, reference count 2.", GOOD),
             ("White blocks are free, or hold cached prefixes", SOFT), ("kept for reuse until evicted.", SOFT),
             ("Only a request's last block is partly empty.", SOFT)]
    for i, (t, colour) in enumerate(notes):
        b.append(_text(pool_x, pool_y + rows * ch + 26 + i * 20, t, 13, colour, weight="600" if colour == GOOD else "normal"))
    return _svg(W, 380, "".join(b), "Block tables of two requests mapping logical KV blocks to physical blocks, with a shared prefix block")


def quant_blocks():
    """Diagram 18.2: the same 256 weights in four ggml formats, drawn to scale in bytes."""
    W, lx, sc, sh = 720, 70, 1.2, 34
    rows = [
        ("F16", [("v", 512)], "512 bytes: 16 bits per weight"),
        ("Q8_0", [("d", 2), ("q", 32)] * 8, "8 blocks of 32, 34 bytes each: 272 bytes, 8.5 bits per weight"),
        ("Q5_0", [("d", 2), ("h", 4), ("q", 16)] * 8, "8 blocks of 32, 22 bytes each: 176 bytes, 5.5 bits per weight"),
        ("Q4_K", [("d", 4), ("h", 12), ("q", 128)], "one super-block of 256: 144 bytes, 4.5 bits per weight"),
    ]
    colours = {"v": ("#eef1f4", SOFT), "d": (WARM, WARM), "h": (GOOD_SOFT, GOOD), "q": (ACC_SOFT, ACC)}
    b = [_text(lx, 24, "256 weights; one byte is one unit of width", 15, SOFT, weight="600")]
    for i, (name, segs, note) in enumerate(rows):
        y = 44 + i * 80
        b.append(_text(lx - 12, y + sh / 2 + 6, name, 16, INK, "end", "700"))
        x = lx
        for kind, n in segs:
            fill, stroke = colours[kind]
            b.append(_rect(x, y, n * sc, sh, fill, stroke, 1))
            x += n * sc
        b.append(_text(lx, y + sh + 22, note, 15, SOFT))
    y = 44 + len(rows) * 80 + 6
    legend = [("d", "scale: one FP16 number (Q4_K: a scale and a min)"),
              ("h", "Q5_0: each weight's fifth bit; Q4_K: a scale and min per 32"),
              ("q", "the quantized weights")]
    for j, (kind, text) in enumerate(legend):
        fill, stroke = colours[kind]
        b.append(_rect(lx, y + j * 26, 18, 15, fill, stroke, 1))
        b.append(_text(lx + 28, y + j * 26 + 13, text, 15, INK))
    y += len(legend) * 26 + 20
    for k, f in enumerate(["Q8_0:  weight = d × q", "Q5_0:  weight = d × (q − 16)",
                           "Q4_K:  weight = d × scale × q − dmin × min"]):
        b.append(_text(lx, y + k * 24, f, 15, INK, weight="600"))
    return _svg(W, y + 3 * 24 - 4, "".join(b), "Byte layouts of F16, Q8_0, Q5_0 and Q4_K for 256 weights, to scale")


def kernel_grid():
    """Diagram 18.3: which ggml CUDA kernel runs a multiply, by weight type and batch width."""
    W, hx, cx, cw, chh = 760, 16, 200, 272, 128
    cols = ["decode: up to 8 columns", "prefill: hundreds of columns"]
    rows = ["quantized weights", "float weights"]
    sub = ["Q8_0, Q5_0, Q4_K, …", "F16, BF16, F32"]
    cells = [[("mul_mat_vec_q", ["dp4a dot products, after the", "activations are made 8-bit"], ACC_SOFT, ACC),
              ("mul_mat_q", ["int8 tensor cores from Turing;", "dp4a tiles on Pascal"], GOOD_SOFT, GOOD)],
             [("mul_mat_vec_f", ["a float dot product", "for each output row"], "#f3f4f6", SOFT),
              ("cuBLAS", ["FP16 and BF16 tensor cores;", "mul_mat_f up to 16 columns"], "#f3f4f6", SOFT)]]
    b = []
    for j, c in enumerate(cols):
        b.append(_text(cx + j * (cw + 12) + cw / 2, 30, c, 15, INK, "middle", "700"))
    for i, r in enumerate(rows):
        y = 48 + i * (chh + 12)
        b.append(_text(hx, y + chh / 2 - 4, r, 15, INK, weight="700"))
        b.append(_text(hx, y + chh / 2 + 18, sub[i], 13.5, SOFT))
        for j in range(2):
            name, lines, fill, stroke = cells[i][j]
            x = cx + j * (cw + 12)
            b.append(_rect(x, y, cw, chh, fill, stroke, 1.4, 6))
            b.append(_text(x + cw / 2, y + 40, name, 17, stroke if stroke != SOFT else INK, "middle", "700"))
            for k, line in enumerate(lines):
                b.append(_text(x + cw / 2, y + 72 + k * 22, line, 14.5, INK, "middle"))
    y = 48 + 2 * (chh + 12) + 18
    b.append(_text(hx, y, "All four are chosen in ggml_cuda_mul_mat (ggml-cuda.cu:1822–1875);", 13.5, SOFT))
    b.append(_text(hx, y + 20, "a type none of them handles goes to cuBLAS.", 13.5, SOFT))
    return _svg(W, y + 32, "".join(b), "ggml kernel choice for a matrix multiply by weight type and batch width")


def request_taps():
    """Diagram 19.1: one streaming request on a time axis, and what each observation layer sees of it."""
    W, lx, x0, tw = 760, 14, 190, 556
    def X(t):
        return x0 + t * tw / 100
    b = []
    # the request itself
    segs = [(0, 2, "", "#eef1f4", SOFT), (2, 20, "queue", WARM_SOFT, WARM), (20, 32, "prefill", ACC_SOFT, ACC),
            (32, 44, "prefill", ACC_SOFT, ACC)]
    b.append(_text(lx, 44, "the request", 15, INK, weight="700"))
    for a, z, label, fill, stroke in segs:
        b.append(_rect(X(a), 26, X(z) - X(a), 28, fill, stroke, 1))
        if label:
            b.append(_text((X(a) + X(z)) / 2, 45, label, 13.5, stroke, "middle", "600"))
    steps = [44 + k * 7 for k in range(8)]
    for s in steps:
        b.append(_rect(X(s), 26, X(s + 7) - X(s) - 2, 28, GOOD_SOFT, GOOD, 1))
    b.append(_text((X(44) + X(100)) / 2, 74, "decode steps, one token each", 13.5, GOOD, "middle", "600"))
    # TTFT and ITL brackets
    b.append(_line(X(0), 92, X(44), 92, INK, 1.4))
    b.append(_line(X(0), 86, X(0), 98, INK, 1.4))
    b.append(_line(X(44), 86, X(44), 98, INK, 1.4))
    b.append(_text((X(0) + X(44)) / 2, 112, "TTFT", 14, INK, "middle", "700"))
    b.append(_line(X(51), 92, X(58), 92, INK, 1.4))
    b.append(_line(X(51), 86, X(51), 98, INK, 1.4))
    b.append(_line(X(58), 86, X(58), 98, INK, 1.4))
    b.append(_text((X(51) + X(58)) / 2, 112, "ITL", 14, INK, "middle", "700"))
    rows = [("socket", "tcp_recvmsg, tcp_sendmsg"), ("server", "metrics, traces, timings"),
            ("step loop", "llama_process, EngineCore"), ("driver", "cuGraphLaunch, ioctls"),
            ("GPU", "bpftime, ncu, nsys")]
    for i, (name, sub) in enumerate(rows):
        y = 136 + i * 52
        b.append(_rect(lx - 6, y - 6, W - lx, 46, "#fafbfc" if i % 2 else "#fff", "none", 0))
        b.append(_text(lx, y + 14, name, 15, INK, weight="700"))
        b.append(_text(lx, y + 32, sub, 12.5, SOFT))
        if i == 0:      # bytes in, then one send per token
            b.append(_rect(X(0), y + 6, X(2) - X(0) + 2, 22, ACC, ACC))
            for s in [44] + steps[1:]:
                b.append(_rect(X(s) - 1, y + 4, 3, 26, ACC, ACC))
        elif i == 1:    # per-request totals
            for a, z, label, colour in [(2, 20, "queue time", WARM), (20, 44, "TTFT, prefill time", ACC), (44, 100, "ITL histogram, decode time", GOOD)]:
                b.append(_line(X(a) + 2, y + 17, X(z) - 2, y + 17, colour, 3))
                b.append(_text((X(a) + X(z)) / 2, y + 34, label, 12.5, colour, "middle"))
        elif i == 2:    # every step, start and end
            for a, z in [(20, 32), (32, 44)] + [(s, s + 7) for s in steps]:
                b.append(_rect(X(a) + 1, y + 6, X(z) - X(a) - 3, 22, "#fff", INK, 1.2, 3))
        elif i == 3:    # submissions: one graph launch per decode step, bursts for prefill
            for a in (20, 32):
                for k in range(6):
                    b.append(_rect(X(a) + k * 4, y + 8, 2, 18, SOFT, SOFT))
            for s in steps:
                b.append(_rect(X(s), y + 8, 3, 18, INK, INK))
        else:           # inside each step: many kernels
            for a, z in [(20, 32), (32, 44)] + [(s, s + 7) for s in steps]:
                x = X(a) + 2
                while x < X(z) - 3:
                    b.append(_rect(x, y + 6, 2.2, 22, GOOD, GOOD))
                    x += 4.5
    return _svg(W, 136 + 5 * 52 + 4, "".join(b), "One request's timeline and what each observation layer sees of it")


def spine_traps():
    """Diagram 20.1: the matvec's trip through the document, with the trap that waits at each stage."""
    W, bx, bw, bh, gap, tx = 760, 10, 226, 42, 18, 268
    rows = [
        ("a matvec in CUDA", ["its floor is bytes over bandwidth:", "311 µs on the laptop, 20 µs on the H100"], GOOD),
        ("nvcc: PTX and SASS", ["no PTX in native builds or stock wheels;", "sm_90a code is outside the JIT path"], WARM),
        ("the host: register, launch", ["a static cudart hides registration from the hooks;", "cudaLaunchKernelEx goes around them"], WARM),
        ("CUDA graphs", ["a graph captured before the probe", "keeps the original kernels"], WARM),
        ("the GPU: blocks and warps", ["waves and occupancy set the tail;", "Pascal preemption is documented two ways"], WARM),
        ("measuring it", ["NVML's busy means a kernel ran;", "ncu fixes clocks and flushes caches"], WARM),
        ("a bpftime probe", ["no kernel arguments; host calls", "about 1,000 per second, GPU-wide"], WARM),
        ("169 matvecs per token", ["a file's quant name is a recipe:", "read its tensor table"], WARM),
        ("a server step", ["TTFT clocks start in different places;", "calls return before the GPU finishes"], WARM),
    ]
    b = []
    for i, (stage, trap, colour) in enumerate(rows):
        y = 16 + i * (bh + gap)
        b.append(_rect(bx, y, bw, bh, ACC_SOFT, ACC, 1.3, 6))
        b.append(_text(bx + bw / 2, y + bh / 2 + 5, stage, 15, ACC, "middle", "700"))
        if i < len(rows) - 1:
            b.append(_line(bx + bw / 2, y + bh, bx + bw / 2, y + bh + gap - 2, ACC, 1.4, arrow=True))
        b.append(_line(bx + bw + 6, y + bh / 2, tx - 8, y + bh / 2, colour, 1.2, "3 3"))
        b.append(_text(tx, y + 15, trap[0], 15.5, colour if colour == GOOD else INK, weight="600" if colour == GOOD else "normal"))
        b.append(_text(tx, y + 35, trap[1], 15.5, colour if colour == GOOD else INK, weight="600" if colour == GOOD else "normal"))
    H = 16 + len(rows) * (bh + gap)
    return _svg(W, H, "".join(b), "The matvec's stages through the document, each with the trap that waits there")


FIGS = {
    "matvec": matvec_picture,
    "flynn": flynn,
    "divergence": divergence,
    "smfloor": sm_floorplan,
    "latency": latency_hiding,
    "memladder": mem_hierarchy,
    "coalesce": coalescing,
    "roofline": roofline,
    "shuffle": shuffle_tree,
    "regocc": reg_occupancy,
    "streams": streams_graphs,
    "waves": waves,
    "tower": tool_tower,
    "taps": tool_taps,
    "roofline3": roofline3,
    "session": bpftime_session,
    "mapcost": map_costs,
    "pipeline": attach_pipeline,
    "hostcalls": host_calls,
    "attention": attention_toy,
    "timeline": request_timeline,
    "kvgrid": kv_grid,
    "rooflinellm": roofline_llm,
    "budget": token_budget,
    "blocktable": block_table,
    "qblocks": quant_blocks,
    "kernelgrid": kernel_grid,
    "reqtaps": request_taps,
    "spinetraps": spine_traps,
}
