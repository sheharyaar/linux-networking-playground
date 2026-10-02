#!/usr/bin/env python3
"""txgaps.py: compare when stamped UDP datagrams were captured with when they were stamped to leave.

  python3 txgaps.py cap.pcap stamps.csv [--src 10.0.1.1] [--port 9000] [--csv matched.csv]

cap.pcap is a tcpdump capture (use --time-stamp-precision nano); stamps.csv is what txtime.py
wrote. Each datagram carries its sequence number and stamp, so the two are matched exactly.
The capture clock is CLOCK_REALTIME; the stamps are in the sender's clock, converted with the
offset txtime.py measured (the first line of stamps.csv).

It prints how many stamped packets were seen, the lateness (captured minus stamped) as median,
1st and 99th percentile and maximum, the median gap between captured packets against the
median gap between stamps, and whether the packets left in stamp order or in send order.
No third-party modules.
"""
import argparse, csv, re, socket, statistics, struct, sys

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('pcap'); p.add_argument('stamps'); p.add_argument('--src', default='10.0.1.1')
p.add_argument('--port', type=int, default=9000); p.add_argument('--csv')
a = p.parse_args()

first = open(a.stamps).readline()
off = int(re.search(r'real_minus_clock_ns=(-?\d+)', first).group(1))
rows = list(csv.DictReader(l for l in open(a.stamps) if not l.startswith('#')))
stamp = {int(r['seq']): int(r['stamp_ns']) for r in rows}
send_order = [int(r['seq']) for r in rows]

f = open(a.pcap, 'rb'); gh = f.read(24)
magic = struct.unpack('<I', gh[:4])[0]
end = '<' if magic in (0xa1b2c3d4, 0xa1b23c4d) else '>'
magic = struct.unpack(end + 'I', gh[:4])[0]
nano = magic == 0xa1b23c4d
linktype = struct.unpack(end + 'I', gh[20:24])[0]
src = socket.inet_aton(a.src)
seen = []                                    # (capture time ns, seq)
while (h := f.read(16)) and len(h) == 16:
    sec, frac, incl, orig = struct.unpack(end + 'IIII', h)
    data = f.read(incl)
    off2 = 14 if linktype == 1 else 16 if linktype == 113 else 0
    if linktype == 1 and data[12:14] != b'\x08\x00': continue
    ip = data[off2:]
    if len(ip) < 28 or ip[9] != 17 or ip[12:16] != src: continue
    ihl = (ip[0] & 15) * 4
    if struct.unpack('!H', ip[ihl + 2:ihl + 4])[0] != a.port: continue
    pay = ip[ihl + 8:]
    if len(pay) < 12: continue
    seq, st = struct.unpack('!IQ', pay[:12])
    if stamp.get(seq) != st: continue
    seen.append((sec * 10**9 + (frac if nano else frac * 1000), seq))
if not seen: sys.exit('txgaps: no stamped datagrams in the capture')

late = [(t - (stamp[q] + off)) / 1e3 for t, q in seen]          # microseconds
q = statistics.quantiles(late, n=100) if len(late) >= 100 else [min(late)] + [statistics.median(late)] * 97 + [max(late)]
cap_gaps = [(seen[i][0] - seen[i - 1][0]) / 1e3 for i in range(1, len(seen))]
st_sorted = sorted(stamp[q2] for _, q2 in seen)
st_gaps = [(st_sorted[i] - st_sorted[i - 1]) / 1e3 for i in range(1, len(st_sorted))]
order = [q2 for _, q2 in seen]
in_stamp_order = order == sorted(order, key=lambda x: stamp[x])
in_send_order = order == [x for x in send_order if x in set(order)]
print(f'{len(seen)} of {len(stamp)} stamped datagrams captured')
print(f'lateness (captured - stamped): median {statistics.median(late):.1f} us, '
      f'p1 {q[0]:.1f}, p99 {q[98]:.1f}, max {max(late):.1f} us')
if cap_gaps:
    print(f'gap between packets: captured median {statistics.median(cap_gaps):.1f} us, stamped median {statistics.median(st_gaps):.1f} us')
print('order on the wire: ' + ('stamp order' if in_stamp_order else 'not stamp order')
      + (', which is also send order' if in_send_order and in_stamp_order else ', not send order' if in_stamp_order else ''))
if a.csv:
    with open(a.csv, 'w', newline='') as o:
        w = csv.writer(o); w.writerow(['wire_index', 'seq', 'stamp_us', 'captured_us', 'late_us'])
        base = min(stamp.values()) + off
        for k, ((t, q2), l) in enumerate(zip(seen, late)):
            w.writerow([k, q2, f'{(stamp[q2] + off - base) / 1e3:.3f}', f'{(t - base) / 1e3:.3f}', f'{l:.3f}'])
