#!/usr/bin/env bash
# Labs 4 and 5 — a three-namespace router: PREROUTING, routing decision, FORWARD, POSTROUTING, conntrack, NAT.
# Topology:  [ns pp-c] c0 10.5.1.2 --- r0 10.5.1.1 [ns pp-rt, ip_forward=1] r1 10.5.2.1 --- s0 10.5.2.2 [ns pp-s]
# The router namespace carries an nftables table with nftrace on, conntrack, and a masquerade rule you can toggle.
source "$(dirname "$0")/lib.sh"
need_root; need ip nft
C=pp-c; RT=pp-rt; S=pp-s

case "${1:-}" in
up)
  ns_add $C; ns_add $RT; ns_add $S
  veth_pair c0 r0; veth_pair s0 r1
  move_to $C c0; move_to $RT r0; move_to $S s0; move_to $RT r1
  addr $C c0 10.5.1.2/24; addr $RT r0 10.5.1.1/24
  addr $S s0 10.5.2.2/24; addr $RT r1 10.5.2.1/24
  ip -n $C route add default via 10.5.1.1
  ip -n $S route add default via 10.5.2.1
  ns_exec $RT sysctl -qw net.ipv4.ip_forward=1
  ns_exec $RT nft -f - <<'NFT'
table inet lab {
  chain rawpre { type filter hook prerouting priority raw; policy accept;
    ip saddr 10.5.1.2 meta nftrace set 1
  }
  chain prerouting { type filter hook prerouting  priority filter; policy accept; }
  chain forward { type filter hook forward     priority filter; policy accept;
    ct state new counter comment "first packet of each flow"
    ct state established,related counter comment "everything after"
  }
  chain postrouting { type filter hook postrouting priority filter; policy accept; }
  chain input { type filter hook input       priority filter; policy accept; }
  chain output { type filter hook output      priority filter; policy accept; }
  chain natpost { type nat hook postrouting priority srcnat; policy accept;
    # uncomment to turn the router into a NAT box for chapter 5:
    # oifname "r1" masquerade
  }
}
NFT
  banner "topology"
  ip -n $RT -br addr show
  echo "traffic:   ip netns exec $C curl -s http://10.5.2.2:8080/ >/dev/null   (server: ip netns exec $S python3 -m http.server 8080 --bind 10.5.2.2 &)"
  echo "counters:  ip netns exec $RT nft list chain inet lab forward"
  echo "conntrack: ip netns exec $RT conntrack -L   (or: ip netns exec $RT cat /proc/net/nf_conntrack)"
  echo "nat on:    ip netns exec $RT nft add rule inet lab natpost oifname r1 masquerade"
  ;;
down)
  ns_del $C; ns_del $RT; ns_del $S
  ;;
trace)
  cat <<'T'
# terminal 1 — kernel functions inside the router namespace only:
pwru --output-tuple --output-meta --filter-netns /run/netns/pp-rt 'tcp and port 8080'
# terminal 2 — the nftables rule walk for the same packets:
ip netns exec pp-rt nft monitor trace
# terminal 3:
ip netns exec pp-c curl -s http://10.5.2.2:8080/ >/dev/null
T
  ;;
*) echo "usage: $0 up|down|trace"; exit 1 ;;
esac
