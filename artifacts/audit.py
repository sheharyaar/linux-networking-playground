# audit.py — spec audit for the dossier; runnable from any directory (python3 artifacts/audit.py)
import re, html, sys
from html.parser import HTMLParser

import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, 'packet-path-dossier.html')
s = open(F, encoding='utf-8').read()
body = s[s.index('<main>'):s.index('</main>')]

# --- 1. structure counts -------------------------------------------------
print("figures", s.count('<figure class="dia">'), "closes", s.count('</figure>'),
      "mermaid", s.count('<div class="mermaid">'), "captions", s.count('<figcaption>'))
for b in ['chapter','recap','words','check','refs','tryit']:
    print(b, s.count('class="%s"' % b))
print("leftover APPEND markers:", s.count('<!--APPEND-->'), "| HOWTO markers:", s.count('<!--HOWTO-->'))

# --- 1b. check-yourself answers: one <details> per question --------------
for i, blk in enumerate(re.findall(r'<div class="check">(.*?)</div>\s*(?=<div class="refs">|<section|</section>)', s, re.S), 1):
    q = len(re.findall(r'<p>\d+\.\s', blk)); d = blk.count('<details')
    short = [len(re.sub('<[^>]+>','',a).split())
             for a in re.findall(r'<details class="ans">(.*?)</details>', blk, re.S)]
    flag = '' if q == d else '  !! %d questions, %d answers' % (q, d)
    thin = [n for n in short if n < 35]
    print('check block', i, 'q=%d a=%d' % (q, d), flag, ('thin answers: %s' % thin) if thin else '')
print("reveal-all control:", s.count('answerctl'), "| beforeprint hook:", s.count('beforeprint'))

# --- 2. mermaid sanity ---------------------------------------------------
for i, m in enumerate(re.findall(r'<div class="mermaid">\n(.*?)\n</div>', s, re.S), 1):
    head = m.strip().split('\n')[0]
    ok = head.startswith(('flowchart', 'sequenceDiagram', 'graph', 'stateDiagram'))
    ents = [c for c in ['&amp;', '&lt;', '&gt;'] if c in m]
    bad_paren = re.findall(r'participant\s+\w+\s+as\s+[^\n]*[()]', m)
    print(i, head[:30], 'OK' if ok else '!! BAD HEADER', 'entities:' + ','.join(ents) if ents else '',
          '!! parens in participant alias' if bad_paren else '')

# --- 3. HTML nesting -----------------------------------------------------
VOID = {'meta','br','hr','img','link','input','source'}
class P(HTMLParser):
    def __init__(self): super().__init__(); self.st=[]; self.err=[]
    def handle_startendtag(self,t,a): pass
    def handle_starttag(self,t,a):
        if t not in VOID: self.st.append((t,self.getpos()))
    def handle_endtag(self,t):
        if t in VOID: return
        if not self.st: self.err.append(('extra close',t,self.getpos())); return
        if self.st[-1][0]!=t: self.err.append(('mismatch',t,'open:'+self.st[-1][0],self.getpos()))
        else: self.st.pop()
p = P(); p.feed(s)
print("unclosed:", p.st[:5], "errors:", p.err[:5])

# --- 4. vocabulary: no term used before its chapter ----------------------
# term -> section id where it is introduced (filled from the plan's terms column)
TERMS = {}
try:
    from audit_terms import TERMS
except ImportError:
    pass
SKIP_SECTIONS = {'whats-new', 'whats-quiz', 'glossary', 'references', 'how-to-read'}
vbody = re.sub(r'<pre>.*?</pre>', lambda m: ' ' * len(m.group(0)), body, flags=re.S)  # keep offsets, blank out commands
ids = [(m.start(), m.group(1)) for m in re.finditer(r'<section id="([\w-]+)"', body)]
order = [i for _, i in ids]
def chapter_of(pos):
    c = 'pre'
    for p_, n in ids:
        if p_ <= pos: c = n
    return c
early = 0
for t, expect in TERMS.items():
    for m in re.finditer(re.escape(t), vbody):
        i = m.start()
        c = chapter_of(i)
        if c in SKIP_SECTIONS: continue
        if c not in order or order.index(c) < order.index(expect):
            print("EARLY USE:", t, "in", c, "expected", expect, "|", vbody[max(0,i-70):i+40].replace('\n',' '))
            early += 1
        break
print("early uses:", early, "of", len(TERMS), "terms")

# --- 5. spine + word counts ---------------------------------------------
total = 0
for m in re.finditer(r'<section id="(ch\d+)"(.*?)(?=<section id="|\Z)', body, re.S):
    t = re.sub(r'<div class="mermaid">.*?</div>', '', m.group(2), flags=re.S)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', t))
    n = len(t.split()); total += n
    spine = 'spine ok' if re.search(r'class="chmeta">.*?</p>', m.group(2), re.S) else '!! no chmeta'
    print(m.group(1), n, "words ->", max(1, round(n/200)), "min", spine)
print("TOTAL chapter words:", total, "->", round(total/200), "min")

# --- 6. banned words -----------------------------------------------------
text = html.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<div class="mermaid">.*?</div>|<pre>.*?</pre>', '', body, flags=re.S)))
BANNED = ['leverage','delve','seamless','robust','cutting-edge',"in today's world",'important to note','smoking gun','unlock','supercharge','game-changer','dive deep','at the end of the day','substrate','route leak','load bearing','load-bearing','sharp edge']
for w in BANNED:
    for m in re.finditer(r'\b'+re.escape(w)+r'\b', text, re.I):
        print("BANNED:", w, "|", text[max(0,m.start()-50):m.end()+30].replace('\n',' '))
for m in re.finditer(r'\b(leaks?|hurts?|bites?|survives?)\b', text, re.I):
    print("METAPHOR?:", m.group(0), "|", text[max(0,m.start()-50):m.end()+30].replace('\n',' '))
dashes = len(re.findall(r'—', text))
print("em-dashes in prose:", dashes)
