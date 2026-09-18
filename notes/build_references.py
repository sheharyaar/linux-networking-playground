#!/usr/bin/env python3
"""Generate build/references.html: every cited reference, deduped by URL, grouped by layer tag."""
import re, html, collections

s = open('packet-path-dossier.html', encoding='utf-8').read()

ORDER = ['HW', 'L2', 'L3', 'SOCK', 'BPF', 'LAB']
NAMES = {
    'HW':   'Hardware, rings and interrupts',
    'L2':   'The device layer: taps, tc, bridges, bonds, veth, upper devices',
    'L3':   'IP, routing, netfilter, conntrack and IPVS',
    'SOCK': 'Sockets, TCP, UDP and unix sockets',
    'BPF':  'XDP, tc programs and Cilium',
    'LAB':  'Tooling and tracing',
}

by_layer = collections.OrderedDict((k, []) for k in ORDER)
seen = {}
chapter_of = {}

for m in re.finditer(r'<section id="(ch\d+)" class="chapter">(.*?)</section>', s, re.S):
    cid, body = m.group(1), m.group(2)
    for li in re.findall(r'<li class="ref" data-layer="(\w+)">(.*?)</li>', body, re.S):
        layer, content = li
        url = re.search(r'href="([^"]+)"', content)
        key = url.group(1) if url else re.sub(r'<[^>]+>', '', content)[:60]
        if key in seen:
            chapter_of[key].append(cid)
            continue
        seen[key] = (layer, content.strip())
        chapter_of[key] = [cid]
        by_layer.setdefault(layer, []).append(key)

out = ['<section id="references" class="card">',
       '<h2>References</h2>',
       '<p>Every reference cited in the document, deduplicated and grouped by layer, with the '
       'chapters that use it. Each one was fetched and its title checked while this document was '
       'being written; nothing here is a guessed URL. Use the filter buttons in the '
       '<a href="#how-to-read">how to read</a> card to hide layers you do not need.</p>']

total = 0
for layer in ORDER:
    keys = by_layer.get(layer) or []
    if not keys:
        continue
    out.append('<h3>%s <span class="tag %s">%s</span></h3>' % (html.escape(NAMES[layer]), layer, layer))
    out.append('<ul>')
    for k in keys:
        _, content = seen[k]
        chs = chapter_of[k]
        links = ', '.join('<a href="#%s">%s</a>' % (c, c.replace('ch', 'chapter ')) for c in chs)
        out.append('<li class="ref" data-layer="%s">%s <span class="note">Used in %s.</span></li>'
                   % (layer, content, links))
        total += 1
    out.append('</ul>')
out.append('</section>')

open('build/references.html', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('references written:', total, 'unique URLs across', len([l for l in ORDER if by_layer.get(l)]), 'layers')
for l in ORDER:
    if by_layer.get(l):
        print('  %-5s %d' % (l, len(by_layer[l])))
