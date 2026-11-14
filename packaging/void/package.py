#!/usr/bin/env python3
"""Assemble experimental XBPS archives from explicit build roots; never install."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import stat
import subprocess
import tomllib
from compliance import add_compliance

RECIPES = json.loads((Path(__file__).parent / "recipes.json").read_text())
VERSION = RECIPES["version"]
PINS = json.loads((Path(__file__).resolve().parents[2] / "security/void-beta27/sources.json").read_text())
assert VERSION.rsplit("_", 1)[0] == PINS["version"].replace("-beta.", "beta")
PRIVATE = set(RECIPES["private_sonames"])
NAMES = {c: r["package"] for c, r in RECIPES["components"].items()}
BINS = {c: r["binaries"] for c, r in RECIPES["components"].items()}
DLOPEN = {c: r["dlopen_dependencies"] for c, r in RECIPES["components"].items()}
SOURCE_DATE_EPOCH = int(os.environ.get("SOURCE_DATE_EPOCH", "1793905368"))


def sha(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def copy(source, destination, mode=0o644):
    assert source.is_file() and not source.is_symlink(), source
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    destination.chmod(mode)


def copy_tree(source, destination):
    assert source.is_dir() and not source.is_symlink(), source
    assert not any(p.is_symlink() for p in source.rglob("*")), source
    shutil.copytree(source, destination)


def run(*args):
    return subprocess.check_output(args, text=True)


def normalize_timestamps(stage, epoch):
    """Discard build/copy times without changing payload bytes or link targets."""
    if epoch < 0:
        raise ValueError("SOURCE_DATE_EPOCH must not be negative")
    for path in [*stage.rglob("*"), stage]:
        os.utime(path, (epoch, epoch), follow_symlinks=False)


def main():
    assert os.getuid() != 0, "Do not run as root"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-root", type=Path, required=True,
                        help="Directory containing wall/suite, deck/suite, lens/suite, paper/suite")
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    args = parser.parse_args()
    build_root = args.build_root.resolve()
    OUTPUT = args.output.resolve()
    assert not OUTPUT.exists(), "Output must be new; never overwrite packages"
    database = plistlib.loads(Path("/var/db/xbps/pkgdb-0.38.plist").read_bytes())
    providers = {}
    for name, package in database.items():
        if name.endswith("-32bit"):
            continue  # Payload ELF headers were checked as x86_64, not multilib i686.
        for soname in package.get("shlib-provides", []):
            providers.setdefault(soname, []).append(name)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    repository = OUTPUT / "repository"
    repository.mkdir(exist_ok=True)
    inventory = []
    for component in ("paper", "deck", "wall", "lens"):
        name = NAMES[component]
        stage = OUTPUT / "stage" / name
        assert not stage.exists(), f"Refusing to overwrite {stage}"
        stage.mkdir(parents=True)
        suite = build_root / component / "suite"
        manifest = json.loads((suite / "release-manifest.json").read_text())
        if manifest["version"] != PINS["version"] or {
            c: value["revision"] for c, value in manifest["products"].items()
        } != PINS["commits"]:
            raise ValueError("Build sources do not match the pinned coordinated beta.27 suite")
        source = suite / f"skwd-{component}"
        for binary, target in BINS[component].items():
            copy(suite / ".skwd-package/bin" / binary, stage / target, 0o755)
        license_name = {"wall": "skwd-wall-v2", "deck": "skwd-deck",
                        "paper": "skwd-paper", "lens": "skwd-lens"}[component]
        licenses = stage / "usr/share/licenses" / license_name
        copy(source / "LICENSE", licenses / "LICENSE")
        copy_tree(source / "LICENSES", licenses / "third-party")
        if component in ("wall", "deck"):
            for directory in (suite / "vendor").glob("option-ext-*"):
                copy(directory / "LICENSE.txt", licenses / "third-party" / directory.name / "LICENSE.txt")
                (licenses / "third-party" / directory.name / "SOURCE.txt").write_text(
                    f"Unmodified source: suite vendor/{directory.name}; crates.io package {directory.name}.\n")
        # Keep notices for every registry package resolved by this component's
        # workspace, including optional/target-specific entries (a safe superset).
        lock = tomllib.loads((source / "Cargo.lock").read_text())
        dependency_notices = []
        for dependency in lock["package"]:
            if not dependency.get("source", "").startswith("registry+"):
                continue
            key = dependency["name"] + "-" + dependency["version"]
            vendor = suite / "vendor" / key
            manifest = vendor / "Cargo.toml"
            metadata = tomllib.loads(manifest.read_text())["package"]
            notice = licenses / "registry" / key
            copy(manifest, notice / "Cargo.toml")
            count = 0
            for file in sorted(vendor.rglob("*")):
                if file.is_file() and (file.name.upper().startswith(("LICENSE", "LICENCE", "COPYING", "NOTICE"))
                                       or str(file.relative_to(vendor)) == metadata.get("license-file")):
                    copy(file, notice / file.relative_to(vendor))
                    count += 1
            dependency_notices.append(dict(package=key, license=metadata.get("license"),
                                           license_file=metadata.get("license-file"), notices=count,
                                           checksum=dependency["checksum"]))
        (licenses / "registry-inventory.json").write_text(json.dumps(dependency_notices, indent=2) + "\n")
        if component == "wall":
            for old, new in (("skwd-wall.desktop", "usr/share/applications/skwd-wall-v2.desktop"),
                             ("skwd-wall.metainfo.xml", "usr/share/metainfo/org.skwd.wall.v2.metainfo.xml")):
                text = (source / "data" / old).read_text()
                text = text.replace("Exec=skwd-wall\n", "Exec=skwd-wall-v2\n").replace("Icon=skwd-wall\n", "Icon=skwd-wall-v2\n")
                text = text.replace("<id>org.skwd.wall</id>", "<id>org.skwd.wall.v2</id>")
                text = text.replace(">skwd-wall.desktop</launchable>", ">skwd-wall-v2.desktop</launchable>")
                text = text.replace("<binary>skwd-wall</binary>", "<binary>skwd-wall-v2</binary>")
                target = stage / new
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text)
            copy(source / "data/skwd-wall.svg", stage / "usr/share/icons/hicolor/scalable/apps/skwd-wall-v2.svg")
        if component == "deck":
            copy_tree(source / "data/matugen/templates", stage / "usr/share/skwd-wall-v2/data/matugen/templates")
        if component == "paper":
            runtime = suite / ".skwd-package/ffmpeg"
            libdir = stage / "usr/lib/skwd-paper"
            libdir.mkdir(parents=True, exist_ok=True)
            for library in (runtime / "lib").glob("*.so.*"):
                if library.is_symlink():
                    target = os.readlink(library)
                    assert "/" not in target and target not in ("", ".", "..")
                    (libdir / library.name).symlink_to(target)
                else:
                    copy(library, libdir / library.name, 0o755)
            copy_tree(runtime / "share/licenses/ffmpeg", licenses / "ffmpeg")
            copy(source / "packaging/build-ffmpeg-runtime.sh", licenses / "ffmpeg/build-recipe.sh")
        add_compliance(stage, component, name, suite, licenses, PINS)
        dependencies = set(DLOPEN[component])
        public = set()
        elf = []
        for file in sorted(stage.rglob("*")):
            if file.is_symlink():
                assert file.resolve().is_relative_to(stage.resolve()), file
                continue
            if file.is_dir():
                file.chmod(0o755)
                continue
            assert file.is_file() and not (file.stat().st_mode & (stat.S_ISUID | stat.S_ISGID))
            with file.open("rb") as stream:
                is_elf = stream.read(4) == b"\x7fELF"
            file.chmod(0o755 if is_elf else 0o644)
            if not is_elf:
                continue
            header = run("readelf", "-h", str(file))
            assert "ELF64" in header and "Advanced Micro Devices X86-64" in header, file
            dynamic = run("readelf", "-d", str(file))
            needed = re.findall(r"\(NEEDED\).*?\[(.*?)\]", dynamic)
            paths = re.findall(r"\((?:RUNPATH|RPATH)\).*?\[(.*?)\]", dynamic)
            assert all(p in ("$ORIGIN", "$ORIGIN/../lib/skwd-paper") for p in paths), (file, paths)
            public.update(set(needed) - PRIVATE)
            versions = run("readelf", "-V", str(file))
            elf.append({"path": "/" + str(file.relative_to(stage)), "architecture": "x86_64",
                        "mode": oct(stat.S_IMODE(file.stat().st_mode)), "sha256": sha(file),
                        "needed": needed, "runpath": paths,
                        "glibc_versions": sorted(set(re.findall(r"GLIBC_[0-9.]+", versions)))})
        for soname in public:
            owners = providers.get(soname, [])
            assert len(owners) == 1, (soname, owners)
            dependencies.add(owners[0])
        runtime_dependencies = []
        for dep in sorted(dependencies):
            package = database[dep]
            version = package["pkgver"][len(dep) + 1:]
            runtime_dependencies.append(f"{dep}>={version}")
        if component in ("deck", "wall"):
            runtime_dependencies.append(f"{NAMES['paper']}-{VERSION}")
        if component == "wall":
            runtime_dependencies.append(f"{NAMES['deck']}-{VERSION}")
        # Building a new archive is allowed while the same package is installed.
        # Only its own registered paths are exempt; unrelated collisions still fail.
        owned_query = subprocess.run(['xbps-query', '-f', name], capture_output=True, text=True)
        owned_paths = {line.split(' -> ', 1)[0].strip() for line in owned_query.stdout.splitlines()
                       if line.strip().startswith('/')} if owned_query.returncode == 0 else set()
        payload = []
        collisions = []
        existing_owned_files = []
        for file in sorted(stage.rglob("*")):
            if file.is_dir() and not file.is_symlink():
                continue
            path = "/" + str(file.relative_to(stage))
            assert not any(token in path for token in ("/systemd/", "/autostart/", "/runit/", "/etc/")), path
            assert not path.endswith(".service"), path
            if Path(path).exists() or Path(path).is_symlink():
                if path in owned_paths:
                    existing_owned_files.append(path)
                else:
                    collisions.append(path)
            payload.append({"path": path, "symlink": os.readlink(file) if file.is_symlink() else None,
                            "sha256": None if file.is_symlink() else sha(file)})
        assert not collisions, collisions
        license_value = RECIPES["components"][component]["license"]
        command = ["xbps-create", "-A", "x86_64", "-n", f"{name}-{VERSION}", "-s",
                   f"Experimental local Skwd {component} beta.27 for Void Linux", "-l", license_value,
                   "-H", f"https://github.com/liixini/skwd-{component}", "-B", "local Void glibc; Rust 1.99.0; beta.27 coordinated",
                   "-D", " ".join(runtime_dependencies), "--shlib-requires", " ".join(sorted(public)), str(stage)]
        normalize_timestamps(stage, SOURCE_DATE_EPOCH)
        environment = dict(os.environ, SOURCE_DATE_EPOCH=str(SOURCE_DATE_EPOCH))
        process = subprocess.run(command, cwd=repository, capture_output=True, text=True,
                                 env=environment)
        archive = repository / f"{name}-{VERSION}.x86_64.xbps"
        item = {"name": name, "component": component, "version": VERSION, "command": command,
                "exit_code": process.returncode, "stdout": process.stdout, "stderr": process.stderr,
                "source_date_epoch": SOURCE_DATE_EPOCH,
                "dependencies": runtime_dependencies, "shlib_requires": sorted(public),
                "dlopen_dependencies": DLOPEN[component], "elf": elf, "payload": payload,
                "existing_file_collisions": collisions, "existing_owned_files": existing_owned_files, "stage": str(stage), "archive": str(archive),
                "license_review": "project and bundled notices retained; metadata is descriptive, not a completed legal audit"}
        if archive.exists():
            item.update(archive_sha256=sha(archive), archive_size=archive.stat().st_size)
        inventory.append(item)
        (OUTPUT / "packages.json").write_text(json.dumps(inventory, indent=2) + "\n")
        print(component, process.returncode, runtime_dependencies, flush=True)
        assert process.returncode == 0, process.stderr
    subprocess.run(["xbps-rindex", "-a", *[x["archive"] for x in inventory]], check=True)


if __name__ == "__main__":
    main()
