#!/bin/sh
# dump.sh DIR: save every node's Maglev tables and backend list into DIR/<node>-*.json.
set -eu
CTX=kind-qbbr-maglev
OUT=${1:?usage: ./dump.sh DIR}
mkdir -p "$OUT"
for pod in $(kubectl --context "$CTX" -n kube-system get pods -l k8s-app=cilium -o name); do
    node=$(kubectl --context "$CTX" -n kube-system get "$pod" -o jsonpath='{.spec.nodeName}')
    kubectl --context "$CTX" -n kube-system exec "$pod" -c cilium-agent -- \
        cilium-dbg bpf lb maglev list -o json > "$OUT/$node-maglev.json"
    kubectl --context "$CTX" -n kube-system exec "$pod" -c cilium-agent -- \
        cilium-dbg bpf lb list --backends -o json > "$OUT/$node-backends.json"
    kubectl --context "$CTX" -n kube-system exec "$pod" -c cilium-agent -- \
        cilium-dbg service list > "$OUT/$node-services.txt"
    echo "dumped $node"
done
