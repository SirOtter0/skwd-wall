# Wayland session usage

Use the normal desktop user in an existing Wayland session. Do not run renderers
as root. Wall needs a Vulkan implementation; Paper static rendering uses wl_shm
and Wayland layer-shell. NVIDIA needs its normal working Wayland/Vulkan stack;
this port installs no driver, Secure Boot, bootloader or firmware changes.
Software Vulkan on a VM is not NVIDIA hardware qualification.

## Roles and manual start

Deck (`skwd-walld`) supplies the catalogue/IPC and manages workers; Wall
(`skwd-wall-v2`) is the picker. Paper supplies the renderers. Lens provides optional
semantic/model functionality; it is not required to display one static wallpaper.
Run these commands only when you intend to start a test session:

```sh
skwd-walld
# In a second terminal of the same graphical session:
skwd-helm list --json
skwd-helm current --json
SKWD_WALL_FORCE_WINIT=1 skwd-wall-v2
```

Do not start a second daemon if your session already runs one. Inspect the
configuration/help and use one session owner; do not globally kill similarly
named processes. Closing the picker is not equivalent to stopping Deck or Paper.
Winit in this revision STILL requests fullscreen, transparency and no decorations;
it is not a small conventional window. Default Wall uses layer-shell.

For an explicitly temporary independent static renderer:

```sh
skwd-wall-still OUTPUT /absolute/path/to/synthetic.png --layer bottom
```

Replace OUTPUT with the compositor's real output name. Ctrl+C closes that renderer's
surface. Layer stacking with another wallpaper owner is compositor-dependent;
verify recovery before choosing a persistent manager. No instructions here disable
Noctalia or change a greeter/XFCE wallpaper. Do not assume that closing Paper
restores a theme or file changed by an independently enabled hook.

## Configuration and optional functions

Skwd settings are under `$XDG_CONFIG_HOME/skwd-wall-v2/config.json` (normally
`~/.config/skwd-wall-v2/config.json`), data under `$XDG_DATA_HOME/skwd-wall-v2`,
cache under `$XDG_CACHE_HOME/skwd-wall-v2`. Use separate XDG directories and a
synthetic image for the first trial. `SKWD_WALL_V2_CONFIG`, `SKWD_WALL_V2_CACHE`
and `SKWD_WALL_V2_SOCK`, if overridden, must agree for Deck and clients.

Use `pickOnlyMode: true` to inspect a catalogue without requesting wallpaper
application. Review theme/post-processing hooks, schedules, remote sources and
external integrations before explicitly enabling them. No personal config is shipped.
For selection/application syntax use the installed `skwd-helm --help`; this guide
does not invent a CLI migration contract across beta revisions.

Lens basic check (no downloads):

```sh
skwd-lens --list-packs --models-dir /absolute/path/to/empty-model-directory
```

Inference requires a compatible model pack and ONNX Runtime, installed explicitly
and with their own license/checksum review. No model, credential or SDK is bundled
automatically. Empty-pack listing does not establish model/inference compatibility.

## Niri, session startup and runit

Manual startup works without systemd. The owner has reported successful startup
and static restoration on one existing Niri/NVIDIA session, but its personal startup
configuration is NOT shipped. This preparation does not alter any active session.

Choose only one startup mechanism AFTER manual validation: an explicit Niri
session startup command or a per-user runit supervisor launched inside that session.
A service's basic command is `exec skwd-walld`; it needs the session's correct
HOME/XDG, XDG_RUNTIME_DIR, WAYLAND_DISPLAY and user identity. A system-wide root
service in /var/service does not acquire that environment correctly by magic.
No service template is installed/enabled and no global daemon is required.

Do not combine a Niri spawn entry with another daemon supervisor or assume a root
boot service can restore a user's Wayland wallpaper. Configure logs/lifetime for
that session and deliberately disable only your chosen startup entry when testing
rollback. Multi-session/X11 startup and cross-desktop synchronization remain outside
this publication's validation. Catalogue/schema rollback needs separate backups.
