#!/usr/bin/env python3
"""compare.py: read the dumps written by dump.sh.

  python3 compare.py DIR            per node: each Maglev table, slots per backend address,
                                    and whether all nodes hold the same table
  python3 compare.py BEFORE AFTER   per node: which slots changed backend between two dumps,
                                    split into slots of removed backends and extra moves

Backend IDs are node-local (pkg/maglev/maglev.go:258-261), so tables are compared after
mapping each ID to its address with the node's own backend list.
The formats come from cilium-dbg's source: `bpf lb maglev list -o json` prints
{"[ID]/v4": ["[id id ...]"]} and `bpf lb list --backends -o json` prints {"id": ["TCP://ip"]}.
"""
import collections, glob, json, os, re, sys

def load(d):
    nodes = {}
    for f in sorted(glob.glob(os.path.join(d, '*-maglev.json'))):
        node = os.path.basename(f)[:-len('-maglev.json')]
        tables = json.load(open(f))
        backends = json.load(open(os.path.join(d, node + '-backends.json')))
        addr = {}
        for k, v in backends.items():
            m = re.search(r'\d+', k); a = re.search(r'[\d.]+\.\d+|[0-9a-f:]+:[0-9a-f:]+', ' '.join(v))
            if m and a: addr[int(m.group())] = a.group()
        mapped = {}
        for svc, val in tables.items():
            ids = [int(x) for x in re.findall(r'\d+', ' '.join(val))]
            mapped[svc] = [addr.get(i, 'id%d?' % i) for i in ids]
        nodes[node] = mapped
    if not nodes: sys.exit('no *-maglev.json in %s' % d)
    return nodes

def show(nodes):
    seen = set()
    for node, tables in nodes.items():
        for svc, t in sorted(tables.items()):
            c = collections.Counter(t)
            print(f'{node} {svc}: {len(t)} slots; ' + ', '.join(f'{a} {n}' for a, n in sorted(c.items())))
            seen.add(tuple(t))
    print('every table on every node is the same after mapping IDs:', 'yes' if len(seen) == 1 else f'no ({len(seen)} different)')

def diff(a, b):
    for node in sorted(set(a) & set(b)):
        for svc in sorted(set(a[node]) & set(b[node])):
            before, after = a[node][svc], b[node][svc]
            gone = set(before) - set(after)
            own = sum(1 for x, y in zip(before, after) if x in gone)
            extra = sum(1 for x, y in zip(before, after) if x not in gone and x != y)
            print(f'{node} {svc}: removed {sorted(gone) or "none"}; their slots {own}; '
                  f'extra moves between backends that stayed {extra} of {len(before)} '
                  f'({100 * extra / len(before):.1f}%)')

if __name__ == '__main__':
    if len(sys.argv) == 2: show(load(sys.argv[1]))
    elif len(sys.argv) == 3: diff(load(sys.argv[1]), load(sys.argv[2]))
    else: sys.exit(__doc__)
