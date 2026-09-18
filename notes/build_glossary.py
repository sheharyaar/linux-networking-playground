#!/usr/bin/env python3
"""Generate build/glossary.html by merging every chapter's .words dl, grouped by chapter."""
import re, html

s = open('packet-path-dossier.html', encoding='utf-8').read()
out = ['<section id="glossary" class="card">',
       '<h2>Glossary</h2>',
       '<p>Every term defined in the document, grouped by the chapter that introduces it and in '
       'reading order. A term appears once, under the chapter where it is first defined; if you '
       'meet it earlier than that, it was being named rather than taught. Each heading links back '
       'to its chapter.</p>']

n_terms = 0
for m in re.finditer(r'<section id="(ch\d+)" class="chapter">(.*?)</section>', s, re.S):
    cid, body = m.group(1), m.group(2)
    title = re.search(r'<h2>(.*?)</h2>', body, re.S)
    dl = re.search(r'<div class="words">.*?<dl>(.*?)</dl>', body, re.S)
    if not (title and dl):
        continue
    num = re.search(r'<span class="chnum">(.*?)</span>', body, re.S)
    label = re.sub(r'<[^>]+>', '', num.group(1)).strip() if num else cid
    out.append('<h3 id="gloss-%s">%s &middot; <a href="#%s">%s</a></h3>'
               % (cid, html.escape(label), cid, title.group(1).strip()))
    items = dl.group(1).strip()
    n_terms += len(re.findall(r'<dt>', items))
    out.append('<dl class="glossdl">')
    out.append(items)
    out.append('</dl>')

out.append('</section>')
open('build/glossary.html', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('glossary written:', n_terms, 'terms')
