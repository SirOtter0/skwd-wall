# Void Linux packaging: beta27_3

Target: **x86_64 glibc, runit, Wayland**. Packages:
`skwd-wall-v2-local`, `skwd-deck-local`, `skwd-lens-local`, `skwd-paper-local`.
All four use `1.0.0beta27_3`. Wall and Deck require exact coordinated companions;
Lens is separate, so include all four explicitly when installing or upgrading.

No signed public binary channel is declared here. Existing candidate hashes are
review evidence, not release approval or a substitute for distribution signatures.
This guide does not modify your desktop until you deliberately run/configure it.

## Requirements

Use a coherent, updated Void glibc builder. Old rolling-release snapshots may need
an independently reviewed system update in that builder: do not force dependency
versions to install this port. Existing candidates require glibc>=2.41_1,
zlib>=1.4_1 and their recorded providers; see ../../docs/void/CANDIDATES.json.
Do not interpret builder-derived minimum versions as proven minimum API versions.

Build dependencies (review a simulation IN YOUR BUILD ENVIRONMENT first):

```sh
sudo xbps-install -n base-devel git curl python3 rust cargo bubblewrap patch cmake nasm patchelf pkg-config shaderc Vulkan-Headers vulkan-loader-devel libva-devel alsa-lib-devel pulseaudio-devel libyuv-devel clang19 libclang19 clang19-headers fontconfig-devel libxkbcommon-devel wayland-devel libdrm-devel libglvnd-devel libdav1d-devel zlib-devel
```

Install only after reviewing that transaction. The recorded builds use Rust/Cargo
1.99.0 and SOURCE_DATE_EPOCH=1793905368. Newer tools are not automatically
qualified. `glslc` comes from shaderc; LLVM19 runtime/resource headers require
libclang19 and clang19-headers. Override LIBCLANG_PATH and CLANG_RESOURCE_DIR
TOGETHER for a deliberately validated alternative. No shaderc compatibility
symlink or system-library replacement is required.

## Obtain and prepare exact sources

Start from this publication branch and record `git rev-parse HEAD`. Source pins
are in security/void-beta27/sources.json, relative to the repository root.
The public Wall branch alone lacks the coordinated companions/vendor. Obtain the
exact upstream suite plus the separately pinned FFmpeg9.0.2 archive:

```sh
curl --fail --location --proto '=https' --proto-redir '=https' -o official-suite.tar.xz https://github.com/liixini/skwd-wall/releases/download/v1.0.0-beta.27/skwd-suite-1.0.0-beta.27.tar.xz
curl --fail --location --proto '=https' --proto-redir '=https' -o ffmpeg-9.0.2.tar.xz https://ffmpeg.org/releases/ffmpeg-9.0.2.tar.xz
python3 - <<'CHECK'
import hashlib,json,pathlib
pins=json.loads(pathlib.Path('security/void-beta27/sources.json').read_text())
for name, expected in [('official-suite.tar.xz', pins['original_archive_sha256']), ('ffmpeg-9.0.2.tar.xz', pins['ffmpeg']['sha256'])]:
    with open(name,'rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=expected: raise SystemExit('Hash mismatch: '+name)
if pathlib.Path('official-suite.tar.xz').stat().st_size!=pins['archive_bytes']: raise SystemExit('Wrong suite size')
CHECK
mkdir -p work/build
python3 packaging/void/prepare-source.py official-suite.tar.xz "$PWD/work/source" --ffmpeg-archive "$PWD/ffmpeg-9.0.2.tar.xz"
```

All output destinations must be new. Preparation checks the coordinated revisions,
patches the private FFmpeg recipe and verifies vendor checksums/locks. No moving
branch is substituted. If an exact crate is missing, inspect the error and explicitly
retry in a NEW directory with `--fetch-missing-crates`; that opt-in downloads only
lockfile-checksummed versions before the offline build. No personal cache is needed.
HTTPS plus a committed hash pins origin/content, not an independent signing
identity. Verify upstream release signatures against separately authenticated keys
when your threat model requires them; do not trust a key merely downloaded beside
an archive. The historical FFmpeg authentication receipt is summarized in the audit.

## Compile and package

As a normal user, from the repository root:

```sh
for component in paper deck wall lens; do
  bash packaging/void/build.sh "$PWD/work/source/suite" "$PWD/work/build/$component" "$component"
done
SOURCE_DATE_EPOCH=1793905368 python3 packaging/void/package.py --build-root "$PWD/work/build" --output "$PWD/work/xbps"
```

Builds use bubblewrap with no network, personal HOME, session sockets or GPU;
Cargo is frozen/offline with per-component source/target/CARGO_HOME. Do not weaken
namespaces to bypass a sandbox error. Build prerequisites must already be present.
Package assembly reads the builder's XBPS database to resolve ELF providers; it
never installs dependencies. Outputs include repository/, packages.json and staging.

FFmpeg is private under /usr/lib/skwd-paper with relative RUNPATH; it does not
replace system FFmpeg. Its9.0.2 source tar, exact recipe/configuration, IJG/native
credits, LGPL licenses and replacement/debugging rights accompany Paper. Imported
compliance texts are hash-checked and retained, not silently relicensed.

## Validate without claiming more than was tested

```sh
python3 -m unittest discover -s packaging/void/tests -v
bash packaging/void/smoke.sh "$PWD/work/build" "$PWD/work/smoke"
```

Smoke runs compiled CLI/IPC/catalogue checks in a non-graphical offline sandbox;
it is not proof of graphical wallpaper rendering. Full Rust tests are separate:
`SKWD_TEST_INPUTS` must explicitly name a verified input directory. The test helper
rejects changed FFmpeg-reference, DXC and Steamworks inputs. Their URLs/hashes are
in security/void-beta27/test-inputs-beta27-3.json; preparation helpers are included.
The reference CLI recipe is reference-ffmpeg.sh. Test-only SDK/compiler/model inputs
must never be silently bundled into production packages or sources. No private
historical test directory is a default. Rebuilt reference CLI hash drift is a
review event, not permission to edit expected hashes or use system FFmpeg instead.
Two Wall checks require the exact unavailable skwd-verify input documented in the
audit; preserve BLOCKED until supplied/authenticated. Do not synthesize it.

For reproducibility use two NEW independent build roots/Cargo homes from the same
verified suite and unchanged installed dependency versions, then package each:

```sh
python3 packaging/void/compare.py work/xbps-A work/xbps-B --output work/comparison.json
```

Compare payloads, dependencies, metadata, ELF and archive hashes separately.
Historical A/B equality is environment-specific; this publication-branch assembly
has not repeated those long builds. See ../../docs/void/COMPATIBILITY.md.

## Install a reviewed local repository

After building or authenticating a future release, review packages.json and the
complete transaction. Replace /absolute/path/to/repository with your actual NEW
repository directory. These are instructions, not an active public channel:

```sh
sudo xbps-install -n -R /absolute/path/to/repository skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local
sudo xbps-install -R /absolute/path/to/repository skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local
```

Never disable remote signature verification. The payload adds no /etc configuration,
INSTALL/REMOVE hooks, autostart or runit/systemd services. Installation alone does
not start Deck, change wallpapers or initialize personal data. Review collisions
with another Skwd installation rather than overwriting it.

## Update and uninstall

Back up Skwd-specific settings/data and your previous package set. Review source,
license and migration changes; update all four companions together using the same
local repository command with `-n -u` first, then `-u`. Installed processes continue
to use old files until deliberately closed/restarted by YOU in your session. This
publication preparation performs no restart or startup change.

For removal, close only your Skwd session and deliberately enabled startup entry,
then simulate before confirming:

```sh
sudo xbps-remove -n skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local
sudo xbps-remove skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local
```

Owned files are removed; personal settings/library/cache remain. Do not recursively
delete generic XDG directories. Revert only integrations you explicitly enabled;
package removal cannot undo arbitrary hooks or themes. Rollback requires a reviewed
coordinated earlier package set and compatible backed-up data; schema migration
reversibility is not established by the synthetic sentinel test alone.
