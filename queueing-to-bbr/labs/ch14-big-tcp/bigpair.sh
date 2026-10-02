#!/usr/bin/env bash
# bigpair.sh: two namespaces joined by one veth pair, offloads ON, IPv4 and IPv6, no bottleneck.
#
#   snd (10.0.14.1, fd14::1) --s0==c0-- rcv (10.0.14.2, fd14::2)      MTU 1500 on both ends
#
# usage:  bigpair.sh [--size N] [--gro-path] [--rate R] [-- command ...]
#   --size N    set gso_max_size, gro_max_size, gso_ipv4_max_size and gro_ipv4_max_size to N
#               on both ends (default: leave the kernel's 65536)
#   --gro-path  make the receiver's skbs come from GRO: s0 segments in software (tso off), and c0
#               runs NAPI GRO (gro on). Without it, the sender's GSO skb crosses the veth whole.
#   --rate R    put `tbf rate R` on s0, a slow sender (use it with --gro-path)
# With no command it opens $SHELL inside the lab. Everything disappears when that shell exits.
#
# No sudo needed: like ../common/qnet.sh, the script re-runs itself under
# `unshare --user --map-root-user --net --mount`, so you are root only inside a private user
# namespace, which owns the two network namespaces. That is enough for every `ip link set` here.
set -euo pipefail
SIZE=${SIZE:-} GROPATH=${GROPATH:-0} RATE=${RATE:-}
while [ $# -gt 0 ]; do
  case "$1" in
    --size) SIZE=$2; shift 2;;
    --gro-path) GROPATH=1; shift;;
    --rate) RATE=$2; shift 2;;
    --) shift; break;;
    -h|--help) sed -n '2,17p' "$0"; exit 0;;
    *) break;;
  esac
done

if [ "${BIGPAIR_INSIDE:-}" != 1 ]; then
  export BIGPAIR_INSIDE=1 SIZE GROPATH RATE
  exec unshare --user --map-root-user --net --mount --propagation private "$0" -- "$@"
fi

mount -t tmpfs tmpfs /run && mkdir -p /run/netns
for ns in snd rcv; do ip netns add $ns; ip -n $ns link set lo up; done
ip link add s0 netns snd type veth peer name c0 netns rcv
ip -n snd addr add 10.0.14.1/24 dev s0
ip -n rcv addr add 10.0.14.2/24 dev c0
ip -n snd addr add fd14::1/64 dev s0 nodad
ip -n rcv addr add fd14::2/64 dev c0 nodad
if [ -n "$SIZE" ]; then
  # IPv6 knobs first: a gso_max_size of 65536 or less also rewrites gso_ipv4_max_size
  ip -n snd link set s0 gso_max_size "$SIZE" gro_max_size "$SIZE"
  ip -n rcv link set c0 gso_max_size "$SIZE" gro_max_size "$SIZE"
  ip -n snd link set s0 gso_ipv4_max_size "$SIZE" gro_ipv4_max_size "$SIZE"
  ip -n rcv link set c0 gso_ipv4_max_size "$SIZE" gro_ipv4_max_size "$SIZE"
fi
if [ "$GROPATH" = 1 ]; then
  ip netns exec snd ethtool -K s0 tso off >/dev/null
  ip netns exec rcv ethtool -K c0 gro on >/dev/null
fi
ip -n snd link set s0 up
ip -n rcv link set c0 up
[ -n "$RATE" ] && tc -n snd qdisc add dev s0 root tbf rate "$RATE" burst 15140 latency 50ms

for pair in snd:s0 rcv:c0; do
  ns=${pair%%:*} dev=${pair##*:}
  echo "bigpair: $ns:$dev $(ip -n $ns -d link show dev $dev | grep -o 'gso_max_size [0-9]*\|gro_max_size [0-9]*\|gso_ipv4_max_size [0-9]*\|gro_ipv4_max_size [0-9]*' | tr '\n' ' ')" >&2
done
echo "bigpair: snd 10.0.14.1 fd14::1 -> rcv 10.0.14.2 fd14::2 | gro-path $GROPATH | rate ${RATE:-none}" >&2
if [ $# -gt 0 ]; then exec "$@"; else exec "${SHELL:-bash}"; fi
