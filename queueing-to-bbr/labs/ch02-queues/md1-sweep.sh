#!/usr/bin/env bash
# md1-sweep.sh: Poisson UDP arrivals into netem's 10 Mbit/s bottleneck, one run per load.
#
#   ./md1-sweep.sh [--sizes fixed|exp] [--batch B] [--seconds 20] [--out DIR] [RHO ...]
#
# Builds the rootless bench (../common/qnet.sh) with a 1000-packet limit, so nothing is dropped,
# then for each load rho runs: qwatch on the bottleneck, the receiver, and the Poisson sender.
# Each run leaves DIR/<sizes>-<rho>.csv (per packet) and DIR/<sizes>-<rho>-q.csv (backlog),
# and appends one line to DIR/sweep-<sizes>.csv via summarise.py. Default loads: 0.1 to 0.95.
# --batch B sends each Poisson arrival as B back-to-back packets (files get a -bB suffix).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
SIZES=fixed BATCH=1 SECONDS_EACH=20 OUT=$here/out
while [ $# -gt 0 ]; do
  case "$1" in
    --sizes) SIZES=$2; shift 2;;
    --batch) BATCH=$2; shift 2;;
    --seconds) SECONDS_EACH=$2; shift 2;;
    --out) OUT=$2; shift 2;;
    -h|--help) sed -n '2,10p' "$0"; exit 0;;
    *) break;;
  esac
done
RHOS=${*:-0.1 0.3 0.5 0.7 0.8 0.9 0.95}
mkdir -p "$OUT"
if [ "${QNET_INSIDE:-}" != 1 ]; then
  exec "$here/../common/qnet.sh" --limit 1000 -- "$0" --sizes "$SIZES" --batch "$BATCH" --seconds "$SECONDS_EACH" --out "$OUT" $RHOS
fi
cd "$here/../common"
for rho in $RHOS; do
  tag=$SIZES; [ "$BATCH" != 1 ] && tag=$SIZES-b$BATCH
  f=$OUT/$tag-$rho
  ip netns exec rtr python3 qwatch.py --dev r1 --every 0.02 --seconds $((SECONDS_EACH + 2)) --csv "$f-q.csv" &
  ip netns exec rcv python3 "$here/poisson.py" recv --csv "$f.csv" --seconds $((SECONDS_EACH + 4)) &
  sleep 0.5
  ip netns exec snd python3 "$here/poisson.py" send --dst 10.0.2.1 --rho "$rho" --sizes "$SIZES" --batch "$BATCH" --seconds "$SECONDS_EACH"
  wait
  python3 "$here/summarise.py" "$f.csv" --q "$f-q.csv" --label "$tag-$rho" --out "$OUT/sweep-$tag.csv"
done
