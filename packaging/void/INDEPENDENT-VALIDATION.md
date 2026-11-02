# Independent clean-VM validation

Void Linux x86_64 glibc/runit; Rust/Cargo 1.99.0; coordinated beta.26,
XBPS revision 1.0.0beta26_3. This validates the community port, not an official
upstream release. No pull request has been opened by this validation.

## Method and inputs

Two newly created, independent virtual disks started from a minimal pre-port Void
snapshot containing 215 OS packages. Original disks/snapshots were not changed.
The builder freshly cloned the public fork and downloaded the official coordinated
source asset, the three exact patched crates, FFmpeg source and official XBPS build
dependencies. No earlier Skwd binary, package, Cargo cache or build tree was an input.

The tested build/preparation code is commit
`c2aac7f2a312b84b3e47825a831b7eb762e1522e`, including the corrections discovered
in this run. Each of the eight component builds has a separate source copy, target
and Cargo home. A and B use the same prepared, checksummed inputs and installed
build-package inventory. Compilation uses the published bubblewrap wrapper as an
unprivileged user, Cargo --frozen/offline, no network/HOME/graphical session and
read-only system libraries. Source acquisition occurs explicitly before compilation.

The coordinated archive retains its upstream vendored/prebuilt inputs; this test
does not prove that every upstream bundled object can be regenerated from source.
Source authenticity is HTTPS official-origin verification plus pinned hashes,
not an independently authenticated detached release signature.

Validation performed on 2026-11-02.

## Clean installation and functionality

A second fresh VM had no Rust/C compiler and received only freshly downloaded
Labwc/seatd/Foot/Grim/fonts/Lavapipe packages and the four new A archives. Transfer
used a temporary QEMU loopback port forward, with package hashes checked against
receipts obtained over the private serial console; no host directory was shared.
XBPS installed all four packages and resolved libva, libyuv, glslang and shaderc.
No installed package was upgraded or removed by that transaction.

| Check | Result | Evidence / scope |
|---|---|---|
| Clean installation | PASS | Four packages installed; package database check clean |
| Deck | PASS | Daemon/IPC, scan, catalogue with one locally generated PNG and thumbnails |
| Wall | PASS | Winit picker, IPC list and visible synthetic thumbnail in VM-only screenshot |
| Paper | PASS | Static wl_shm renderer, Virtual-1, READY; synthetic image visible; surface removed at termination |
| Lens | PARTIAL | --list-packs returns success and empty packs; inference intentionally not attempted |
| Uninstallation | PASS | Four removals succeed; no package-owned file remains; personal test data retained |
| Service state | PASS | Port installs no service/autostart; service symlinks unchanged during tests |

The VM uses KVM, 4 vCPU, 8 GiB RAM, 50 GiB dynamic qcow2, VirtIO-VGA 2D,
Labwc 0.20.2/Pixman and an explicit x86_64 Lavapipe ICD. Host 3D, GPU/USB
passthrough, clipboard and shared folders were disabled. Captures show only the
guest framebuffer. The before/after Paper screenshots have identical SHA-256:
`2457f2738993e61b06d4be559750a48e97198c86cd4a7d944aa7ebcfbbee1656`.

Initial Labwc startup raced seatd availability; retrying after seatd readiness
worked. A DRM client-fd clone warning and unavailable Vulkan direct-display
extensions did not prevent rendering. Wall's GPU-tier probe logged no ranked
adapter; the renderer still presented frames using the explicitly selected
software ICD. These are virtual-graphics limitations, not evidence of NVIDIA
validation in this VM. The earlier host Niri/NVIDIA result remains separate.

No video/Wallpaper Engine scene, hardware decoding, semantic model inference,
X11 wallpaper mode, musl or other architecture is covered. No models downloaded.
No host package, service, desktop configuration or wallpaper was changed.

## Corrections found by the clean process

- Correct shaderc package name (provides glslc).
- Explicit LLVM 19 runtime/resource-header packages and missing fontconfig,
  XKB/Wayland/DRM/GL/dav1d/zlib development prerequisites.
- Public coordinated-source URL, size, checksum and explicit fresh-clone instructions.
- Explicit checksummed FFmpeg source preparation and fail-closed offline preflight.
  The first offline Deck attempt exposed a missing source archive; isolation was
  not weakened and network access was not enabled for the build.
- A package comparator that validates actual archive payload/ELF/dependencies
  against inventories and reports metadata/timestamps separately.

## Repeatability

| Check | Result |
|---|---|
| Clean builds | PASS: Wall, Deck, Lens and Paper built twice |
| Content/dependencies | PASS: identical payload bytes, links, modes/ownership and dependency lists |
| ELF reproducibility | PASS: all 10 executables and 5 private libraries identical |
| Final XBPS reproducibility | PASS: all four normalized archives identical |
| Private-path check | PASS: no original workstation/build-home prefix found in the 15 ELF files |

The initial archives differed solely in tar mtimes (and the corresponding tar
header checksum); payload bytes and XBPS property dictionaries already matched.
The final packager normalizes staged timestamps to SOURCE_DATE_EPOCH=1792079636.
Both independent build results were reassembled into new destinations without
recompilation or executable modification. A separate comparison confirmed that
normalization preserved all payload/dependency/ELF values. Original outputs and
their differing hashes were retained. The normalized archives were also checked
for installation and removal.

SHA-256 of the final archives (identical in A and B):

| Package | SHA-256 |
|---|---|

| skwd-paper-local | `c4bf5b1cc5f13f040db051b7b8b7be4db4f567193f2f56a56e3c3ba0d4eea275` |
| skwd-deck-local | `05cd1e8776643257c5bb6ce566dc1752deb517f510f5968eb781d0fd3c21db9d` |
| skwd-wall-v2-local | `1105a50ac7cbb99b39f16a47206acdc2647512022164192b678b9070e5ec7902` |
| skwd-lens-local | `42448b8f31b13e40f596739881804937731535338972dd08a12771c22cc8eb43` |

This demonstrates repeatable functional builds, equivalent content/dependencies,
and byte-identical output for two independent builds with the same prepared
sources, build-package inventory, compiler, CPU/VM and epoch. It is not a
cross-machine, cross-toolchain or future repository-state reproducibility promise.
XBPS dependency versions are derived from installed providers; official system
packages are recorded for this run, not permanently vendored or snapshot-pinned.

The preparer/packager/comparator regression suite has 15 passing tests. Known
upstream Clippy/AsyncFd deprecations remain visible; this run changes no Rust
production code or the verified TLS/Tokio patch set.

**Recommendation: ready for PR with these limitations documented.** Opening a PR
still requires the fork owner's explicit confirmation.
