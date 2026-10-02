#!/bin/sh
# shot.sh N [height] : render chapter N alone to /tmp/gpu-dossier/ch-N.png and report Mermaid errors
N=$1; H=${2:-6000}
python3 "$(dirname "$0")/build.py" --only "$N" >/dev/null
timeout 90 google-chrome-stable --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
  --enable-logging=stderr --v=0 --window-size=1300,$H --virtual-time-budget=15000 \
  --screenshot=/tmp/gpu-dossier/ch-$N.png file:///tmp/gpu-dossier/preview-ch$N.html 2>&1 \
  | grep -E 'mermaid block|Error' | grep -v 'ERROR:' | head -5
echo /tmp/gpu-dossier/ch-$N.png
