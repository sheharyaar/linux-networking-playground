#!/usr/bin/env python3
"""poisson.py: Poisson arrivals of UDP packets into the bench's bottleneck, and a receiver
that logs each packet's one-way delay.

  receiver:  python3 poisson.py recv --csv rx.csv [--port 6001] [--seconds 25]
  sender:    python3 poisson.py send --dst 10.0.2.1 --rho 0.8 [--seconds 20]
                                   [--rate 10e6] [--sizes fixed|exp] [--batch 1] [--seed 1]

The sender draws exponentially distributed gaps (mean 1/lambda), so arrivals are a Poisson
process. lambda is chosen so that the load on the bottleneck is rho:
    rho = lambda * E[X],  X = frame_bytes * 8 / rate   (frame = UDP payload + 8 + 20 + 14)
With --sizes fixed every frame is 1514 bytes: deterministic service, an M/D/1 queue.
With --sizes exp the frame is 62 bytes plus an exponential part (mean 400 B), capped at 1514:
a general service time, an M/G/1 queue whose service-time spread you can compute.

With --batch b each Poisson arrival is a burst of b packets sent back to back (the burst rate is
lambda / b, so rho is unchanged): the batch-arrival queue of Bertsekas and Gallager's Problem 3.43.

Each payload carries (seq, send time in ns, intended frame bytes); the receiver logs the real size. Send time is CLOCK_REALTIME; the
receiver reads the kernel's receive timestamp (SO_TIMESTAMPNS, also CLOCK_REALTIME). Both
namespaces share the host clock, so recv - send is the one-way delay.
"""
import argparse, csv, ctypes, random, socket, struct, sys, time

HDR = struct.Struct('!QQI')          # seq, send_ns, frame_bytes
L2_L3_L4 = 14 + 20 + 8               # Ethernet + IPv4 + UDP, as netem's rate counts them on a veth
SO_TIMESTAMPNS = 35                  # include/uapi/asm-generic/socket.h (SO_TIMESTAMPNS_OLD)

def frames(kind, rng):
    if kind == 'fixed':
        while True: yield 1514
    while True:                      # 62 B minimum (42 B of headers + our 20 B) plus an exponential part
        yield min(1514, L2_L3_L4 + HDR.size + int(rng.expovariate(1 / 400)))

def send(a):
    try:                             # 1 us timer slack, so sleeps end close to when we asked
        ctypes.CDLL(None).prctl(29, 1, 0, 0, 0)          # PR_SET_TIMERSLACK
    except OSError:
        pass
    rng = random.Random(a.seed)
    gen = frames(a.sizes, rng)
    # mean frame size by sampling the same generator family (a separate stream, so the run is unchanged)
    probe = frames(a.sizes, random.Random(a.seed + 99))
    mean_bytes = sum(next(probe) for _ in range(200000)) / 200000
    lam = a.rho * a.rate / (8 * mean_bytes)          # packets per second
    lam_b = lam / a.batch                              # bursts per second
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 22)
    dst = (a.dst, a.port)            # unconnected: an ICMP port-unreachable cannot abort the run
    pad = bytes(1500)
    t0 = time.monotonic_ns(); due = t0; end = t0 + int(a.seconds * 1e9); k = 0; late = 0
    while due < end:
        due += int(rng.expovariate(lam_b) * 1e9)
        d = due - time.monotonic_ns()
        if d > 0:
            time.sleep(d / 1e9)
        else:
            late += 1
        for _ in range(a.batch):
            fb = next(gen)
            s.sendto(HDR.pack(k, time.clock_gettime_ns(time.CLOCK_REALTIME), fb) + pad[:fb - L2_L3_L4 - HDR.size], dst)
            k += 1
    dt = (time.monotonic_ns() - t0) / 1e9
    print(f'poisson send: sizes={a.sizes} batch={a.batch} rho={a.rho} lambda={lam:.1f}/s mean_frame={mean_bytes:.1f} B '
          f'sent={k} in {dt:.1f} s ({k / dt:.1f}/s), {late} sent late', file=sys.stderr)

def recv(a):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 22)
    s.setsockopt(socket.SOL_SOCKET, SO_TIMESTAMPNS, 1)
    s.bind(('0.0.0.0', a.port)); s.settimeout(a.idle)
    rows = []; t_end = time.monotonic() + a.seconds
    while time.monotonic() < t_end:
        try:
            data, anc, _, _ = s.recvmsg(2048, 64)
        except socket.timeout:
            if rows: break
            continue
        rx = None
        for lvl, typ, val in anc:
            if lvl == socket.SOL_SOCKET and typ == SO_TIMESTAMPNS:
                sec, nsec = struct.unpack('qq', val[:16]); rx = sec * 10**9 + nsec
        seq, tx, fb = HDR.unpack_from(data)
        rows.append((seq, tx, rx, len(data) + L2_L3_L4))   # the size that actually crossed the bottleneck
    with open(a.csv, 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['seq', 'send_ns', 'recv_ns', 'frame_bytes']); w.writerows(rows)
    print(f'poisson recv: {len(rows)} packets -> {a.csv}', file=sys.stderr)

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = p.add_subparsers(dest='mode', required=True)
r = sub.add_parser('recv'); r.add_argument('--port', type=int, default=6001); r.add_argument('--csv', required=True)
r.add_argument('--seconds', type=float, default=60); r.add_argument('--idle', type=float, default=2.0)
t = sub.add_parser('send'); t.add_argument('--dst', required=True); t.add_argument('--port', type=int, default=6001)
t.add_argument('--rho', type=float, required=True); t.add_argument('--seconds', type=float, default=20)
t.add_argument('--rate', type=float, default=10e6, help='bottleneck rate in bit/s (netem rate 10mbit = 10e6)')
t.add_argument('--sizes', choices=['fixed', 'exp'], default='fixed'); t.add_argument('--seed', type=int, default=1)
t.add_argument('--batch', type=int, default=1, help='packets per arrival, sent back to back')
a = p.parse_args()
recv(a) if a.mode == 'recv' else send(a)
