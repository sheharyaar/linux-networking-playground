# audit.py: run from the dossier folder (the one holding index.html and NOTES.md)
# The spec's audit (BOOK_GUIDED_BLOG_STYLE_LEARNING.md section 13), plus checks for this dossier:
# derivation toggles and SVG plots are left out of reading time, KaTeX delimiters must balance,
# and prose is scanned for the banned words and shapes (spec section 6.1 and the learner profile).
import re, os, glob, json, html, sys
from html.parser import HTMLParser
# `python3 audit.py ch05.html` reports only that page's problems (builders use this); no argument = everything
ONLY = [x for x in sys.argv[1:] if x.endswith('.html')]
CUR = None

NOTES = open('NOTES.md', encoding='utf-8').read() if os.path.exists('NOTES.md') else ''
def fenced(tag, default):
    m = re.search(r'```json %s\n(.*?)\n```' % tag, NOTES, re.S)
    return json.loads(m.group(1)) if m else default
TERMS  = fenced('terms', {})                          # {"standing queue": "ch03", ...}
for _f in sorted(glob.glob('notes/chapters/ch[0-9][0-9].md')):   # each builder's own term list
    _m = re.search(r'```json terms\n(.*?)\n```', open(_f, encoding='utf-8').read(), re.S)
    if _m: TERMS.update(json.loads(_m.group(1)))
BUDGET = fenced('budget', {"before": 10, "after": 20}) # minutes, from the reader contract
WPM = 200

PAGES = sorted(glob.glob('ch[0-9][0-9].html'))
ALL = PAGES + [f for f in ('index.html', 'capstone.html') if os.path.exists(f)]
bad = 0
warns = []
def flag(*a):
    global bad
    if ONLY and CUR not in ONLY: return
    bad += 1; print('   !!', *a)
def warn(*a): warns.append(' '.join(str(x) for x in a))

def read(f): return open(f, encoding='utf-8').read()
def strip(fr):
    fr = re.sub(r'<div class="mermaid">.*?</div>', ' ', fr, flags=re.S)
    fr = re.sub(r'<svg.*?</svg>', ' ', fr, flags=re.S)
    fr = re.sub(r'<details class="(hint|sol|deriv)">.*?</details>', ' ', fr, flags=re.S)
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', fr)).split())
def words(fr):           # reading time: prose only; code and prompts are run or copied, not read
    return len(strip(re.sub(r'<pre.*?</pre>', ' ', fr, flags=re.S)).split())
def blocks(s, cls):      # cards never nest a <div>, so a lazy match is safe
    return re.findall(r'<div class="%s(?: [^"]*)?"[^>]*>(.*?)</div>' % cls, s, re.S)
def section(s, sid):
    m = re.search(r'<section id="%s"[^>]*>(.*?)</section>' % sid, s, re.S)
    return m.group(1) if m else ''
def main_of(s):
    body = s[s.index('<main>'):s.index('</main>')] if '<main>' in s else s
    return re.sub(r'<section id="revision[\w-]*".*?</section>', ' ', body, flags=re.S)

VOID = {'meta', 'br', 'hr', 'img', 'link', 'input', 'source', 'wbr'}
class Nest(HTMLParser):
    def __init__(s): super().__init__(); s.st = []; s.err = []; s.ids = set()
    def _id(s, a):
        i = dict(a).get('id')
        if i in s.ids: s.err.append(('duplicate id', i))
        if i: s.ids.add(i)
    def handle_startendtag(s, t, a): s._id(a)
    def handle_starttag(s, t, a):
        s._id(a)
        if t not in VOID: s.st.append((t, s.getpos()))
    def handle_endtag(s, t):
        if t in VOID: return
        if not s.st: s.err.append(('extra close', t, s.getpos())); return
        if s.st[-1][0] != t: s.err.append(('mismatch', t, 'open:' + s.st[-1][0], s.getpos()))
        else: s.st.pop()

# --- 1. every file: nesting, markers, mermaid, maths ---------------------------
IDS = {}
print('== files')
for f in ALL:
    s = read(f); p = Nest(); p.feed(s); IDS[f] = p.ids; CUR = f
    print(f)
    if p.st: flag('unclosed', p.st[:3])
    for e in p.err[:5]: flag(*e)
    if '<!--APPEND-->' in s: flag('leftover APPEND marker')
    for i, m in enumerate(re.findall(r'<div class="mermaid">(.*?)</div>', s, re.S), 1):
        head = m.strip().split('\n')[0]
        if not head.startswith(('flowchart', 'sequenceDiagram', 'graph', 'stateDiagram', 'timeline', 'xychart')):
            flag('mermaid', i, 'bad first line:', head[:40])
        if '&' in m or re.search(r'<(?!br\s*/?>)', m): flag('mermaid', i, 'has & or < in a label')
        if re.search(r'participant [^\n]* as [^\n]*\(', m): flag('mermaid', i, 'parens in participant alias')
    prose = re.sub(r'<pre.*?</pre>|<code>.*?</code>', ' ', s, flags=re.S)
    for l, r in (('\\(', '\\)'), ('\\[', '\\]')):
        if prose.count(l) != prose.count(r): flag('maths delimiters unbalanced: %d %s vs %d %s' % (prose.count(l), l, prose.count(r), r))
    for m in re.finditer(r'\\[(\[](.*?)\\[)\]]', prose, re.S):
        if '\\(' in m.group(1) or '\\[' in m.group(1): flag('nested maths:', m.group(0)[:60])
    if s.count('<figure class="dia">') != len(re.findall(r'<figure class="dia">\s*<div class="(?:mermaid|plot)">', s)):
        flag('a figure.dia does not start with a .mermaid or .plot holder (zoom needs one)')

# --- 2. links and anchors across files ----------------------------------------
print('== links')
for f in ALL:
    CUR = f
    for href in re.findall(r'href="([^"]+)"', read(f)):
        if re.match(r'(https?|mailto):', href): continue
        path, _, anchor = href.partition('#')
        path = path or f
        if not os.path.exists(path): flag(f, 'broken link', href); continue
        if anchor and path.endswith('.html') and path.startswith('..'):    # another dossier: check its ids directly
            if not re.search(r'id="%s"' % re.escape(anchor), read(path)): flag(f, 'missing anchor', href)
            continue
        if anchor and path.endswith('.html') and anchor not in IDS.get(path, set()):
            flag(f, 'missing anchor', href)

# --- 3. chapter pages ----------------------------------------------------------
print('== chapter pages')
FIRST, WORDS = {}, {}
for f in PAGES:
    s = read(f); print(f); CUR = f
    before, after = section(s, 'before'), section(s, 'after')
    if not before or not after: flag('missing the before or after section'); continue
    if not section(s, 'book'): flag('missing the read-the-book card')
    for half, fr in (('before', before), ('after', after)):
        w = words(fr); got = max(1, round(w / WPM))
        st = re.search(r'~(\d+) min %s' % half, s)
        print('   %-6s %5d words  ~%d min' % (half, w, got))
        if st and int(st.group(1)) != got: flag(half, 'stated ~%s min, measured ~%d' % (st.group(1), got))
        if got > BUDGET[half] * 1.25: flag(half, 'over budget: ~%d min against %d' % (got, BUDGET[half]))
    if 'class="spine"' not in before: flag('no spine sentence in the metadata line')
    fb, fa = before.count('<figure class="dia">'), after.count('<figure class="dia">')
    if fb < 1 or fa < 1: flag('diagrams before %d, after %d; need one in each half' % (fb, fa))
    if s.count('<figure class="dia">') != s.count('<figcaption>'): flag('figure and caption counts differ')
    # word list
    wl = blocks(before, 'words')
    WORDS[f[:4]] = [strip(x).lower() for x in re.findall(r'<dt[^>]*>(.*?)</dt>', wl[0], re.S)] if wl else []
    if not WORDS[f[:4]]: flag('no "Words you will meet" list')
    # carried questions: asked before, answered after
    carry, carried = blocks(before, 'carry'), blocks(after, 'carried')
    nq = carry[0].count('<li') if carry else 0
    na = carried[0].count('<details class="ans">') if carried else 0
    if nq < 3 or nq != na: flag('carry-in questions %d, answered after reading %d' % (nq, na))
    # every question has an answer
    total = 0
    for cls in ('carried', 'bookq', 'check'):
        for blk in blocks(after, cls):
            q = len(re.findall(r'<p>\d+\.\s', blk)); d = blk.count('<details class="ans">')
            if cls != 'carried': total += q
            thin = [n for n in (len(strip(a).split()) for a in
                    re.findall(r'<details class="ans">(.*?)</details>', blk, re.S)) if n < 35]
            if q != d: flag(cls, '%d questions, %d answers' % (q, d))
            if thin: flag(cls, 'thin answers (word counts):', thin)
    if total < 5: flag('only %d book and check-yourself questions; want at least 5' % total)
    # labs
    labs = blocks(after, 'lab')
    if not 2 <= len(labs) <= 3: flag('%d labs; want 2 or 3' % len(labs))
    for i, lab in enumerate(labs, 1):
        h, so = lab.count('<details class="hint">'), lab.count('<details class="sol">')
        if h < 2 or so != 1: flag('lab %d: %d hints, %d solutions' % (i, h, so))
        for need in ('class="labmeta"', 'Done when'):
            if need not in lab: flag('lab %d: missing %s' % (i, need))
    # real systems: one full card per system per book, back cards afterwards
    for m in re.finditer(r'<div class="system( back)?"([^>]*)>(.*?)</div>', after, re.S):
        back, attrs, body = m.groups()
        sm = re.search(r'data-system="([\w-]+)"', attrs)
        if not sm: flag('system card without data-system'); continue
        slug = sm.group(1)
        if back:
            if slug not in FIRST: flag('back card for %s but no earlier full card' % slug)
            elif '%s#sys-%s' % (FIRST[slug], slug) not in body: flag('back card %s does not link to its full card' % slug)
        else:
            if slug in FIRST: flag('second full card for %s (first in %s); use a back card' % (slug, FIRST[slug]))
            FIRST.setdefault(slug, f)
            for need in ('class="here"', '<pre', 'What you should see', 'class="drift"'):
                if need not in body: flag('system %s: missing %s' % (slug, need))
    # key learnings = quiz strands, each with a page reference
    strands = re.findall(r'<h3 class="strand" id="s-([\w-]+)"', after)
    if not 4 <= len(strands) <= 7: flag('%d key learnings; want 4 to 7' % len(strands))
    for part in re.split(r'<h3 class="strand"', after)[1:]:
        sid = re.match(r' id="s-([\w-]+)"', part)
        part = re.split(r'<h3|<div class="(?:system|lab)', part)[0]
        if not re.search(r'pp?\.\s?\d+|§\s?\d|slide \d', part): flag('learning', sid.group(1) if sid else '?', 'has no page reference')
    quizzes = re.findall(r'<div class="quiz" data-when="(before|after)"[^>]*>(.*?)</div>', s, re.S)
    if sorted(w for w, _ in quizzes) != ['after', 'before']: flag('quiz cards found:', [w for w, _ in quizzes])
    for w, q in quizzes:
        listed = re.findall(r'data-strand="([\w-]+)"', q)
        if set(listed) != set(strands): flag('quiz', w, 'strands differ from key learnings:', sorted(set(listed) ^ set(strands)))
        if 'class="prompt"' not in q: flag('quiz', w, 'no prompt block')

# --- 4. vocabulary: no term before the chapter that defines it -----------------
print('== vocabulary')
# quiz prompts quote the reading list's title (which names BBR), and the chnav names the next chapter by its
# title, so both are left out of the vocabulary scan
TEXT = {f[:4]: strip(re.sub(r'<pre class="prompt">.*?</pre>|<nav class="chnav">.*?</nav>', ' ', main_of(read(f)), flags=re.S)).lower() for f in PAGES}
for term, home in TERMS.items():
    pat = re.compile(r'\b%s\b' % re.escape(term.lower()))
    for ch, t in TEXT.items():
        CUR = ch + '.html'
        if int(ch[2:]) >= int(home[2:]): continue
        m = pat.search(t)
        if m: flag('EARLY USE %r in %s (defined in %s): ...%s...' % (term, ch, home, t[max(0, m.start()-60):m.end()+30]))
    CUR = home + '.html'
    if home in WORDS and not any(term.lower() in w for w in WORDS[home]):
        flag('%r is mapped to %s but is not in its word list' % (term, home))

# --- 5. hub consistency --------------------------------------------------------
print('== hub')
CUR = 'index.html'
if os.path.exists('index.html'):
    hub = read('index.html'); gloss = strip(section(hub, 'glossary')).lower()
    for f in PAGES:
        if not re.search(r'href="%s(#[^"]*)?"' % re.escape(f), hub): flag('hub does not link', f)
        for w in WORDS.get(f[:4], []):
            if w not in gloss: flag('glossary is missing %r from %s' % (w, f))
    for slug, f in FIRST.items():
        if 'systems-%s' % slug not in IDS['index.html']: flag('systems index has no row for', slug)
else:
    flag('no index.html')

# --- 6. prose: banned words and shapes ------------------------------------------
print('== prose')
BANNED = ['leverage', 'delve', 'seamless', 'robust', 'cutting-edge', "in today's world", "it's important to note",
          'smoking gun', 'unlock', 'supercharge', 'game-changer', 'journey', 'dive deep', 'at the end of the day',
          'comprehensive', 'cornerstone', 'load bearing', 'load-bearing', 'under the hood', 'sharp edge',
          'leak', 'leaks', 'leaked', 'hurt', 'hurts', 'bites', 'substrate', 'survive', 'survives']
for f in ALL:
    s = read(f); CUR = f
    s = re.sub(r'<div class="quiz".*?</div>', ' ', s, flags=re.S)        # quiz cards use "edge" as a status label
    s = re.sub(r'<span class="chnum">.*?</span>', ' ', s, flags=re.S)   # the spec's own "Chapter N · before you read" label
    prose = strip(re.sub(r'<pre.*?</pre>|<code>.*?</code>', ' ', main_of(s), flags=re.S))
    low = prose.lower()
    for w in BANNED:
        for m in re.finditer(r'\b%s\b' % re.escape(w), low):
            flag(f, 'banned word %r: ...%s...' % (w, prose[max(0, m.start()-50):m.end()+30]))
    for m in re.finditer(r'\b(chapter|strand|lab|section)\s+\d+\b(?!\))', low):
        ctx = low[max(0, m.start()-2):m.start()]
        if '(' not in ctx: flag(f, 'bare index %r (name it, then put the number in brackets)' % prose[m.start():m.end()])
    for m in re.finditer(r'\bQ\d+\b', prose): flag(f, 'bare question code %r' % m.group(0))
    for para in re.findall(r'<p[^>]*>(.*?)</p>', main_of(s), re.S):
        t = strip(para)
        if t.count('—') > 1 and not t.startswith('Diagram'): flag(f, 'em-dash pile-up: %s...' % t[:80])
    for m in re.finditer(r'[^.;:]{3,40}, not (a|an|the)?\s?\w+', prose):
        warn(f, 'possible "X, not Y": ...%s...' % m.group(0)[-70:])
    for m in re.finditer(r'\bedge\b', low):
        warn(f, '"edge" in prose (literal network edge is fine): ...%s...' % prose[max(0, m.start()-40):m.end()+20])

if warns:
    print('== warnings (judge by hand)')
    for w in [w for w in warns if not ONLY or any(o in w for o in ONLY)][:60]: print('   ~', w)
    if len(warns) > 60: print('   ~ ... %d more' % (len(warns) - 60))
print('\n%d problem(s), %d warning(s)' % (bad, len(warns)))
