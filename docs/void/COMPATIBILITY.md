# Compatibility and evidence matrix

Scope: community beta27_3, x86_64 glibc/runit. PASS means the stated scenario,
not every feature of a product. Hardware rows are owner-reported on2026-11-14;
this publication task did not restart processes or repeat graphical tests.

| Area | State | Evidence and limit |
|---|---|---|
| Four native XBPS packages | Tested | Historical A/B archives match byte for byte; eight existing hashes rechecked during publication preparation |
| Offline build/source pinning | Tested historically | Per-component Cargo homes/targets; frozen vendored graph; FFmpeg9.0.2. New branch assembly has NOT repeated all builds |
| Clean install, reinstall, upgrade beta27_2→_3, removal | Tested |53 checks in a recovered/coherently updated historical Void VM overlay, not a fresh current ISO; earlier solver failure preserved privately |
| Integrity, tampered payload/signature, unknown key | Tested in lab | Disposable signatures/keys only, not production signing or HTTPS-channel acceptance |
| Private FFmpeg loader/15ELF, ABI/RUNPATH inspection | Tested |9.0.2 private paths, no system FFmpeg replacement; not proof of every decoder's security |
| Niri/Wayland, NVIDIA RTX4060Ti, two monitors | Owner-reported tested | beta27_3 installed; Deck current reports connected outputs with static backgrounds |
| Paper static rendering | Owner-reported tested | Both outputs display static wallpaper; temporary layer-surface lifecycle also historically tested, not all compositors |
| Session startup/static restoration | Owner-reported tested | Existing session configuration, no visible delay reported; personal launcher excluded and no timing benchmark |
| Deck daemon/IPC/catalogue/thumbnails | Tested | CLI/IPC and synthetic catalogue smoke; owner reports daemon operating; no claim of arbitrary personal library migration |
| Wall picker/NVIDIA | Partial | Prior beta.26 hardware and beta.27 CLI/build evidence; current user report does not independently qualify every beta27_3 UI panel |
| Lens basic CLI/packs | Tested | Empty-pack smoke and40 Python tests from authentic pinned Git/LFS metadata; no model payload needed |
| Lens inference and Drawing | Pending | External models/runtime not qualified or bundled |
| Video, hardware decoding, Wallpaper Engine scenes | Pending | FFmpeg maintenance upgrade compiled; no comprehensive format/GPU/media qualification |
| Widgets, themes, remote sources | Pending | Not covered by static wallpaper success |
| Wall shared verifier gates | Blocked input | Two checks need authentic skwd-verify d53b670e6561b7882c64477048b18f377486831a; no substitute or fabricated PASS |
| Noctalia experimental hooks/backend | Excluded | Prototype branches are not part of this publication tree |
| Noctalia Greeter/XFCE sync | Out of scope | Personal integration is not a base-port requirement |
| X11, other GPUs/compositors, musl/other architectures | Not qualified | No general compatibility claim |
| Signed public repository/install URL | Pending | No production key access, package signing, Pages deployment or official release performed here |

Versions of system dependencies are builder-derived. A coherent current Void
snapshot is required; passing on one machine does not prove installation on every
old rolling-release snapshot. Hashes and exact runtime dependencies: CANDIDATES.json.
