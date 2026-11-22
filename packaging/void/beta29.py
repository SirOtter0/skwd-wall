"""Validated input and license material for the beta.29 local candidate."""

import hashlib
from itertools import islice
import json
from pathlib import Path
import shutil
import tomllib

ROOT = Path(__file__).resolve().parents[2]
PINS = json.loads((ROOT / "security/void-beta29/xbps-inputs.json").read_text())
COMPONENTS = ("wall", "deck", "lens", "paper")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require_digest(path, expected):
    if not path.is_file() or path.is_symlink() or digest(path) != expected:
        raise ValueError(f"Unexpected beta.29 file: {path}")


def validate_sources(suite, receipt):
    require_digest(receipt, PINS["receipt_sha256"])
    provenance = json.loads(receipt.read_text())
    release = json.loads((suite / "release-manifest.json").read_text())
    if (set(release["products"]) != set(COMPONENTS)
            or {c: release["products"][c]["revision"] for c in COMPONENTS} != provenance["commits"]
            or release["version"] != provenance["version"]
            or release["source_date_epoch"] != provenance["source_date_epoch"]):
        raise ValueError("Coordinated beta.29 release mismatch")
    native = provenance["ffmpeg"]
    require_digest(suite / native["path"], native["sha256"])
    require_digest(suite / "skwd-paper/packaging/build-ffmpeg-runtime.sh",
                   provenance["native_recipe_sha256"])
    for path, expected in (provenance["imports"] | provenance["notices"] | native["patches"]).items():
        require_digest(suite / path, expected)
    icons = provenance["icon_replacement"]
    for relative, expected in icons["changed"].items():
        require_digest(suite / relative, expected)
    for relative in icons["removed"]:
        retired = suite / relative
        if retired.exists() or retired.is_symlink():
            raise ValueError(f"Retired font or notice remains: {relative}")
    for component, expected in provenance["locks"].items():
        require_digest(suite / f"skwd-{component}/Cargo.lock", expected)
    return provenance


def native_delivery(directory):
    manifest = directory / "SHA256SUMS"
    require_digest(manifest, PINS["native_manifest_sha256"])
    names = {row.split(maxsplit=1)[1]: row.split(maxsplit=1)[0]
             for row in manifest.read_text().splitlines()}
    if set(names) | {"SHA256SUMS"} != {path.name for path in directory.iterdir()}:
        raise ValueError("Unexpected files in native delivery")
    for name, expected in names.items():
        require_digest(directory / name, expected)
    return [directory / name for name in sorted(set(names) | {"SHA256SUMS"})]


def add_component_notices(suite, component, licenses):
    if component == "wall":
        local = suite / "skwd-wall/vendor-patches/cryoglyph-0.1.0"
        destination = licenses / "local-overrides" / "cryoglyph-0.1.0"
        destination.mkdir(parents=True)
        for name in ("Cargo.toml", "LICENSE-APACHE", "LICENSE-MIT", "LICENSE-ZLIB"):
            shutil.copyfile(local / name, destination / name)
        (destination / "SOURCE.txt").write_text(
            "The corresponding source archive includes suite/skwd-wall/vendor-patches/cryoglyph-0.1.0.\n")
    if component == "deck":
        sqlite = next(entry for entry in tomllib.loads((suite / "skwd-deck/Cargo.lock").read_text())["package"]
                      if entry["name"] == "libsqlite3-sys")
        source = suite / "vendor" / ("libsqlite3-sys-" + sqlite["version"]) / "sqlite3/sqlite3.c"
        with source.open() as stream:
            header = "".join(islice(stream, 100))
        marker = "** The author disclaims copyright to this source code."
        if marker not in header:
            raise ValueError("Missing SQLite copyright notice")
        start = header.rfind("/*", 0, header.index(marker))
        end = header.index("*/", header.index(marker)) + 2
        (licenses / "SQLITE-SOURCE.txt").write_text(header[start:end] + "\n")
    (licenses / "SOURCE-DELIVERY.txt").write_text(
        f"Keep the matching {PINS['version']} corresponding-source.tar.xz and its SHA-256 manifest beside the XBPS.\n"
        "This local candidate is unsigned and has no distribution approval.\n")
