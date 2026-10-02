#!/usr/bin/env python3
"""gaps.py: inter-packet gaps of one TCP data stream, from a tcpdump capture file.

  python3 gaps.py cap.pcap [--src 10.0.1.1] [--skip 2] [--csv gaps.csv]

Reads a classic pcap file (tcpdump -w; microsecond or nanosecond timestamps), keeps the IPv4
TCP packets from --src that carry payload, drops the first --skip seconds (slow start), and
prints the packet count, the median gap, a small histogram of gaps, the average wire rate, and
the burst sizes: packets less than 30 us apart count as one burst, which on this bench is one
GSO skb cut into segments after the qdisc.
With --csv it writes one row per packet: t_s, frame_bytes, payload_bytes, gap_us.
No third-party modules.
"""
import argparse, csv, socket, statistics, struct, sys

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('pcap'); p.add_argument('--src', default='10.0.1.1')
p.add_argument('--skip', type=float, default=2.0); p.add_argument('--csv')
a = p.parse_args()

f = open(a.pcap, 'rb'); gh = f.read(24)
magic = struct.unpack('<I', gh[:4])[0]
if magic in (0xa1b2c3d4, 0xa1b23c4d): end = '<'
else: end = '>'; magic = struct.unpack('>I', gh[:4])[0]
scale = 1e-9 if magic == 0xa1b23c4d else 1e-6
linktype = struct.unpack(end + 'I', gh[20:24])[0]
src = socket.inet_aton(a.src)
pk = []                                   # (time, frame length, payload length)
while (h := f.read(16)) and len(h) == 16:
    sec, frac, incl, orig = struct.unpack(end + 'IIII', h)
    data = f.read(incl)
    off = 14 if linktype == 1 else 16 if linktype == 113 else 0   # Ethernet or Linux cooked
    if linktype == 1 and data[12:14] != b'\x08\x00': continue
    ip = data[off:]
    if len(ip) < 20 or ip[9] != 6 or ip[12:16] != src: continue
    ihl = (ip[0] & 15) * 4; tot = struct.unpack('!H', ip[2:4])[0]
    doff = (ip[ihl + 12] >> 4) * 4
    pay = tot - ihl - doff
    if pay > 0: pk.append((sec + frac * scale, orig, pay))
if not pk: sys.exit('no data packets from %s' % a.src)
t0 = pk[0][0]
pk = [x for x in pk if x[0] - t0 >= a.skip]
gaps = [(pk[i][0] - pk[i - 1][0]) * 1e6 for i in range(1, len(pk))]
dur = pk[-1][0] - pk[0][0]
wire = sum(x[1] for x in pk[1:]) * 8 / dur / 1e6
pay = sum(x[2] for x in pk[1:]) * 8 / dur / 1e6
print(f'{len(pk)} data packets after {a.skip:g} s, {dur:.2f} s; frame sizes {sorted(set(x[1] for x in pk))[:4]}')
print(f'average rate: {wire:.3f} Mbit/s of frames, {pay:.3f} Mbit/s of payload')
print(f'gap median {statistics.median(gaps):.0f} us, mean {statistics.mean(gaps):.0f} us')
edges = [0, 50, 500, 1000, 2000, 3000, 5000, 10000, 1e9]
names = ['<50us', '50-500us', '0.5-1ms', '1-2ms', '2-3ms', '3-5ms', '5-10ms', '>10ms']
cnt = [sum(1 for g in gaps if lo <= g < hi) for lo, hi in zip(edges, edges[1:])]
for n, c in zip(names, cnt):
    print(f'  {n:>9} {c:6d} {"#" * round(50 * c / max(cnt))}')
bursts, cur = [], 1
for g in gaps:
    if g < 30: cur += 1
    else: bursts.append(cur); cur = 1
bursts.append(cur)
between = [g for g in gaps if g >= 30]
sizes = sorted(set(bursts), key=lambda b: -bursts.count(b))[:3]
print('bursts (packets < 30 us apart): ' + ', '.join(f'{bursts.count(b)} of {b} packets' for b in sizes)
      + (f'; median gap between bursts {statistics.median(between):.0f} us' if between else ''))
if a.csv:
    with open(a.csv, 'w', newline='') as o:
        w = csv.writer(o); w.writerow(['t_s', 'frame_bytes', 'payload_bytes', 'gap_us'])
        for i, (t, fl, pl) in enumerate(pk):
            w.writerow([f'{t - t0:.6f}', fl, pl, f'{gaps[i - 1]:.1f}' if i else ''])
