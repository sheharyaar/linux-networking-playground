#!/usr/bin/env bash
# qnet.sh: a rootless three-namespace path, snd -> rtr -> rcv, with one bottleneck on rtr.
#
#   snd (10.0.1.1) --s0==r0-- rtr (10.0.1.2 | 10.0.2.2) --r1==c0-- rcv (10.0.2.1)
#
#   snd:s0 egress  netem delay $DELAY             (data, one way)
#   rtr:r1 egress  netem rate $RATE limit $LIMIT  (the bottleneck and its drop-tail queue)
#   rcv:c0 egress  netem delay $DELAY             (acks, the other way)
#
# usage:  qnet.sh [--rate 10mbit] [--delay 20ms] [--limit 50] [--keep-offloads] [-- command ...]
# With no command it opens $SHELL inside the lab. Everything disappears when that shell exits.
#
# No sudo needed: the script re-runs itself under `unshare --user --map-root-user --net --mount`,
# so you are root only inside a private user namespace. It mounts a private tmpfs on /run inside
# that namespace so `ip netns add` works; the host's /run is untouched.
set -euo pipefail
RATE=${RATE:-10mbit} DELAY=${DELAY:-20ms} LIMIT=${LIMIT:-50} OFFLOADS=${OFFLOADS:-off}
while [ $# -gt 0 ]; do
  case "$1" in
    --rate) RATE=$2; shift 2;;
    --delay) DELAY=$2; shift 2;;
    --limit) LIMIT=$2; shift 2;;
    --keep-offloads) OFFLOADS=on; shift;;
    --) shift; break;;
    -h|--help) sed -n '2,15p' "$0"; exit 0;;
    *) break;;
  esac
done

if [ "${QNET_INSIDE:-}" != 1 ]; then
  export QNET_INSIDE=1 RATE DELAY LIMIT OFFLOADS
  exec unshare --user --map-root-user --net --mount --propagation private "$0" -- "$@"
fi

mount -t tmpfs tmpfs /run && mkdir -p /run/netns
for ns in snd rtr rcv; do ip netns add $ns; ip -n $ns link set lo up; done
ip link add s0 netns snd type veth peer name r0 netns rtr
ip link add r1 netns rtr type veth peer name c0 netns rcv
ip -n snd addr add 10.0.1.1/24 dev s0
ip -n rtr addr add 10.0.1.2/24 dev r0
ip -n rtr addr add 10.0.2.2/24 dev r1
ip -n rcv addr add 10.0.2.1/24 dev c0
for pair in snd:s0 rtr:r0 rtr:r1 rcv:c0; do
  ns=${pair%%:*} dev=${pair##*:}
  ip -n $ns link set $dev up
  # one skb = one wire packet, so the bottleneck counts real packets
  [ "$OFFLOADS" = off ] && ip netns exec $ns ethtool -K $dev tso off gso off gro off >/dev/null 2>&1 || true
done
ip -n snd route add default via 10.0.1.2
ip -n rcv route add default via 10.0.2.2
ip netns exec rtr sysctl -qw net.ipv4.ip_forward=1
tc -n snd qdisc add dev s0 root netem delay $DELAY limit 100000
tc -n rcv qdisc add dev c0 root netem delay $DELAY limit 100000
tc -n rtr qdisc add dev r1 root handle 1: netem rate $RATE limit $LIMIT

echo "qnet: snd 10.0.1.1 -> rtr -> rcv 10.0.2.1 | bottleneck rtr:r1 netem rate $RATE limit $LIMIT | delay $DELAY each way | offloads $OFFLOADS" >&2
if [ $# -gt 0 ]; then exec "$@"; else exec "${SHELL:-bash}"; fi
