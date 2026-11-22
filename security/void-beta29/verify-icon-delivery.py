#!/usr/bin/env python3
"""Verify icon payloads, the XBPS index and the coordinated beta29_2 delta."""
import argparse
import hashlib
import json
from pathlib import Path
import plistlib
import runpy
import tarfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
VERSION = "1.0.0beta29_2"
PREVIOUS = "1.0.0beta29_1"
FONT_NAMES = ("SymbolsNerdFont-Regular.ttf", "Iced-Icons.ttf")
WALL = "skwd-wall-v2-local"


def scan(archive, retired):
    with tarfile.open(archive, "r|*") as stream:
        for member in stream:
            if Path(member.name).name in FONT_NAMES:
                raise ValueError(f"Retired member in {archive.name}: {member.name}")
            if member.isfile():
                data = stream.extractfile(member).read()
                if any(font in data for font in retired):
                    raise ValueError(f"Retired font bytes in {archive.name}: {member.name}")
                yield member, data


def audit(candidate, baseline, references, source):
    inventory = runpy.run_path(str(ROOT / "packaging/void/compare.py"))["inventory"]
    before = inventory(baseline)
    after = inventory(candidate)
    assert set(before) == set(after) and len(after) == 4
    fonts = HERE / "icons"
    manifest = json.loads((fonts / "glyphs.json").read_text())
    retired = tuple((references / (key + "-original.ttf")).read_bytes() for key in ("wall", "iced"))
    generated = tuple((fonts / name).read_bytes() for name in
                      ("Skwd-Experiment-Wall-Icons.ttf", "Skwd-Experiment-Widget-Icons.ttf"))
    for key, old, new in zip(("wall", "iced"), retired, generated, strict=True):
        assert hashlib.sha256(old).hexdigest() == manifest[key]["original_sha256"]
        assert hashlib.sha256(new).hexdigest() == manifest[key]["experimental_sha256"]
    repo = candidate / "repository"
    with tarfile.open(repo / "x86_64-repodata") as stream:
        index = plistlib.load(stream.extractfile("index.plist"))
    assert set(index) == set(after)
    report = {}
    for name, new in after.items():
        old = before[name]
        assert new["dependencies"] == [dep.replace(PREVIOUS, VERSION) for dep in old["dependencies"]]
        assert new["properties"]["architecture"] == "x86_64"
        assert new["properties"]["pkgver"] == index[name]["pkgver"] == f"{name}-{VERSION}"
        assert index[name]["filename-sha256"] == new["archive_sha256"]
        assert not new["properties"].get("conflicts") and not new["properties"].get("replaces")
        assert set(new["elf"]) == set(old["elf"])
        changed_elf = [path for path in new["elf"] if new["elf"][path] != old["elf"][path]]
        assert changed_elf == (["/usr/bin/skwd-wall-v2"] if name == WALL else []), changed_elf
        assert all(new["file_metadata"][path] == old["file_metadata"][path]
                   for path in new["file_metadata"].keys() & old["file_metadata"].keys())
        notices = {}
        for member, data in scan(repo / f"{name}-{VERSION}.x86_64.xbps", retired):
            path = member.name.removeprefix("./")
            assert Path(path).name not in {"INSTALL", "REMOVE"}
            if "/licenses/" in path:
                notices[path] = hashlib.sha256(data).hexdigest()
            if path == "usr/bin/skwd-wall-v2":
                assert all(data.count(font) == 1 for font in generated)
        if name == WALL:
            license_path = "usr/share/licenses/skwd-wall-v2/third-party/tabler-icons/TABLER-LICENSE.txt"
            assert notices[license_path] == hashlib.sha256((fonts / "TABLER-LICENSE.txt").read_bytes()).hexdigest()
        report[name] = {
            "version": VERSION,
            "sha256": new["archive_sha256"],
            "dependencies": new["dependencies"],
            "changed_elf": changed_elf,
            "added_files": sorted(new["payload"].keys() - old["payload"].keys()),
            "removed_files": sorted(old["payload"].keys() - new["payload"].keys()),
            "changed_files": sorted(path for path in new["payload"].keys() & old["payload"].keys()
                                    if new["payload"][path] != old["payload"][path]),
            "notices": notices,
        }
    if source:
        found = set()
        expected = dict(zip(("Skwd-Experiment-Wall-Icons.ttf", "Skwd-Experiment-Widget-Icons.ttf"),
                            generated, strict=True))
        for member, data in scan(source, retired):
            basename = Path(member.name).name
            if basename in expected:
                assert data == expected[basename]
                found.add(member.name)
        assert found == {
            "suite/skwd-wall/assets/Skwd-Experiment-Wall-Icons.ttf",
            "suite/vendor/iced_graphics-0.14.0/fonts/Skwd-Experiment-Widget-Icons.ttf",
            "void-port/security/void-beta29/icons/Skwd-Experiment-Wall-Icons.ttf",
            "void-port/security/void-beta29/icons/Skwd-Experiment-Widget-Icons.ttf",
        }, found
    return {"packages": report, "icon_provenance": manifest, "source_font_check": bool(source)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("references", type=Path)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.candidate, args.baseline, args.references, args.source), indent=2))
