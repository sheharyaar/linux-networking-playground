#!/usr/bin/env python3
"""skblen.py: how big were the skbs in a capture? One line of numbers per file.

  python3 skblen.py cap.pcap [more.pcap ...] [--csv lengths.csv]

Reads classic pcap files (tcpdump -w, any snap length; Ethernet link type), keeps IPv4 and IPv6
TCP packets that carry payload, and prints per file: packets, the largest frame, the median frame,
the share of frames above 65,535 bytes, how many had the IP length field set to 0 (IPv4 tot_len,
IPv6 payload_len), and how many IPv6 packets carried a hop-by-hop header first.
The frame length is the pcap record's original length, which for a GSO or GRO skb is skb->len:
the whole skb, as the capture point saw it. Payload = frame - 14 - IP header - TCP header.
With --csv it writes one row per data packet: file, family, frame_bytes, payload_bytes, ip_len_field.
No third-party modules.
"""
import argparse, csv, statistics, struct, sys

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('pcap', nargs='+'); p.add_argument('--csv')
a = p.parse_args()
w = None
if a.csv:
    out = open(a.csv, 'w', newline=''); w = csv.writer(out)
    w.writerow(['file', 'family', 'frame_bytes', 'payload_bytes', 'ip_len_field'])

for name in a.pcap:
    f = open(name, 'rb'); gh = f.read(24)
    end = '<' if struct.unpack('<I', gh[:4])[0] in (0xa1b2c3d4, 0xa1b23c4d) else '>'
    if struct.unpack(end + 'I', gh[20:24])[0] != 1:
        sys.exit(f'{name}: not an Ethernet capture')
    frames, zero, hbh, fams = [], 0, 0, set()
    while (h := f.read(16)) and len(h) == 16:
        _, _, incl, orig = struct.unpack(end + 'IIII', h)
        d = f.read(incl)
        et = d[12:14]
        if et == b'\x08\x00':                                  # IPv4
            ip = d[14:]; ihl = (ip[0] & 15) * 4
            if ip[9] != 6: continue
            lenf = struct.unpack('!H', ip[2:4])[0]; l4 = 14 + ihl; fam = 4
        elif et == b'\x86\xdd':                                # IPv6
            ip = d[14:]; nh = ip[6]; l4 = 14 + 40; fam = 6
            lenf = struct.unpack('!H', ip[4:6])[0]
            if nh == 0:                                         # hop-by-hop header (pre-7.0 BIG TCP)
                hbh += 1; nh = ip[40]; l4 += (ip[41] + 1) * 8
            if nh != 6: continue
        else:
            continue
        doff = (d[l4 + 12] >> 4) * 4
        pay = orig - l4 - doff
        if pay <= 0: continue
        frames.append(orig); fams.add(fam); zero += (lenf == 0)
        if w: w.writerow([name, fam, orig, pay, lenf])
    if not frames:
        print(f'{name}: no TCP data packets'); continue
    big = sum(1 for x in frames if x > 65535)
    print(f'{name}: IPv{"/".join(map(str, sorted(fams)))} {len(frames)} data skbs, max {max(frames)} B, '
          f'median {int(statistics.median(frames))} B, above 65,535: {big} ({100 * big / len(frames):.1f}%), '
          f'IP length field 0: {zero}, hop-by-hop first: {hbh}')
