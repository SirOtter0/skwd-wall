# Validation: beta.26 local revision 3

Tested platform: Void Linux x86_64 glibc/runit, Rust/Cargo 1.99.0.
This is a community port, not an accepted official Skwd release.

The subsequent [independent clean-VM validation](INDEPENDENT-VALIDATION.md)
records fresh public-source builds, clean installation/removal and a separate
Labwc/Pixman/Lavapipe functional test. Historical checks below remain distinct
from that run.

| Area | Result |
|---|---|
| Builds | Wall, Deck, Lens and Paper compiled individually, offline, without privileges in bubblewrap |
| Packages | Four XBPS archives created; ELF dependencies, architecture, RUNPATH and payload inspected; installed offline in a disposable Void VM |
| Wall/Deck | On Niri with NVIDIA RTX 4060 Ti/Vulkan: IPC, synthetic catalogue, frames and thumbnail rendering passed; user confirmed UI/thumbnail |
| Paper | Static wl_shm renderer decoded the synthetic PNG, reported READY and created its surface on one Niri output. External timeout ended at 14.04 s; surface disappeared; prior Noctalia layers and settings unchanged. User confirmed both the synthetic image and return of the original background |
| Lens | Executable starts and --list-packs returns an empty catalogue offline. Model inference has NOT been validated |
| TLS | Selected rustls-webpki distrusted_spki regression passed with ring and AWS-LC, using verified test-only dependencies in offline bubblewrap |
| Tests/Clippy | Known compiler lints/AsyncFd deprecations remain. No new unsafe AsyncFd adaptation is included. Passing builds or selected tests are not a complete security audit |

Not yet validated: Paper video/Wallpaper Engine scenes/NVIDIA hardware decoding,
Lens semantic inference, every Wayland compositor, X11 wallpaper support, cross-environment
bit-for-bit reproducibility, other architectures or musl. Noctalia Greeter/XFCE
custom synchronization is explicitly outside the port.

The first Wall supervisor encountered an already-exited PID during cleanup. The
wallpaper/configuration checks and rendering logs were preserved; some network
samples and the supervisor's in-memory summary were not. Do not claim an exhaustive
network audit. A corrected temporary supervisor was used for the subsequent static
Paper check; this host-specific harness and personal desktop data are not published.

The public packaging CLI accepts explicit build/output directories rather than
requiring a particular workstation. Its payload assembly is derived from the tested
packager. Package dependency minima are obtained from the build machine's XBPS
providers; use a clean supported Void build environment when producing releases.

The public source preparation was exercised against the pinned official archive:
patches applied, missing locked crates verified and vendor checks passed. The
1,694 source/manifest/script files compared across the four component trees match
the previously compiled inputs exactly. Four final XBPS payloads and dependency
lists match the VM/host-validated packages. Six archive-path/link validation tests
passed. These are source/payload equivalence checks, not bit-for-bit reproducibility.
