# Build and assemble Skwd-wall beta29_2 on Void

Use an isolated Void Linux x86_64 glibc builder with runit. The recorded build used Rust/Cargo 1.99.0, XBPS 0.60.7, LLVM/libclang 19 and source epoch `1794252032`. Record the installed versions in your builder. The packager reads Void's XBPS provider database and refuses mismatched input hashes. Rolling-system dependency versions can affect ELF and archive output.

Build tools are Git, Python 3, Bubblewrap, GCC/G++, Make, CMake, NASM, patchelf, pkg-config and glslc (shaderc). Install the matching development libraries in the builder for fontconfig, FreeType, xkbcommon, Wayland, libva, libdrm, Vulkan, dav1d, zlib, ALSA, PulseAudio and libyuv. Use the Void LLVM 19 development libraries and headers, or set both `LIBCLANG_PATH` and `CLANG_RESOURCE_DIR` to the selected installation. See the [recipe](../../packaging/void/build.sh) for the preflight checks and the [signed license and dependency inventory](https://github.com/SirOtter0/skwd-void-repo/releases/download/xbps-beta29_2/LICENSE-INVENTORY.json) for the exact packaged dependency metadata.

## Obtain the exact inputs

Use the [authenticated installation guide](https://github.com/SirOtter0/skwd-void-repo/blob/main/README.md#installation) to download and authenticate the public key, manifest and delivery. Extract the verified `corresponding-source.tar.xz` into a fresh absolute directory, referred to below as `prepared`. It contains `sources.json`, the four source components and locked Cargo vendor tree under `suite/`, and the native FFmpeg files and notices under `native-ffmpeg/`. Keep these original inputs intact.

The prepared sources already include the Void adaptation and the Tabler icon change. The historical preparation scripts in [security/void-beta29](../../security/void-beta29) document how the upstream suite and pinned earlier inputs were transformed. Use the prepared archive to avoid needing a historical local worktree. The [release source manifest](https://github.com/SirOtter0/skwd-void-repo/releases/download/xbps-beta29_2/SOURCE-FILES.json) records original port commit `08e344a7bf2518aba18f84eebd04f8e66525abae`. The public handoff keeps the archived recipe and security files byte for byte, with upstream Skwd tag `v1.0.0-beta.29` at `92202807ba4edc239ef723edeed2026b832bbc62` as Git parent. Local validation reports are summarized here.

## Compile from source

From the port checkout, use absolute values for `prepared` and a fresh `build_root`. Run as an ordinary user. The driver copies the verified suite per component, builds offline and leaves the staged payload under `<component>/suite/.skwd-package/`.

```sh
mkdir -- "$build_root"
for component in wall deck lens paper; do
    bash packaging/void/build.sh "$prepared/suite" "$build_root/$component" "$component"
done
```

This is the source-build procedure. A full independent clean rebuild of all four components with byte-identical results was outside the beta29_2 verification. The published revision rebuilt Wall twice from the same verified dependency inputs and reused nine other executables and five FFmpeg 9.1 libraries from beta29_1. The FFmpeg material includes its pinned source and JPEG-LS backport. See [the executable, library and receipt pins](../../security/void-beta29/xbps-inputs.json).

## Assemble and compare

Assembly requires the staged suite and the exact binaries under `.skwd-package/bin/` for each component. Paper's five pinned shared libraries and their SONAME links belong under `.skwd-package/ffmpeg/lib/`. The original build reused the nine executables and five libraries described above from its verified beta29_1 inputs. For an assembly-only replay without the historical build directories, these identical bytes can be obtained from the authenticated beta29_2 XBPS and placed in the staging layout. The path mapping is in [package.py](../../packaging/void/package.py) and [recipes.json](../../packaging/void/recipes.json). Verify every staged executable and library against the pins before assembly. A newly rebuilt input with a different hash requires investigation before claiming equivalence.

```sh
python3 packaging/void/package.py --build-root "$build_root" \
    --output "$new_candidate" --beta29-receipt "$prepared/sources.json" \
    --native-notices "$prepared/native-ffmpeg"
```

Use a new absolute output directory. The assembler creates the four XBPS and index beneath `repository/`. Compare the archive SHA-256 values against the authenticated public manifest. The locally generated index is unsigned. Compare its package metadata and its unchanged XBPS hashes with the published set; the production metadata accounts for the index hash difference. Two original assemblies with identical pinned binary inputs produced identical packages and unsigned indexes. Signing is a separate release operation.

## Validation and limits

Void x86_64 glibc/runit guests covered clean install, coordinated update, removal and rollback. The signed public release also installed in a clean guest and passed `xbps-pkgdb -a`. Wall was checked in a real Niri/Wayland session with NVIDIA RTX 4060 Ti and driver 595.112.07. The required support paths do not depend on systemd. These results do not cover musl, other CPU architectures, all GPU decoding paths or every desktop configuration.
