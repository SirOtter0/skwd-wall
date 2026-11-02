# Void Linux: native XBPS packages (x86_64 glibc + runit)

Community support for the coordinated Skwd suite **1.0.0-beta.26**, package revision
`1.0.0beta26_3`. Not an official Skwd or Void repository. No systemd or Nix needed.
[Validation and limitations](VALIDATION.md) · [Pinned sources and patches](../../security/void-beta26/README.md)

## Requirements

A working Wayland session with layer-shell for wallpaper rendering (Niri tested),
Vulkan for Wall/animated renderers, and the appropriate graphics driver. Static
`skwd-wall-still` uses wl_shm without a Vulkan renderer. NVIDIA RTX 4060 Ti was
validated for Wall; this does not validate Paper hardware video decoding.
X11 wallpaper support and musl/other architectures are not claimed.

Build prerequisites (install inside the build environment, not on an unrelated host):

```sh
sudo xbps-install -n base-devel git curl python3 rust cargo bubblewrap patch cmake nasm patchelf pkg-config shaderc Vulkan-Headers vulkan-loader-devel libva-devel alsa-lib-devel pulseaudio-devel libyuv-devel clang19 libclang19 clang19-headers fontconfig-devel libxkbcommon-devel wayland-devel libdrm-devel libglvnd-devel libdav1d-devel zlib-devel
# Review the transaction, then repeat without -n to install.
```

`glslc` is supplied by **shaderc**, not a package named glslc. LLVM 19's runtime
and resource headers need **libclang19** and **clang19-headers**; the unversioned
clang/libclang meta-packages may select another major version. Fontconfig/XKB/Wayland development files and the FFmpeg modules libdrm, dav1d
and zlib are explicit clean-build requirements; do not assume that a desktop
already installed them. LLVM 19 is the
explicit default in build.sh. For another installed version set LIBCLANG_PATH and
CLANG_RESOURCE_DIR together. No compatibility symlinks are needed.

The four declarative recipes live in `recipes.json`; `package.py` assembles them.
Runtime dependencies are derived from ELF DT_NEEDED and XBPS shlib providers, plus
explicit dlopen providers (fontconfig/Wayland/xkbcommon/Vulkan/GL loader for Wall).
See the generated packages.json for exact versions required by a particular build.
FFmpeg is private under `/usr/lib/skwd-paper`, with relative RUNPATHs; it does not
replace the system FFmpeg. Lens semantic inference additionally needs a compatible
ONNX Runtime and model pack; these are not downloaded or bundled automatically.

## Prepare and build

Obtain the pinned coordinated source asset over HTTPS from the official release.
A GitHub branch archive is **not** that suite (it lacks coordinated companions/vendor).
The URL, byte size and independently pinned hash are in
`security/void-beta26/sources.json`. No private source archive or previous cache is required.

```sh
curl --fail --location --proto '=https' --proto-redir '=https' \
  -o official-suite.tar.xz \
  https://github.com/liixini/skwd-wall/releases/download/v1.0.0-beta.26/skwd-suite-1.0.0-beta.26.tar.xz
python3 - <<'CHECK'
import hashlib,json,pathlib
m=json.loads(pathlib.Path('security/void-beta26/sources.json').read_text())
p=pathlib.Path('official-suite.tar.xz')
assert p.stat().st_size == m['archive_bytes']
with p.open('rb') as f: assert hashlib.file_digest(f,'sha256').hexdigest() == m['original_archive_sha256']
CHECK
mkdir -p work/build
```

The official release API also publishes the same SHA-256 asset digest. This is
HTTPS origin verification plus a pinned hash, **not** a claim of a detached GPG
signature. If your policy requires a separate signing identity, authenticate that
through upstream before building. Build as a normal user in a clean Void environment.

```sh
python3 packaging/void/prepare-source.py official-suite.tar.xz "$PWD/work/source" --fetch-missing-crates --fetch-ffmpeg
for component in wall deck lens paper; do
  packaging/void/build.sh "$PWD/work/source/suite" "$PWD/work/build/$component" "$component"
done
python3 packaging/void/package.py --build-root "$PWD/work/build" --output "$PWD/work/xbps"
```

Create `work/build` beforehand. Every build/output destination must be new.
Source preparation may download exact checksummed crates only when explicitly
requested. `--fetch-ffmpeg` additionally obtains the pinned FFmpeg source from
ffmpeg.org and verifies its SHA-256 before any build; the original coordinated
suite does not include that archive. Its path/hash are recorded in the prepared
manifest. Deck and Paper fail their preflight if it is missing or modified.
The four builds run in bubblewrap without network, HOME, graphics or
root privileges, using Cargo --frozen and vendored dependencies. They preserve
separate per-component build trees, avoiding stage cleanup between components.
The builder does not claim deterministic binary output. Review generated metadata,
package licenses, dependency versions and hashes before redistribution.

## Install XBPS archives

After reviewing a repository built locally or authenticated from a trusted publisher:

```sh
xbps-query -R --repository /absolute/path/to/work/xbps/repository -x skwd-wall-v2-local
sudo xbps-install -n --repository /absolute/path/to/work/xbps/repository skwd-wall-v2-local skwd-lens-local
sudo xbps-install --repository /absolute/path/to/work/xbps/repository skwd-wall-v2-local skwd-lens-local
```

Wall pulls the exact companion Deck/Paper package revision. Lens is separate.
For future downloads, verify the publisher's repository key/signature through a
trusted channel: a SHA256SUMS next to an untrusted archive is not authentication.
This fork currently publishes packaging sources, not a trusted binary repository.
Never disable signature checks on a remote repository to install these packages.

Packages contain binaries, private libraries, desktop/icon metadata, templates and
licenses under /usr. They contain no /etc configuration, installation hooks,
autostart entries, runit services or systemd unit. Installation does not initialize
a personal catalogue or change wallpapers/themes. Review collision checks if a
portable installation or other Skwd package is already present.

## Run manually

Back up your desktop settings first. Start inside the Wayland session as your normal
user. Do not run the graphical components as root or enable a system-wide daemon.

```sh
skwd-walld
# In another terminal:
skwd-helm list --json
SKWD_WALL_FORCE_WINIT=1 skwd-wall-v2
```

Deck supplies the catalogue and manages workers. Wall is the picker. Configuration:
`$XDG_CONFIG_HOME/skwd-wall-v2/config.json` (default ~/.config); library/database:
`$XDG_DATA_HOME/skwd-wall-v2`; cache: `$XDG_CACHE_HOME/skwd-wall-v2`. Use separate
XDG directories for initial trials. See upstream settings for library folders.
Disable themes, hooks, remote sources, schedules and lock-screen integrations until
explicitly configured. In particular, `pickOnlyMode: true` prevents applying a
wallpaper while validating the picker. Environment overrides SKWD_WALL_V2_CONFIG,
SKWD_WALL_V2_CACHE and SKWD_WALL_V2_SOCK must agree between clients and Deck.

**Winit here still requests fullscreen, transparency and no decorations.** It is
not an ordinary decorated window. Without FORCE_WINIT, Wall uses layer-shell.
Do not confuse the picker overlay with a persistent wallpaper renderer.

Paper can also run independently for a static test:

```sh
skwd-wall-still OUTPUT /absolute/path/image.png --layer background
# Ctrl+C removes this renderer's surface.
skwd-paper-v2 outputs
skwd-paper-v2 status
```

Use actual output names from your compositor. Multiple wallpaper managers on the
same layer have compositor-dependent stacking. The validated temporary coexistence
check used Bottom above the existing Background surface, not a permanent wallpaper
integration. Closing Paper should expose the underlying manager; verify before
changing any shell settings. Do not enable two permanent wallpaper managers blindly.

Lens without models:

```sh
skwd-lens --list-packs --models-dir "$HOME/.local/share/skwd-lens/models"
```

For inference, obtain a compatible model pack and ONNX Runtime through upstream's
pack workflow, review licenses/checksums, install explicitly, and enable semantic
features in settings. For example, after verifying the pack/runtime:

```sh
skwd-lens --install-pack /absolute/path/to/pack --models-dir "$HOME/.local/share/skwd-lens/models" --runtime /absolute/path/to/libonnxruntime.so --threads 2
```

The runtime library can also be selected via SKWD_LENS_ORT_DYLIB.
Empty-pack listing is tested; model inference is not. No
credentials or automatic model download are required for basic package operation.

## Runit and autostart

Manual Deck startup is sufficient; systemd is not needed. A user may later supervise
`skwd-walld` with a per-user runit service launched **inside the graphical session**,
with the correct UID, HOME/XDG and Wayland environment. Do not put a root daemon in
/var/service or hardcode another user's socket. No such service is installed or
enabled by these packages. Configure one session instance only; the socket provides
client communication, not a substitute for reviewing process lifetime.

## Remove / update

Stop Wall and Deck normally and stop Paper renderers belonging to your session.
Review reverse dependencies, then remove the four packages:

```sh
sudo xbps-remove -n skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local
sudo xbps-remove skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local
```

XBPS removes owned system files. Personal settings/database/cache deliberately remain;
archive or remove only the Skwd-specific directories you actually used after reviewing
them. Restore any separately enabled app/theme integration using its receipts/backups;
uninstalling packages alone does not reverse arbitrary hooks or personal theme edits.
Update by reviewing a new coordinated suite, reapplying only compatible patches,
rerunning relevant tests and rebuilding all coordinated packages together. Never
silently substitute private/missing revisions or update Cargo.lock to branch heads.
