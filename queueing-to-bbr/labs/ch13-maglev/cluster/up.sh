#!/bin/sh
# up.sh: create the throwaway cluster qbbr-maglev, install Cilium with Maglev and M = 251,
# and deploy three echo backends behind a NodePort. Every kubectl and cilium call names the
# context kind-qbbr-maglev explicitly, so your other clusters are never touched.
set -eu
CTX=kind-qbbr-maglev
VERSION=${CILIUM_VERSION:-1.19.5}
cd "$(dirname "$0")"
if kind get clusters 2>/dev/null | grep -qx qbbr-maglev; then
    echo "a cluster called qbbr-maglev already exists; run ./down.sh first"; exit 1
fi
kind create cluster --config kind-maglev.yaml
SEED=$(head -c12 /dev/urandom | base64 -w0)
cilium install --context "$CTX" --version "$VERSION" \
    --set kubeProxyReplacement=true \
    --set k8sServiceHost=qbbr-maglev-control-plane --set k8sServicePort=6443 \
    --set loadBalancer.algorithm=maglev \
    --set maglev.tableSize=251 \
    --set maglev.hashSeed="$SEED"
cilium status --context "$CTX" --wait
kubectl --context "$CTX" apply -f echo.yaml
kubectl --context "$CTX" rollout status deploy/echo --timeout=180s
kubectl --context "$CTX" -n kube-system exec ds/cilium -c cilium-agent -- cilium-dbg config | grep -iE 'maglev|LBAlgorithm' || true
