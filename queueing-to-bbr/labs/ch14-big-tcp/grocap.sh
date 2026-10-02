#!/usr/bin/env bash
# grocap.sh: run inside ./bigpair.sh --gro-path [...]. One flow per family; capture the first 5,000
# data skbs that GRO hands up at rcv:c0, then summarise them with the flow's throughput.
#   ./bigpair.sh --gro-path --size 185000 -- ./grocap.sh [SECONDS] [PREFIX]
set -euo pipefail
SECS=${1:-3} PFX=${2:-gro}; HERE=$(cd "$(dirname "$0")" && pwd)
for dst in fd14::2 10.0.14.2; do
  fam=v4; [ "${dst#*:}" != "$dst" ] && fam=v6
  ip netns exec rcv python3 "$HERE/bulk.py" recv --once >/dev/null 2>&1 &
  ip netns exec rcv timeout $((SECS + 2)) tcpdump -i c0 -n -s 128 -c 5000 -w "$PFX-$fam.pcap" "tcp dst port 5014 and greater 1000" 2>/dev/null &
  sleep 0.5
  echo "flow: $fam $(ip netns exec snd python3 "$HERE/bulk.py" send --dst $dst --seconds "$SECS" | grep -o '"gbps": [0-9.]*')"
  wait
  python3 "$HERE/skblen.py" "$PFX-$fam.pcap"
done
