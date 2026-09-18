#!/usr/bin/env python3
"""Replace RTn placeholders and the hero totals with measured values."""
import re, html

P = 'packet-path-dossier.html'
s = open(P, encoding='utf-8').read()
body = s[s.index('<main>'):s.index('</main>')]

# --- measure each chapter exactly the way audit.py does -------------------
mins, total_words = {}, 0
for m in re.finditer(r'<section id="(ch\d+)"(.*?)(?=<section id="|\Z)', body, re.S):
    t = re.sub(r'<div class="mermaid">.*?</div>', '', m.group(2), flags=re.S)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', t))
    n = len(t.split())
    total_words += n
    mins[int(m.group(1)[2:])] = max(1, round(n / 200))

# --- RTn -> measured minutes, everywhere, boundary-safe (RT1 vs RT16) -----
def sub_rt(m):
    n = int(m.group(1))
    if n not in mins:
        raise SystemExit('no measurement for RT%d' % n)
    return str(mins[n])

s, n_rt = re.subn(r'\bRT(\d+)\b', sub_rt, s)

# --- hero meta ------------------------------------------------------------
diagrams = s.count('<figure class="dia">')
total_min = sum(mins.values())
hero_old = '~WORDS words · ~MINUTES minutes · DIAGRAMS diagrams'
assert s.count(hero_old) == 1, s.count(hero_old)
hero_new = '~%s words · ~%d minutes · %d diagrams' % (format(total_words, ',d'), total_min, diagrams)
s = s.replace(hero_old, hero_new)

open(P, 'w', encoding='utf-8').write(s)
print('replaced %d RTn placeholders' % n_rt)
print('per-chapter minutes:', ' '.join('ch%d=%d' % (k, v) for k, v in sorted(mins.items())))
print('hero ->', hero_new)
print('sum of chapter minutes:', total_min)
