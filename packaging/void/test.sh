#!/bin/bash
# Test a completed disposable component build, with no host session or network.
set -euo pipefail
[[ $(id -u) != 0 && $# == 2 ]] || { echo 'Usage: test.sh BUILD-DIRECTORY wall|deck|lens|paper' >&2; exit 2; }
build_dir=$(realpath -- "$1")
component=$2
script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
: "${SKWD_TEST_INPUTS:?Set SKWD_TEST_INPUTS to your explicitly prepared and verified test-input directory}"
test_inputs=$(realpath -- "$SKWD_TEST_INPUTS")
python3 "$script_dir/verify-test-inputs.py" "$test_inputs"
test_log="$build_dir/test-verified-$(date +%Y%m%d-%H%M%S)-$$.log"
case "$component" in
    wall|lens) target=host ;;
    deck|paper) target=private-ffmpeg ;;
    *) exit 2 ;;
esac
[[ -d $build_dir/suite && -d $build_dir/target/$target ]] || exit 2
libclang=${LIBCLANG_PATH:-/usr/lib/llvm/19/lib}
resource_dir=${CLANG_RESOURCE_DIR:-/usr/lib/llvm/19/lib/clang/19}
nice -n 10 bwrap --unshare-all --die-with-parent --new-session \
    --ro-bind /usr /usr \
    --symlink usr/bin /bin --symlink usr/bin /sbin \
    --symlink usr/lib /lib --symlink usr/lib /lib64 \
    --proc /proc --dev /dev --tmpfs /tmp \
    --bind "$build_dir" /work \
    --ro-bind "$test_inputs" /test-inputs \
    --clearenv --setenv PATH /usr/bin:/usr/sbin \
    --setenv SKWD_E2E_BIN_DIR /work/target/"$target"/release \
    --setenv TMPDIR /work/test-tmp \
    --setenv SKWD_DXC_PATH /test-inputs/dxc/lib/libdxcompiler.so \
    --setenv STEAM_SDK_LOCATION /test-inputs/steam-sdk \
    --setenv HOME /tmp/home --setenv XDG_RUNTIME_DIR /tmp/runtime \
    --setenv XDG_CONFIG_HOME /tmp/config --setenv XDG_CACHE_HOME /tmp/cache \
    --setenv XDG_DATA_HOME /tmp/data --setenv XDG_STATE_HOME /tmp/state \
    --setenv CARGO_HOME /work/cargo --setenv CARGO_TARGET_DIR /work/target/"$target" \
    --setenv CARGO_NET_OFFLINE true --setenv CARGO_BUILD_JOBS 2 \
    --setenv LIBCLANG_PATH "$libclang" \
    --setenv BINDGEN_EXTRA_CLANG_ARGS -resource-dir="$resource_dir" \
    --setenv SHADERC_LIB_DIR /usr/lib --setenv SOURCE_DATE_EPOCH 1793905368 \
    --setenv RUSTFLAGS --remap-path-prefix=/work/suite=/usr/src/skwd-suite \
    --chdir /work/suite -- /bin/bash -c '
        set -euo pipefail
        mkdir -m700 -p "$TMPDIR" "$HOME" "$XDG_RUNTIME_DIR" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_DATA_HOME" "$XDG_STATE_HOME"
        component=$1
        export PATH=$CARGO_TARGET_DIR/release:$PATH
        [[ -x /test-inputs/bin/ffmpeg ]] || exit 2
        export PATH=/test-inputs/bin:$PATH
        [[ $(command -v ffmpeg) == /test-inputs/bin/ffmpeg ]] || exit 2
        sha256sum /test-inputs/bin/ffmpeg /test-inputs/dxc/lib/libdxcompiler.so /test-inputs/steam-sdk/redistributable_bin/linux64/libsteam_api.so
        reference_version=$(ffmpeg -version)
        [[ $reference_version == "ffmpeg version 9.0.2 "* ]] || exit 2
        printf "%s\n" "$reference_version"
        # Required E2E fixture generation; never discover missing capabilities after Cargo.
        ffmpeg -v error -nostdin -y -f lavfi -i color=c=red:s=32x32 -frames:v 1 -update 1 /tmp/reference-check.png
        [[ -s /tmp/reference-check.png ]] || exit 2
        if [[ $component == deck || $component == paper ]]; then
            export FFMPEG_DIR=/work/suite/.skwd-package/ffmpeg
            export SKWD_FFMPEG_PREFIX=$FFMPEG_DIR
            export PKG_CONFIG_PATH=$FFMPEG_DIR/lib/pkgconfig
            export LD_LIBRARY_PATH=$FFMPEG_DIR/lib
            export CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER=/work/suite/skwd-paper/packaging/link-private-ffmpeg.sh
        fi
        cd "skwd-$component"
        if [[ $component == wall ]]; then
            cargo test --frozen --release --features obs-heap -- --skip alloc_free
            cargo test --frozen --release --features obs-heap --bin skwd-wall alloc_free -- --test-threads=1
        else
            cargo test --frozen --release --workspace --no-fail-fast
        fi
    ' test "$component" >"$test_log" 2>&1
echo "Tests completed; inspect $test_log, including ignored tests."
