#!/usr/bin/env bash
# Lab 13 — scenario 9: IPVS masquerading, a virtual service over two real servers.
# HOST LAB, not run on the dossier bench: ipvsadm was not installed and installing it was
# out of scope, so chapter 13's transcript is labelled expected. The ip_vs module itself
# does load on kernel 7.2.
# Topology:
#   pp-ipvs0 (dummy)  10.15.0.100   the virtual address, local, nothing listening on it
#   pp-rs         10.15.0.1/24  <-veth->  pp-r1 10.15.0.11 (netns pp-rs1)
#                                <-veth->  pp-r2 10.15.0.12 (netns pp-rs2)   via bridge pp-rsbr
source "$(dirname "$0")/lib.sh"
need_root; need ip ipvsadm curl
VIP=10.15.0.100
SCHED="${SCHED:-rr}"

case "${1:-}" in
up)
  modprobe ip_vs; modprobe "ip_vs_${SCHED}"
  # the virtual address must be LOCAL or the routing decision never returns RTN_LOCAL
  ip link add pp-ipvs0 type dummy
  ip addr add "$VIP/32" dev pp-ipvs0
  ip link set pp-ipvs0 up

  ip link add pp-rsbr type bridge
  ip addr add 10.15.0.1/24 dev pp-rsbr
  ip link set pp-rsbr up
  for n in 1 2; do
    ns_add "pp-rs$n"
    veth_pair "pp-b$n" "pp-r$n"
    ip link set "pp-b$n" master pp-rsbr
    ip link set "pp-b$n" up
    move_to "pp-rs$n" "pp-r$n"
    addr "pp-rs$n" "pp-r$n" "10.15.0.1$n/24"
    ip netns exec "pp-rs$n" ip route add default via 10.15.0.1
    ip netns exec "pp-rs$n" sh -c "cd /tmp && nohup python3 -m http.server 80 --bind 10.15.0.1$n >/tmp/pp-rs$n.log 2>&1 &"
  done
  sysctl -q -w net.ipv4.ip_forward=1

  ipvsadm -A -t "$VIP:80" -s "$SCHED"
  ipvsadm -a -t "$VIP:80" -r 10.15.0.11:80 -m      # -m = masquerade
  ipvsadm -a -t "$VIP:80" -r 10.15.0.12:80 -m

  banner "virtual service"
  ipvsadm -Ln
  banner "the routing decision this chapter depends on"
  ip route get "$VIP"
  echo "traffic:  curl -s --max-time 2 http://$VIP/     # round-robins over the two real servers"
  echo "note:     ss -tln shows NOTHING on $VIP. Nothing listens; IPVS takes the packet in LOCAL_IN."
  ;;
down)
  ipvsadm -D -t "$VIP:80" 2>/dev/null || true
  for n in 1 2; do ns_del "pp-rs$n"; link_del "pp-b$n"; done
  link_del pp-rsbr; link_del pp-ipvs0
  ;;
trace)
  cat <<'T'
# Expect: LOCAL_IN, then the ip_vs functions, then LOCAL_OUT and POST_ROUTING,
# and NO tcp_v4_rcv anywhere, because no socket is ever consulted.
pwru --kmods ip_vs --output-meta 'tcp and host 10.15.0.100'
curl -s --max-time 2 -o /dev/null http://10.15.0.100/

# the connection table: one ip_vs_conn per client connection, with the chosen real server
ipvsadm -Lnc
# per-service and per-real-server counters
ipvsadm -Ln --stats

# the scheduler is consulted once per connection, not once per packet:
# open one connection, send many requests, and watch ActiveConn stay at 1.
curl -s --max-time 5 -o /dev/null http://10.15.0.100/ --keepalive-time 5 --next http://10.15.0.100/

# conntrack is bypassed by default (ip_vs_notrack). Turn it on and compare:
sysctl -w net.ipv4.vs.conntrack=1
conntrack -L | grep 10.15.0.100
T
  ;;
*) echo "usage: $0 up|down|trace    (SCHED=rr|wrr|lc|wlc $0 up)"; exit 1 ;;
esac
