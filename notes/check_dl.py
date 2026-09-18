#!/usr/bin/env python3
"""Report any .words dt term that appears in more than one chapter's word list."""
import re, collections
s = open('packet-path-dossier.html', encoding='utf-8').read()
seen = collections.defaultdict(list)
for m in re.finditer(r'<section id="(ch\d+)".*?<dl>(.*?)</dl>', s, re.S):
    for dt in re.findall(r'<dt>(.*?)</dt>', m.group(2), re.S):
        seen[re.sub('<[^>]+>', '', dt).strip()].append(m.group(1))
dups = {k: v for k, v in seen.items() if len(v) > 1}
print("word-list terms:", len(seen), "| duplicated across chapters:", len(dups))
for k, v in dups.items():
    print("  DUP:", k, v)
