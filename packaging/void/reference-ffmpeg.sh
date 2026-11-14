#!/bin/bash
# Build a test-only FFmpeg 9 CLI; never modify the production private runtime.
set -euo pipefail
[[ $(id -u) != 0 && $# == 2 ]] || { echo 'Usage: reference-ffmpeg.sh PREPARED-SUITE NEW-OUTPUT' >&2; exit 2; }
suite=$(realpath -- "$1")
output=$2
[[ $output == /* && ! -e $output && ! -L $output ]] || exit 2
python3 - "$suite/vendor-ffmpeg/ffmpeg-9.0.2.tar.xz" <<'CHECK'
import hashlib,pathlib,sys
p=pathlib.Path(sys.argv[1])
assert hashlib.file_digest(p.open('rb'),'sha256').hexdigest()=='8c3850283eb25fa026482078a04051e0be17347b09ef81a0849bec15a96e002e'
CHECK
mkdir -m700 -- "$output"
nice -n 10 bwrap --unshare-all --die-with-parent --new-session \
    --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/bin /sbin \
    --symlink usr/lib /lib --symlink usr/lib /lib64 \
    --proc /proc --dev /dev --tmpfs /tmp \
    --ro-bind "$suite/vendor-ffmpeg/ffmpeg-9.0.2.tar.xz" /source.tar.xz \
    --bind "$output" /work --clearenv --setenv PATH /usr/bin:/usr/sbin \
    --setenv SOURCE_DATE_EPOCH 1793905368 --chdir /work -- /bin/bash -c '
        set -euo pipefail
        tar -xf /source.tar.xz
        cd ffmpeg-9.0.2
        ./configure --disable-autodetect --disable-doc --disable-debug --disable-network \
            --disable-shared --enable-static --disable-everything --enable-ffmpeg \
            --enable-protocol=file,pipe --enable-demuxer=mov,wav,ogg \
            --enable-decoder=pcm_s16le,pcm_f32le,aac,vorbis,opus,wrapped_avframe \
            --enable-encoder=pcm_f32le,png --enable-muxer=pcm_f32le,image2 \
            --enable-filter=aresample,aformat,anull,abuffer,abuffersink,color,format,scale,null \
            --enable-swresample --enable-avfilter --enable-avdevice --enable-indev=lavfi --enable-zlib
        make -j2 ffmpeg
        mkdir /work/bin
        cp ffmpeg /work/bin/ffmpeg
    ' >"$output/build.log" 2>&1
echo "Test-only reference CLI: $output/bin/ffmpeg"
