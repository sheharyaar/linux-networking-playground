#!/usr/bin/env bash
# Shared helpers for the packet-path labs. Source this; do not run it.
# Every lab script takes one argument: up | down | trace. `up` builds the
# topology, `down` removes everything it built, `trace` prints the tracer
# command lines to run in a second terminal while you generate traffic.

set -euo pipefail

need_root() {
  if [ "$(id -u)" -ne 0 ]; then
    echo "run as root: sudo $0 $*" >&2
    exit 1
  fi
}

have() { command -v "$1" >/dev/null 2>&1; }

need() {
  local missing=0
  for t in "$@"; do
    if ! have "$t"; then echo "missing tool: $t" >&2; missing=1; fi
  done
  [ "$missing" -eq 0 ] || exit 1
}

# ns_exec NAME cmd...  — run inside a named network namespace
ns_exec() { ip netns exec "$@"; }

# ns_add NAME  — create a namespace with lo up
ns_add() {
  ip netns add "$1"
  ip -n "$1" link set lo up
}

# ns_del NAME  — remove a namespace if it exists
ns_del() { ip netns del "$1" 2>/dev/null || true; }

# link_del NAME — remove a link if it exists
link_del() { ip link del "$1" 2>/dev/null || true; }

# veth_pair A B  — create a veth pair with those names in the current namespace
veth_pair() { ip link add "$1" type veth peer name "$2"; }

# move_to NS LINK — move a link into a namespace and bring it up
move_to() { ip link set "$2" netns "$1"; ip -n "$1" link set "$2" up; }

# addr NS LINK CIDR — assign an address inside a namespace
addr() { ip -n "$1" addr add "$3" dev "$2"; }

banner() { printf '\n== %s ==\n' "$*"; }

show_trace_hint() {
  cat <<'HINT'

Tracer cheat sheet (run each in its own terminal, as root):
  pwru --output-tuple --output-meta 'FILTER'        # every kernel function the skb visits
  pwru --output-tuple --filter-netns /run/netns/NS   # restrict to one namespace
  nft monitor trace                                  # netfilter rule walk, needs a rule with 'meta nftrace set 1'
  bpftrace -e 'kprobe:FUNC { printf("%s %s\n", comm, kstack(4)); }'
HINT
}
