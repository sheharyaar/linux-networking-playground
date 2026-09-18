#!/usr/bin/env bash
# Lab 7 — the socket as a file, the three TCP queues, and UDP overflow. Uses the veth topology from 09-veth.sh.
source "$(dirname "$0")/lib.sh"
need_root; need ip ss nstat python3

case "${1:-}" in
up)
  ip netns list | grep -q "^pp-b" || { echo "run 09-veth.sh up first"; exit 1; }
  ip netns exec pp-b sh -c 'cd /tmp && nohup python3 -m http.server 8080 --bind 10.9.0.2 >/tmp/pp-b-http.log 2>&1 &'
  sleep 1
  SRV=$(pgrep -f 'http.server 8080 --bind 10.9.0.2' | head -1)
  banner "the listening socket as a file (pid $SRV)"
  ls -l /proc/$SRV/fd | grep socket
  ip netns exec pp-b ss -tlnpm
  ;;
down)
  pkill -f 'http.server 8080 --bind 10.9.0.2' || true
  pkill -f 'SOCK_DGRAM.*9000' || true
  ;;
tcp)
  banner "200 requests; count which queue each segment took (bpftrace, ten seconds)"
  ( ip netns exec pp-a sh -c 'sleep 1; for i in $(seq 200); do curl -s -o /dev/null http://10.9.0.2:8080/; done' & )
  bpftrace -e '
kprobe:tcp_v4_do_rcv     { @direct  = count(); }
kprobe:tcp_add_backlog   { @backlog = count(); }
kprobe:sock_def_readable { @wakeups = count(); }
interval:s:10 { exit(); }'
  ;;
udp)
  banner "a UDP reader that never reads, a sender that floods, then the drop counter"
  ip netns exec pp-b python3 -c 'import socket,time; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.bind(("10.9.0.2",9000)); time.sleep(20)' &
  sleep 0.5
  ip netns exec pp-a python3 -c 'import socket; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); [s.sendto(b"x"*1400,("10.9.0.2",9000)) for _ in range(5000)]'
  ip netns exec pp-b nstat -az UdpRcvbufErrors
  ip netns exec pp-b ss -unpm | grep -A1 9000
  ;;
*) echo "usage: $0 up|down|tcp|udp"; exit 1 ;;
esac
