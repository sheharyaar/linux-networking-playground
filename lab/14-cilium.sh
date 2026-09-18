#!/usr/bin/env bash
# Lab 14/15 — scenario 7: read and trace the Cilium datapath on an existing kind cluster.
# READ ONLY. This script never changes the cluster or the agent configuration.
# It wraps kubectl and docker exec; pwru runs inside the node.
#
# Prerequisites: kubectl, docker, a kind cluster with Cilium, and pwru copied into the node:
#   docker cp /usr/bin/pwru kind-worker:/usr/local/bin/pwru
set -euo pipefail
NODE="${NODE:-kind-worker}"
NS="${NS:-pp-demo}"
PWRU="${PWRU:-/usr/local/bin/pwru}"
SECS="${SECS:-40}"

agent() {
  local pod
  pod=$(kubectl -n kube-system get pod -l k8s-app=cilium \
        --field-selector "spec.nodeName=$NODE" -o jsonpath='{.items[0].metadata.name}')
  kubectl -n kube-system exec "$pod" -c cilium-agent -- "$@"
}

case "${1:-}" in
status)
  echo "== datapath configuration that decides which branches run =="
  agent cilium-dbg status --verbose | grep -iE 'Routing|Masquerading|Attach Mode|Device Mode|KubeProxyReplacement:' || true
  ;;
progs)
  echo "== which program is attached to which device on $NODE =="
  agent bpftool net show 2>/dev/null || echo "bpftool lives in the agent image; if this fails the agent has no bpftool"
  ;;
endpoints)
  agent cilium-dbg endpoint list
  ;;
pods)
  kubectl -n "$NS" get pod -o wide 2>/dev/null || echo "namespace $NS not found; set NS=..."
  ;;
same-node)
  # $2 = destination pod IP. Traces pod -> pod on one node.
  DST="${2:?usage: $0 same-node <dst-pod-ip>}"
  docker exec -d "$NODE" timeout "$SECS" "$PWRU" --filter-trace-tc --kmods veth \
    --output-meta "tcp and host $DST and port 80" >/dev/null
  echo "pwru started in $NODE for ${SECS}s; generate traffic now, then run: $0 report same-node"
  ;;
cross-node)
  DST="${2:?usage: $0 cross-node <dst-pod-ip>}"
  docker exec -d "$NODE" timeout "$SECS" "$PWRU" --filter-trace-tc --kmods geneve,veth \
    --output-meta "(udp and port 6081) or (tcp and host $DST and port 80)" >/dev/null
  echo "pwru started in $NODE for ${SECS}s; generate traffic now, then run: $0 report cross-node"
  ;;
world)
  DST="${2:?usage: $0 world <dst-ip>}"
  PORT="${3:-9099}"
  docker exec -d "$NODE" timeout "$SECS" "$PWRU" --filter-trace-tc --kmods veth \
    --output-meta "tcp and host $DST and port $PORT" >/dev/null
  echo "pwru started in $NODE for ${SECS}s; generate traffic now, then run: $0 report world"
  ;;
*)
  cat <<'T'
usage: 14-cilium.sh status | progs | endpoints | pods
       14-cilium.sh same-node  <dst-pod-ip>
       14-cilium.sh cross-node <dst-pod-ip>
       14-cilium.sh world      <dst-ip> [port]

Because pwru writes to the node's stdout, the simplest workflow is to run it
in the foreground in one terminal and generate traffic in another:

  # same node: expect ONE veth_xmit, ONE enqueue_to_backlog, ONE skb_do_redirect
  # per packet, and ZERO nf_hook_slow anywhere.
  docker exec kind-worker /usr/local/bin/pwru --filter-trace-tc --kmods veth \
      --output-meta 'tcp and host 10.128.0.82 and port 80'
  kubectl -n pp-demo exec pp-cli -- curl -s -o /dev/null http://10.128.0.82/

  # cross node: capture the outer tunnel and the inner packet together, then check
  # that every hook call carries the OUTER tuple.
  docker exec kind-worker /usr/local/bin/pwru --filter-trace-tc --kmods geneve,veth \
      --output-meta '(udp and port 6081) or (tcp and host 10.128.0.82 and port 80)'
  kubectl -n pp-demo exec pp-cli-far -- curl -s -o /dev/null http://10.128.0.82/

  # to the world: watch the source address change inside cil_to_netdev.
  docker exec kind-worker /usr/local/bin/pwru --filter-trace-tc --kmods veth \
      --output-meta 'tcp and host 172.18.0.1 and port 9099'
  kubectl -n pp-demo exec pp-cli -- curl -s --max-time 4 http://172.18.0.1:9099/

Notes
  * pwru inside one kind node sees the WHOLE host kernel, so the NETNS column
    distinguishes the nodes. It is not limited to the node you ran it in.
  * This pwru build (1.0.12) has NO --filter-dst-ip. Filtering is a pcap
    expression given as a positional argument.
  * rx_handlers (br_handle_frame, bond_handle_frame, macvlan_handle_frame,
    ipvlan_handle_frame) take struct sk_buff **pskb and are never printed.
  * A policy denial appears as sk_skb_reason_drop(SKB_DROP_REASON_TC_INGRESS)
    immediately after cil_from_container.
T
  exit 1 ;;
esac
