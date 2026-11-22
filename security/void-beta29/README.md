# Preparing the coordinated beta.29 inputs on Void Linux

Scope is x86_64 glibc. Use the official
[beta.29 suite archive](https://github.com/liixini/skwd-wall/releases/tag/v1.0.0-beta.29)
and the preserved beta27_7 source manifest. The preparation script checks
the suite and historical-manifest digests and every carried-forward
file. The inputs include the six regenerated fonts, the cryoglyph/lru
and rustix fixes, FFmpeg 9.1 and the official JPEG-LS backport. The
preparer verifies both the FFmpeg archive and the backport. Check the
upstream release signature before staging. There are no reused
executables in a full build of the suite.
The suite's original SBOM and release-policy report describe the
publisher's inputs. The generated `sources.json` describes the Void
changes and pins the exact locks and native recipe.

Run as a normal user. Use a fresh output directory and sufficient disk
space for four Cargo worktrees. See the Void packaging prerequisites
and the audit for required tools and versions.

```sh
python3 security/void-beta29/prepare.py \
  "$archive" "$beta27_source_manifest" "$beta27_prepared_suite" "$new_output" \
  --ffmpeg-archive "$ffmpeg_archive"

for component in lens wall deck paper; do
  bash packaging/void/build.sh "$new_output/suite" "$build_root/$component" "$component"
done
```

Set the input and output shell variables to absolute paths. The build driver uses
Bubblewrap with a fresh network and process namespace. The build log,
Cargo outputs and staged executables are stored underneath the chosen
build directory. Use an isolated check, Clippy and Rust test run with the
same vendored sources and Cargo options. Deck and Paper require the
private FFmpeg environment for their media tests. For the shared pinned
FFmpeg fixture CLI, DXC and optional SDK inputs, follow the existing
Void test-input verification procedure.

## Candidate validation

- Proposed XBPS identity is `1.0.0beta29_1`, with the four existing
  package names and coordinated Wall → Deck/Paper and Deck → Paper pins.
  Verify actual ELF dependencies, RUNPATH, `dlopen` libraries and Void
  package floors against the fresh builds. Refresh the Deck license
  inventory from its new SQLite graph before enabling the package
  assembler for beta.29. The historical assembler and source delivery
  gates still refer to beta27 and must not relabel either build.
- Check that Wall carries `Iced-MIT.txt`,
  `Iced-Icons-PROVENANCE.txt` and `Font-Awesome-OFL-1.1.txt`.
  Include the corresponding materials in the source delivery. Verify
  the deployed font hash and all three notices against the final XBPS
  and archive. Preserve the existing Deck photo and Paper font credits.
- In disposable Void glibc guests with separate disks and private local
  package repositories, exercise clean install and beta27_7 → beta29
  upgrade. Capture the dry run and actual XBPS transaction, verify all
  exact versions and `xbps-pkgdb`, then uninstall. Compare installed
  paths and owners, unrelated packages and configuration sentinels.
  Check runit state and launch all four components in the guest.
- In an isolated Wayland session with test data, open Wall, browse the
  library, test JPG/WebP thumbnails and filter and Arrange settings.
  Test cold and warm transition previews, catalogue IPC, switching
  wallpapers and configuration persistence across restart. Review text
  shaping and all dropdown indicators. Run test media in H.264 at 1080p
  and 4K, with software and hardware paths exercised independently.
  Capture evidence of the actual VAAPI, DRM PRIME and Vulkan paths.
  Use a GPU-backed Niri/NVIDIA test environment for the hardware results.
  Test Wallpaper Engine scenes against a named fixture set, including
  widget composition and shared renderer lifetimes. Record each result
  by compositor, device and driver rather than extrapolating.

### Guest XBPS transactions

Use a new or restored guest for each scenario. Mount only the
hash-verified test repository as read-only media. Resolve official
dependencies in the guest first. Verify the guest identity, Void glibc
and x86_64 before running any transaction. Use the following commands
only inside the guest, with `$repo` set to the mounted repository path
for the scenario's target version.

```sh
set -- skwd-wall-v2-local skwd-deck-local skwd-lens-local skwd-paper-local
xbps-install --dry-run --ignore-conf-repos --repository "$repo" "$@"
# Inspect the dry run. Proceed only if all four expected versions are selected.
xbps-install --ignore-conf-repos --repository "$repo" "$@"
for pkg; do
  xbps-query -p pkgver "$pkg"
  xbps-query -f "$pkg"
  xbps-pkgdb "$pkg"
done
xbps-remove --dry-run "$@"
xbps-remove "$@"
```

For the update scenario, install and verify all four beta27_7 packages
first, seed a guest-only configuration sentinel, and then set `$repo`
to the beta29 repository for the dry run and update. Compare recorded
ownership, services, configuration hashes and unrelated package state
before and after removal. Keep the logs outside the disposable guest
disk. The eventual public installation procedure must use the
signed repository.

### Hardware evidence

Use two hash-recorded H.264 clips, one 1920×1080 and one 3840×2160,
inside the disposable GPU-backed test session. Record the Niri version,
driver version and renderer node. Run this against the renderer from
the candidate package inside that session:

```sh
skwd-wall-vk --decode-probe "$clip_1080" "$clip_2160" > decode-probe.txt
```

Read the per-backend results. The command's exit status alone does
not identify which decoder was accepted. Apply and restore the two
clips and an image using a synthetic catalogue, then inspect Deck's
IPC output and Paper's logs for renderer selection, DRM PRIME and
fallback. Save a separate result for visual playback and transitions
in Niri. The provided runit procedure uses a temporary supervisor or a
disposable guest, with no session service activation required by XBPS.

## beta29_2 icon assembly

Apply `prepare-icons.py BASELINE OUTPUT` to a new directory. Its
baseline is the exact beta29_1 FFmpeg-remediated source suite and
receipt. The beta29_2 receipt verifies the approved replacement TTFs,
modified embedding paths, vendor metadata and omission of the original
fonts. The Tabler license and provenance ship under Wall's third-party
license directory. The refreshed `xbps-inputs.json` describes beta29_2.

Build Wall only, using an offline writable copy of the prepared suite
and a fresh Cargo target or an isolated copy of the verified target.
Invalidate stale vendored Iced output before using a copied target.
For XBPS assembly, point each component at this same prepared source
suite and the pinned payloads for its component. Reuse the nine
unchanged executables and five FFmpeg 9.1 libraries from beta29_1 by
their recorded hashes. Generate the package index and source archive
in new directories. The resulting revision stays unsigned until
authorized separately.
