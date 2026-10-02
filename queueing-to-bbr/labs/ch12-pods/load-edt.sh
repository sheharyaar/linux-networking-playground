#!/usr/bin/env bash
# load-edt.sh: attach edt_lab.o (Cilium's EDT limiter, cut down) to rtr:r1 egress in a running
# rootless bench. Needs sudo: loading a BPF program is refused to normal users while
# kernel.unprivileged_bpf_disabled = 2, and the bench's own namespace cannot help, because the
# check is made against the first user namespace.
#
# 1. In the lab shell (../common/qnet.sh), leave a process in rtr so its netns can be found:
#        ip netns exec rtr sh -c 'echo $$ > rtr.pid; exec sleep 3600' &
# 2. As yourself, build the object (no sudo):
#        clang -O2 -g -target bpf -DRATE_BPS=1250000 -c edt_lab.bpf.c -o edt_lab.o
# 3. From another terminal, in this folder:
#        sudo ./load-edt.sh            attach (clsact on r1, the program at egress)
#        sudo ./load-edt.sh --show     dump the program's counters and r1's qdiscs
#        sudo ./load-edt.sh --off      remove it
# Root enters only the bench's network namespace (nsenter --net), so it keeps its capabilities
# in the first user namespace, which is what tc needs to load the program.
set -euo pipefail
cd "$(dirname "$0")"
[ -r rtr.pid ] || { echo "load-edt: no rtr.pid; run step 1 in the lab shell first" >&2; exit 1; }
NS=(nsenter --net=/proc/$(cat rtr.pid)/ns/net)
case "${1:-}" in
  --show) bpftool map dump name edt_state; "${NS[@]}" tc -s qdisc show dev r1; exit 0;;
  --off)  "${NS[@]}" tc qdisc del dev r1 clsact; echo "load-edt: removed"; exit 0;;
esac
[ -r edt_lab.o ] || { echo "load-edt: build edt_lab.o first (step 2)" >&2; exit 1; }
"${NS[@]}" tc qdisc replace dev r1 clsact
"${NS[@]}" tc filter replace dev r1 egress bpf direct-action obj edt_lab.o sec tc
"${NS[@]}" tc filter show dev r1 egress
