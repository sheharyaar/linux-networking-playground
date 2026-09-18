#!/usr/bin/env bash
# Confirms the machine can run the labs. Read-only.
source "$(dirname "$0")/lib.sh"

banner "kernel"
uname -r
[ -r /sys/kernel/btf/vmlinux ] && echo "BTF: present" || echo "BTF: MISSING (pwru and bpftrace need CONFIG_DEBUG_INFO_BTF)"

banner "tools"
for t in ip tc bridge nft tcpdump ss ethtool pwru bpftrace bpftool perf ipvsadm conntrack python3 curl docker kind kubectl cilium; do
  printf '%-10s %s\n' "$t" "$(command -v "$t" 2>/dev/null || echo '-')"
done

banner "modules available"
for m in veth bridge br_netfilter bonding vrf macvlan ipvlan ip_vs dummy vxlan geneve nf_conntrack nft_log xt_TRACE; do
  printf '%-14s %s\n' "$m" "$(modinfo -F filename "$m" 2>/dev/null >/dev/null && echo yes || echo MISSING)"
done

banner "tracefs"
if [ -r /sys/kernel/tracing/available_events ]; then
  echo "tracefs readable; net events: $(grep -c '^net:' /sys/kernel/tracing/available_events)"
else
  echo "tracefs not readable as this user (use sudo)"
fi

banner "sysctls the chapters mention"
sysctl net.core.netdev_budget net.core.netdev_budget_usecs net.core.netdev_max_backlog \
       net.ipv4.ip_forward net.ipv4.tcp_rmem net.core.rmem_default 2>/dev/null || true
sysctl net.bridge.bridge-nf-call-iptables 2>/dev/null || echo "net.bridge.bridge-nf-call-iptables: br_netfilter not loaded (expected until the bridge chapter)"

banner "kind cluster"
kind get clusters 2>/dev/null || echo "kind: no clusters"
