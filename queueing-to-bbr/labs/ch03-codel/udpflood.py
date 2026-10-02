#!/usr/bin/env python3
"""udpflood.py: a constant-rate UDP sender that ignores loss, and a sink for it.

  sink:    python3 udpflood.py recv [--port 6001] [--seconds 15]
  sender:  python3 udpflood.py send --dst 10.0.2.1 [--port 6001] [--mbit 11] [--seconds 10]

The sender is open loop: drops do not slow it down, unlike TCP. It sends 1472-byte
payloads (1514-byte frames) in small bursts every 2 ms so that the average wire rate
is --mbit. Through a 10 Mbit/s bottleneck at 11 Mbit/s it keeps CoDel in its dropping
state long enough to watch the drop spacing shrink.
"""
import argparse, socket, sys, time

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = p.add_subparsers(dest='mode', required=True)
r = sub.add_parser('recv'); r.add_argument('--port', type=int, default=6001); r.add_argument('--seconds', type=float, default=15)
s = sub.add_parser('send'); s.add_argument('--dst', required=True); s.add_argument('--port', type=int, default=6001)
s.add_argument('--mbit', type=float, default=11); s.add_argument('--seconds', type=float, default=10)
a = p.parse_args()

if a.mode == 'recv':
    u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); u.bind(('0.0.0.0', a.port)); u.settimeout(0.5)
    n, t0 = 0, time.monotonic()
    while time.monotonic() - t0 < a.seconds:
        try:
            u.recv(2048); n += 1
        except socket.timeout:
            pass
    print(f'udpflood recv: {n} packets', file=sys.stderr)
    sys.exit(0)

u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
u.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 20)
payload = b'\0' * 1472
pps = a.mbit * 1e6 / (1514 * 8)          # packets per second on the wire
step = 0.002
sent, t0 = 0, time.monotonic()
while (t := time.monotonic() - t0) < a.seconds:
    due = int(t * pps) - sent
    for _ in range(max(due, 0)):
        try:
            u.sendto(payload, (a.dst, a.port)); sent += 1
        except BlockingIOError:
            break
    time.sleep(step)
print(f'udpflood send: {sent} packets in {a.seconds:.1f} s = {sent * 1514 * 8 / a.seconds / 1e6:.2f} Mbit/s on the wire',
      file=sys.stderr)
