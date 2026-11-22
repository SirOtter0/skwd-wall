#!/bin/bash
# Run only in the disposable validation VM with the read-only test ISO.
set -euo pipefail
set -x
[[ $(id -u) == 0 && $(cat /sys/block/vda/serial) == skwd-r29-disposable ]]
[[ $(uname -m) == x86_64 && $(cat /proc/1/comm) == runit && $(ls /sys/class/net) == lo ]]
! findmnt -rn -t 9p,virtiofs
cat /etc/os-release
uname -r
ldd --version | sed -n '1p'
scenario=${1:?A or B required}
[[ $scenario == A || $scenario == B ]]
media=/mnt/skwd-r29-validation
state=/run/skwd-r29-validation
mkdir -p "$media" "$state/xbps.d" /var/lib/skwd-validation /root/.config/skwd-wall-v2
mount -o ro /dev/sr0 "$media"
(cd "$media" && sha256sum -c SHA256SUMS)
printf 'user data sentinel\n' > /var/lib/skwd-validation/beta29.txt
test ! -e /root/.config/skwd-wall-v2/config.json
printf '{"paths":{"wallpaper":"/var/lib/skwd-validation"}}\n' > /root/.config/skwd-wall-v2/config.json
sha256sum /var/lib/skwd-validation/beta29.txt /root/.config/skwd-wall-v2/config.json > "$state/sentinels"
find /var/service /etc/sv -maxdepth 2 -printf '%p %l\n' | sort > "$state/services"
pkgs=(skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local)
for p in "${pkgs[@]}"; do ! xbps-query "$p"; done
xbps-query -l > "$state/guest-original"
xbps-install -C "$state/xbps.d" -i -M -y -R "$media/deps" libdav1d-1.5.5_1
xbps-query -p pkgver libdav1d

unrelated() {
    xbps-query -l | awk '$2 !~ /^skwd-(wall-v2|deck|lens|paper)-local-/ {print $1, $2}' | sort
}
unrelated > "$state/unrelated"
preservation() {
    unrelated | diff -u "$state/unrelated" -
    sha256sum -c "$state/sentinels"
    find /var/service /etc/sv -maxdepth 2 -printf '%p %l\n' | sort | diff -u "$state/services" -
}
owned() {
    for p in "${pkgs[@]}"; do xbps-query -f "$p"; done | awk '$1 ~ /^\// {print $1}' | sort -u
}
no_residue() {
    while IFS= read -r path; do [[ ! -e $path && ! -L $path ]]; done
}
install_revision() {
    local repo=$1 rev=$2 flag=$3 p a installed comparison
    local -a args=() force=()
    if [[ $flag == downgrade ]]; then
        force=(-f)
        for p in "${pkgs[@]}"; do
            installed=$(xbps-query -p pkgver "$p")
            comparison=0
            xbps-uhelper cmpver "${installed#"$p"-}" "$rev" || comparison=$?
            [[ $comparison == 1 ]]
        done
    fi
    for p in "${pkgs[@]}"; do args+=("$p-$rev"); done
    xbps-install -C "$state/xbps.d" -i -M -n -R "$media/$repo" "${force[@]}" "${args[@]}" | tee "$state/dry"
    printf '%s\n' "${args[@]}" | sort | diff -u - <(awk '{print $1}' "$state/dry" | sort)
    if [[ $flag == downgrade ]]; then
        awk '$2 != "downgrade" && $2 != "reinstall" {exit 1}' "$state/dry"
    fi
    xbps-install -C "$state/xbps.d" -i -M -y -R "$media/$repo" "${force[@]}" "${args[@]}"
    for a in "${args[@]}"; do
        p=${a%-1.0.0beta*}
        [[ $(xbps-query -p pkgver "$p") == "$a" ]]
        xbps-pkgdb "$p"
    done
    preservation
}

if [[ $scenario == B ]]; then
    install_revision previous 1.0.0beta27_7 install
    owned > "$state/old-paths"
    xbps-query -p pkgver "${pkgs[0]}"
fi
install_revision next 1.0.0beta29_1 install
owned > "$state/new-paths"
(cd / && sha256sum -c "$media/installed.sha256")
if [[ $scenario == B ]]; then
    comm -23 "$state/old-paths" "$state/new-paths" | no_residue
    echo 'PASS B beta27_7 to beta29_1'
else
    echo 'PASS A clean beta29_1'
fi
for command in skwd-wall-v2 skwd-walld skwd-helm skwd-lens skwd-paper-v2 skwd-wall-scan skwd-wall-vk; do
    file="/usr/bin/$command"
    [[ $(stat -c '%a %u:%g' "$file") == '755 0:0' ]]
    ldd "$file" | tee "$state/ldd-$command"
    ! grep -F 'not found' "$state/ldd-$command"
done
for c in skwd-wall-scan skwd-wall-vk; do
    [[ $(grep -cE 'lib(av(codec|format|util)|sw(scale|resample)).* => /usr/bin/\.\./lib/skwd-paper/' "$state/ldd-$c") == 5 ]]
done
for library in /usr/lib/skwd-paper/*.so.*; do
    [[ $(stat -Lc '%a %u:%g' "$library") == '755 0:0' ]]
    xbps-query -o "$library" | grep -F 'skwd-paper-local-1.0.0beta29_1'
done
test -s /usr/share/licenses/skwd-wall-v2/third-party/remediation/Iced-MIT.txt
test -s /usr/share/licenses/skwd-wall-v2/third-party/remediation/Font-Awesome-OFL-1.1.txt
test -s /usr/share/licenses/skwd-wall-v2/Symbols-Nerd-Font-MIT.txt
test -s /usr/share/licenses/skwd-deck/OUTDOOR-IMAGE-CREDITS.md
test -s /usr/share/licenses/skwd-deck/SQLITE-SOURCE.txt
test -s /usr/share/licenses/skwd-paper/ffmpeg/COPYING.LGPLv2.1
test -s /usr/share/licenses/skwd-paper/Roboto-3.015-OFL.txt
printf '%s\n' 'PASS guest library paths, ownership, hashes, notices'
if [[ $scenario == A ]]; then
    scratch=$(mktemp -d)
    chown nobody:"$(id -gn nobody)" "$scratch"
    runtime_status=0
    su -s /bin/bash nobody -c "timeout 130 python3 '$media/runtime.py' '$media' '$scratch'" || runtime_status=$?
    xbps-remove -C "$state/xbps.d" -y "${pkgs[@]}"
    for p in "${pkgs[@]}"; do ! xbps-query "$p"; done
    no_residue < "$state/new-paths"
    preservation
    xbps-pkgdb -a
    echo 'PASS C remove beta29_1'
    echo "Runtime exit: $runtime_status"
    exit "$runtime_status"
else
    install_revision previous 1.0.0beta27_7 downgrade
    owned | diff -u "$state/old-paths" -
    (cd / && sha256sum -c "$media/rollback.sha256")
    comm -13 "$state/old-paths" "$state/new-paths" | no_residue
    xbps-pkgdb -a
    echo 'PASS D rollback to beta27_7'
fi
