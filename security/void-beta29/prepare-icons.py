#!/usr/bin/env python3
"""Prepare beta29_2 sources in a new directory from the pinned beta29_1 suite."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
BASE_RECEIPT = "1fc883bd0e1ce3e65cff3f587e6bb2b4e2e3052d0bb62ba1e77a0504d8e8aea8"
FILES = (
    ("wall", "skwd-wall/assets", "skwd-wall/src/shell/shell.rs",
     "SymbolsNerdFont-Regular.ttf", "Skwd-Experiment-Wall-Icons.ttf"),
    ("iced", "vendor/iced_graphics-0.14.0/fonts", "vendor/iced_graphics-0.14.0/src/text.rs",
     "Iced-Icons.ttf", "Skwd-Experiment-Widget-Icons.ttf"),
)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def replace_once(path, old, new):
    text = path.read_text()
    if text.count(old) != 1:
        raise ValueError(f"Unexpected baseline in {path}")
    path.write_text(text.replace(old, new))


def prepare(base, output):
    if digest(base / "sources.json") != BASE_RECEIPT:
        raise ValueError("Expected the validated beta29_1 source receipt")
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(base.resolve()):
        raise ValueError("Output must be new and outside the baseline")
    output.mkdir(mode=0o700)
    suite = output / "suite"
    shutil.copytree(base / "suite", suite, symlinks=True)
    baseline = json.loads((base / "sources.json").read_text())
    icons = HERE / "icons"
    inventory = json.loads((icons / "glyphs.json").read_text())
    changes = {}
    removed = {}
    for face, relative, source, original, replacement in FILES:
        old = suite / relative / original
        new = suite / relative / replacement
        row = inventory[face]
        if digest(old) != row["original_sha256"] or digest(icons / replacement) != row["experimental_sha256"]:
            raise ValueError(f"Unexpected icon inputs: {face}")
        shutil.copyfile(icons / replacement, new)
        replace_once(suite / source, f'{original}"', f'{replacement}"')
        removed[str(old.relative_to(suite))] = digest(old)
        old.unlink()
        changes[str(new.relative_to(suite))] = digest(new)
        changes[source] = digest(suite / source)
    test = "skwd-wall/src/shell/tests.rs"
    replace_once(suite / test, "assert!(NERD_FONT_BYTES.len() > 100_000);",
                 'assert!(NERD_FONT_BYTES.starts_with(b"\\0\\x01\\0\\0"));')
    changes[test] = digest(suite / test)
    vendor = suite / "vendor/iced_graphics-0.14.0"
    checksums = vendor / ".cargo-checksum.json"
    metadata = json.loads(checksums.read_text())
    if metadata["files"].pop("fonts/Iced-Icons.ttf") != inventory["iced"]["original_sha256"]:
        raise ValueError("Iced vendor manifest mismatch")
    for name in ("src/text.rs", "fonts/Skwd-Experiment-Widget-Icons.ttf"):
        metadata["files"][name] = digest(vendor / name)
    checksums.write_text(json.dumps(metadata, sort_keys=True) + "\n")
    changes[str(checksums.relative_to(suite))] = digest(checksums)
    for name in ("Iced-Icons-PROVENANCE.txt", "Font-Awesome-OFL-1.1.txt"):
        relative = f"skwd-wall/LICENSES/remediation/{name}"
        if digest(suite / relative) != baseline["notices"].pop(relative):
            raise ValueError(f"Historical notice differs: {name}")
        removed[relative] = digest(suite / relative)
        (suite / relative).unlink()
    notices = suite / "skwd-wall/LICENSES/tabler-icons"
    notices.mkdir()
    for name in ("TABLER-LICENSE.txt", "PROVENANCE.md", "glyphs.json"):
        shutil.copyfile(icons / name, notices / name)
        baseline["notices"][str((notices / name).relative_to(suite))] = digest(notices / name)
    baseline["icon_replacement"] = {
        "approved_experiment": "bc30345",
        "base_receipt_sha256": BASE_RECEIPT,
        "changed": changes,
        "removed": removed,
    }
    (output / "sources.json").write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    prepare(args.baseline, args.output)
