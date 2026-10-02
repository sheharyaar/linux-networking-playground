#!/usr/bin/env bash
# run-overload.sh: hold a UDP "pod" to 10 Mbit/s with Cilium's EDT arithmetic, then offer it more.
#
#   ../common/qnet.sh -- ./run-overload.sh [outdir]        (from labs/ch12-pods, no sudo)
#
# snd is the pod. Its packets cross the veth and the router, which takes their socket away at
# ip_rcv (net/ipv4/ip_input.c:580-583), as the host stack does without BPF host routing.
# rtr:r1 gets fq with the Bandwidth Manager's settings (horizon 2s, buckets 32768,
# pkg/datapath/linux/bandwidth/ops.go:141-149); flow_limit stays at fq's default, 100.
# Four runs of 8 s: under the limit; over it; over it with fq flow_limit 2000; over it with a
# 100 ms drop horizon. Then two runs with the fq on snd:s0 instead, where each skb still belongs
# to the sending socket while fq holds it (as with BPF host routing): default SO_SNDBUF, then 4 MB.
set -euo pipefail
OUT=${1:-.}
mkdir -p "$OUT"
cd "$(dirname "$0")"
uname -r
tc -n snd qdisc del dev s0 root
ip netns exec snd ping -c 1 -q 10.0.2.1 >/dev/null     # resolve the neighbours before timing anything

run() {   # name, fq flow_limit, podedt arguments...
  local name=$1 fl=$2; shift 2
  tc -n rtr qdisc del dev r1 root
  tc -n rtr qdisc add dev r1 root fq horizon 2s buckets 32768 flow_limit "$fl"
  echo "=== $name: fq flow_limit $fl; podedt.py $*"
  ip netns exec rcv python3 rxcount.py --seconds 16 --csv "$OUT/$name-rx.csv" & local rx=$!
  sleep 0.3
  ip netns exec snd python3 podedt.py --dst 10.0.2.1 "$@" --csv "$OUT/$name-tx.csv"
  wait $rx || true
  tc -n rtr -s qdisc show dev r1 | sed -n '2p;4,5p'
}
run under   100  --limit 10M --offer 8mbit  --seconds 8
run over    100  --limit 10M --offer 20mbit --seconds 8
run bigfq   2000 --limit 10M --offer 20mbit --seconds 8
run short   100  --limit 10M --offer 20mbit --seconds 8 --horizon-ms 100

runpod() {   # name, podedt arguments...: fq on the pod's own s0, nothing on r1
  local name=$1; shift
  tc -n rtr qdisc del dev r1 root 2>/dev/null || true
  tc -n snd qdisc del dev s0 root 2>/dev/null || true
  tc -n snd qdisc add dev s0 root fq horizon 2s buckets 32768
  echo "=== $name: fq on snd:s0 (socket still attached); podedt.py $*"
  ip netns exec rcv python3 rxcount.py --seconds 16 --csv "$OUT/$name-rx.csv" & local rx=$!
  sleep 0.3
  ip netns exec snd python3 podedt.py --dst 10.0.2.1 "$@" --csv "$OUT/$name-tx.csv"
  wait $rx || true
  tc -n snd -s qdisc show dev s0 | sed -n '2p;4,5p'
}
runpod kept     --limit 10M --offer 20mbit --seconds 8
runpod keptbig  --limit 10M --offer 20mbit --seconds 8 --sndbuf 4194304
