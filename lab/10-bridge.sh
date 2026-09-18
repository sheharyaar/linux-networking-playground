#!/usr/bin/env bash
# Lab 10 — two veth pairs joined by a Linux bridge (scenario 6).
# Topology:  [ns pp-l] vl 10.10.0.1 --- vl-br [br0 in root ns] vr-br --- vr 10.10.0.2 [ns pp-r]
# Optional:  br_netfilter, so IP hooks run for bridged frames (chapter 10, second half).
source "$(dirname "$0")/lib.sh"
need_root; need ip bridge
L=pp-l; R=pp-r; BR=pp-br0

case "${1:-}" in
up)
  ns_add $L; ns_add $R
  ip link add $BR type bridge
  ip link set $BR up
  veth_pair vl vl-br; veth_pair vr vr-br
  move_to $L vl; move_to $R vr
  ip link set vl-br master $BR up; ip link set vr-br master $BR up
  addr $L vl 10.10.0.1/24; addr $R vr 10.10.0.2/24
  banner "topology"
  bridge link show | grep $BR
  echo "traffic:   ip netns exec $L curl -s http://10.10.0.2:8080/ >/dev/null   (start a server first: ip netns exec $R python3 -m http.server 8080 --bind 10.10.0.2 &)"
  echo "fdb:       bridge fdb show br $BR | grep -v permanent"
  echo "brnf on:   modprobe br_netfilter; sysctl -w net.bridge.bridge-nf-call-iptables=1"
  echo "brnf off:  sysctl -w net.bridge.bridge-nf-call-iptables=0"
  ;;
down)
  ns_del $L; ns_del $R; link_del $BR
  ;;
trace)
  cat <<'T'
# terminal 1 — the bridge path. Note --filter-track-skb-by-stackid: the bridge may clone for flooding.
pwru --output-tuple --output-meta --filter-track-skb-by-stackid 'tcp and host 10.10.0.2 and port 8080'
# terminal 1 alternative — watch the IP hooks appear once br_netfilter is on:
nft add table bridge t; nft add chain bridge t pre '{ type filter hook prerouting priority -300; }'; nft add rule bridge t pre meta nftrace set 1
nft monitor trace
# terminal 2:
ip netns exec pp-l curl -s http://10.10.0.2:8080/ >/dev/null
T
  ;;
*) echo "usage: $0 up|down|trace"; exit 1 ;;
esac
