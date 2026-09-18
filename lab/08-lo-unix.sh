#!/usr/bin/env bash
# Lab 8 — scenarios 1, 2, 3 and 8: two programs on one host over lo, two addresses on two interfaces, and unix sockets.
source "$(dirname "$0")/lib.sh"
need_root; need ip python3 curl

case "${1:-}" in
up)
  ip link add pp-dummy0 type dummy 2>/dev/null || true
  ip addr replace 10.8.0.1/32 dev pp-dummy0; ip link set pp-dummy0 up
  cd /tmp && nohup python3 -m http.server 8082 --bind 0.0.0.0 >/tmp/pp-lo-http.log 2>&1 &
  sleep 1
  MAIN=$(ip -4 -o addr show scope global | awk '!/pp-dummy0|docker|br-|veth|cilium/ {print $4; exit}' | cut -d/ -f1)
  banner "two addresses on two interfaces: $MAIN and 10.8.0.1 (pp-dummy0)"
  ip route get 10.8.0.1 from "$MAIN"
  echo "traffic:  curl --interface $MAIN -s -o /dev/null http://10.8.0.1:8082/     # both addresses local: goes via lo"
  echo "traffic:  curl -s -o /dev/null http://127.0.0.1:8082/"
  echo "unix:     python3 $(dirname "$0")/unix_pair.py"
  ;;
down)
  pkill -f 'http.server 8082' || true
  link_del pp-dummy0
  ;;
trace)
  cat <<'T'
# lo: the interface column says lo for both halves, the netns never changes
pwru 'tcp and port 8082'
# unix sockets carry no IP header, so pwru cannot filter them; use bpftrace on the unix functions:
bpftrace -e '
kprobe:unix_stream_sendmsg { printf("%-16s sendmsg %d bytes\n", comm, ((struct msghdr *)arg1)->msg_iter.count); }
kretprobe:sock_alloc_send_pskb /comm == "python3"/ { printf("%-16s skb allocated %p\n", comm, retval); }
kprobe:unix_stream_read_generic { printf("%-16s recvmsg\n", comm); }
kprobe:ip_rcv, kprobe:__netif_rx, kprobe:nf_hook_slow /comm == "python3"/ { printf("!! %s ran for python3\n", probe); }'
# or with ftrace, no pid filter, one second, then keep the python3 lines:
cd /sys/kernel/tracing; for f in unix_stream_sendmsg sock_alloc_send_pskb skb_queue_tail sock_def_readable unix_stream_read_generic ip_rcv __netif_rx nf_hook_slow; do echo $f >> set_ftrace_filter; done
echo function > current_tracer; python3 lab/unix_pair.py; echo nop > current_tracer; grep python3 trace; echo > set_ftrace_filter
T
  ;;
*) echo "usage: $0 up|down|trace"; exit 1 ;;
esac
