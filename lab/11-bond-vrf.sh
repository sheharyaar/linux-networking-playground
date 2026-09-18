#!/usr/bin/env bash
# Lab 11 — scenarios 10 and 11: a bond over two veth slaves, and a VRF with one enslaved veth.
# Topology:
#   bond:  pp-bond0 10.11.0.1  over slaves pp-s1 / pp-s2
#          peers pp-p1 / pp-p2 bridged by pp-pbr 10.11.0.2 inside netns pp-peer
#   vrf:   pp-vrf (table 10) enslaving pp-ve 10.12.0.1
#          peer pp-vp 10.12.0.2 inside netns pp-vpeer
source "$(dirname "$0")/lib.sh"
need_root; need ip curl
MODE="${BOND_MODE:-active-backup}"

case "${1:-}" in
up)
  # --- bond ---------------------------------------------------------------
  ns_add pp-peer
  veth_pair pp-s1 pp-p1
  veth_pair pp-s2 pp-p2
  move_to pp-peer pp-p1; move_to pp-peer pp-p2
  ip link add pp-bond0 type bond mode "$MODE" miimon 100
  ip link set pp-s1 down; ip link set pp-s2 down
  ip link set pp-s1 master pp-bond0; ip link set pp-s2 master pp-bond0
  ip addr add 10.11.0.1/24 dev pp-bond0
  ip link set pp-bond0 up; ip link set pp-s1 up; ip link set pp-s2 up
  ip -n pp-peer link add pp-pbr type bridge
  ip -n pp-peer link set pp-p1 master pp-pbr; ip -n pp-peer link set pp-p2 master pp-pbr
  ip -n pp-peer addr add 10.11.0.2/24 dev pp-pbr
  ip -n pp-peer link set pp-pbr up

  # --- vrf ----------------------------------------------------------------
  ns_add pp-vpeer
  ip link add pp-vrf type vrf table 10
  ip link set pp-vrf up
  ip route add table 10 unreachable default metric 4278198272 2>/dev/null || true
  veth_pair pp-ve pp-vp
  move_to pp-vpeer pp-vp
  ip link set pp-ve master pp-vrf
  ip addr add 10.12.0.1/24 dev pp-ve
  ip link set pp-ve up
  addr pp-vpeer pp-vp 10.12.0.2/24

  sleep 2
  banner "bond"
  grep -E 'Bonding Mode|Currently Active Slave|MII Status' /proc/net/bonding/pp-bond0 | head -4
  banner "vrf"
  ip -br link show master pp-vrf
  ip rule show | grep l3mdev
  ip route show table 10
  echo
  echo "traffic (bond): curl -s --max-time 2 http://10.11.0.2:9099/     # refused is fine, the SYN still crosses"
  echo "traffic (vrf):  ip vrf exec pp-vrf curl -s --max-time 2 http://10.12.0.2:9099/"
  ;;
down)
  link_del pp-bond0; link_del pp-s1; link_del pp-s2
  link_del pp-vrf;   link_del pp-ve
  ns_del pp-peer;    ns_del pp-vpeer
  ip route flush table 10 2>/dev/null || true
  ;;
trace)
  cat <<'T'
# bond: expect TWO __dev_queue_xmit lines for one skb, on pp-bond0 then on the slave,
# and on receive the device column flipping from the slave to pp-bond0 inside the core.
pwru --kmods bonding,veth,bridge --output-meta 'tcp and host 10.11.0.2'
curl -s --max-time 2 -o /dev/null http://10.11.0.2:9099/

# vrf: expect PRE_ROUTING twice on receive (once per device) and FOUR nf_hook_slow on output.
pwru --kmods vrf,veth --output-meta 'tcp and host 10.12.0.2'
ip vrf exec pp-vrf curl -s --max-time 2 -o /dev/null http://10.12.0.2:9099/

# bond_handle_frame is NOT printed by pwru: rx_handlers take struct sk_buff **pskb,
# so there is no skb argument for pwru to read. Same for br_handle_frame.
# Count the doubled hook with nftables instead:
nft add table inet pp \; add chain inet pp pre '{ type filter hook prerouting priority -150; }'
nft add rule inet pp pre counter
nft list chain inet pp pre        # counts 2 packets per received packet inside the VRF
nft delete table inet pp
T
  ;;
*) echo "usage: $0 up|down|trace    (BOND_MODE=balance-rr $0 up to change mode)"; exit 1 ;;
esac
