#!/usr/bin/env python3
"""Stage an offline beta.29 build suite from verified official and Void inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tomllib

HERE = Path(__file__).resolve().parent
COMPONENTS = ("wall", "deck", "lens", "paper")
SUITE_NAME = "skwd-suite-1.0.0-beta.29"
SUITE_SHA = "da903c5e999ad7792dcb3b5e5d7db1820de092abe92942329211483518617df4"
HISTORICAL_MANIFEST_SHA = "d059030e1bc8d954d86cfd5fe44dc5c9fc713fad0dc50c56d1d0da2a442ccece"
FONT_SHA = "2289860dbd2201295bf451deb155561abf4b1fb06899d6f1f81eb294bfebb7ec"
RUSTIX_OLD = "b6fe4565b9518b83ef4f91bb47ce29620ca828bd32cb7e408f0062e9930ba190"
RUSTIX_NEW = "e5e76742e5294153d4dde1207dbec5bdd81eef6fabdc0d2118babadabfd858aa"
LRU_NEW = "5d2f2f9b4ba7e6b24d95e7e899329d35be83bcded72c8540cdd5368932d1d90a"
FFMPEG_VERSION = "9.1"
FFMPEG_COMMIT = "74e4393595cf2b5857f0da925c4e0dd74ea306e5"
FFMPEG_SHA = "1a4d394ae63d190a526cd052eb4415c156b5c5e2df37efab41a7de0b8fde2433"
FFMPEG_PATCH_COMMIT = "60bc31fcf6543505e6d2fc1a9399cca95f54ba4d"
FFMPEG_PATCH_SHA = "879a5869de63b3300ddb36e430610b15b58b5a575942dab900833857153acfad"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require_hash(path, expected):
    if path.is_symlink() or digest(path) != expected:
        raise ValueError(f"Checksum mismatch: {path}")


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Unexpected lockfile baseline: {old!r}")
    return text.replace(old, new, 1)


def update_lock(path, component):
    original = path.read_text()
    packages = tomllib.loads(original)["package"]
    lock = replace_once(
        original,
        f'name = "rustix"\nversion = "1.1.4"\nsource = "registry+https://github.com/rust-lang/crates.io-index"\nchecksum = "{RUSTIX_OLD}"',
        f'name = "rustix"\nversion = "1.1.6"\nsource = "registry+https://github.com/rust-lang/crates.io-index"\nchecksum = "{RUSTIX_NEW}"',
    ).replace('"rustix 1.1.4"', '"rustix 1.1.6"')
    if component == "wall":
        cryo = next(p for p in packages if p["name"] == "cryoglyph")
        lru = next(p for p in packages if p["name"] == "lru")
        lock = replace_once(
            lock,
            f'name = "cryoglyph"\nversion = "0.1.0"\nsource = "{cryo["source"]}"\nchecksum = "{cryo["checksum"]}"',
            'name = "cryoglyph"\nversion = "0.1.0"',
        )
        lock = replace_once(lock, 'name = "lru"\nversion = "0.16.4"', 'name = "lru"\nversion = "0.18.2"')
        lock = replace_once(lock, lru["checksum"], LRU_NEW)
    path.write_text(lock)


def stage(args):
    if os.getuid() == 0:
        raise ValueError("Run source preparation as an ordinary user")
    require_hash(args.archive, SUITE_SHA)
    require_hash(args.historical_manifest, HISTORICAL_MANIFEST_SHA)
    require_hash(args.ffmpeg_archive, FFMPEG_SHA)
    ffmpeg_patch = HERE / "patches" / f"{FFMPEG_PATCH_COMMIT}.patch"
    require_hash(ffmpeg_patch, FFMPEG_PATCH_SHA)
    historical = args.historical_suite.resolve(strict=True)
    rows = {row["path"]: row["sha256"] for row in json.loads(args.historical_manifest.read_text())["files"]}
    output = args.output.resolve()
    if args.output.is_symlink() or output.exists() or output.is_relative_to(historical):
        raise ValueError("Output must be new and outside the historical suite")
    output.mkdir(mode=0o700)
    with tarfile.open(args.archive) as archive:
        for member in archive.getmembers():
            name = Path(member.name)
            if name.is_absolute() or ".." in name.parts or not name.parts or name.parts[0] != SUITE_NAME or not (member.isfile() or member.isdir()):
                raise ValueError(f"Unexpected archive member: {member.name}")
        archive.extractall(output, filter="data")
    suite = output / "suite"
    (output / SUITE_NAME).rename(suite)
    require_hash(suite / "vendor/iced_graphics-0.14.0/fonts/Iced-Icons.ttf", FONT_SHA)

    prefixes = (
        "vendor/rustix-1.1.6/", "vendor/lru-0.18.2/",
        "skwd-wall/vendor-patches/cryoglyph-0.1.0/",
        "skwd-wall/LICENSES/remediation/",
    )
    exact = {f"skwd-wall/assets/RobotoCondensed-Bold-{suffix}.ttf"
             for suffix in ("UI", "AR", "BN", "HI", "JP", "SC")}
    imported = {}
    for name, expected in sorted(rows.items()):
        if not name.startswith("suite/"):
            continue
        relative = name.removeprefix("suite/")
        if relative not in exact and not relative.startswith(prefixes):
            continue
        source = historical / relative
        require_hash(source, expected)
        target = suite / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        imported[relative] = expected
    if not exact.issubset(imported) or any(not any(r.startswith(p) for r in imported) for p in prefixes):
        raise ValueError("Incomplete imports from historical manifest")

    patch = HERE / "patches/void-port.patch"
    subprocess.run(["patch", "--batch", "--forward", "--fuzz=0", "-p1", "-i", str(patch)], cwd=suite, check=True)
    for name in ("Flower-3.webp", "Tori-Jade.webp"):
        (suite / "skwd-wall/data/preview" / name).unlink()
    for name in ("cryoglyph-0.1.0", "lru-0.16.4", "rustix-1.1.4"):
        shutil.rmtree(suite / "vendor" / name)
    (suite / "vendor-ffmpeg/ffmpeg-9.0.1.tar.xz").unlink()
    native_archive = f"vendor-ffmpeg/ffmpeg-{FFMPEG_VERSION}.tar.xz"
    native_patch = f"vendor-ffmpeg/security-patches/{ffmpeg_patch.name}"
    (suite / native_patch).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.ffmpeg_archive, suite / native_archive)
    shutil.copyfile(ffmpeg_patch, suite / native_patch)
    notice_sources = {
        "skwd-wall/LICENSES/remediation": sorted((HERE / "notices/wall").iterdir()),
        "skwd-deck/LICENSES/void-redistribution": [
            *sorted((HERE / "notices/deck").iterdir()),
            HERE.parents[1] / "docs/void/BETA27-5-DECK-IMAGE-CREDITS.md",
        ],
        "skwd-paper/LICENSES/void-redistribution": [
            HERE.parents[1] / "docs/void/notices/Roboto-3.015-OFL.txt",
        ],
    }
    notices = {}
    for relative, files in notice_sources.items():
        destination = suite / relative
        destination.mkdir(exist_ok=True)
        for notice in files:
            shutil.copyfile(notice, destination / notice.name)
            notices[f"{relative}/{notice.name}"] = digest(notice)
    for component in COMPONENTS:
        update_lock(suite / f"skwd-{component}/Cargo.lock", component)
    release = json.loads((suite / "release-manifest.json").read_text())
    receipt = {
        "scope": "build inputs only; original SBOM and release policy are upstream evidence",
        "version": release["version"],
        "commits": {c: release["products"][c]["revision"] for c in COMPONENTS},
        "original_archive_sha256": SUITE_SHA,
        "historical_manifest_sha256": HISTORICAL_MANIFEST_SHA,
        "imports": imported,
        "patch_sha256": digest(patch),
        "notices": notices,
        "ffmpeg": {
            "version": FFMPEG_VERSION, "commit": FFMPEG_COMMIT,
            "path": native_archive, "sha256": FFMPEG_SHA,
            "patches": {native_patch: FFMPEG_PATCH_SHA},
        },
        "locks": {c: digest(suite / f"skwd-{c}/Cargo.lock") for c in COMPONENTS},
        "native_recipe_sha256": digest(suite / "skwd-paper/packaging/build-ffmpeg-runtime.sh"),
        "source_date_epoch": release["source_date_epoch"],
    }
    (output / "sources.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in ("archive", "historical_manifest", "historical_suite", "output"):
        parser.add_argument(argument, type=Path)
    parser.add_argument("--ffmpeg-archive", type=Path, required=True)
    stage(parser.parse_args())
