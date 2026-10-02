#!/usr/bin/env python3
"""flow.py (chapter 6 copy of labs/common/flow.py): many bulk TCP flows started together, and a sink.

  sink:    python3 flow.py recv [--port 5001]
  senders: python3 flow.py send --dst 10.0.2.1 [--port 5001] --flows 8 [--paced 4]
                              [--seconds 20 | --bytes 157200] [--mss 536] [--cc reno]
                              [--every 0.01] [--csv out.csv] [--tag NAME]

Added for the TCP pacing chapter:
  --flows N        open N connections, wait until every one is established, then let all N
                   start writing at the same instant (a threading.Barrier).
  --paced K        the first K flows set SO_MAX_PACING_RATE to --pace-cap (default 1 Gbit/s,
                   far above any rate on this bench). Any value other than ~0 marks the socket
                   SK_PACING_NEEDED (net/core/sock.c:1263-1266), so with no fq on the path TCP's
                   own timer paces it at the rate TCP computes (tcp_pacing_check(),
                   net/ipv4/tcp_output.c:2815). The other N-K flows are not paced unless fq is
                   the qdisc, in which case fq paces every flow and --paced changes nothing.
  --mss M          TCP_MAXSEG before connect. 536 gives 576-byte IP packets, the paper's size.
  --bytes B        each flow sends exactly B bytes, then shuts down its side and waits for the
                   sink to close; the flow's completion time is printed (the paper's latency).
  --seconds S      each flow writes for S seconds (bulk runs).
  CSV              one row per flow per sample: t_s (seconds since the common start), flow,
                   paced, ca_state, cwnd, ssthresh, rtt_ms, unacked, lost, retrans, total_retrans,
                   pacing_mbps (tcpi_pacing_rate, which TCP fills in for every socket whether or
                   not anything paces it), bytes_acked, backoff, done (1 once the flow finished).

  The sink accepts any number of connections and reads each to the end in its own thread.
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

def rate_bps(s):
    m = re.fullmatch(r'([\d.]+)\s*(kbit|mbit|gbit|bit)?', s.lower())
    if not m: raise argparse.ArgumentTypeError(f'bad rate {s!r}; try 1gbit')
    return int(float(m.group(1)) * {'kbit': 1e3, 'mbit': 1e6, 'gbit': 1e9, 'bit': 1, None: 1}[m.group(2)])

def tcp_info(sock):
    raw = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO, 256)
    return dict(zip(FIELDS, struct.unpack_from(TCP_INFO_FMT, raw)))

def recv(args):
    srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', args.port)); srv.listen(256)
    print(f'flow recv: listening on :{args.port}', file=sys.stderr, flush=True)
    def drain(c):
        while c.recv(1 << 16):
            pass
        c.close()
    while True:
        c, _ = srv.accept()
        threading.Thread(target=drain, args=(c,), daemon=True).start()

def send(args):
    socks = []
    for k in range(args.flows):
        s = socket.socket()
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_CONGESTION, args.cc.encode())
        if args.mss: s.setsockopt(socket.IPPROTO_TCP, socket.TCP_MAXSEG, args.mss)
        if k < args.paced:
            s.setsockopt(socket.SOL_SOCKET, SO_MAX_PACING_RATE, struct.pack('@Q', args.pace_cap // 8))
        s.connect((args.dst, args.port))
        socks.append(s)
    n = len(socks)
    gate = threading.Barrier(n + 1)
    done = [None] * n                      # completion time per flow (seconds after the start)
    t0box = []
    chunk = b'\0' * (1 << 16)
    def writer(k):
        s = socks[k]
        gate.wait()
        t0 = t0box[0]
        try:
            if args.bytes:
                left = args.bytes
                while left > 0:
                    sent = s.send(chunk[:min(left, len(chunk))])
                    left -= sent
                s.shutdown(socket.SHUT_WR)
                while s.recv(1 << 12):      # the sink closes after it has read everything
                    pass
            else:
                while time.monotonic() - t0 < args.seconds:
                    s.sendall(chunk)
        except (BrokenPipeError, ConnectionResetError) as e:
            print(f'flow send: flow {k}: {e}', file=sys.stderr)
        done[k] = time.monotonic() - t0
    ths = [threading.Thread(target=writer, args=(k,), daemon=True) for k in range(n)]
    for th in ths: th.start()
    rows = []
    stop = threading.Event()
    def sample():
        t0 = t0box[0]
        while not stop.is_set():
            t = time.monotonic() - t0
            for k, s in enumerate(socks):
                try:
                    i = tcp_info(s)
                except OSError:
                    continue
                rows.append({
                    't_s': f'{t:.3f}', 'flow': k, 'paced': int(k < args.paced),
                    'ca_state': CA_STATE.get(i['ca_state'], i['ca_state']),
                    'cwnd': i['snd_cwnd'], 'ssthresh': i['snd_ssthresh'] if i['snd_ssthresh'] < 1 << 30 else '',
                    'rtt_ms': i['rtt'] / 1000, 'unacked': i['unacked'], 'lost': i['lost'],
                    'retrans': i['retrans'], 'total_retrans': i['total_retrans'],
                    'pacing_mbps': round(i['pacing_rate'] * 8 / 1e6, 3) if i['pacing_rate'] < 1 << 62 else '',
                    'bytes_acked': i['bytes_acked'], 'backoff': i['backoff'],
                    'done': int(done[k] is not None)})
            time.sleep(args.every)
    t0box.append(time.monotonic())
    gate.wait()                            # every writer starts now
    smp = threading.Thread(target=sample, daemon=True); smp.start()
    for th in ths: th.join()
    stop.set(); smp.join()
    finals = [tcp_info(s) for s in socks]
    for s in socks: s.close()
    dt = max(done)
    acked = [f['bytes_acked'] for f in finals]
    tot = sum(acked)
    jain = tot * tot / (n * sum(a * a for a in acked)) if tot else 0
    tag = f'{args.tag} ' if args.tag else ''
    for k, (f, d) in enumerate(zip(finals, done)):
        kind = 'paced' if k < args.paced else 'unpaced-by-tcp'
        print(f'flow send: {tag}flow {k} {kind} {f["bytes_acked"]} bytes in {d:.3f} s, '
              f'total_retrans={f["total_retrans"]}', file=sys.stderr)
    if args.bytes:
        pc = [d for k, d in enumerate(done) if k < args.paced]; uc = [d for k, d in enumerate(done) if k >= args.paced]
        mean = lambda v: sum(v) / len(v) if v else float('nan')
        print(f'flow send: {tag}completion mean: paced {mean(pc):.3f} s ({len(pc)} flows), '
              f'unpaced {mean(uc):.3f} s ({len(uc)} flows), all {mean(done):.3f} s', file=sys.stderr)
    print(f'flow send: {tag}{n} flows, {args.paced} with SO_MAX_PACING_RATE, cc={args.cc}: '
          f'{tot} bytes acked in {dt:.2f} s = {tot * 8 / dt / 1e6:.2f} Mbit/s, '
          f'Jain {jain:.3f}, total_retrans={sum(f["total_retrans"] for f in finals)}, rows={len(rows)}',
          file=sys.stderr)
    if args.csv:
        with open(args.csv, 'w', newline='') as out:
            w = csv.DictWriter(out, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = p.add_subparsers(dest='mode', required=True)
r = sub.add_parser('recv'); r.add_argument('--port', type=int, default=5001)
t = sub.add_parser('send'); t.add_argument('--dst', required=True); t.add_argument('--port', type=int, default=5001)
t.add_argument('--flows', type=int, default=1); t.add_argument('--paced', type=int, default=0)
t.add_argument('--pace-cap', type=rate_bps, default=10 ** 9)
t.add_argument('--cc', default='reno'); t.add_argument('--mss', type=int, default=0)
t.add_argument('--seconds', type=float, default=20); t.add_argument('--bytes', type=int, default=0)
t.add_argument('--every', type=float, default=0.01); t.add_argument('--csv'); t.add_argument('--tag', default='')
a = p.parse_args()
recv(a) if a.mode == 'recv' else send(a)
