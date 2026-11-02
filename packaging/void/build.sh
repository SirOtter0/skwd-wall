#!/bin/bash
# Build one component offline as an ordinary user. No system installation.
set -euo pipefail
umask 077
[[ $(id -u) != 0 && $# == 3 ]] || { echo 'Usage: build.sh PREPARED-SUITE NEW-OUTPUT wall|deck|lens|paper' >&2; exit 2; }
suite=$(realpath -- "$1")
build_dir=$2
component=$3
case "$component" in wall|deck|lens|paper) ;; *) exit 2;; esac
[[ $build_dir == /* && ! -e $build_dir && ! -L $build_dir ]] || exit 2
for tool in bwrap cargo rustc cc c++ make cmake nasm patchelf pkg-config glslc python3; do command -v "$tool" >/dev/null || { echo "Missing $tool" >&2; exit 1; }; done
# Fail before copying sources or starting Cargo when the clean environment is incomplete.
for module in fontconfig xkbcommon wayland-client libva libva-drm libdrm vulkan dav1d zlib; do
    pkg-config --exists "$module" || { echo "Missing pkg-config module: $module (see README prerequisites)" >&2; exit 1; }
done
# Override both variables together for another supported LLVM installation.
libclang=${LIBCLANG_PATH:-/usr/lib/llvm/19/lib}
resource_dir=${CLANG_RESOURCE_DIR:-/usr/lib/llvm/19/lib/clang/19}
[[ -d $libclang && -f $resource_dir/include/stddef.h ]] && compgen -G "$libclang/libclang.so*" >/dev/null || { echo 'Set LIBCLANG_PATH and CLANG_RESOURCE_DIR for installed libclang' >&2; exit 1; }
python3 - "$suite" "$component" <<'CHECK'
import pathlib,json,hashlib,sys
p=pathlib.Path(sys.argv[1]);m=json.loads((p.parent/'sources.json').read_text())
if sys.argv[2] in ['deck','paper']:
 f=m['ffmpeg'];archive=p/f['path']
 assert archive.is_file() and not archive.is_symlink(), 'Prepare the pinned FFmpeg source before offline builds'
 assert hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()==f['sha256'], 'FFmpeg checksum mismatch'
for c,h in m['locks'].items():
 assert hashlib.file_digest((p/('skwd-'+c)/'Cargo.lock').open('rb'),'sha256').hexdigest()==h
CHECK
mkdir -m700 -- "$build_dir"
cp -a -- "$suite" "$build_dir/suite"
mkdir -m700 -- "$build_dir/cargo"
# Sin red, HOME, sesión gráfica, D-Bus, /run, GPU ni privilegios de administrador.
# El único árbol persistente modificable es una copia desechable en /work.
nice -n 10 bwrap --unshare-all --die-with-parent --new-session \
    --ro-bind /usr /usr \
    --symlink usr/bin /bin --symlink usr/bin /sbin \
    --symlink usr/lib /lib --symlink usr/lib /lib64 \
    --proc /proc --dev /dev --tmpfs /tmp \
    --bind "$build_dir" /work \
    --clearenv --setenv PATH /usr/bin:/usr/sbin \
    --setenv CARGO_HOME /work/cargo --setenv CARGO_TARGET_DIR /work/target \
    --setenv CARGO_NET_OFFLINE true --setenv CARGO_BUILD_JOBS 2 \
    --setenv CARGO_PROFILE_RELEASE_PANIC abort \
    --setenv SKWD_FFMPEG_JOBS 2 --setenv SKWD_KEEP_TARGET 1 \
    --setenv SKWD_FFMPEG_TARBALL /work/suite/vendor-ffmpeg/ffmpeg-9.0.1.tar.xz \
    --setenv SHADERC_LIB_DIR /usr/lib \
    --setenv LIBCLANG_PATH "$libclang" \
    --setenv BINDGEN_EXTRA_CLANG_ARGS -resource-dir="$resource_dir" \
    --setenv SOURCE_DATE_EPOCH 1792079636 \
    --chdir /work/suite -- /bin/sh distribution/build.sh "$component" \
    >"$build_dir/build.log" 2>&1
echo "Compilación terminada; revisar $build_dir/build.log. No se ha instalado nada."
