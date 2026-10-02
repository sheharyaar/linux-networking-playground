#!/usr/bin/env python3
"""Assemble gpu-programming-dossier.html from the parts in this directory.

  head.html      skeleton, TOC, how-to-read card; placeholders @@CSS@@ @@META@@
                 @@MIN@@ @@BEFORE@@ @@ZOOM@@ @@RTn@@
  before.html    the prerequisites-and-benches card (@@BENCHES@@)
  benches.html   the three-bench table
  chNN.html      one file per chapter; its meta line carries @@RT@@
  (back matter)  merged glossary and references, generated from the chapters' word
                 lists and Go-deeper lists by back_matter()
  svg.py         hand-drawn figures, referenced as @@SVG:name@@

Reading time = words outside Mermaid and SVG / 200, rounded, minimum 1.
Run:  python3 build.py   (writes ../../../gpu-programming-dossier.html)
"""
import html
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent.parent.parent / "gpu-programming-dossier.html"
sys.path.insert(0, str(HERE))
import svg  # noqa: E402


def read(name):
    p = HERE / name
    return p.read_text(encoding="utf-8") if p.exists() else ""


def words(fragment):
    t = re.sub(r'<div class="mermaid">.*?</div>', " ", fragment, flags=re.S)
    t = re.sub(r"<svg.*?</svg>", " ", t, flags=re.S)
    t = re.sub(r"@@SVG:\w+@@", " ", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    return len(t.split())


def sub_svgs(s):
    def rep(m):
        name = m.group(1)
        if name not in svg.FIGS:
            raise SystemExit(f"unknown SVG {name}")
        return svg.FIGS[name]()
    return re.sub(r"@@SVG:(\w+)@@", rep, s)


LAYERS = [("HW", "Hardware"), ("ISA", "Instruction sets: PTX and SASS"), ("CUDA", "CUDA and its runtime"),
          ("TOOLS", "Measuring tools"), ("EBPF", "eBPF and bpftime"), ("LLM", "Language models and their servers")]


def back_matter(texts):
    """Merged glossary (by chapter, first definition wins) and references (by layer, deduplicated by URL)."""
    gl, seen_terms = [], set()
    refs, order = {}, []
    for n, c in texts:
        title = re.search(r"<h2>(.*?)</h2>", c, re.S).group(1).strip()
        m = re.search(r'<div class="words">.*?<dl>(.*?)</dl>', c, re.S)
        items = re.findall(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", m.group(1), re.S) if m else []
        keep = [(t, d) for t, d in items if re.sub(r"<[^>]+>", "", t).lower() not in seen_terms]
        seen_terms.update(re.sub(r"<[^>]+>", "", t).lower() for t, _ in keep)
        if keep:
            gl.append(f'<h3 id="gloss-ch{n}">{title} (chapter {n}) &middot; <a href="#ch{n}">read it</a></h3>\n<dl class="glossdl">\n'
                      + "\n".join(f"<dt>{t}</dt><dd>{d}</dd>" for t, d in keep) + "\n</dl>")
        for li in re.findall(r'<li class="ref" data-layer="(\w+)">(.*?)</li>', c, re.S):
            layer, body = li
            url = re.search(r'href="([^"]+)"', body).group(1)
            if url not in refs:
                body = re.sub(r"\b([Tt])his chapter", lambda m: ("T" if m.group(1) == "T" else "t") + "he chapter", body)
                refs[url] = [layer, body.strip(), []]
                order.append(url)
            if (n, title) not in refs[url][2]:
                refs[url][2].append((n, title))
    out = ['<section id="glossary" class="card">\n<h2>Glossary</h2>\n<p>Every term defined in the document, grouped by the chapter that '
           'introduces it, in reading order. A term appears once, under the chapter where it is first defined.</p>']
    out += gl
    out.append("</section>")
    out.append('<section id="references" class="card">\n<h2>References</h2>\n<p>Every reference cited in the document, deduplicated '
               'and grouped by layer, with the chapters that use it. Use the filter buttons in the '
               '<a href="#how-to-read">how to read</a> card to hide layers you do not need.</p>')
    for key, name in LAYERS:
        items = [u for u in order if refs[u][0] == key]
        if not items:
            continue
        out.append(f'<h3>{name} <span class="tag {key}">{key}</span></h3>\n<ul>')
        for u in items:
            layer, body, used = refs[u]
            where = ", ".join(f'<a href="#ch{n}">{t} (chapter {n})</a>' for n, t in used)
            out.append(f'<li class="ref" data-layer="{layer}">{body} <span class="note">Used in {where}.</span></li>')
        out.append("</ul>")
    out.append("</section>")
    return "\n".join(out)


def main():
    only = None
    if len(sys.argv) > 2 and sys.argv[1] == "--only":
        only = int(sys.argv[2])
    head = read("head.html")
    css = read("base.css") + "\n" + read("extra.css")
    before = read("before.html").replace("@@BENCHES@@", read("benches.html"))
    chapters, total_words, minutes, rts, texts = [], 0, 0, {}, []
    for n in range(0, 21):
        c = read(f"ch{n:02d}.html")
        if not c or (only is not None and n != only):
            continue
        wc = words(c)
        rt = max(1, round(wc / 200))
        rts[n] = (wc, rt)
        total_words += wc
        minutes += rt
        chapters.append(c.replace("@@RT@@", f"~{rt} min"))
        texts.append((n, c))
    body = "\n".join(chapters)
    back = back_matter(texts) if only is None else ""
    out = head.replace("@@CSS@@", css).replace("@@BEFORE@@", before if only is None else "")
    if only is not None:
        out = re.sub(r'<section id="how-to-read".*?</section>', "", out, flags=re.S)
    out = out.replace("<!--APPEND-->", body + "\n" + back + ("\n<!--APPEND-->" if len(rts) < 21 else ""))
    out = out.replace("@@ZOOM@@", read("zoom.js"))
    # TOC reading times: chapter minutes plus its layer tags, taken from the chapter meta line
    for n in range(0, 21):
        tags = ""
        c = read(f"ch{n:02d}.html")
        m = re.search(r'<p class="chmeta">(.*?)</p>', c, re.S)
        if m:
            tags = " ".join(re.findall(r'<span class="tag (\w+)">', m.group(1)))
        if n in rts:
            out = out.replace(f"@@RT{n}@@", f"{rts[n][1]} min · {tags}".strip(" ·"))
        else:
            out = out.replace(f"@@RT{n}@@", "to come")
    out = sub_svgs(out)
    n_mermaid = out.count('<div class="mermaid">')
    n_svg = out.count('<svg class="hand"')
    meta = (f"21 sections · ~{round(total_words, -2):,} words · ~{minutes} minutes · "
            f"{n_mermaid + n_svg} diagrams · written October 2026")
    out = out.replace("@@META@@", meta).replace("@@MIN@@", str(minutes))
    target = OUT if only is None else pathlib.Path(f"/tmp/gpu-dossier/preview-ch{only}.html")
    target.write_text(out, encoding="utf-8")
    for n, (wc, rt) in rts.items():
        print(f"ch{n:<3} {wc:6d} words  ~{rt} min")
    print(f"total {total_words} words, {minutes} min, {n_mermaid} mermaid + {n_svg} svg -> {target}")


if __name__ == "__main__":
    main()
