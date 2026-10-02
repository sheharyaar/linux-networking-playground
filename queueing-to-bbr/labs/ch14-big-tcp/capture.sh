#!/usr/bin/env bash
# capture.sh: run inside ./bigpair.sh. For IPv6 and IPv4, at 65536 and at 185000, capture the first
# 20,000 data skbs that reach the receiver's c0 (2 s flows, 128-byte snaps), then summarise them.
#   ./bigpair.sh -- ./capture.sh [OUTDIR]
set -euo pipefail
OUT=${1:-.}; HERE=$(cd "$(dirname "$0")" && pwd)
for size in 65536 185000; do
  for pair in snd:s0 rcv:c0; do
    ns=${pair%%:*} dev=${pair##*:}
    ip -n $ns link set $dev gso_max_size $size gro_max_size $size
    ip -n $ns link set $dev gso_ipv4_max_size $size gro_ipv4_max_size $size
  done
  for dst in fd14::2 10.0.14.2; do
    fam=v4; [ "${dst#*:}" != "$dst" ] && fam=v6
    f=$OUT/cap-$fam-$size.pcap
    ip netns exec rcv python3 "$HERE/bulk.py" recv --once >/dev/null 2>&1 &
    ip netns exec rcv tcpdump -i c0 -n -s 128 -c 20000 -w "$f" "tcp dst port 5014 and greater 1000" 2>/dev/null &
    sleep 0.5
    ip netns exec snd python3 "$HERE/bulk.py" send --dst $dst --seconds 2 >/dev/null
    wait
    python3 "$HERE/skblen.py" "$f"
  done
done
