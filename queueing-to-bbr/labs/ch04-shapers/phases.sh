#!/usr/bin/env bash
# phases.sh: two bulk flows through the bench's router, one per customer, with staggered starts.
# Run it inside ../common/qnet.sh AFTER you have built your HTB tree on rtr:r1.
#
#   bash phases.sh [--tag run] [--a 40] [--b-start 10] [--b 20] [--cc reno]
#
# Flow A goes to 10.0.2.1:5001 for --a seconds; flow B goes to 10.0.2.1:5002 for --b seconds,
# starting --b-start seconds after A (--b 0: flow A only). While they run, cwatch.py samples every class on rtr:r1.
# Output: TAG-a.csv, TAG-b.csv (flow.py rows), TAG-classes.csv (cwatch.py rows),
# TAG-class-end.txt (tc -s class show at the end), and per-phase goodput on stderr.
set -euo pipefail
TAG=run A=40 BSTART=10 B=20 CC=reno
while [ $# -gt 0 ]; do
  case "$1" in
    --tag) TAG=$2; shift 2;; --a) A=$2; shift 2;; --b-start) BSTART=$2; shift 2;;
    --b) B=$2; shift 2;; --cc) CC=$2; shift 2;; *) echo "unknown option $1" >&2; exit 1;;
  esac
done
here=$(cd "$(dirname "$0")" && pwd)
ip netns exec rcv python3 "$here/flow.py" recv --port 5001 --once &
[ "$B" != 0 ] && ip netns exec rcv python3 "$here/flow.py" recv --port 5002 --once &
sleep 0.5
ip netns exec rtr python3 "$here/cwatch.py" --dev r1 --seconds "$A" --csv "$TAG-classes.csv" &
ip netns exec snd python3 "$here/flow.py" send --dst 10.0.2.1 --port 5001 --cc "$CC" --seconds "$A" --csv "$TAG-a.csv" &
if [ "$B" != 0 ]; then
  sleep "$BSTART"
  ip netns exec snd python3 "$here/flow.py" send --dst 10.0.2.1 --port 5002 --cc "$CC" --seconds "$B" --csv "$TAG-b.csv" &
fi
wait
tc -n rtr -s class show dev r1 > "$TAG-class-end.txt"
files="$TAG-a.csv"; [ "$B" != 0 ] && files="$files $TAG-b.csv"
if [ "$B" != 0 ]; then
  python3 "$here/goodput.py" $files --bin 1 --csv "$TAG-goodput.csv" \
    --phase "A-alone:2:$BSTART" --phase "both:$((BSTART + 2)):$((BSTART + B))" \
    --phase "A-alone-again:$((BSTART + B + 2)):$A"
else
  python3 "$here/goodput.py" $files --bin 1 --csv "$TAG-goodput.csv" --phase "A-alone:2:$A"
fi
