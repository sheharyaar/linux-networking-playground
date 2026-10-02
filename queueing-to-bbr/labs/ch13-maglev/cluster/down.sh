#!/bin/sh
# down.sh: delete the throwaway cluster, and only that one.
set -eu
kind delete cluster --name qbbr-maglev
