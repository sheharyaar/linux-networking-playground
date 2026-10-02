#!/usr/bin/env python3
"""Self-audit for gpu-programming-dossier.html, per BLOG_STYLE_LEARNING.md section 7.

Run:  python3 audit.py          (after build.py)
Prints counts and every finding; nothing is fixed automatically.
"""
import html
import pathlib
import re
from html.parser import HTMLParser

HERE = pathlib.Path(__file__).resolve().parent
F = HERE.parent.parent.parent / "gpu-programming-dossier.html"
s = F.read_text(encoding="utf-8")
body = s[s.index("<main>"):s.index("</main>")]

# --- 1. structure counts ------------------------------------------------------
print("figures", s.count('<figure class="dia">'), "closes", s.count("</figure>"),
      "mermaid", s.count('<div class="mermaid">'), "svg", s.count('<svg class="hand"'),
      "captions", s.count("<figcaption>"))
for b in ["chapter", "recap", "words", "check", "refs", "tryit"]:
    print(b, s.count('class="%s"' % b))
print("leftover APPEND markers:", s.count("<!--APPEND-->"), "| leftover @@ placeholders:", len(re.findall(r"@@\w+", s)))

# --- 1b. check-yourself answers: one <details> per question, 40-150 words -----
for i, blk in enumerate(re.findall(r'<div class="check">(.*?)\n      </div>', s, re.S)):
    q = len(re.findall(r"<p>\d+\.\s", blk))
    d = blk.count("<details")
    lens = [len(html.unescape(re.sub("<[^>]+>", " ", a)).split())
            for a in re.findall(r'<details class="ans">(.*?)</details>', blk, re.S)]
    flag = "" if q == d else "  !! %d questions, %d answers" % (q, d)
    odd = [n for n in lens if n < 40 or n > 150]
    if flag or odd or not 2 <= q <= 3:
        print("check block ch%d q=%d a=%d%s%s" % (i, q, d, flag, ("  answer lengths outside 40-150: %s" % odd) if odd else ""))
print("reveal-all control:", s.count("answerctl"), "| beforeprint hook:", s.count("beforeprint"))

# --- 1c. per-chapter anatomy ----------------------------------------------------
chapters = [(m.group(1), m.group(2)) for m in re.finditer(r'<section id="(ch\d+)" class="chapter">(.*?)\n    </section>', body, re.S)]
for cid, c in chapters:
    tryit = c.count('class="tryit"')
    refs = c.count('<li class="ref"')
    figs = c.count('<figure class="dia">')
    rec = re.search(r'<div class="recap">.*?<p>(.*?)</p>', c, re.S)
    sents = len(re.findall(r"[.!?](\s|$)", html.unescape(re.sub("<[^>]+>", "", rec.group(1))))) if rec else 0
    probs = []
    if tryit > 1: probs.append("%d sidebars" % tryit)
    if not 2 <= refs <= 5: probs.append("%d refs" % refs)
    if figs < 1: probs.append("no diagram")
    if not 3 <= sents <= 5: probs.append("recap %d sentences" % sents)
    if probs:
        print("anatomy", cid, "; ".join(probs))

# --- 2. mermaid sanity ----------------------------------------------------------
for i, m in enumerate(re.findall(r'<div class="mermaid">\n(.*?)\n\s*</div>', s, re.S), 1):
    head = m.strip().split("\n")[0]
    ok = head.startswith(("flowchart", "sequenceDiagram", "graph", "stateDiagram", "%%{"))
    if not ok:
        print("mermaid", i, "!! BAD HEADER", head[:40])

# --- 3. HTML nesting ------------------------------------------------------------
VOID = {"meta", "br", "hr", "img", "link", "input", "source", "path", "rect", "line", "circle", "polygon", "polyline"}


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.st, self.err = [], []

    def handle_startendtag(self, t, a):
        pass

    def handle_starttag(self, t, a):
        if t not in VOID:
            self.st.append((t, self.getpos()))

    def handle_endtag(self, t):
        if t in VOID:
            return
        if not self.st:
            self.err.append(("extra close", t, self.getpos()))
            return
        if self.st[-1][0] != t:
            self.err.append(("mismatch", t, "open:" + self.st[-1][0], self.getpos()))
        else:
            self.st.pop()


p = P()
p.feed(s)
print("unclosed:", p.st[:5], "errors:", p.err[:5])

# --- 4. vocabulary: no term used before its chapter ------------------------------
# Terms come from each chapter's "New words" list. Everyday words the reader owns,
# and words that are also ordinary English, are excluded by hand.
EVERYDAY = {"kernel", "token", "vector", "matrix", "gpu", "host / device", "latency / throughput", "slot", "block",
            "graph", "step", "cache", "batch", "occupancy", "thread", "warp", "stream", "event", "map", "probe",
            "bandwidth", "register", "lane", "tile", "layer", "head", "sampling", "logits", "prompt", "model",
            "server", "worker", "scheduler", "budget", "recipe", "family", "page", "kprobe", "uprobe", "helper",
            "driver", "runtime", "fence", "scope", "atomic", "cuda", "nsight", "pascal / ada / hopper", "trampoline",
            "verifier", "pass", "attach", "shared memory", "global memory", "observation layer", "step probe",
            "grid", "tail", "target", "handler", "vocabulary", "query", "key", "value", "loader"}
SKIP_SECTIONS = {"before", "glossary", "references", "how-to-read", "whats-new", "whats-quiz"}
TERMS = {}
for cid, c in chapters:
    m = re.search(r'<div class="words">.*?<dl>(.*?)</dl>', c, re.S)
    for dt in re.findall(r"<dt>(.*?)</dt>", m.group(1), re.S) if m else []:
        for t in re.split(r",\s*| / ", html.unescape(re.sub("<[^>]+>", "", dt))):
            t = re.sub(r"\s*\(.*?\)", "", t).strip()
            if len(t) > 2 and t.lower() not in EVERYDAY and t not in TERMS:
                TERMS[t] = cid
ids = [(m.start(), m.group(1)) for m in re.finditer(r'<section id="([\w-]+)"', body)]
order = [i for _, i in ids]


def section_of(pos):
    c = "pre"
    for q, n in ids:
        if q <= pos:
            c = n
    return c


def visible(seg):
    seg = re.sub(r'<div class="mermaid">.*?</div>', " ", seg, flags=re.S)
    seg = re.sub(r"<svg.*?</svg>", " ", seg, flags=re.S)
    seg = re.sub(r'<li class="ref".*?</li>', " ", seg, flags=re.S)     # citation titles are allowed
    seg = re.sub(r"<pre>.*?</pre>", " ", seg, flags=re.S)                 # listings and commands are literal
    seg = re.sub(r"<code>[^<]*/[^<]*</code>", " ", seg)                  # file paths
    seg = seg.replace("Tensor Memory Accelerator", "TMA")
    return seg


early = 0
for t, expect in TERMS.items():
    pat = re.compile(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])", re.I if " " in t or t.islower() else 0)
    for q, n in ids:
        if n in SKIP_SECTIONS or n not in order:
            continue
        if order.index(n) >= order.index(expect):
            break
        nxt = [x for x, _ in ids if x > q]
        seg = visible(body[q:nxt[0] if nxt else len(body)])
        txt = html.unescape(re.sub(r"<[^>]+>", " ", seg))
        for hit in pat.finditer(txt):
            early += 1
            print("EARLY USE: %-28s in %-5s defined %-5s | %s" % (t, n, expect, txt[max(0, hit.start() - 60):hit.end() + 30].replace("\n", " ")))
print("terms checked:", len(TERMS), "early uses:", early)

# --- 5. prose rules ---------------------------------------------------------------
prose = re.sub(r"<pre>.*?</pre>|<code>.*?</code>|<div class=\"mermaid\">.*?</div>|<svg.*?</svg>", " ", body, flags=re.S)
prose_txt = html.unescape(re.sub(r"<[^>]+>", " ", prose))
BANNED = ["leverage", "delve", "seamless", "robust", "cutting-edge", "in today's world", "it's important to note",
          "smoking gun", "unlock", "supercharge", "game-changer", "dive deep", "at the end of the day", "substrate",
          "load bearing", "load-bearing", "survives", "sharp edge", "hurts", "bites", "leak", "leaks", "simply",
          "quietly", "really", "actually", "basically", "essentially", "journey"]
for w in BANNED:
    for m in re.finditer(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", prose_txt, re.I):
        print("BANNED %-12s| %s" % (w, prose_txt[max(0, m.start() - 60):m.end() + 40].replace("\n", " ")))
for m in re.finditer(r"\b[\w'-]+, not (a |an |the )?[\w'-]+", prose_txt):
    print("X, NOT Y   | %s" % prose_txt[max(0, m.start() - 40):m.end() + 30].replace("\n", " "))
for m in re.finditer(r"\bnot \w+, not \w+", prose_txt):
    print("NEG LIST   | %s" % prose_txt[max(0, m.start() - 40):m.end() + 30].replace("\n", " "))
for para in re.findall(r"<p>(.*?)</p>", prose, re.S):
    if para.count("—") >= 3:
        print("DASHES     | %s" % html.unescape(re.sub("<[^>]+>", "", para))[:120])
# bare numbers: "chapter N" must follow a name, as "(chapter N)"; "Part N" likewise
for m in re.finditer(r"(.{0,1})\b[Cc]hapters? (\d+)", prose_txt):
    if m.group(1) != "(" and not re.match(r"Chapter \d+$", prose_txt[m.start(0) + len(m.group(1)):m.end()]):
        print("BARE CHAPTER | %s" % prose_txt[max(0, m.start() - 60):m.end() + 20].replace("\n", " "))
for m in re.finditer(r"(.{0,1})\bPart (I|II|III|IV|V)\b", prose_txt):
    if m.group(1) != "(":
        ctx = prose_txt[max(0, m.start() - 60):m.end() + 40].replace("\n", " ")
        if " · " not in prose_txt[m.end():m.end() + 4] and " is " not in prose_txt[m.end():m.end() + 4] \
                and "runs the code" not in prose_txt[m.end():m.end() + 16]:
            print("BARE PART  | %s" % ctx)

# --- 6. spine line + word counts --------------------------------------------------
total = 0
for cid, c in chapters:
    meta = re.search(r'<p class="chmeta">(.*?)</p>', c, re.S)
    mt = html.unescape(re.sub(r"<[^>]+>", "", meta.group(1))) if meta else ""
    t = re.sub(r'<div class="mermaid">.*?</div>', "", c, flags=re.S)
    t = re.sub(r"<svg.*?</svg>", "", t, flags=re.S)
    n = len(html.unescape(re.sub(r"<[^>]+>", " ", t)).split())
    total += n
    first = mt.split("—", 1)[-1].strip()[:110]
    print("%-5s %5d words ~%2d min | %s" % (cid, n, max(1, round(n / 200)), first))
print("total words", total)
