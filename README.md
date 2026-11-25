# Skwd-wall v2 for Void Linux

Community-maintained port by **SirOtter0** for **Void Linux x86_64 glibc with runit**. The coordinated release `1.0.0beta29_2` contains Wall, Deck, Lens and Paper. Skwd-wall is maintained upstream by [liixini](https://github.com/liixini/skwd-wall). See the [upstream README](README-UPSTREAM.md) for application features.

- [Download the signed beta29_2 release](https://github.com/SirOtter0/skwd-void-repo/releases/tag/xbps-beta29_2)
- [Native XBPS installation](https://github.com/SirOtter0/skwd-void-repo/blob/main/README.md#quick-installation) · [User guide](https://github.com/SirOtter0/skwd-void-repo/blob/main/docs/USERS.md)
- [Build and reproduce the beta29_2 packages](docs/void/BETA29-2-REBUILD.md)
- [Review the Void integration for Skwd-release](docs/void/UPSTREAM.md)
- [Report Void packaging issues](https://github.com/SirOtter0/skwd-void-repo/issues)

Native XBPS is the default installation method. Verify the repository key fingerprint when prompted, then use `sudo xbps-install -Su` for updates. For independent index authentication and freshness checks, use the [authenticated installation guide](https://github.com/SirOtter0/skwd-void-repo#authenticated-installation). The original sources and license notices ship alongside the XBPS files. No systemd dependency, service activation or desktop configuration changes are required by the packages.

The signed delivery passed clean installation in a Void VM. Upgrade, removal and rollback were tested in isolated Void guests. Wall beta29_2 rendered in Niri on Wayland with NVIDIA RTX 4060 Ti; the user confirmed general visual operation. These results cover the tested environment. Other architectures, musl and further hardware acceleration paths remain outside the validated scope.

The port follows the hybrid maintenance arrangement described in [upstream issue #155](https://github.com/liixini/skwd-wall/issues/155#issuecomment-6547549776). SirOtter0 maintains Void packaging externally; upstream can review the relevant changes for Skwd-release.
