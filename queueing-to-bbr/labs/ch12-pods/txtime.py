#!/usr/bin/env python3
"""txtime.py: a UDP sender that stamps each datagram's departure time with SO_TXTIME.
(Copied from labs/ch08-edt/ for the pods chapter and extended: --clock real, and --no-stamp.)

  python3 txtime.py --dst 10.0.2.1 [--port 9000] [--clock mono|tai|real] [--no-stamp] [--count 500]
                    [--gap-us 1000] [--lead-ms 5] [--size 200] [--reverse 0]
                    [--offset-ms 0] [--burst] [--report-errors] [--csv stamps.csv]
  python3 txtime.py --listen [--port 9000] [--seconds 60]      (a sink for the receiver)

Packet i is stamped  t0 + lead + i * gap + offset  on the chosen clock, where t0 is the clock
when the run starts. By default the script hands packet i to the kernel about --lead-ms before
its stamp, the way a QUIC server writes a little ahead and lets the kernel pace. --burst hands
every packet down at once instead (keep --count under fq's flow_limit, 100).
--reverse N stamps each group of N packets in reverse order, so the kernel sees the stamps out
of order. --offset-ms moves every stamp: a negative value puts it in the past, a large one
(11000) beyond fq's horizon.

The socket asks for SO_TXTIME with CLOCK_MONOTONIC (fq's clock, allowed for any user) or
CLOCK_TAI (ETF's clock, which needs CAP_NET_ADMIN in the user namespace that owns the
network namespace), or CLOCK_REALTIME (also CAP_NET_ADMIN, sock.c:1628-1632). Since v6.11 the
skb remembers which clock its stamp is on (skb->tstamp_type, set by ip_output.c:1474): mono and
tai stamps are kept when the packet is forwarded, a realtime stamp is cleared like a receive
timestamp (skb_clear_tstamp(), include/linux/skbuff.h:4507-4513). --no-stamp is the control:
no SO_TXTIME at all; the planned stamps still go into the payload and the CSV, so txgaps.py can
measure each packet against the time it would have been stamped with.
--report-errors sets SOF_TXTIME_REPORT_ERRORS and IP_RECVERR and then
prints what ETF put on the socket's error queue (SO_EE_ORIGIN_TXTIME).

Each payload starts with the sequence number and the stamp (network order, !IQ), so a capture
can be matched packet by packet (txgaps.py does it). The CSV has one row per packet, and its
first line is a comment with  real_minus_clock_ns, the offset that converts the stamp clock to
the CLOCK_REALTIME that tcpdump uses.
--listen just receives and discards datagrams on --port, so the receiver answers no packet
with an ICMP port-unreachable (with IP_RECVERR set, those errors would fail later sends).
No third-party modules.
"""
import argparse, csv, errno, socket, struct, sys, time

SO_TXTIME = SCM_TXTIME = 61                    # include/uapi/asm-generic/socket.h:104-105
SOF_TXTIME_REPORT_ERRORS = 1 << 1              # include/uapi/linux/net_tstamp.h:207
SO_EE_ORIGIN_TXTIME = 6                        # include/uapi/linux/errqueue.h:34
EE_CODE = {1: 'TXTIME_INVALID_PARAM', 2: 'TXTIME_MISSED'}   # errqueue.h:41-42
CLOCKS = {'mono': time.CLOCK_MONOTONIC, 'tai': time.CLOCK_TAI, 'real': time.CLOCK_REALTIME}

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('--dst'); p.add_argument('--port', type=int, default=9000)
p.add_argument('--listen', action='store_true'); p.add_argument('--seconds', type=float, default=60)
p.add_argument('--clock', choices=CLOCKS, default='mono')
p.add_argument('--count', type=int, default=500); p.add_argument('--gap-us', type=float, default=1000)
p.add_argument('--lead-ms', type=float, default=5); p.add_argument('--size', type=int, default=200)
p.add_argument('--reverse', type=int, default=0); p.add_argument('--offset-ms', type=float, default=0)
p.add_argument('--burst', action='store_true'); p.add_argument('--report-errors', action='store_true')
p.add_argument('--no-stamp', action='store_true')
p.add_argument('--csv')
a = p.parse_args()
if a.listen:
    r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); r.bind(('0.0.0.0', a.port)); r.settimeout(0.5)
    n, end = 0, time.monotonic() + a.seconds
    while time.monotonic() < end:
        try: r.recv(65536); n += 1
        except socket.timeout: pass
    print(f'txtime listen: {n} datagrams on :{a.port}', file=sys.stderr); sys.exit(0)
if not a.dst: p.error('--dst is required unless --listen')
clk = CLOCKS[a.clock]
now = lambda: time.clock_gettime_ns(clk)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
flags = SOF_TXTIME_REPORT_ERRORS if a.report_errors else 0
if not a.no_stamp:
    try:
        s.setsockopt(socket.SOL_SOCKET, SO_TXTIME, struct.pack('@iI', clk, flags))
    except OSError as e:
        sys.exit(f'txtime: setsockopt(SO_TXTIME, {a.clock}) failed: {errno.errorcode[e.errno]} ({e.strerror})')
if a.report_errors:
    s.setsockopt(socket.IPPROTO_IP, socket.IP_RECVERR, 1)

offset = time.clock_gettime_ns(time.CLOCK_REALTIME) - now()
t0 = now(); lead = int(a.lead_ms * 1e6); gap = int(a.gap_us * 1e3); shift = int(a.offset_ms * 1e6)
order = list(range(a.count))
if a.reverse > 1:
    order = [i for g in range(0, a.count, a.reverse) for i in reversed(range(g, min(g + a.reverse, a.count)))]
rows, failed = [], 0
for k, i in enumerate(order):
    stamp = t0 + lead + i * gap + shift
    if not a.burst:                      # hand packet k down about `lead` before slot k
        due = t0 + k * gap
        while (d := due - now()) > 0:
            time.sleep(d / 1e9)
    data = struct.pack('!IQ', i, stamp).ljust(a.size, b'\0')
    sent = now()
    try:
        anc = [] if a.no_stamp else [(socket.SOL_SOCKET, SCM_TXTIME, struct.pack('@Q', stamp))]
        s.sendmsg([data], anc, 0, (a.dst, a.port))
        res = 'ok'
    except OSError as e:
        res = errno.errorcode.get(e.errno, str(e.errno)); failed += 1
    rows.append({'seq': i, 'stamp_ns': stamp, 'handed_down_ns': sent, 'send': res})

errs = []
if a.report_errors:                      # ETF reports a dropped packet with its stamp
    deadline = time.monotonic() + max(0.2, (lead + a.count * gap + max(shift, 0)) / 1e9 + 0.2)
    while time.monotonic() < deadline:
        try:                             # a queued error shows as POLLERR; just poll the queue
            _, anc, _, _ = s.recvmsg(2048, 512, socket.MSG_ERRQUEUE | socket.MSG_DONTWAIT)
        except BlockingIOError:
            time.sleep(0.01); continue
        for lvl, typ, d in anc:
            if lvl == socket.IPPROTO_IP and typ == socket.IP_RECVERR:
                ee_errno, origin, _type, code, _pad, info, edata = struct.unpack_from('@IBBBBII', d)
                if origin == SO_EE_ORIGIN_TXTIME:
                    errs.append((errno.errorcode.get(ee_errno, ee_errno), EE_CODE.get(code, code), (edata << 32) | info))
offset2 = time.clock_gettime_ns(time.CLOCK_REALTIME) - now()

print(f'txtime: clock={a.clock}' + (' (NOT attached: --no-stamp)' if a.no_stamp else '') + f' sent {a.count - failed} of {a.count} datagrams of {a.size} B, '
      f'stamps {a.gap_us:g} us apart, first {(lead + shift) / 1e6:g} ms after start'
      + (f', groups of {a.reverse} reversed' if a.reverse > 1 else '') + (', all handed down at once' if a.burst else ''),
      file=sys.stderr)
if failed: print(f'txtime: {failed} sendmsg() calls failed: {sorted(set(r["send"] for r in rows if r["send"] != "ok"))}', file=sys.stderr)
if a.report_errors:
    print(f'txtime: {len(errs)} SO_EE_ORIGIN_TXTIME errors on the error queue', file=sys.stderr)
    for kind in sorted(set((e[0], e[1]) for e in errs)):
        print(f'  {kind[0]} {kind[1]}: {sum(1 for e in errs if (e[0], e[1]) == kind)}', file=sys.stderr)
if a.csv:
    with open(a.csv, 'w', newline='') as f:
        f.write(f'# clock={a.clock}{" no-stamp" if a.no_stamp else ""} real_minus_clock_ns={offset} (end of run {offset2})\n')
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
