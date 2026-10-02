#!/usr/bin/env python3
"""mflow.py: N bulk TCP flows from one process, and a sink for them, for the Carousel chapter.

  sink:    python3 mflow.py recv --flows 16 [--port 5001]
  sender:  python3 mflow.py send --dst 10.0.2.1 --flows 16 [--port 5001] [--seconds 30]
                                 [--every 0.1] [--csv flows.csv] [--cc reno]

Flow i uses destination port PORT+i, so a tc filter can put each flow in its own class.
Every --every seconds the sender reads TCP_INFO and SO_MEMINFO of every socket and writes one
CSV row per flow: t_s, flow, bytes_acked, cwnd, rtt_ms, total_retrans, wmem_alloc (the bytes of
this socket's packets below TCP that are not freed yet, the number TCP small queues limits).
At the end it prints each flow's goodput over the run after --skip seconds, and the total.
"""
import argparse, csv, socket, statistics, struct, sys, threading, time

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
SO_MEMINFO, SK_MEMINFO_WMEM_ALLOC = 55, 2

def tcp_info(s): return dict(zip(FIELDS, struct.unpack_from(TCP_INFO_FMT, s.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO, 256))))
def wmem(s): return struct.unpack_from('@9I', s.getsockopt(socket.SOL_SOCKET, SO_MEMINFO, 64))[SK_MEMINFO_WMEM_ALLOC]

def recv(a):
    def serve(port):
        srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', port)); srv.listen(4)
        c, _ = srv.accept()
        while c.recv(1 << 16): pass
        c.close(); srv.close()
    ths = [threading.Thread(target=serve, args=(a.port + i,)) for i in range(a.flows)]
    [t.start() for t in ths]
    print(f'mflow recv: listening on :{a.port}-{a.port + a.flows - 1}', file=sys.stderr, flush=True)
    [t.join() for t in ths]

def send(a):
    socks = []
    for i in range(a.flows):
        s = socket.socket(); s.setsockopt(socket.IPPROTO_TCP, socket.TCP_CONGESTION, a.cc.encode())
        s.connect((a.dst, a.port + i)); socks.append(s)
    t0 = time.monotonic(); stop = threading.Event()
    def pump(s):
        chunk = b'\0' * (1 << 16)
        try:
            while not stop.is_set(): s.sendall(chunk)
        except OSError: pass
    ths = [threading.Thread(target=pump, args=(s,), daemon=True) for s in socks]
    [t.start() for t in ths]
    rows = []
    while (t := time.monotonic() - t0) < a.seconds:
        for i, s in enumerate(socks):
            x = tcp_info(s)
            rows.append({'t_s': f'{t:.2f}', 'flow': i, 'bytes_acked': x['bytes_acked'], 'cwnd': x['snd_cwnd'],
                         'rtt_ms': x['rtt'] / 1000, 'total_retrans': x['total_retrans'], 'wmem_alloc': wmem(s)})
        time.sleep(a.every)
    stop.set()
    for s in socks: s.shutdown(socket.SHUT_RDWR); s.close()
    if a.csv:
        w = csv.DictWriter(open(a.csv, 'w', newline=''), fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    # per-flow goodput after --skip seconds
    good = []
    for i in range(a.flows):
        r = [x for x in rows if x['flow'] == i and float(x['t_s']) >= a.skip]
        good.append((r[-1]['bytes_acked'] - r[0]['bytes_acked']) * 8 / (float(r[-1]['t_s']) - float(r[0]['t_s'])) / 1e6)
    rtt = [x['rtt_ms'] for x in rows if float(x['t_s']) >= a.skip]
    ret = sum(max(x['total_retrans'] for x in rows if x['flow'] == i) for i in range(a.flows))
    print(f'mflow send: {a.flows} flows, goodput after {a.skip:g} s (Mbit/s): min {min(good):.3f} median {statistics.median(good):.3f} '
          f'max {max(good):.3f} total {sum(good):.2f}; RTT median {statistics.median(rtt):.0f} ms; retransmissions {ret}', file=sys.stderr)

p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
sub = p.add_subparsers(dest='mode', required=True)
r = sub.add_parser('recv'); r.add_argument('--flows', type=int, default=16); r.add_argument('--port', type=int, default=5001)
t = sub.add_parser('send'); t.add_argument('--dst', required=True); t.add_argument('--flows', type=int, default=16)
t.add_argument('--port', type=int, default=5001); t.add_argument('--seconds', type=float, default=30)
t.add_argument('--every', type=float, default=0.1); t.add_argument('--skip', type=float, default=5)
t.add_argument('--csv'); t.add_argument('--cc', default='reno')
a = p.parse_args()
recv(a) if a.mode == 'recv' else send(a)
