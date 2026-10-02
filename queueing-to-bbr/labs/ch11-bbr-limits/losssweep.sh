#!/usr/bin/env bash
# losssweep.sh: one flow at a time through the bottleneck with random loss; goodput per loss rate.
# Run it through qnet, from this folder:
#
#   ../common/qnet.sh -- ./losssweep.sh --cc "cubic bbr" --loss "0 1 5 10 15 18 20 22 25 30" --out sweep
#
# The bench is duel.sh's (fq on snd:s0, 40 ms on the ack path), with the bottleneck
#   rtr:r1 egress  netem rate 10mbit limit 300 loss P%
# netem drops at enqueue, before its rate limit, so a sender can make up for losses by sending
# faster than 10 Mbit/s (the paper's Mininet links work the same way). 300 packets is about nine
# BDPs, so almost every loss is a random one.
#
# options: --cc "LIST" (cubic)  --loss "LIST" (0 1 5 10 15 20 25 30)  --seconds S (30)
#          --limit L (300)  --out NAME (required)
# It appends one row per run to NAME.csv: cc, limit, loss %, goodput (Mbit/s, last two thirds of the
# run), mean RTT, retransmissions, segments sent, and for BBR the share of samples in each pacing gain.
set -u
CCS=cubic LOSSES="0 1 5 10 15 20 25 30" SECS=30 L=300 OUT=
while [ $# -gt 0 ]; do
  case "$1" in
    --cc) CCS=$2;; --loss) LOSSES=$2;; --seconds) SECS=$2;; --limit) L=$2;; --out) OUT=$2;;
    *) echo "losssweep.sh: unknown option $1" >&2; exit 2;;
  esac; shift 2
done
[ -n "$OUT" ] || { echo "losssweep.sh: --out NAME is required" >&2; exit 2; }
[ "${QNET_INSIDE:-}" = 1 ] || { echo "losssweep.sh: run it through ../common/qnet.sh -- ./losssweep.sh ..." >&2; exit 2; }
HERE=$(cd "$(dirname "$0")" && pwd)

tc -n snd qdisc del dev s0 root
tc -n snd qdisc add dev s0 root fq
tc -n rcv qdisc del dev c0 root
tc -n rcv qdisc add dev c0 root netem delay 40ms limit 100000
ip netns exec rcv python3 "$HERE/flow.py" recv 2>/dev/null &
RP=$!
sleep 0.3
[ -f "$OUT.csv" ] || echo "cc,limit,loss_pct,goodput_mbps,mean_rtt_ms,retrans,segs_out,retrans_pct,gain_1.25,gain_0.75,gain_1.0,longest_gain1_s" > "$OUT.csv"
for cc in $CCS; do
  for p in $LOSSES; do
    tc -n rtr qdisc del dev r1 root
    tc -n rtr qdisc add dev r1 root handle 1: netem rate 10mbit limit "$L" loss "$p%"
    run="$OUT-$cc-L$L-p$p"
    ip netns exec snd python3 "$HERE/flow.py" send --dst 10.0.2.1 --cc "$cc" --seconds "$SECS" --csv "$run.csv" 2>/dev/null
    python3 - "$run.csv" "$cc" "$p" "$SECS" "$L" >> "$OUT.csv" <<'EOF'
import csv, sys
f, cc, p, secs, lim = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5]
rows = list(csv.DictReader(open(f)))
w = [r for r in rows if float(r['t_s']) >= secs / 3]
dt = float(w[-1]['t_s']) - float(w[0]['t_s'])
gp = (int(w[-1]['bytes_acked']) - int(w[0]['bytes_acked'])) * 8 / dt / 1e6
retr = int(w[-1]['total_retrans']) - int(w[0]['total_retrans'])
segs = int(w[-1]['segs_out']) - int(w[0]['segs_out'])
rtt = sum(float(r['rtt_ms']) for r in w) / len(w)
gains = ['', '', '', '']
if cc == 'bbr' and w[0].get('pacing_gain', '') != '':
    g = [float(r['pacing_gain']) for r in w]
    n = len(g)
    gains = [f'{100 * sum(1 for x in g if abs(x - v) < 0.01) / n:.1f}' for v in (1.25, 0.75, 1.0)]
    best, t_start = 0.0, None   # longest unbroken stretch at pacing gain 1.0 with cwnd gain 2 (policer mode)
    for r in w:
        if abs(float(r['pacing_gain']) - 1.0) < 0.01 and abs(float(r['cwnd_gain']) - 2.0) < 0.01:
            t_start = float(r['t_s']) if t_start is None else t_start
            best = max(best, float(r['t_s']) - t_start)
        else:
            t_start = None
    gains.append(f'{best:.2f}')
print(f'{cc},{lim},{p},{gp:.3f},{rtt:.1f},{retr},{segs},{100 * retr / max(segs, 1):.2f},' + ','.join(gains))
EOF
    tail -1 "$OUT.csv"
  done
done
kill $RP 2>/dev/null
