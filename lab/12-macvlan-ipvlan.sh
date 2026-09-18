#!/usr/bin/env bash
# Lab 12 — scenario 12: macvlan and ipvlan on veth lower devices.
# Two lower devices are needed on purpose: a device has ONE rx_handler slot, so a
# macvlan and an ipvlan cannot share a lower device (netdev_rx_handler_register
# returns -EBUSY, net/core/dev.c:5913).
# Topology:
#   pp-lo0 <-> pp-lo1 (netns pp-sw, 10.13.0.9)   macvlan pp-mv0 10.13.0.1 mode bridge
#   pp-lo2 <-> pp-lo3 (netns pp-sw, 10.14.0.9)   ipvlan  pp-iv0 10.14.0.2 mode l2
# Set LOWER=<ifname> to build on a real interface instead. On a wireless interface the
# macvlan will be created and will then silently fail: the access point drops frames whose
# source MAC it has not associated. That is the lesson, not a broken lab.
source "$(dirname "$0")/lib.sh"
need_root; need ip curl
MV_MODE="${MV_MODE:-bridge}"
IV_MODE="${IV_MODE:-l2}"

case "${1:-}" in
up)
  ns_add pp-sw
  veth_pair pp-lo0 pp-lo1
  veth_pair pp-lo2 pp-lo3
  move_to pp-sw pp-lo1; move_to pp-sw pp-lo3
  ip link set pp-lo0 up; ip link set pp-lo2 up
  addr pp-sw pp-lo1 10.13.0.9/24
  addr pp-sw pp-lo3 10.14.0.9/24

  ip link add pp-mv0 link pp-lo0 type macvlan mode "$MV_MODE"
  ip addr add 10.13.0.1/24 dev pp-mv0
  ip link set pp-mv0 up

  ip link add pp-iv0 link pp-lo2 type ipvlan mode "$IV_MODE"
  ip addr add 10.14.0.2/24 dev pp-iv0
  ip link set pp-iv0 up

  banner "the whole difference, before any traffic"
  printf 'lower pp-lo0 %s  (macvlan lower)\n' "$(ip -br link show pp-lo0 | awk '{print $3}')"
  printf 'macvlan      %s  <- its own address\n' "$(ip -br link show pp-mv0 | awk '{print $3}')"
  printf 'lower pp-lo2 %s  (ipvlan lower)\n'  "$(ip -br link show pp-lo2 | awk '{print $3}')"
  printf 'ipvlan       %s  <- the same address as its lower\n' "$(ip -br link show pp-iv0 | awk '{print $3}')"
  echo
  ip -d link show pp-lo0 | sed -n 2p | grep -o 'promiscuity [0-9]*' | sed 's/^/pp-lo0 /'
  ip -d link show pp-lo2 | sed -n 2p | grep -o 'promiscuity [0-9]*' | sed 's/^/pp-lo2 /'
  echo
  echo "one handler slot per device, try it:  ip link add pp-x link pp-lo0 type ipvlan mode l2"
  echo "traffic (macvlan): ip netns exec pp-sw curl -s --max-time 2 http://10.13.0.1:9099/"
  echo "traffic (ipvlan):  ip netns exec pp-sw curl -s --max-time 2 http://10.14.0.2:9099/"
  ;;
down)
  link_del pp-mv0; link_del pp-iv0
  link_del pp-lo0; link_del pp-lo2
  ns_del pp-sw
  ;;
trace)
  cat <<'T'
# The two receive paths are identical except for ONE line. Run both and diff them.
pwru --kmods macvlan,ipvlan,veth --output-meta 'tcp and (host 10.13.0.1 or host 10.14.0.2)'
ip netns exec pp-sw curl -s --max-time 2 -o /dev/null http://10.13.0.1:9099/
ip netns exec pp-sw curl -s --max-time 2 -o /dev/null http://10.14.0.2:9099/
# expect, on the lower device, just before the device column changes:
#   macvlan_forward_source[macvlan]   <- keyed by destination MAC
#   ipvlan_get_L3_hdr[ipvlan]         <- keyed by destination IP
# macvlan_handle_frame and ipvlan_handle_frame are NOT printed: rx_handlers take
# struct sk_buff **pskb, so pwru has no skb argument to read.

# ipvlan l3 mode moves the route lookup and output chains to the parent:
MV_MODE=bridge IV_MODE=l3 ./12-macvlan-ipvlan.sh up
# ipvlan l3s mode swaps the device in a LOCAL_IN hook instead of the rx_handler:
MV_MODE=bridge IV_MODE=l3s ./12-macvlan-ipvlan.sh up
T
  ;;
*) echo "usage: $0 up|down|trace    (MV_MODE=private|vepa|bridge|passthru  IV_MODE=l2|l3|l3s)"; exit 1 ;;
esac
