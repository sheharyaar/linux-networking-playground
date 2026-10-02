#!/usr/bin/env python3
"""flow.py (chapter 5 copy of labs/common/flow.py): a bulk TCP sender and a sink.

  sink:    python3 flow.py recv [--port 5001] [--once]
  sender:  python3 flow.py send --dst 10.0.2.1 [--port 5001] [--cc reno] [--seconds 20]
                              [--every 0.01] [--csv out.csv] [--max-pacing-rate 5mbit]

Added for the small-queues chapter:
  --max-pacing-rate RATE   setsockopt(SO_MAX_PACING_RATE) before connect. RATE takes the
                           suffixes kbit, mbit, gbit (bits per second); the kernel wants bytes
                           per second, so the script divides by 8.
  wmem_alloc column        sk_wmem_alloc from getsockopt(SO_MEMINFO): the bytes of this
                           socket's packets that sit below TCP (qdisc, device) and have not
                           been freed yet. This is the number TCP small queues limits.
  wmem_queued, sndbuf      the socket's whole send queue (sent and unsent, in truesize) and
                           its limit, also from SO_MEMINFO.
  notsent column           bytes the application wrote that TCP has not sent yet.
  pacing_mbps              sk_pacing_rate as TCP_INFO reports it (tcpi_pacing_rate).
"""
import argparse, csv, re, socket, struct, sys, threading, time

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
SO_MAX_PACING_RATE = 47          # include/uapi/asm-generic/socket.h
SO_MEMINFO = 55                  # same file; returns u32[SK_MEMINFO_VARS]
SK_MEMINFO_WMEM_ALLOC, SK_MEMINFO_SNDBUF, SK_MEMINFO_WMEM_QUEUED = 2, 3, 5   # include/uapi/linux/sock_diag.h

def rate_bps(s):
    m = re.fullmatch(r'([\d.]+)\s*(kbit|mbit|gbit|bit)?', s.lower())
    if not m: raise argparse.ArgumentTypeError(f'bad rate {s!r}; try 5mbit')
    return int(float(m.group(1)) * {'kbit': 1e3, 'mbit': 1e6, 'gbit': 1e9, 'bit': 1, None: 1}[m.group(2)])

def tcp_info(sock):
    raw = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO, 256)
    return dict(zip(FIELDS, struct.unpack_from(TCP_INFO_FMT, raw)))

def meminfo(sock):
    raw = sock.getsockopt(socket.SOL_SOCKET, SO_MEMINFO, 4 * 16)
    return struct.unpack_from('@9I', raw)

def recv(args):
    srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', args.port)); srv.listen(8)
    print(f'flow recv: listening on :{args.port}', file=sys.stderr, flush=True)
    while True:
        c, peer = srv.accept(); n = 0; t0 = time.monotonic()
        while (b := c.recv(1 << 16)):
            n += len(b)
        dt = time.monotonic() - t0
        print(f'flow recv: {peer[0]} sent {n} bytes in {dt:.2f} s = {n * 8 / dt / 1e6:.2f} Mbit/s', file=sys.stderr, flush=True)
        c.close()
        if args.once: return

def send(args):
    s = socket.socket()
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_CONGESTION, args.cc.encode())
    if args.max_pacing_rate:
        s.setsockopt(socket.SOL_SOCKET, SO_MAX_PACING_RATE, struct.pack('@Q', args.max_pacing_rate // 8))
    s.connect((args.dst, args.port))
    t0 = time.monotonic(); stop = threading.Event(); rows = []
    def sample():
        while not stop.is_set():
            i = tcp_info(s); m = meminfo(s); t = time.monotonic() - t0
            rows.append({
                't_s': f'{t:.3f}', 'ca_state': CA_STATE.get(i['ca_state'], i['ca_state']),
                'cwnd': i['snd_cwnd'], 'ssthresh': i['snd_ssthresh'] if i['snd_ssthresh'] < 1 << 30 else '',
                'rtt_ms': i['rtt'] / 1000, 'minrtt_ms': i['min_rtt'] / 1000 if i['min_rtt'] < 1 << 31 else '',
                'unacked': i['unacked'], 'total_retrans': i['total_retrans'],
                'pacing_mbps': round(i['pacing_rate'] * 8 / 1e6, 3) if i['pacing_rate'] < 1 << 62 else '',
                'delivery_mbps': round(i['delivery_rate'] * 8 / 1e6, 3),
                'wmem_alloc': m[SK_MEMINFO_WMEM_ALLOC], 'wmem_queued': m[SK_MEMINFO_WMEM_QUEUED],
                'sndbuf': m[SK_MEMINFO_SNDBUF], 'notsent': i['notsent_bytes'], 'bytes_acked': i['bytes_acked']})
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
    cap = f' max_pacing_rate={args.max_pacing_rate / 1e6:g}Mbit' if args.max_pacing_rate else ''
    print(f'flow send: cc={args.cc}{cap} {last["bytes_acked"]} bytes acked in {dt:.1f} s = '
          f'{last["bytes_acked"] * 8 / dt / 1e6:.2f} Mbit/s, total_retrans={last["total_retrans"]}, '
          f'rows={len(rows)}', file=sys.stderr)
    out = open(args.csv, 'w', newline='') if args.csv else sys.stdout
    w = csv.DictWriter(out, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    if args.csv: out.close()

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = p.add_subparsers(dest='mode', required=True)
r = sub.add_parser('recv'); r.add_argument('--port', type=int, default=5001); r.add_argument('--once', action='store_true')
t = sub.add_parser('send'); t.add_argument('--dst', required=True); t.add_argument('--port', type=int, default=5001)
t.add_argument('--cc', default='reno'); t.add_argument('--seconds', type=float, default=20)
t.add_argument('--every', type=float, default=0.01); t.add_argument('--csv')
t.add_argument('--max-pacing-rate', type=rate_bps, default=0)
a = p.parse_args()
recv(a) if a.mode == 'recv' else send(a)
