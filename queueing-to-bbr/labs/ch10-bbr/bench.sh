#!/usr/bin/env bash
# bench.sh: one bulk flow on the BBR chapter's path, 10 Mbit/s and 40 ms. Run it through qnet,
# from this folder:
#
#   ../common/qnet.sh -- ./bench.sh --cc bbr --out data/bbr
#
# The path (qnet's bottleneck kept as built; the sender's 20 ms moved to the ack path):
#   snd:s0 egress  fq (or --s0 fq_codel, so that TCP's own timer paces)   the sender's qdisc
#   rtr:r1 egress  netem rate 10mbit limit 50 (qnet's, or --limit N)      the bottleneck
#   rcv:c0 egress  netem delay 40ms                                       acks, the whole RTT
# netem on the sender's own egress would orphan each skb at enqueue, so TSQ and fq would never
# see the sender's queue (the small-queues chapter). With fq on s0 and the delay on the ack path,
# the bottleneck queue is the only queue, and the round trip is still 40 ms plus 1.21 ms per
# queued packet.
#
# options: --cc bbr|cubic|reno (bbr)  --seconds S (25)  --limit N (50)  --s0 fq|fq_codel (fq)
#          --every SEC (0.005, TCP_INFO and TCP_CC_INFO sampling)  --out PREFIX (required)
# It writes PREFIX-f.csv (bbrflow.py), PREFIX-q.csv (qwatch.py on rtr:r1, every 20 ms),
# PREFIX-ss.txt (ss -tin at 5 s and 15 s) and PREFIX-tc.txt (tc -s on s0 and r1 at the end).
set -u
CC=bbr SECS=25 LIMIT=50 S0=fq EVERY=0.005 OUT=
while [ $# -gt 0 ]; do
  case "$1" in
    --cc) CC=$2;; --seconds) SECS=$2;; --limit) LIMIT=$2;; --s0) S0=$2;; --every) EVERY=$2;;
    --out) OUT=$2;;
    *) echo "bench.sh: unknown option $1" >&2; exit 2;;
  esac; shift 2
done
[ -n "$OUT" ] || { echo "bench.sh: --out PREFIX is required" >&2; exit 2; }
[ "${QNET_INSIDE:-}" = 1 ] || { echo "bench.sh: run it through ../common/qnet.sh -- ./bench.sh ..." >&2; exit 2; }
HERE=$(cd "$(dirname "$0")" && pwd)
grep -qw "$CC" /proc/sys/net/ipv4/tcp_available_congestion_control || {
  echo "bench.sh: $CC is not in tcp_available_congestion_control; for bbr run: sudo modprobe tcp_bbr" >&2; exit 1; }

tc -n snd qdisc del dev s0 root
tc -n snd qdisc add dev s0 root "$S0"
tc -n rcv qdisc del dev c0 root
tc -n rcv qdisc add dev c0 root netem delay 40ms limit 100000
if [ "$LIMIT" != 50 ]; then
  tc -n rtr qdisc del dev r1 root
  tc -n rtr qdisc add dev r1 root handle 1: netem rate 10mbit limit "$LIMIT"
fi

ip netns exec rcv python3 "$HERE/bbrflow.py" recv --once 2>/dev/null &
ip netns exec snd ping -q -c 1 -W 1 10.0.2.1 >/dev/null   # resolve ARP first: the 40 ms ack-path delay
sleep 0.3                                                    # also delays ARP replies
ip netns exec rtr python3 "$HERE/../common/qwatch.py" --dev r1 --every 0.02 --seconds "$((${SECS%.*} + 1))" \
  --csv "$OUT-q.csv" &
QP=$!
( sleep 5;  echo "== ss -tin at 5 s";  ip netns exec snd ss -tin dst 10.0.2.1
  sleep 10; echo "== ss -tin at 15 s"; ip netns exec snd ss -tin dst 10.0.2.1 ) > "$OUT-ss.txt" 2>&1 &
ip netns exec snd python3 "$HERE/bbrflow.py" send --dst 10.0.2.1 --cc "$CC" --seconds "$SECS" \
  --every "$EVERY" --csv "$OUT-f.csv"
{ echo "== snd:s0"; tc -n snd -s qdisc show dev s0; echo "== rtr:r1"; tc -n rtr -s qdisc show dev r1; } > "$OUT-tc.txt"
wait $QP
wait
