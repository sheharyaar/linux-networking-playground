#!/usr/bin/env bash
# run.sh: one pacing experiment on a fresh qnet bench. Run it through qnet, from this folder:
#
#   ../common/qnet.sh -- ./run.sh --s0 fq --out fq1
#
# The bench it builds (qnet's default delays are moved, see below):
#   snd:s0 egress  --s0 fq      fq paces every TCP flow (TCP stamps each packet, fq holds it)
#                  --s0 pfifo   pfifo limit 10000: nothing paces, unless a flow asked (--paced)
#   rtr:r1 egress  netem rate 10mbit limit BUFFER, no delay: the bottleneck and its drop-tail queue
#   rtr:r0 egress  netem delay 20ms   (acks)
#   rcv:c0 egress  netem delay 20ms   (acks; qnet's own)
# Both 20 ms delays sit on the ack path, because netem's limit counts the packets in its delay
# line (sch_netem.c:552), so a 21-packet limit on a netem that also delays by 20 ms would leave
# no room for a queue. The RTT is still 40 ms.
#
# options: --s0 fq|pfifo  --flows N (8)  --paced K (0)  --buffer B (21)  --initcwnd W (1)
#          --ratios SS/CA (200/120)  --sack 0|1 (1)  --seconds S (15) | --bytes B
#          --mss M (536)  --out NAME (required)
# It writes NAME-f.csv (flow.py), NAME-q.csv (qwatch.py on rtr:r1), NAME-s0.txt and NAME-r1.txt
# (tc -s at the end), and prints flow.py's summary and epochs.py's.
set -u
S0=pfifo N=8 PACED=0 B=21 IW=1 RATIOS=200/120 SACK=1 SECS=15 BYTES=0 MSS=536 OUT=
while [ $# -gt 0 ]; do
  case "$1" in
    --s0) S0=$2;; --flows) N=$2;; --paced) PACED=$2;; --buffer) B=$2;; --initcwnd) IW=$2;;
    --ratios) RATIOS=$2;; --sack) SACK=$2;; --seconds) SECS=$2;; --bytes) BYTES=$2;;
    --mss) MSS=$2;; --out) OUT=$2;;
    *) echo "run.sh: unknown option $1" >&2; exit 2;;
  esac; shift 2
done
[ -n "$OUT" ] || { echo "run.sh: --out NAME is required" >&2; exit 2; }
[ "${QNET_INSIDE:-}" = 1 ] || { echo "run.sh: run it through ../common/qnet.sh -- ./run.sh ..." >&2; exit 2; }
HERE=$(cd "$(dirname "$0")" && pwd)

tc -n rtr qdisc del dev r1 root
tc -n rtr qdisc add dev r1 root netem rate 10mbit limit "$B"
tc -n rtr qdisc replace dev r0 root netem delay 20ms limit 100000
tc -n snd qdisc del dev s0 root
case $S0 in
  fq) tc -n snd qdisc add dev s0 root fq;;
  pfifo) tc -n snd qdisc add dev s0 root pfifo limit 10000;;
  *) echo "run.sh: --s0 must be fq or pfifo" >&2; exit 2;;
esac
ip -n snd route change default via 10.0.1.2 initcwnd "$IW"
ip netns exec snd sysctl -qw net.ipv4.tcp_pacing_ss_ratio="${RATIOS%/*}" net.ipv4.tcp_pacing_ca_ratio="${RATIOS#*/}" \
  net.ipv4.tcp_sack="$SACK"

ip netns exec rcv python3 "$HERE/flow.py" recv >/dev/null 2>&1 &
RP=$!
sleep 0.3
QSECS=$SECS; [ "$BYTES" != 0 ] && QSECS=3
ip netns exec rtr python3 "$HERE/../common/qwatch.py" --dev r1 --every 0.01 --seconds "$((QSECS + 1))" --csv "$OUT-q.csv" &
QP=$!
if [ "$BYTES" != 0 ]; then LEN=(--bytes "$BYTES"); else LEN=(--seconds "$SECS"); fi
ip netns exec snd python3 "$HERE/flow.py" send --dst 10.0.2.1 --flows "$N" --paced "$PACED" --mss "$MSS" \
  "${LEN[@]}" --csv "$OUT-f.csv" --tag "$OUT" 2>&1 | grep -E 'flows,|completion'
tc -n snd -s qdisc show dev s0 > "$OUT-s0.txt"
tc -n rtr -s qdisc show dev r1 > "$OUT-r1.txt"
wait $QP
kill $RP 2>/dev/null
WIN=$(python3 -c "print(round((40 + $B * 0.472 + 10) / 1000, 3))")   # one full-queue RTT, plus 10 ms
python3 "$HERE/epochs.py" "$OUT-f.csv" --window "$WIN"
