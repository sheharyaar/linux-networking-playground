#!/usr/bin/env python3
"""bulk.py: one bulk TCP flow over IPv4 or IPv6, and the CPU it cost.

  sink:    python3 bulk.py recv [--port 5014] [--once]
  sender:  python3 bulk.py send --dst fd14::2 [--port 5014] [--seconds 8] [--cpus 2,4] [--zerocopy]

The sink listens on both families (one IPv6 socket with IPV6_V6ONLY off) and reads into a
preallocated 1 MiB buffer. The sender picks the family from --dst and writes 1 MiB chunks for
--seconds. It then prints one JSON line:
  family, mss, bytes (acked), seconds, gbps,
  utime_s, stime_s     its own CPU seconds (getrusage). With IRQ time accounting
                       (CONFIG_IRQ_TIME_ACCOUNTING=y on Arch) softirq work is NOT in these.
  cpus_busy_s          with --cpus: busy seconds of those CPUs from /proc/stat
                       (user + nice + system + irq + softirq + steal). Pin the sender and the
                       sink to those CPUs with taskset, and both ends' softirq work lands there.
  host_busy_frac       the whole machine's busy fraction during the run, to show how shared it was
With --zerocopy the sender uses SO_ZEROCOPY and MSG_ZEROCOPY: the kernel pins the user's 4 KB pages
as the skb's fragments instead of copying, and reports completions on the error queue, which the
sender drains. Each skb can then hold at most MAX_SKB_FRAGS pages.
The sink prints one JSON line per connection with its bytes and its own CPU seconds.
No third-party modules.
"""
import argparse, errno, json, os, resource, socket, sys, time

HZ = os.sysconf('SC_CLK_TCK')
SO_ZEROCOPY, MSG_ZEROCOPY = 60, 0x4000000        # include/uapi/asm-generic/socket.h, linux/socket.h

def drain(s):                                    # zerocopy completions: just empty the error queue
    while True:
        try:
            s.recvmsg(0, 256, socket.MSG_ERRQUEUE | socket.MSG_DONTWAIT)
        except BlockingIOError:
            return

def cpustat():
    rows = {}
    for line in open('/proc/stat'):
        if not line.startswith('cpu'):
            break
        f = line.split()
        v = list(map(int, f[1:9]))          # user nice system idle iowait irq softirq steal
        rows[f[0]] = (v[0] + v[1] + v[2] + v[5] + v[6] + v[7], sum(v))
    return rows

def recv(a):
    srv = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    srv.bind(('::', a.port)); srv.listen(8)
    print(f'bulk recv: listening on [::]:{a.port}', file=sys.stderr, flush=True)
    buf = bytearray(1 << 20); mv = memoryview(buf)
    while True:
        c, peer = srv.accept()
        r0 = resource.getrusage(resource.RUSAGE_SELF); t0 = time.monotonic(); n = 0
        while (k := c.recv_into(mv)):
            n += k
        dt = time.monotonic() - t0; r1 = resource.getrusage(resource.RUSAGE_SELF)
        print(json.dumps({'role': 'recv', 'peer': peer[0], 'bytes': n, 'seconds': round(dt, 3),
                          'utime_s': round(r1.ru_utime - r0.ru_utime, 3),
                          'stime_s': round(r1.ru_stime - r0.ru_stime, 3)}), flush=True)
        c.close()
        if a.once:
            return

def send(a):
    fam = socket.AF_INET6 if ':' in a.dst else socket.AF_INET
    s = socket.socket(fam, socket.SOCK_STREAM)
    s.connect((a.dst, a.port))
    cpus = ['cpu' + c for c in a.cpus.split(',')] if a.cpus else []
    chunk = memoryview(bytearray(1 << 20))
    if a.zerocopy:
        s.setsockopt(socket.SOL_SOCKET, SO_ZEROCOPY, 1)
    c0 = cpustat(); r0 = resource.getrusage(resource.RUSAGE_SELF); t0 = time.monotonic()
    while time.monotonic() - t0 < a.seconds:
        if not a.zerocopy:
            s.sendall(chunk); continue
        off = 0
        while off < len(chunk):
            try:
                off += s.send(chunk[off:], MSG_ZEROCOPY)
            except OSError as e:
                if e.errno != errno.ENOBUFS: raise
                time.sleep(0.0001)
            drain(s)
    s.shutdown(socket.SHUT_WR)
    s.recv(1)                                # wait for the sink to close: everything delivered
    dt = time.monotonic() - t0; r1 = resource.getrusage(resource.RUSAGE_SELF); c1 = cpustat()
    raw = s.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO, 256)
    mss = int.from_bytes(raw[8 + 4 * 2: 8 + 4 * 3], sys.byteorder)   # tcpi_snd_mss
    acked = int.from_bytes(raw[8 + 24 * 4 + 16: 8 + 24 * 4 + 24], sys.byteorder)  # tcpi_bytes_acked
    s.close()
    busy = sum(c1[c][0] - c0[c][0] for c in cpus) / HZ if cpus else None
    hb, ht = c1['cpu'][0] - c0['cpu'][0], c1['cpu'][1] - c0['cpu'][1]
    print(json.dumps({'role': 'send', 'family': 6 if fam == socket.AF_INET6 else 4, 'mss': mss,
                      'bytes': acked, 'seconds': round(dt, 3), 'gbps': round(acked * 8 / dt / 1e9, 3),
                      'utime_s': round(r1.ru_utime - r0.ru_utime, 3),
                      'stime_s': round(r1.ru_stime - r0.ru_stime, 3),
                      'cpus': a.cpus, 'cpus_busy_s': busy, 'zerocopy': a.zerocopy,
                      'host_busy_frac': round(hb / ht, 3) if ht else None}), flush=True)

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = p.add_subparsers(dest='mode', required=True)
r = sub.add_parser('recv'); r.add_argument('--port', type=int, default=5014); r.add_argument('--once', action='store_true')
t = sub.add_parser('send'); t.add_argument('--dst', required=True); t.add_argument('--port', type=int, default=5014)
t.add_argument('--seconds', type=float, default=8); t.add_argument('--cpus', default='')
t.add_argument('--zerocopy', action='store_true')
a = p.parse_args()
recv(a) if a.mode == 'recv' else send(a)
