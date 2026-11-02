# Coordinated beta.26 security inputs

These patches apply only to the original coordinated suite identified in sources.json.
They are not automatically applied to newer branches or releases.

- Deck/Paper: rustls-webpki 0.103.16, webpki-roots 1.0.10, Tokio 1.53.3.
- Lens: Tokio 1.53.3, preserving existing features.
- Wall: original sources/lockfile unchanged.
- Deck retains its original OwnedFd/AsyncFd constructors. Tokio deprecates these;
  no new unsafe registration blocks are added.

TLS/Tokio advisory entries RUSTSEC-2026-0381/0382/0386 no longer appeared in the
recorded audit of these resolved inputs. Applicability was assessed separately;
this does not assert that the original application was demonstrably exploitable.
Existing lru unsoundness and unmaintained-dependency notices remain visible in the
historical audit. They are not fixed or waived by this packaging contribution.
Selected TLS regressions passed with ring and AWS-LC; see the validation summary.
No claim of a currently clean cargo-audit or complete security audit is made.

Obtain the coordinated official beta.26 source archive from the maintainer's release
publication, authenticate its release manifest/signature independently, and verify
its SHA-256 against sources.json. Individual GitHub repos may not expose every
coordinated revision. Do not substitute current branch heads. This fork does not
publish the original or derived archive, vendor tree, binaries, private releases,
credentials or test-only TLS dependency bundles.

prepare-source.py verifies the original archive checksum, applies the three pinned
patches and checks vendored registry packages against patched Cargo.lock checksums.
With explicit --fetch-missing-crates it fetches only missing locked crates from
static.crates.io and verifies their checksum before extraction. That is a network
preparation step, not a build. Compilation uses the resulting vendor offline.
Upstream vendor includes precompiled ISPC objects; an independent bit-for-bit
rebuild of these objects has not been demonstrated.

Public Void maintenance is intended to remain in this fork. The maintainer can
review/copy this packaging into the private release repository manually; there is
no claim that this integration has been accepted or shipped officially.
