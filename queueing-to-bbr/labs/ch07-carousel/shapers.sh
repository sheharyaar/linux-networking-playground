#!/usr/bin/env bash
# shapers.sh: put one of three shapers on the qnet bench, for the Carousel chapter's lab.
# Run it inside a qnet.sh shell (it uses the snd, rtr and rcv namespaces).
#
#   ./shapers.sh htb-snd   16 flows each in its own HTB class at EACH, on snd:s0 (TCP small queues sees it);
#                          s0's 20 ms data delay moves to rtr:r1, which keeps no rate, so the shaper is the only queue
#   ./shapers.sh fq-snd    fq on snd:s0 with maxrate EACH for every flow; the delay moves as for htb-snd
#   ./shapers.sh htb-rtr   the same 16 HTB classes on rtr:r1, past the namespace boundary where
#                          TCP small queues cannot see; snd:s0 keeps qnet's netem delay
#
# Options through the environment: FLOWS (16), EACH (500kbit, the rate per flow), LEAF (100, the packet limit of each
# HTB class's pfifo), PORT (5001, flow i uses PORT+i). The empty-path RTT stays 40 ms in all three.
# ROUTER=qnet keeps qnet's 10 Mbit/s netem on r1 and moves s0's delay to the ack path instead (rcv:c0 40 ms);
# at 8 Mbit/s that hop then queues the classes' bursts and adds 15-35 ms of RTT (data/ackpath/).
set -euo pipefail
FLOWS=${FLOWS:-16} EACH=${EACH:-500kbit} LEAF=${LEAF:-100} PORT=${PORT:-5001}

htb() {            # htb NS DEV: one class per flow, matched on the TCP destination port
  local ns=$1 dev=$2
  tc -n $ns qdisc del dev $dev root 2>/dev/null || true
  tc -n $ns qdisc add dev $dev root handle 1: htb default 999
  for i in $(seq 0 $((FLOWS - 1))); do
    local cls=$((16#10 + i))
    tc -n $ns class add dev $dev parent 1: classid 1:$(printf %x $cls) htb rate $EACH ceil $EACH
    tc -n $ns qdisc add dev $dev parent 1:$(printf %x $cls) pfifo limit $LEAF
    tc -n $ns filter add dev $dev parent 1: protocol ip prio 1 u32 match ip dport $((PORT + i)) 0xffff flowid 1:$(printf %x $cls)
  done
}
move_delay() {     # free s0 for the shaper and keep the 40 ms RTT
  if [ "${ROUTER:-}" = qnet ]; then      # r1 stays netem rate 10mbit limit 50; the acks carry 40 ms
    tc -n rcv qdisc del dev c0 root
    tc -n rcv qdisc add dev c0 root netem delay 40ms limit 100000
  else                                   # r1 carries the 20 ms data delay and no rate (its delay line holds ~14 packets)
    tc -n rtr qdisc del dev r1 root
    tc -n rtr qdisc add dev r1 root netem delay 20ms limit 10000
  fi
}

case "${1:-}" in
  htb-snd) move_delay; htb snd s0 ;;
  fq-snd)  move_delay; tc -n snd qdisc del dev s0 root; tc -n snd qdisc add dev s0 root fq maxrate $EACH ;;
  htb-rtr) htb rtr r1 ;;
  *) sed -n '2,13p' "$0"; exit 1 ;;
esac
echo "shapers.sh: $1, $FLOWS flows at $EACH each" >&2
