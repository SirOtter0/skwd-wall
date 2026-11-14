# Base-port publication audit

## Scope and branch isolation

Source inspected: prototype/void-beta27-postprocessing-noctalia-20261113 at2cbd352.
The base port is a78dad4, before all bridge/hook/native Noctalia prototype commits.
Publication is assembled on the fork's public v2 base
5d93c1411300220f4bc9c8c8820ae0244b36c12c, preserving its application source.
No worktree or source branch is rewritten. Only an explicit packaging/source-pin
allowlist, legal inputs and new documentation are carried into the publication tree.
No experimental commits become ancestors of the new branch.

Root application code has no downstream change in this branch. The native FFmpeg
recipe patch applies to the separately pinned companion suite at preparation time.
The original README is retained as README-UPSTREAM.md. No personal launchers,
active configs, logs, VM harnesses/disks, test archives, credentials or compiled
binaries are copied. Prototype branches remain local and intact.

## Inputs and package audit

Suite: official beta.27 coordinated release, SHA256
3337c85f91b2e8b61f1df5d31b9797379b8ac83e3824b17c910317826dfdb70a.
FFmpeg:9.0.2, SHA256
8c3850283eb25fa026482078a04051e0be17347b09ef81a0849bec15a96e002e.
Both are pinned with exact component revisions/recipe patch in sources.json.
The private9.0.2 input was previously authenticated in its preparation receipt;
this publication task reuses the pinned content identity, not a fresh signature/key
ceremony or claim of independent authenticity of a hash alone.

The eight existing candidate archives rechecked against preserved receipts agree.
CANDIDATES.json contains sanitized file sizes/hashes/dependencies/license metadata,
without private artifact paths. Names and beta27_3 versions are coordinated. Exact
FFmpeg consumers use /usr/lib/skwd-paper; no driver/system-library modification,
systemd dependency, install hook, personal configuration, service/autostart payload
is added. Native dependencies are resolved from recorded ELF/provider information;
zlib>=1.4_1 and the other recorded versions are not lowered to bypass a solver.

The portable packager/imported compliance files are retained. All1889 imported
notice files are checked against BETA27-2-IMPORT.json. Crate/std/native/font/icon
licenses and source/relink documentation remain separate from the MIT project
grant. FFmpeg/JPEG attributions and the9.0.2 source/recipe are refreshed at package
assembly, not treated as covered by a wrapper license. Steam SDK/DXC are test-only
inputs, not implicitly redistributable application runtime or model bundles.

## Portability corrections made for publication

Full-test input path must be explicitly supplied with SKWD_TEST_INPUTS; the old
work/beta27_3/continuation private default is removed. Its hash checks are unchanged.
The source/test helpers have all their required pinned JSON inputs in this branch.
The source/build/package scripts use repository-relative inputs and new explicitly
chosen output directories; /tmp inside isolated sandboxes is intentional ephemeral
storage, not an external missing input. Host-specific orchestration/resume/diagnostic
scripts and personal test receipts are excluded.

No long Rust/native builds were repeated for documentation-only publication work.
The public preparation path still needs a fresh external-user build acceptance;
historical A/B equality does not certify a new toolchain or every future checkout.

## Release gates and limitations

This is suitable for a DRAFT PR in the owner's fork, NOT a definitive binary release.
The owner reports successful beta27_3 static dual-output operation; acceptance is
bounded by COMPATIBILITY.md. Remaining gates:

* authentic pinned Wall verifier input for two shared Python checks;
* current full RustSec review, including lru exception expiration2026-11-30;
* candidate-specific final licensing/source-offer review and complete corresponding
  source delivery/public hosting for beta27_3 (not an old beta27_1/_2 archive);
* fresh publication-branch source-build acceptance by an independent user/builder;
* unqualified video/Wallpaper Engine/inference/widget/other hardware paths remain
  documented limitations, not invented PASS results;
* explicitly authorized signing/publication and verified public channel/keys.

No package signing, private-key read, production upload, Pages activation or upstream
PR is part of this preparation. No dependency/driver/system package or live session
configuration is changed and no running Skwd process is stopped.
