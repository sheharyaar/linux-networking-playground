#!/usr/bin/env python3
"""podedt.py: a UDP "pod" whose egress limit is Cilium's EDT arithmetic, run in user space.

  python3 podedt.py --dst 10.0.2.1 --limit 10mbit --offer 20mbit [--seconds 8]
                    [--horizon-ms 2000] [--size 1472] [--port 9000] [--csv log.csv]

The sender offers --offer of UDP (datagrams of --size bytes, paced by the application) and, for
every datagram, does what Cilium's edt_sched_departure() does on the host (bpf/lib/edt.h:89-107
in the reader's fork, v1.19.6-vpc):

    now    = CLOCK_MONOTONIC
    t      = now                         (this sender writes no departure time of its own)
    delay  = wire_len * 1e9 / bytes_per_second
    t_next = t_last + delay
    if t_next <= t:          t_last = t,      send unstamped        ("passed")
    elif t_next - now >= horizon:              drop, t_last unchanged ("horizon drop")
    else:                    t_last = t_next, send with SO_TXTIME t_next ("stamped")

wire_len is size + 42 (UDP 8, IPv4 20, Ethernet 14): 1514 bytes for the default 1472.
--limit takes Kubernetes-style quantities as Cilium reads the annotation (GetBytesPerSec(),
pkg/datapath/linux/bandwidth/bandwidth.go:158-164): 10M or 10mbit = 10,000,000 bit/s, 10Mi =
10 x 2^20 bit/s. The stamp is written on CLOCK_MONOTONIC, which any user may use (sock.c:1628-1632).
Cilium stamps after the pod's veth; this sender stamps before it. Since v6.11 a monotonic UDP stamp
is kept when the packet is forwarded, so a qdisc downstream (fq on rtr:r1) sees the same times.
Like the BPF program, this sender never learns whether fq later dropped a packet it stamped.

--sndbuf sets the send buffer (SO_SNDBUFFORCE, else SO_SNDBUF; the kernel doubles the value). A UDP socket blocks in sendmsg() once its skbs below it hold sndbuf bytes
of memory; that is the only backpressure it gets, and it works only while the skb still belongs to
the socket, so only when the stamping and the fq sit before the hop that takes the socket away.

Every 100 ms it logs t_last - now (how far ahead the aggregate's clock runs) and the counters.
No third-party modules.
"""
import argparse, csv, re, socket, struct, sys, time

SO_TXTIME = SCM_TXTIME = 61                    # include/uapi/asm-generic/socket.h:104-105

def bits(q):
    m = re.fullmatch(r'([\d.]+)\s*(mbit|kbit|gbit|M|k|G|Mi|Ki|Gi)?', q)
    if not m: sys.exit(f'podedt: cannot read rate {q!r}')
    v, u = float(m.group(1)), m.group(2) or ''
    return v * {'': 1, 'k': 1e3, 'kbit': 1e3, 'M': 1e6, 'mbit': 1e6, 'G': 1e9, 'gbit': 1e9,
                'Ki': 2**10, 'Mi': 2**20, 'Gi': 2**30}[u]

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
p.add_argument('--dst', required=True); p.add_argument('--port', type=int, default=9000)
p.add_argument('--limit', default='10mbit'); p.add_argument('--offer', default='20mbit')
p.add_argument('--seconds', type=float, default=8); p.add_argument('--horizon-ms', type=float, default=2000)
p.add_argument('--size', type=int, default=1472); p.add_argument('--csv')
p.add_argument('--sndbuf', type=int, help='send buffer in bytes (the kernel doubles it)')
a = p.parse_args()

Bps = int(bits(a.limit) / 8)                       # bytes per second, as in the BPF map
wire = a.size + 42
delay = wire * 10**9 // Bps                        # edt.h:93
horizon = int(a.horizon_ms * 1e6)
gap = wire * 8 * 1e9 / bits(a.offer)               # the application's own spacing
now = lambda: time.clock_gettime_ns(time.CLOCK_MONOTONIC)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, SO_TXTIME, struct.pack('@iI', time.CLOCK_MONOTONIC, 0))
if a.sndbuf:                                       # SO_SNDBUFFORCE (32) passes net.core.wmem_max; needs CAP_NET_ADMIN,
    try: s.setsockopt(socket.SOL_SOCKET, 32, a.sndbuf)   # which the rootless bench has inside its namespace
    except OSError: s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, a.sndbuf)
sndbuf = s.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
t0 = now(); t_last = 0
n = passed = stamped = hdrop = errs = 0
log, next_log = [], t0
end = t0 + int(a.seconds * 1e9)
while True:
    due = t0 + int(n * gap)
    while (d := due - now()) > 0:
        if d > 200_000: time.sleep((d - 100_000) / 1e9)
    t = now()
    if t >= end: break
    data = struct.pack('!IQ', n, t).ljust(a.size, b'\0')
    t_next = t_last + delay                        # edt.h:94
    try:
        if t_next <= t:                            # edt.h:95-98
            t_last = t; passed += 1
            s.sendto(data, (a.dst, a.port))
        elif t_next - t >= horizon:                # edt.h:104-105
            hdrop += 1
        else:                                      # edt.h:106-107
            t_last = t_next; stamped += 1
            s.sendmsg([data], [(socket.SOL_SOCKET, SCM_TXTIME, struct.pack('@Q', t_next))], 0, (a.dst, a.port))
    except OSError:
        errs += 1
    n += 1
    if t >= next_log:
        log.append({'t_s': f'{(t - t0) / 1e9:.3f}', 'ahead_ms': f'{max(t_last - t, 0) / 1e6:.3f}',
                    'offered': n, 'passed': passed, 'stamped': stamped, 'horizon_drops': hdrop})
        next_log += 100_000_000

print(f'podedt: limit {a.limit} ({Bps} B/s, {delay / 1e3:.1f} us per {wire} B), offered {a.offer} for {a.seconds:g} s, '
      f'horizon {a.horizon_ms:g} ms, SO_SNDBUF {sndbuf}', file=sys.stderr)
print(f'podedt: offered {n}, passed unstamped {passed}, stamped {stamped}, horizon drops {hdrop}, '
      f'send errors {errs}; aggregate clock ends {max(t_last - now(), 0) / 1e6:.0f} ms ahead of now', file=sys.stderr)
if a.csv:
    with open(a.csv, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(log[0])); w.writeheader(); w.writerows(log)
