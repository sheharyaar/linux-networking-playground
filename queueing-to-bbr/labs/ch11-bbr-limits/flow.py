#!/usr/bin/env python3
"""flow.py (chapter 11 copy): bulk TCP senders and a sink, sampling TCP_INFO and, for BBR, TCP_CC_INFO.

  sink:    python3 flow.py recv [--port 5001]            (serves any number of connections at once)
  sender:  python3 flow.py send --dst 10.0.2.1 [--port 5001] [--cc bbr] [--seconds 60]
                              [--start 0] [--every 0.05] [--label bbr] [--csv out.csv]

Copied from labs/common/flow.py and extended for this chapter:
  - the sink threads each connection, so a BBR flow and a CUBIC flow can share it;
  - the sender can wait --start seconds before connecting, and tags its rows with --label;
  - when the congestion control is bbr it also reads TCP_CC_INFO (struct tcp_bbr_info,
    include/uapi/linux/inet_diag.h:234): BBR's bandwidth estimate, its min_rtt, and both gains.
    pacing_gain held at 1.0 with cwnd_gain 2.0 for more than one gain cycle is the policer mode
    (tcp_bbr.c:1002-1004); 1.25 / 0.75 / 1.0 in turn is the normal gain cycle.
The sender sets the congestion control per socket (TCP_CONGESTION). `bbr` needs the module:
`sudo modprobe tcp_bbr` once, on the host (ENOENT from setsockopt means it is not loaded).
"""
import argparse, csv, socket, struct, sys, threading, time

TCP_INFO_FMT = '@8B24I4Q6I4Q2I2Q'
FIELDS = ('state ca_state retransmits probes backoff options wscale flags '
          'rto ato snd_mss rcv_mss unacked sacked lost retrans fackets '
          'last_data_sent last_ack_sent last_data_recv last_ack_recv '
          'pmtu rcv_ssthresh rtt rttvar snd_ssthresh snd_cwnd advmss reordering '
          'rcv_rtt rcv_space total_retrans '
          'pacing_rate max_pacing_rate bytes_acked bytes_received '
          'segs_out segs_in notsent_bytes min_rtt data_segs_in data_segs_out '
          'delivery_rate busy_time rwnd_limited sndbuf_limited delivered delivered_ce '
          'bytes_sent bytes_retrans').split()
CA_STATE = {0: 'open', 1: 'disorder', 2: 'cwr', 3: 'recovery', 4: 'loss'}
TCP_CC_INFO = getattr(socket, 'TCP_CC_INFO', 26)

def tcp_info(sock):
    raw = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO, 256)
    return dict(zip(FIELDS, struct.unpack_from(TCP_INFO_FMT, raw)))

def bbr_info(sock):
    """struct tcp_bbr_info: bw_lo, bw_hi (bytes/s), min_rtt (us), pacing_gain, cwnd_gain (<< 8)."""
    raw = sock.getsockopt(socket.IPPROTO_TCP, TCP_CC_INFO, 20)
    if len(raw) < 20:
        return {}
    lo, hi, mrtt, pg, cg = struct.unpack('<5I', raw)
    return {'bbr_bw_mbps': round(((hi << 32) | lo) * 8 / 1e6, 3), 'bbr_mrtt_ms': mrtt / 1000,
            'pacing_gain': round(pg / 256, 3), 'cwnd_gain': round(cg / 256, 3)}

def serve(c, peer):
    n, t0 = 0, time.monotonic()
    while (b := c.recv(1 << 16)):
        n += len(b)
    dt = time.monotonic() - t0
    print(f'flow recv: {peer[0]}:{peer[1]} sent {n} bytes in {dt:.2f} s = {n * 8 / dt / 1e6:.2f} Mbit/s',
          file=sys.stderr, flush=True)
    c.close()

def recv(args):
    srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', args.port)); srv.listen(16)
    print(f'flow recv: listening on :{args.port}', file=sys.stderr, flush=True)
    while True:
        c, peer = srv.accept()
        threading.Thread(target=serve, args=(c, peer), daemon=True).start()

def send(args):
    time.sleep(args.start)
    s = socket.socket()
    try:
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_CONGESTION, args.cc.encode())
    except OSError as e:
        sys.exit(f'flow send: cannot set {args.cc!r} ({e}); for bbr run `sudo modprobe tcp_bbr` on the host')
    s.connect((args.dst, args.port))
    t0 = time.monotonic(); stop = threading.Event(); rows = []
    is_bbr = args.cc == 'bbr'
    def sample():
        while not stop.is_set():
            i = tcp_info(s); t = time.monotonic() - t0 + args.start
            row = {'t_s': f'{t:.3f}', 'label': args.label or args.cc,
                   'ca_state': CA_STATE.get(i['ca_state'], i['ca_state']), 'cwnd': i['snd_cwnd'],
                   'rtt_ms': i['rtt'] / 1000, 'min_rtt_ms': i['min_rtt'] / 1000,
                   'lost': i['lost'], 'total_retrans': i['total_retrans'],
                   'pacing_mbps': round(i['pacing_rate'] * 8 / 1e6, 3),
                   'delivery_mbps': round(i['delivery_rate'] * 8 / 1e6, 3),
                   'bytes_acked': i['bytes_acked'], 'segs_out': i['data_segs_out']}
            if is_bbr:
                row.update(bbr_info(s) or {'bbr_bw_mbps': '', 'bbr_mrtt_ms': '', 'pacing_gain': '', 'cwnd_gain': ''})
            rows.append(row)
            time.sleep(args.every)
    th = threading.Thread(target=sample, daemon=True); th.start()
    chunk = b'\0' * (1 << 16)
    try:
        while time.monotonic() - t0 < args.seconds:
            s.sendall(chunk)
    except (BrokenPipeError, ConnectionResetError) as e:
        print(f'flow send: {e}', file=sys.stderr)
    stop.set(); th.join()
    last = tcp_info(s); s.close()
    dt = time.monotonic() - t0
    print(f'flow send: cc={args.cc} label={args.label or args.cc} {last["bytes_acked"]} bytes acked in {dt:.1f} s = '
          f'{last["bytes_acked"] * 8 / dt / 1e6:.2f} Mbit/s, total_retrans={last["total_retrans"]}, '
          f'segs_out={last["data_segs_out"]}, rows={len(rows)}', file=sys.stderr)
    out = open(args.csv, 'w', newline='') if args.csv else sys.stdout
    w = csv.DictWriter(out, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    if args.csv: out.close()

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = p.add_subparsers(dest='mode', required=True)
r = sub.add_parser('recv'); r.add_argument('--port', type=int, default=5001)
t = sub.add_parser('send'); t.add_argument('--dst', required=True); t.add_argument('--port', type=int, default=5001)
t.add_argument('--cc', default='cubic'); t.add_argument('--seconds', type=float, default=60)
t.add_argument('--start', type=float, default=0); t.add_argument('--every', type=float, default=0.05)
t.add_argument('--label'); t.add_argument('--csv')
a = p.parse_args()
recv(a) if a.mode == 'recv' else send(a)
