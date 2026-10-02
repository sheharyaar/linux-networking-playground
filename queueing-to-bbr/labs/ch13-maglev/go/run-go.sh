#!/bin/sh
# run-go.sh: run Cilium's own Maglev code from your fork, offline, without editing the fork.
#
#   ./run-go.sh            the package's own unit tests (go test ./pkg/maglev/)
#   ./run-go.sh lab        this chapter's probe, ch13_lab_test.go, added through -overlay
#
# Nothing is downloaded: the fork's vendor/ directory supplies every dependency
# (GOFLAGS=-mod=vendor, GOPROXY=off) and GOTOOLCHAIN=local forbids fetching a newer Go.
# Nothing is written into the fork: -overlay makes the go command see our file at
# pkg/maglev/zz_ch13_lab_test.go while the file stays here. Build output goes to Go's
# cache in your home directory, as for any go test.
set -eu
FORK=${CILIUM_FORK:-$HOME/workspace/neverinstall/cilium}
HERE=$(cd "$(dirname "$0")" && pwd)
[ -f "$FORK/pkg/maglev/maglev.go" ] || { echo "no Cilium tree at $FORK (set CILIUM_FORK)"; exit 1; }
[ -d "$FORK/vendor" ] || { echo "$FORK has no vendor/ directory; this would need the network, so stop"; exit 1; }
export GOFLAGS=-mod=vendor GOPROXY=off GOTOOLCHAIN=local
cd "$FORK"
echo "fork: $(git -C "$FORK" describe --tags 2>/dev/null || echo '?') at $(git -C "$FORK" rev-parse --short HEAD 2>/dev/null || echo '?')"
if [ "${1:-}" = lab ]; then
    OV=$(mktemp -d)/overlay.json
    printf '{"Replace":{"%s/pkg/maglev/zz_ch13_lab_test.go":"%s/ch13_lab_test.go"}}\n' "$FORK" "$HERE" > "$OV"
    go test -count=1 -overlay="$OV" -run '^TestCh13MaglevLab$' -v ./pkg/maglev/
    rm -rf "$(dirname "$OV")"
else
    go test -count=1 -v ./pkg/maglev/
fi
echo "fork still clean: $(git -C "$FORK" status --porcelain | wc -l) changed files"
