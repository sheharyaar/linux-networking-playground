#!/usr/bin/env python3
"""rxcount.py: receive UDP datagrams and count them in 100 ms bins.

  python3 rxcount.py [--port 9000] [--seconds 12] [--bin-ms 100] [--csv rx.csv]

Each datagram from podedt.py starts with its sequence number and the sender's CLOCK_MONOTONIC
send time (!IQ). Both namespaces share the kernel's monotonic clock, so arrival minus send time
is the one-way delay, most of it time spent waiting in fq on the router. Bins start at the first
datagram. Wire bytes are counted as payload + 42 (UDP, IPv4, Ethernet).
Prints the delivered rate per second, then the median one-way delay per second.
No third-party modules.
"""
import argparse, csv, socket, statistics, struct, sys, time

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('--port', type=int, default=9000); p.add_argument('--seconds', type=float, default=12)
p.add_argument('--bin-ms', type=float, default=100); p.add_argument('--csv')
a = p.parse_args()
r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); r.bind(('0.0.0.0', a.port)); r.settimeout(0.2)
now = lambda: time.clock_gettime_ns(time.CLOCK_MONOTONIC)
end = now() + int(a.seconds * 1e9)
got = []                                          # (arrival ns, wire bytes, one-way delay ns)
while now() < end:
    try:
        d = r.recv(65536)
    except socket.timeout:
        if got and now() - got[-1][0] > 3e9: break
        continue
    t = now()
    sent = struct.unpack('!IQ', d[:12])[1] if len(d) >= 12 else t
    got.append((t, len(d) + 42, t - sent))
if not got: sys.exit('rxcount: nothing received')
t0, binw = got[0][0], int(a.bin_ms * 1e6)
nb = (got[-1][0] - t0) // binw + 1
pk, by, dl = [0] * nb, [0] * nb, [[] for _ in range(nb)]
for t, b, owd in got:
    i = (t - t0) // binw; pk[i] += 1; by[i] += b; dl[i].append(owd)
rows = [{'t_s': f'{(i + 1) * a.bin_ms / 1e3:.2f}', 'pkts': pk[i], 'mbit_wire': f'{by[i] * 8 / (a.bin_ms / 1e3) / 1e6:.3f}',
         'owd_ms_median': f'{statistics.median(dl[i]) / 1e6:.1f}' if dl[i] else ''} for i in range(nb)]
per = int(1000 / a.bin_ms)
print(f'rxcount: {len(got)} datagrams in {(got[-1][0] - t0) / 1e9:.2f} s', file=sys.stderr)
print('  second  Mbit/s(wire)  median one-way delay', file=sys.stderr)
for s in range(0, nb, per):
    b = sum(by[s:s + per]); ds = [x for l in dl[s:s + per] for x in l]
    print(f'  {s // per:>6}  {b * 8 / (min(per, nb - s) * a.bin_ms / 1e3) / 1e6:12.3f}  '
          f'{statistics.median(ds) / 1e6 if ds else float("nan"):8.1f} ms', file=sys.stderr)
if a.csv:
    with open(a.csv, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
