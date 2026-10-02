#!/usr/bin/env bash
# matrix.sh: run inside ./bigpair.sh. Bulk flows over IPv6 and IPv4 at two skb limits, repeated.
#
#   ./bigpair.sh -- ./matrix.sh [REPS] [SECONDS] [OUT.jsonl]
#
# For each repetition: 2 s of idle baseline on the two pinned CPUs, then four 8 s flows in turn:
# IPv6 and IPv4, each at the kernel default (65536) and at BIG TCP's 185000. All four knobs are
# set on both ends before each flow (IPv6 knobs first). The sender runs on CPU $SND_CPU and the
# sink on CPU $RCV_CPU (taskset); both ends' softirq work lands on those two CPUs.
set -euo pipefail
REPS=${1:-5} SECS=${2:-8} OUT=${3:-veth-matrix.jsonl}
SND_CPU=${SND_CPU:-5} RCV_CPU=${RCV_CPU:-6}
HERE=$(cd "$(dirname "$0")" && pwd)

setsize() {   # setsize N: all four knobs on both ends
  for pair in snd:s0 rcv:c0; do
    ns=${pair%%:*} dev=${pair##*:}
    ip -n $ns link set $dev gso_max_size "$1" gro_max_size "$1"
    ip -n $ns link set $dev gso_ipv4_max_size "$1" gro_ipv4_max_size "$1"
  done
}
idle() {      # busy seconds of the two CPUs over 2 s with nothing of ours running
  python3 - "$SND_CPU" "$RCV_CPU" <<'EOF'
import sys, time, os, json
hz = os.sysconf('SC_CLK_TCK'); cpus = ['cpu' + c for c in sys.argv[1:]]
def st():
    r = {}
    for l in open('/proc/stat'):
        if not l.startswith('cpu'): break
        f = l.split(); v = list(map(int, f[1:9])); r[f[0]] = v[0] + v[1] + v[2] + v[5] + v[6] + v[7]
    return r
a = st(); time.sleep(2); b = st()
print(json.dumps({'role': 'idle', 'cpus_busy_s': sum(b[c] - a[c] for c in cpus) / hz, 'seconds': 2}))
EOF
}

: > "$OUT"
for rep in $(seq 1 "$REPS"); do
  echo "{\"rep\": $rep, $(idle | cut -c2-)" >> "$OUT"
  for size in 65536 185000; do
    for dst in fd14::2 10.0.14.2; do
      setsize $size
      ip netns exec rcv taskset -c "$RCV_CPU" python3 "$HERE/bulk.py" recv --once > /tmp/bulk-recv.$$ 2>/dev/null &
      sleep 0.4
      s=$(ip netns exec snd taskset -c "$SND_CPU" python3 "$HERE/bulk.py" send --dst $dst --seconds "$SECS" --cpus "$SND_CPU,$RCV_CPU")
      wait
      r=$(cat /tmp/bulk-recv.$$)
      echo "{\"rep\": $rep, \"size\": $size, $(echo "$s" | cut -c2- | sed 's/}$//'), \"recv_utime_s\": $(echo "$r" | python3 -c 'import json,sys; print(json.load(sys.stdin)["utime_s"])'), \"recv_stime_s\": $(echo "$r" | python3 -c 'import json,sys; print(json.load(sys.stdin)["stime_s"])')}" >> "$OUT"
      tail -1 "$OUT" >&2
    done
  done
done
rm -f /tmp/bulk-recv.$$
