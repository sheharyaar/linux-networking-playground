#!/usr/bin/env python3
"""bbrflow.py (chapter 10 copy of labs/common/flow.py): one bulk TCP flow and a sink, sampling the
sender's TCP_INFO and, for BBR, its model through TCP_CC_INFO.

  sink:    python3 bbrflow.py recv [--port 5001] [--once]
  sender:  python3 bbrflow.py send --dst 10.0.2.1 [--port 5001] [--cc bbr] [--seconds 25]
                                 [--every 0.005] [--csv out.csv]

Added for the BBR chapter:
  TCP_CC_INFO (getsockopt level IPPROTO_TCP, option 26, include/uapi/linux/tcp.h:119) returns
  struct tcp_bbr_info (include/uapi/linux/inet_diag.h:234): five u32 fields, bw_lo and bw_hi
  (the windowed-max bandwidth in bytes per second), min_rtt in microseconds, and pacing_gain and
  cwnd_gain shifted left 8 bits. bbr_get_info() fills it (net/ipv4/tcp_bbr.c:1108). CUBIC and
  Reno have no get_info, so the call returns zero bytes and those columns stay empty.
  The state column is decoded from the two gains (bbr_update_gains(), tcp_bbr.c:988):
    739/739 startup   88/739 drain   x/512 probe_bw (x = 320, 192 or 256)   256/256 probe_rtt
  inflight is tcp_packets_in_flight(): unacked - sacked - lost + retrans (include/net/tcp.h).

The congestion control is set per socket with TCP_CONGESTION, so no sysctl is needed. Any user may
pick bbr once the module is loaded (TCP_CONG_NON_RESTRICTED, tcp_bbr.c:1145); if it is not loaded
the setsockopt fails with ENOENT, and this script says so.
"""
import argparse, csv, errno, socket, struct, sys, threading, time

TCP_CC_INFO = getattr(socket, 'TCP_CC_INFO', 26)
# struct tcp_info, in order, up to tcpi_bytes_retrans: 8 x u8, 24 x u32, 4 x u64, 6 x u32,
# 4 x u64 (delivery_rate, busy, rwnd_limited, sndbuf_limited), 2 x u32, 2 x u64
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
STATE = {(739, 739): 'startup', (88, 739): 'drain', (256, 256): 'probe_rtt'}

def tcp_info(sock):
    raw = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO, 256)
    return dict(zip(FIELDS, struct.unpack_from(TCP_INFO_FMT, raw)))

def bbr_info(sock):
    raw = sock.getsockopt(socket.IPPROTO_TCP, TCP_CC_INFO, 20)
    if len(raw) < 20:
        return None
    bw_lo, bw_hi, min_rtt, pg, cg = struct.unpack('<5I', raw)
    state = STATE.get((pg, cg), 'probe_bw' if cg == 512 else '?')
    return {'bbr_bw_mbps': round(((bw_hi << 32) | bw_lo) * 8 / 1e6, 3),
            'bbr_mrtt_ms': min_rtt / 1000, 'pacing_gain': pg / 256, 'cwnd_gain': cg / 256,
            'state': state}

def recv(args):
    srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', args.port)); srv.listen(8)
    print(f'bbrflow recv: listening on :{args.port}', file=sys.stderr, flush=True)
    while True:
        c, peer = srv.accept(); n = 0; t0 = time.monotonic()
        while (b := c.recv(1 << 16)):
            n += len(b)
        dt = time.monotonic() - t0
        print(f'bbrflow recv: {peer[0]} sent {n} bytes in {dt:.2f} s = {n * 8 / dt / 1e6:.2f} Mbit/s',
              file=sys.stderr, flush=True)
        c.close()
        if args.once: return

def send(args):
    s = socket.socket()
    try:
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_CONGESTION, args.cc.encode())
    except OSError as e:
        if e.errno == errno.ENOENT:
            sys.exit(f'bbrflow send: congestion control {args.cc!r} is not loaded '
                     f'(see /proc/sys/net/ipv4/tcp_available_congestion_control); '
                     f'for bbr, run: sudo modprobe tcp_bbr')
        raise
    s.connect((args.dst, args.port))
    t0 = time.monotonic(); stop = threading.Event(); rows = []
    empty = dict.fromkeys(('bbr_bw_mbps', 'bbr_mrtt_ms', 'pacing_gain', 'cwnd_gain', 'state'), '')
    def sample():
        while not stop.is_set():
            i = tcp_info(s); b = bbr_info(s) or empty; t = time.monotonic() - t0
            rows.append({
                't_s': f'{t:.4f}', 'cc': args.cc, 'ca_state': CA_STATE.get(i['ca_state'], i['ca_state']),
                'cwnd': i['snd_cwnd'], 'ssthresh': i['snd_ssthresh'] if i['snd_ssthresh'] < 1 << 30 else '',
                'inflight': i['unacked'] - i['sacked'] - i['lost'] + i['retrans'],
                'rtt_ms': i['rtt'] / 1000, 'minrtt_ms': i['min_rtt'] / 1000,
                'pacing_mbps': round(i['pacing_rate'] * 8 / 1e6, 3),
                'delivery_mbps': round(i['delivery_rate'] * 8 / 1e6, 3),
                'bytes_acked': i['bytes_acked'], 'total_retrans': i['total_retrans'], **b})
            time.sleep(args.every)
    th = threading.Thread(target=sample, daemon=True); th.start()
    chunk = b'\0' * (1 << 16)
    try:
        while time.monotonic() - t0 < args.seconds:
            s.sendall(chunk)
    except (BrokenPipeError, ConnectionResetError) as e:
        print(f'bbrflow send: {e}', file=sys.stderr)
    stop.set(); th.join()
    last = tcp_info(s); s.close()
    dt = time.monotonic() - t0
    print(f'bbrflow send: cc={args.cc} {last["bytes_acked"]} bytes acked in {dt:.1f} s = '
          f'{last["bytes_acked"] * 8 / dt / 1e6:.2f} Mbit/s, total_retrans={last["total_retrans"]}, '
          f'rows={len(rows)}', file=sys.stderr)
    out = open(args.csv, 'w', newline='') if args.csv else sys.stdout
    w = csv.DictWriter(out, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    if args.csv: out.close()

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = p.add_subparsers(dest='mode', required=True)
r = sub.add_parser('recv'); r.add_argument('--port', type=int, default=5001); r.add_argument('--once', action='store_true')
t = sub.add_parser('send'); t.add_argument('--dst', required=True); t.add_argument('--port', type=int, default=5001)
t.add_argument('--cc', default='bbr'); t.add_argument('--seconds', type=float, default=25)
t.add_argument('--every', type=float, default=0.005); t.add_argument('--csv')
a = p.parse_args()
recv(a) if a.mode == 'recv' else send(a)
