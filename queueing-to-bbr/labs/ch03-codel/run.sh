#!/usr/bin/env bash
# run.sh: one rootless bench run for the queue-delay chapter (ch03.html).
#
#   ./run.sh CHILD [--seconds 40] [--step-at T] [--ecn] [--out data/NAME]
#
#   CHILD     pfifo | codel | fq_codel   the qdisc that holds the bottleneck queue
#   --step-at T   at T seconds, drop the bottleneck from 10 Mbit/s to 1 Mbit/s
#   --ecn         the sender asks for ECN (net.ipv4.tcp_ecn=1 in its namespace)
#   --udp MBIT    send a constant-rate UDP stream (udpflood.py) instead of the Reno flow
#   --every S     qstat.py sampling period (default 0.01)
#   --flows N     run N Reno flows at once (ports 5001..), each writing NAME-tcpK.csv
#   --snap "T1 T2"  at these times, append `tc -s qdisc show dev r1` to NAME-snap.txt
#   --out NAME    file prefix (default out/CHILD); writes NAME-tcp.csv, NAME-q.csv, NAME-ping.txt
#                 (the author's own runs are kept in data/, so a default run never overwrites them)
#
# It builds the qnet bench (labs/common/qnet.sh: snd -> rtr -> rcv, 20 ms each way, offloads off),
# then replaces the bottleneck on rtr:r1 with a plain 10 Mbit/s rate limiter (tbf) and puts CHILD
# under it, where the queue builds. One Reno flow runs for --seconds, with a ping alongside and
# qstat.py sampling the child qdisc every 10 ms. No sudo: everything runs in a user namespace.
set -euo pipefail
cd "$(dirname "$0")"
if [ "${QNET_INSIDE:-}" != 1 ]; then exec ../common/qnet.sh -- "$PWD/run.sh" "$@"; fi

CHILD=$1; shift
SECS=40 STEP= ECN=0 UDP= EVERY=0.01 FLOWS=1 SNAP= OUT=out/$CHILD
while [ $# -gt 0 ]; do
  case "$1" in
    --seconds) SECS=$2; shift 2;;
    --step-at) STEP=$2; shift 2;;
    --ecn) ECN=1; shift;;
    --udp) UDP=$2; shift 2;;
    --every) EVERY=$2; shift 2;;
    --flows) FLOWS=$2; shift 2;;
    --snap) SNAP=$2; shift 2;;
    --out) OUT=$2; shift 2;;
    *) echo "unknown option $1" >&2; exit 2;;
  esac
done
case "$CHILD" in
  pfifo) CHILDQ="pfifo limit 1000";;
  codel) CHILDQ="codel";;
  fq_codel) CHILDQ="fq_codel";;
  *) echo "CHILD must be pfifo, codel or fq_codel" >&2; exit 2;;
esac
mkdir -p "$(dirname "$OUT")"

# the bottleneck: a plain rate limiter at the root, the queue in its child
tc -n rtr qdisc del dev r1 root
tc -n rtr qdisc add dev r1 root handle 1: tbf rate 10mbit burst 1540 latency 2s
tc -n rtr qdisc add dev r1 parent 1:1 handle 2: $CHILDQ
[ "$ECN" = 1 ] && ip netns exec snd sysctl -qw net.ipv4.tcp_ecn=1
tc -n rtr qdisc show dev r1 >&2

if [ -n "$UDP" ]; then
  ip netns exec rcv python3 udpflood.py recv --seconds $((SECS + 3)) &
elif [ "$FLOWS" = 1 ]; then
  ip netns exec rcv python3 ../common/flow.py recv --once &
else
  for k in $(seq 1 "$FLOWS"); do ip netns exec rcv python3 ../common/flow.py recv --once --port $((5000 + k)) & done
fi
sleep 0.3
ip netns exec rtr python3 qstat.py --dev r1 --handle 2: --every "$EVERY" --seconds $((SECS + 2)) --csv "$OUT-q.csv" &
ip netns exec snd ping -D -n -i 0.1 -w "$SECS" 10.0.2.1 > "$OUT-ping.txt" &
for T in $SNAP; do
  (sleep "$T"; { echo "# t = $T s"; tc -n rtr -s qdisc show dev r1; } >> "$OUT-snap.txt") &
done
if [ -n "$STEP" ]; then
  # Changing tbf also resets a pfifo child's limit (tbf_change() calls fifo_set_limit(),
  # net/sched/sch_tbf.c:444), so put the 1000-packet limit back straight away.
  (sleep "$STEP"; tc -n rtr qdisc change dev r1 root handle 1: tbf rate 1mbit burst 1540 latency 2s
   [ "$CHILD" = pfifo ] && tc -n rtr qdisc change dev r1 parent 1:1 handle 2: pfifo limit 1000
   echo "step: bottleneck now 1 Mbit/s at ${STEP} s" >&2) &
fi
if [ -n "$UDP" ]; then
  ip netns exec snd python3 udpflood.py send --dst 10.0.2.1 --mbit "$UDP" --seconds "$SECS"
elif [ "$FLOWS" = 1 ]; then
  ip netns exec snd python3 ../common/flow.py send --dst 10.0.2.1 --cc reno --seconds "$SECS" --csv "$OUT-tcp.csv"
else
  for k in $(seq 1 "$FLOWS"); do
    ip netns exec snd python3 ../common/flow.py send --dst 10.0.2.1 --port $((5000 + k)) --cc reno --seconds "$SECS" --csv "$OUT-tcp$k.csv" &
  done
fi
wait
tc -n rtr -s qdisc show dev r1 >&2
