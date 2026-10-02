"""integrate.py: fold built chapter pages into the hub and NOTES. Run from the dossier folder.

For every chNN.html that exists it:
  - links the chapter's row in the hub table, fills "before · after" minutes from the page's chmeta, sets status "built"
    (it never downgrades a status that is already probed / edges / locked);
  - regenerates the hub glossary from every page's word list (dt id="w-SLUG" -> g-SLUG), in chapter order;
  - regenerates the hub systems index from the pages' system cards (full card + back cards);
  - wires each page's "next" link in .chnav once the next page exists;
  - updates "K of 14 built" in the hub hero and the chapter-status table in NOTES.md;
  - merges notes/chapters/chNN.md term maps into the NOTES.md terms JSON.
It prints what it changed. It does not touch revision-log entries (write those by hand).
"""
import glob, html, json, os, re

HUB_TITLES = {  # the hub's row label for each chapter (the page title may be longer)
    'ch01': 'Congestion avoidance and control', 'ch02': 'Queues in numbers', 'ch03': 'Controlling queue delay',
    'ch04': 'Shapers and fair schedulers', 'ch05': 'Small queues on the host', 'ch06': 'TCP pacing',
    'ch07': 'Carousel', 'ch08': 'Teaching NICs about time', 'ch09': 'Eiffel', 'ch10': 'BBR',
    'ch11': 'Where BBR loses', 'ch12': 'Pods with a speed limit', 'ch13': 'Maglev (side path)',
    'ch14': 'BIG TCP (side path)'}

def read(f): return open(f, encoding='utf-8').read()
def text(fr): return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', fr)).split())
PROPER = ('Carousel', 'Eiffel', 'Maglev')   # chapter titles that start with a name
def lc(t):   # lower-case a title's first letter for use mid-sentence; keep acronyms ("TCP pacing") and names
    if t.startswith(PROPER) or len(t) < 2 or not t[1].islower(): return t
    return t[0].lower() + t[1:]

# hand-written "what it is" lines where a card's first sentence is too thin for the index
SYSTEM_WHAT = {
    'htb': 'Two Linux qdiscs: TBF, one token bucket in front of a queue, and HTB, a tree of token-bucket classes that borrow unused rate from their parent.',
    'so-txtime': 'A socket option that stamps each packet with the time it should leave, and the ETF qdisc that sends packets at those times; both since Linux 4.19 (2018).',
}

pages = sorted(glob.glob('ch[0-9][0-9].html'))
info = {}
for f in pages:
    s = read(f); ch = f[:4]
    before = re.search(r'<section id="before"[^>]*>(.*?)</section>', s, re.S).group(1)
    title = text(re.search(r'<h2>(.*?)</h2>', before, re.S).group(1))
    mb = re.search(r'~(\d+) min before', s); ma = re.search(r'~(\d+) min after', s)
    wl = re.search(r'<div class="words" id="words">(.*?)</div>', s, re.S)
    words = re.findall(r'<dt id="w-([\w-]+)">(.*?)</dt>\s*<dd>(.*?)</dd>', wl.group(1), re.S) if wl else []
    cards = []
    for m in re.finditer(r'<div class="system( back)?" id="([\w-]+)" data-system="([\w-]+)">\s*<h4>(.*?)</h4>(.*?)</div>', s, re.S):
        back, cid, slug, h4, body = m.groups()
        what = re.search(r'<b>What it is\.</b>(.*?)</p>', body, re.S)
        w = ' '.join(html.unescape(re.sub(r'<[^>]+>', '', what.group(1))).split()) if what else ''
        w = re.split(r'(?<=[a-z0-9)])\. ', w)[0].rstrip('.') + '.' if w else ''   # first sentence only
        cards.append(dict(back=bool(back), id=cid, slug=slug, h4=h4, what=w))
    info[ch] = dict(file=f, title=title, before=mb and mb.group(1), after=ma and ma.group(1), words=words, cards=cards)

# ---- hub -------------------------------------------------------------------------
h = read('index.html')
for ch, d in info.items():
    label = HUB_TITLES[ch]
    row = re.search(r'<tr><td>(?:<a href="%s">)?%s(?:</a>)?(.*?)</tr>' % (re.escape(d['file']), re.escape(label)), h, re.S)
    if not row: print('!! no hub row for', ch, label); continue
    cells = re.findall(r'<td>(.*?)</td>', row.group(0), re.S)
    status = cells[4]
    if 'not built' in status: status = '<span class="status">built</span>'
    tag = re.search(r'(\s*<span class="tag [A-Z]+">[A-Z]+</span>)+', cells[0])
    first = '<a href="%s">%s</a>%s' % (d['file'], label, tag.group(0) if tag else '')
    times = '%s · %s min' % (d['before'], d['after']) if d['before'] and d['after'] else cells[2]
    new = '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (first, cells[1], times, cells[3], status)
    h = h.replace(row.group(0), new)
built = len(info)
h = re.sub(r'· \d+ of 14 built ·', '· %d of 14 built ·' % built, h)

# glossary
parts = ['      <h2>Glossary</h2>', '      <p class="note">Every term, in the order the chapters introduce it. Each links to the chapter that defines it.</p>']
for ch, d in info.items():
    if not d['words']: continue
    parts.append('      <h3>%s</h3>' % d['title'])
    parts.append('      <div class="words"><dl>')
    for slug, dt, dd in d['words']:
        parts.append('        <dt id="g-%s">%s</dt><dd>%s <a href="%s#w-%s">in the chapter</a></dd>' % (slug, dt.strip(), dd.strip(), d['file'], slug))
    parts.append('      </dl></div>')
h = re.sub(r'(<section id="glossary" class="card">).*?(</section>)', lambda m: m.group(1) + '\n' + '\n'.join(parts) + '\n    ' + m.group(2), h, flags=re.S)

# systems index
systems = {}
for ch, d in info.items():
    for c in d['cards']:
        e = systems.setdefault(c['slug'], dict(full=None, backs=[], name='', what=''))
        if c['back']: e['backs'].append((ch, c['id'], d['title']))
        else:
            e['full'] = (ch, c['id'], d['title'])
            e['name'] = re.sub(r'^Meet the system · ', '', c['h4']); e['what'] = c['what']
rows = ['      <h2>Real systems</h2>', '      <table><tr><th>System</th><th>What it is</th><th>Full card</th><th>Back cards</th></tr>']
for slug, e in systems.items():
    if not e['full']: print('!! back card without a full card:', slug); continue
    ch, cid, title = e['full']
    backs = ', '.join('<a href="%s.html#%s">%s</a>' % (b[0], b[1], lc(b[2])) for b in e['backs'])
    w = SYSTEM_WHAT.get(slug, e['what'])
    what = w[:180] + ('…' if len(w) > 180 else '')
    rows.append('        <tr id="systems-%s"><td>%s</td><td>%s</td><td><a href="%s.html#%s">%s</a></td><td>%s</td></tr>'
                % (slug, e['name'], html.escape(what, quote=False), ch, cid, lc(title), backs))
rows.append('      </table>')
h = re.sub(r'(<section id="systems" class="card">).*?(</section>)', lambda m: m.group(1) + '\n' + '\n'.join(rows) + '\n    ' + m.group(2), h, flags=re.S)
open('index.html', 'w', encoding='utf-8').write(h)
print('hub: %d chapters, %d glossary terms, %d systems' % (built, sum(len(d['words']) for d in info.values()), len(systems)))

# ---- next links ----------------------------------------------------------------------
for ch, d in info.items():
    n = 'ch%02d' % (int(ch[2:]) + 1)
    if n in info:
        s = read(d['file'])
        s2 = re.sub(r'<span>([^<]*?) → \(not built yet\)</span>', lambda m: '<a href="%s.html">%s →</a>' % (n, info[n]['title']), s)
        if s2 != s: open(d['file'], 'w', encoding='utf-8').write(s2); print('next link wired:', ch, '->', n)

# ---- NOTES ------------------------------------------------------------------------------
notes = read('NOTES.md')
for ch, d in info.items():
    notes = re.sub(r'\| (%s [^|]*)\| no \|' % ch, lambda m: '| %s| built (%s · %s min) |' % (m.group(1), d['before'], d['after']), notes)
m = re.search(r'```json terms\n(.*?)\n```', notes, re.S)
terms = json.loads(m.group(1))
for f in sorted(glob.glob('notes/chapters/ch[0-9][0-9].md')):
    mm = re.search(r'```json terms\n(.*?)\n```', read(f), re.S)
    if mm: terms.update(json.loads(mm.group(1)))
notes = notes[:m.start()] + '```json terms\n' + json.dumps(terms, indent=0, ensure_ascii=False) + '\n```' + notes[m.end():]
open('NOTES.md', 'w', encoding='utf-8').write(notes)
print('NOTES: %d terms' % len(terms))
