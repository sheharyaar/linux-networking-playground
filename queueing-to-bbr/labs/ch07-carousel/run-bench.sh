#!/usr/bin/env bash
# run-bench.sh: the Carousel chapter's three shaper runs, each on a fresh qnet bench.
#   ./run-bench.sh [OUTDIR]     (default: data/)   about 2 minutes; no sudo
# For each shaper it builds the bench, runs shapers.sh, starts 16 flows for 30 s, samples the
# shaper's qdisc every 50 ms, and saves flows.csv, qdisc.csv and the tc -s output 20 s in.
set -euo pipefail
cd "$(dirname "$0")"
OUT=${1:-data}; mkdir -p "$OUT"
for kind in htb-snd fq-snd htb-rtr; do
  case $kind in htb-rtr) where="rtr r1";; *) where="snd s0";; esac
  ../common/qnet.sh -- bash -c "
    set -e
    ./shapers.sh $kind
    ip netns exec rcv python3 mflow.py recv --flows 16 &
    sleep 0.5
    set -- $where
    ip netns exec \$1 python3 qwatch.py --dev \$2 --every 0.05 --seconds 31 --csv $OUT/$kind-qdisc.csv &
    ( sleep 20; tc -n \$1 -s qdisc show dev \$2 | head -12 > $OUT/$kind-tc-at20s.txt
      [ $kind = fq-snd ] || tc -n \$1 -s class show dev \$2 | head -8 >> $OUT/$kind-tc-at20s.txt ) &
    ip netns exec snd python3 mflow.py send --dst 10.0.2.1 --flows 16 --seconds 30 --csv $OUT/$kind-flows.csv 2>&1 | tee $OUT/$kind-summary.txt
    wait
  "
done
