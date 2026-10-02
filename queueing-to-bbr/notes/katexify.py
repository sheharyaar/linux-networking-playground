"""katexify.py: turn inline maths in a page's prose into KaTeX, leaving protected regions alone.

Protected: existing \\( \\) and \\[ \\] maths, <pre>, <code>, Mermaid divs, <svg>, <a> tags,
HTML attributes and quiz prompts. Replacements are (old, new) pairs applied in order.
usage: from katexify import apply; apply('ch01.html', PAIRS)
"""
import re
PROTECT = re.compile(r'(\\\(.*?\\\)|\\\[.*?\\\]|<pre.*?</pre>|<code>.*?</code>|<div class="mermaid">.*?</div>'
                     r'|<svg.*?</svg>|<a [^>]*>|<[^>]+>)', re.S)
def apply(path, pairs, report=True):
    s = open(path, encoding='utf-8').read()
    head, body = s.split('<main>', 1)
    parts = PROTECT.split(body)
    counts = {old: 0 for old, _ in pairs}
    for i in range(0, len(parts), 2):          # even indices are unprotected text
        t = parts[i]
        for old, new in pairs:
            n = t.count(old)
            if n:
                counts[old] += n; t = t.replace(old, new)
        parts[i] = t
    open(path, 'w', encoding='utf-8').write(head + '<main>' + ''.join(parts))
    if report:
        for old, n in counts.items():
            if n == 0: print('   (no match)', repr(old))
    return counts
