#!/usr/bin/env python3
"""Append chapter HTML (from a file) before the <!--APPEND--> marker in the dossier."""
import sys
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(ROOT, 'packet-path-dossier.html')
s = open(p, encoding='utf-8').read()
assert s.count('<!--APPEND-->') == 1, "marker count"
frag = open(sys.argv[1], encoding='utf-8').read().strip('\n')
s = s.replace('<!--APPEND-->', frag + '\n<!--APPEND-->')
open(p, 'w', encoding='utf-8').write(s)
print("appended", sys.argv[1], "->", len(s), "bytes")
