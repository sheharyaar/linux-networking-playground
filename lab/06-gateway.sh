#!/usr/bin/env bash
# Lab 6 — scenario 4: a packet leaving towards the default gateway, with ARP resolution and a real qdisc.
# Uses the router topology from 05-router.sh: pp-c's default route points at 10.5.1.1 (r0 in pp-rt).
source "$(dirname "$0")/lib.sh"
need_root; need ip tc
C=pp-c

case "${1:-}" in
up)
  ip netns list | grep -q "^$C" || { echo "run 05-router.sh up first"; exit 1; }
  ip netns exec $C tc qdisc replace dev c0 root fq_codel
  ip netns exec $C ip neigh flush dev c0
  banner "client view"
  ip netns exec $C ip route get 10.5.2.2
  ip netns exec $C tc qdisc show dev c0
  echo "traffic:  ip netns exec $C curl -s -o /dev/null http://10.5.2.2:8080/"
  echo "after:    ip netns exec $C ip neigh show dev c0; ip netns exec $C tc -s qdisc show dev c0"
  ;;
down)
  ip netns exec $C tc qdisc del dev c0 root 2>/dev/null || true
  ;;
trace)
  cat <<'T'
# ARP and TCP together, client namespace only:
pwru --kmods veth --filter-netns /run/netns/pp-c 'arp or (tcp and port 8080)'
# on the host, the same shape towards your real gateway:
GW=$(ip route show default | awk '{print $3; exit}'); ip neigh flush dev wlan0
pwru "arp or (icmp and host $GW)" & sleep 5; ping -c1 $GW >/dev/null; wait
T
  ;;
*) echo "usage: $0 up|down|trace"; exit 1 ;;
esac
