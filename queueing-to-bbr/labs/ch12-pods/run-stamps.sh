#!/usr/bin/env bash
# run-stamps.sh: does a departure time written on snd still work after the packet crosses rtr?
#
#   ../common/qnet.sh -- ./run-stamps.sh [outdir]          (from labs/ch12-pods, no sudo)
#
# snd:s0 gets no qdisc that reads stamps (noqueue), so every datagram reaches the router
# about --lead-ms (5 ms) before its stamp. rtr:r1 gets plain fq. A capture on r0 times each
# packet as it arrives at the router; a capture on r1 times it as fq lets it go. If fq on the
# router honours the stamp, r1 shows lateness near zero; if the stamp was cleared on the way,
# r1 shows the same -5 ms as r0.
# Five runs: no SO_TXTIME (control), CLOCK_MONOTONIC, CLOCK_TAI, CLOCK_REALTIME, and a burst
# of 50 monotonic stamps handed down at once (spacing comes only from the router's fq).
set -euo pipefail
OUT=${1:-.}
mkdir -p "$OUT"
cd "$(dirname "$0")"
uname -r
tc -n snd qdisc del dev s0 root                 # back to the veth default, noqueue
tc -n rtr qdisc del dev r1 root
tc -n rtr qdisc add dev r1 root fq
tc -n rtr qdisc show dev r1
ip netns exec rcv python3 txtime.py --listen --seconds 120 &
sleep 0.3

one() {   # name, txtime.py arguments...
  local name=$1; shift
  ip netns exec rtr timeout 4 tcpdump -i r0 -n -s 96 --time-stamp-precision nano -w "$OUT/$name-r0.pcap" udp 2>/dev/null & local p0=$!
  ip netns exec rtr timeout 4 tcpdump -i r1 -n -s 96 --time-stamp-precision nano -w "$OUT/$name-r1.pcap" udp 2>/dev/null & local p1=$!
  sleep 0.7
  echo "=== $name: txtime.py $*"
  ip netns exec snd python3 txtime.py --dst 10.0.2.1 "$@" --csv "$OUT/$name.csv"
  wait $p0 $p1 || true
  echo "--- arriving at rtr:r0"
  python3 txgaps.py "$OUT/$name-r0.pcap" "$OUT/$name.csv" --csv "$OUT/$name-r0.csv"
  echo "--- leaving rtr:r1 (after fq)"
  python3 txgaps.py "$OUT/$name-r1.pcap" "$OUT/$name.csv" --csv "$OUT/$name-r1.csv"
}
one none  --count 1000 --no-stamp
one mono  --count 1000 --clock mono
one tai   --count 1000 --clock tai
one real  --count 1000 --clock real
one burst --count 50   --clock mono --burst
echo "=== tc -s on rtr:r1"
tc -n rtr -s qdisc show dev r1
