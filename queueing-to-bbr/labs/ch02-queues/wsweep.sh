#!/usr/bin/env bash
# wsweep.sh: hold one Reno flow's window fixed at W packets and measure throughput and RTT.
#
#   ./wsweep.sh [--seconds 8] [--out DIR] [W ...]       (default W: 5 10 ... 80, then 0 = no cap)
#
# For each W it builds a fresh rootless bench (../common/qnet.sh, defaults: 10 Mbit/s, 20 ms
# each way, 50-packet queue) and caps the sender's congestion window with a locked route metric:
#     ip -n snd route replace default via 10.0.1.2 cwnd lock W
# Linux copies a locked RTAX_CWND into tp->snd_cwnd_clamp from its TCP metrics cache
# (net/ipv4/tcp_metrics.c, tcp_init_metrics()), and the cache entry only exists after one
# connection to that peer has closed, so the script makes one short connection first. A fresh
# bench per W is needed because `ip tcp_metrics flush` is refused inside a user namespace.
# Output: DIR/w<W>.csv (flow.py's TCP_INFO samples) and one summary line per W in DIR/wsweep.csv.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
SECONDS_EACH=8 OUT=$here/out
while [ $# -gt 0 ]; do
  case "$1" in
    --seconds) SECONDS_EACH=$2; shift 2;;
    --out) OUT=$2; shift 2;;
    --one) shift; W=$1; shift;;          # internal: run one W inside the bench
    -h|--help) sed -n '2,14p' "$0"; exit 0;;
    *) break;;
  esac
done
mkdir -p "$OUT"
if [ -z "${W:-}" ]; then
  for w in ${*:-5 10 15 20 25 30 33 36 40 50 60 70 80 0}; do
    "$here/../common/qnet.sh" -- "$0" --seconds "$SECONDS_EACH" --out "$OUT" --one "$w" 2>/dev/null
  done
  exit 0
fi
cd "$here/../common"
[ "$W" != 0 ] && ip -n snd route replace default via 10.0.1.2 cwnd lock "$W"
ip netns exec rcv python3 flow.py recv 2>/dev/null & sink=$!
sleep 0.3
ip netns exec snd python3 -c "import socket,time; s=socket.create_connection(('10.0.2.1',5001)); time.sleep(0.1); s.close()"
sleep 0.2
ip netns exec snd python3 flow.py send --dst 10.0.2.1 --cc reno --seconds "$SECONDS_EACH" --csv "$OUT/w$W.csv" 2>/dev/null
kill $sink
python3 - "$OUT/w$W.csv" "$W" "$OUT/wsweep.csv" <<'EOF'
import csv, os, statistics as st, sys
f, W, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
r = [x for x in csv.DictReader(open(f))]
late = [x for x in r if float(x['t_s']) >= float(r[-1]['t_s']) - 5]      # the last 5 s: past slow start
t0, t1 = float(late[0]['t_s']), float(late[-1]['t_s'])
gput = (int(late[-1]['bytes_acked']) - int(late[0]['bytes_acked'])) * 8 / (t1 - t0) / 1e6
rtt = st.mean(float(x['rtt_ms']) for x in late)
cw = st.mean(int(x['cwnd']) for x in late)
una = st.mean(int(x['unacked']) for x in late)
pps = gput * 1e6 / 8 / 1448
row = {'W': W or 'none', 'cwnd_mean': round(cw, 1), 'unacked_mean': round(una, 1), 'goodput_mbps': round(gput, 3),
       'rtt_ms': round(rtt, 2), 'pkts_per_s': round(pps, 1), 'littles_inflight': round(pps * rtt / 1000, 1),
       'retrans': r[-1]['total_retrans']}
new = not os.path.exists(out)
with open(out, 'a', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(row))
    if new: w.writeheader()
    w.writerow(row)
print(' '.join(f'{k}={v}' for k, v in row.items()))
EOF
