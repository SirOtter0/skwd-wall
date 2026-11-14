# Skwd-wall v2 — Void Linux community port

Native **Void Linux x86_64 glibc + runit** packaging for the coordinated Skwd
beta.27 suite: Wall, Deck, Lens and Paper. This is community-maintained support,
not an official Void package or an accepted upstream release.

The prepared package revision is **1.0.0beta27_3**, with private **FFmpeg 9.0.2**.
Binary publication is still gated: no signed public download or repository URL is
advertised here. Do not install packages from an unverified link.

## Start here

- [Installation, build, update and removal](packaging/void/README.md)
- [Wayland, Niri, NVIDIA and runit](docs/void/USAGE.md)
- [Compatibility and evidence limits](docs/void/COMPATIBILITY.md)
- [Publication audit and open gates](docs/void/PUBLICATION-AUDIT.md)
- [Reviewed candidate hashes/dependencies](docs/void/CANDIDATES.json)
- [Original upstream presentation](README-UPSTREAM.md)

## What has been observed

The four packages have reproducible A/B build receipts and headless Void VM
installation/upgrade/removal coverage. The owner reports beta27_3 operating on
Void glibc/runit, Niri/Wayland and an NVIDIA RTX 4060 Ti: Deck runs, two outputs
are reported by `skwd-helm current --json`, Paper shows static wallpapers and the
configured login restoration works without a visible delay. This is one reported
hardware configuration, not certification of every GPU, video format or desktop.

Lens inference, downloaded models, Wallpaper Engine, video hardware decoding,
widgets and additional architectures are not certified by those observations.
Two upstream Wall verifier checks remain blocked by an unavailable pinned input.
See the compatibility matrix before enabling additional functionality.

## Scope

No systemd, Nix, root desktop daemon or automatic service activation is needed.
Installing the packages does not install a session startup entry or edit personal
configuration. Experimental Noctalia bridge/hook/native-backend work is deliberately
absent from this branch. Noctalia Greeter/XFCE synchronization is out of scope.

## Contributing

Keep changes focused on Void glibc/runit. Use the pinned coordinated suite rather
than substituting moving companion branches. Record compiler/XBPS dependency
versions and all source hashes; build as an ordinary user, offline in bubblewrap.
Run the portable packaging tests before proposing changes:

```sh
python3 -m unittest discover -s packaging/void/tests -v
```

For runtime reports, state the package hashes, compositor, GPU/driver, output count,
exact feature tested and whether a clean profile was used. Exclude credentials,
personal logs and wallpapers. Do not present skipped or unavailable tests as PASS.

Skwd is developed by [liixini](https://github.com/liixini/skwd-wall). Upstream code
retains its MIT license; bundled/native dependencies and assets retain their own
terms. Per-package notices, FFmpeg source/recipe and LGPL replacement rights are
preserved by the Void packaging. See [LICENSE](LICENSE) and the publication audit.
