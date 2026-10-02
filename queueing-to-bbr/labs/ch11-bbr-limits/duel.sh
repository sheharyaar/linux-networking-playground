#!/usr/bin/env bash
# duel.sh: two bulk flows share the bench's bottleneck; prints each flow's share and Jain's index.
# Run it through qnet, from this folder:
#
#   ../common/qnet.sh -- ./duel.sh --limit 17 --a bbr --b cubic --seconds 120 --out shallow
#
# The bench (qnet's defaults, with the sender's delay moved to the ack path, BUILD-BRIEF section 10):
#   snd:s0 egress  fq                         (paces each flow at its socket's pacing rate)
#   rtr:r1 egress  netem rate 10mbit limit L  (the bottleneck; L packets of drop-tail queue, no delay)
#   rcv:c0 egress  netem delay 40ms           (acks; the RTT is 40 ms)
# The pipe is about 33 full-size packets (825 packets/s x 40 ms), so --limit 17 is half a BDP and
# --limit 333 is ten.
#
# options: --limit L (50)  --a CC (bbr)  --b CC (cubic)  --seconds S (120)  --stagger T (0, start b
#          T seconds after a)  --from F (S/2: start of the window share.py measures)  --out NAME
# It writes NAME-a.csv and NAME-b.csv (flow.py), NAME-q.csv (qwatch.py on rtr:r1) and NAME-r1.txt.
set -u
L=50 A=bbr B=cubic SECS=120 STAG=0 FROM= OUT=
while [ $# -gt 0 ]; do
  case "$1" in
    --limit) L=$2;; --a) A=$2;; --b) B=$2;; --seconds) SECS=$2;; --stagger) STAG=$2;;
    --from) FROM=$2;; --out) OUT=$2;;
    *) echo "duel.sh: unknown option $1" >&2; exit 2;;
  esac; shift 2
done
[ -n "$OUT" ] || { echo "duel.sh: --out NAME is required" >&2; exit 2; }
[ "${QNET_INSIDE:-}" = 1 ] || { echo "duel.sh: run it through ../common/qnet.sh -- ./duel.sh ..." >&2; exit 2; }
HERE=$(cd "$(dirname "$0")" && pwd)
[ -n "$FROM" ] || FROM=$((SECS / 2))

tc -n rtr qdisc del dev r1 root
tc -n rtr qdisc add dev r1 root handle 1: netem rate 10mbit limit "$L"
tc -n snd qdisc del dev s0 root
tc -n snd qdisc add dev s0 root fq
tc -n rcv qdisc del dev c0 root
tc -n rcv qdisc add dev c0 root netem delay 40ms limit 100000

ip netns exec rcv python3 "$HERE/flow.py" recv 2>/dev/null &
RP=$!
sleep 0.3
ip netns exec rtr python3 "$HERE/../common/qwatch.py" --dev r1 --every 0.1 --seconds "$((SECS + STAG + 1))" --csv "$OUT-q.csv" &
QP=$!
ip netns exec snd python3 "$HERE/flow.py" send --dst 10.0.2.1 --cc "$A" --label "a-$A" --seconds "$SECS" --csv "$OUT-a.csv" &
AP=$!
ip netns exec snd python3 "$HERE/flow.py" send --dst 10.0.2.1 --cc "$B" --label "b-$B" --start "$STAG" --seconds "$SECS" --csv "$OUT-b.csv" &
BP=$!
wait $AP $BP
tc -n rtr -s qdisc show dev r1 > "$OUT-r1.txt"
wait $QP
kill $RP 2>/dev/null
echo "duel: limit $L packets, $A against $B, window ${FROM}-$((SECS + STAG)) s"
python3 "$HERE/share.py" --from "$FROM" --to "$((SECS + STAG))" "$OUT-a.csv" "$OUT-b.csv"
grep -o 'dropped [0-9]*' "$OUT-r1.txt" | head -1 | sed 's/^/router: /'
