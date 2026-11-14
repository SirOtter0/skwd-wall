#!/bin/bash
# Check compiled release binaries without exposing the real user session.
set -euo pipefail
[[ $(id -u) != 0 && $# == 2 ]] || { echo 'Usage: smoke.sh BUILD-ROOT NEW-EVIDENCE-DIRECTORY' >&2; exit 2; }
root=$(realpath -- "$1")
output=$2
[[ $output == /* && ! -e $output && ! -L $output ]] || exit 2
for component in wall deck lens paper; do
    [[ -d $root/$component/suite/.skwd-package/bin ]] || exit 2
done
mkdir -m700 -- "$output"
bwrap --unshare-all --die-with-parent --new-session \
    --ro-bind /usr /usr \
    --symlink usr/bin /bin --symlink usr/bin /sbin \
    --symlink usr/lib /lib --symlink usr/lib /lib64 \
    --proc /proc --dev /dev --tmpfs /tmp \
    --ro-bind "$root/wall/suite/.skwd-package/bin" /suite/wall \
    --ro-bind "$root/deck/suite/.skwd-package/bin" /suite/deck \
    --ro-bind "$root/lens/suite/.skwd-package/bin" /suite/lens \
    --ro-bind "$root/paper/suite/.skwd-package/bin" /suite/paper \
    --ro-bind "$root/paper/suite/.skwd-package/ffmpeg/lib" /suite/lib \
    --ro-bind "$(dirname "$(realpath -- "$0")")/smoke.py" /smoke.py \
    --bind "$output" /evidence --clearenv \
    --setenv PATH /suite/wall:/suite/deck:/suite/lens:/suite/paper:/usr/bin:/usr/sbin \
    --setenv LD_LIBRARY_PATH /suite/lib \
    --setenv HOME /tmp/home --setenv XDG_RUNTIME_DIR /tmp/runtime \
    --setenv XDG_CONFIG_HOME /tmp/config --setenv XDG_CACHE_HOME /tmp/cache \
    --setenv XDG_DATA_HOME /tmp/data --setenv XDG_STATE_HOME /tmp/state \
    -- /usr/bin/python3 /smoke.py >"$output/smoke.log" 2>&1
echo "Smoke checks completed; inspect $output/summary.json."
