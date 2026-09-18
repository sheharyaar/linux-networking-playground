#!/usr/bin/env bash
# Lab 9 — one veth pair, two network namespaces (scenario 5).
# Topology:  [ns pp-a] va 10.9.0.1 <----veth----> vb 10.9.0.2 [ns pp-b]
source "$(dirname "$0")/lib.sh"
need_root; need ip
A=pp-a; B=pp-b

case "${1:-}" in
up)
  ns_add $A; ns_add $B
  veth_pair va vb
  move_to $A va; move_to $B vb
  addr $A va 10.9.0.1/24; addr $B vb 10.9.0.2/24
  banner "topology"
  ip -n $A -br addr show va; ip -n $B -br addr show vb
  echo "traffic:  ip netns exec $A ping -c1 -W1 10.9.0.2"
  echo "gro mode: ip netns exec $B ethtool -K vb gro on     # flips the peer into NAPI mode (chapter 9)"
  ;;
down)
  ns_del $A; ns_del $B
  ;;
trace)
  cat <<'T'
# terminal 1 — every function the ICMP echo request and reply visit, both namespaces:
pwru --output-tuple --output-meta 'icmp and host 10.9.0.2'
# terminal 1 alternative — only what happens inside pp-b:
pwru --output-tuple --filter-netns /run/netns/pp-b 'icmp'
# terminal 2:
ip netns exec pp-a ping -c1 -W1 10.9.0.2
T
  ;;
*) echo "usage: $0 up|down|trace"; exit 1 ;;
esac
