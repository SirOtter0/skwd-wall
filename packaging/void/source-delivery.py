#!/usr/bin/env python3
"""Create a local source delivery from a verified prepared suite and tracked port files.

This verifies integrity, not legal approval or binary reproducibility.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tarfile
import tomllib

import beta29

from compliance import validate_revision7_wall

ROOT = Path(__file__).resolve().parents[2]
VERSION = json.loads((ROOT/"packaging/void/recipes.json").read_text())["version"]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_path(name):
    p = Path(name)
    if p.is_absolute() or '..' in p.parts or '.git' in p.parts:
        raise ValueError('Unsafe source path')
    return p


def validate_delivery_revision(release, expected_version=None):
    expected_version = expected_version or VERSION
    legacy_default = expected_version if expected_version == '1.0.0beta27_3' else None
    if release.get('void_package_version', legacy_default) != expected_version:
        raise ValueError('Source revision differs from this delivery recipe; do not relabel sources')


def prepare(suite, output, native_notices=None):
    if os.getuid() == 0 or suite.is_symlink() or output.exists() or output.is_symlink():
        raise ValueError('Normal user, regular input and new output required')
    current = native_notices is not None
    version = beta29.PINS["version"] if current else VERSION
    receipt = suite.parent / "sources.json"
    if current:
        provenance = beta29.validate_sources(suite, receipt)
        native_inputs = beta29.native_delivery(native_notices)
        epoch = provenance["source_date_epoch"]
    else:
        provenance = json.loads(receipt.read_text())
        native_inputs = []
        pins = json.loads((ROOT/'security/void-beta27/sources.json').read_text())
        release = json.loads((suite/'release-manifest.json').read_text())
        validate_delivery_revision(release)
        if release['version'] != pins['version'] or {c: v['revision'] for c,v in release['products'].items()} != pins['commits']:
            raise ValueError('Release manifest mismatch')
        if provenance['original_archive_sha256'] != pins['original_archive_sha256'] or provenance['commits'] != pins['commits']:
            raise ValueError('Coordinated source mismatch')
        if provenance['ffmpeg'] != {k: pins['ffmpeg'][k] for k in ('version','path','sha256')}:
            raise ValueError('Native source mismatch')
        if digest(suite/pins['ffmpeg']['path']) != pins['ffmpeg']['sha256']:
            raise ValueError('FFmpeg checksum mismatch')
        for name, expected in provenance['patches'].items():
            if digest(ROOT/'security/void-beta27/patches'/name) != expected:
                raise ValueError('Patch mismatch')
        if digest(suite/'skwd-paper/packaging/build-ffmpeg-runtime.sh') != provenance['native_recipe_sha256']:
            raise ValueError('Native recipe mismatch')
        if VERSION in ('1.0.0beta27_4', '1.0.0beta27_5', '1.0.0beta27_6', '1.0.0beta27_7'):
            revision = ROOT/'security/void-beta27/revision4'
            for name, expected in provenance['security_revision4']['patches'].items():
                if digest(revision/'patches'/name) != expected:
                    raise ValueError('Security patch changed')
            if digest(suite/'skwd-deck/vendor/libsqlite3-sys/sqlite3/sqlite3.c') != provenance['security_revision4']['sqlite_c_sha256']:
                raise ValueError('Local SQLite source changed')
        if VERSION in ('1.0.0beta27_5', '1.0.0beta27_6', '1.0.0beta27_7'):
            patches = suite/'vendor-ffmpeg/security-patches'
            expected = provenance['ffmpeg_security_patches']
            if {p.name: digest(p) for p in patches.iterdir()} != expected:
                raise ValueError('FFmpeg security patch integrity mismatch')
        if VERSION in ('1.0.0beta27_6', '1.0.0beta27_7'):
            wall = suite/'skwd-wall'
            forbidden = {'Flower-3.webp', 'Tori-Jade.webp'}
            if any(p.name in forbidden for p in wall.rglob('*')):
                raise ValueError('Retired preview is present in Wall sources')
            for name, expected in provenance['wall_remediation']['font_sha256'].items():
                if digest(wall/'assets'/safe_path(name)) != expected:
                    raise ValueError('Regenerated font mismatch')
            patch = ROOT/'security/void-beta27/proposals/skwd-wall-generated-previews.patch'
            if digest(patch) != provenance['wall_remediation']['preview_patch_sha256']:
                raise ValueError('Preview patch mismatch')
        if VERSION == '1.0.0beta27_7':
            validate_revision7_wall(suite)
        epoch = pins["source_date_epoch"]
    registry = {}
    for component, expected in provenance['locks'].items():
        lock = suite/f'skwd-{component}/Cargo.lock'
        if digest(lock) != expected:
            raise ValueError('Lock mismatch')
        for entry in tomllib.loads(lock.read_text())['package']:
            if entry.get('source','').startswith('registry+'):
                key = entry['name']+'-'+entry['version']
                if key in registry and registry[key] != entry['checksum']:
                    raise ValueError('Conflicting registry checksum')
                registry[key] = entry['checksum']
    for key, checksum in registry.items():
        vendor = suite/'vendor'/key
        metadata = json.loads((vendor/'.cargo-checksum.json').read_text())
        if metadata['package'] != checksum:
            raise ValueError('Registry package checksum mismatch: '+key)
        actual = {str(p.relative_to(vendor)) for p in vendor.rglob('*') if p.is_file()}
        if actual != set(metadata['files']) | {'.cargo-checksum.json'}:
            raise ValueError('Unlisted vendor files: '+key)
        for rel, expected in metadata['files'].items():
            path = vendor/safe_path(rel)
            if path.is_symlink() or digest(path) != expected:
                raise ValueError('Vendor content mismatch: '+key+'/'+rel)
    allowed = {'.cargo','SBOM.spdx.json','distribution','release-manifest.json',
               'release-policy','release-policy-report.json','skwd-wall','skwd-deck',
               'skwd-lens','skwd-paper','vendor','vendor-ffmpeg'}
    if {p.name for p in suite.iterdir()} != allowed:
        raise ValueError('Unexpected suite top-level entries')
    # SDK native payloads are not covered by a wrapper's license.
    for folder in (suite/'vendor').glob('steamworks-sys-*'):
        if any(p.is_file() for p in (folder/'lib').rglob('*')):
            raise ValueError('Steam SDK payload requires separate redistribution review')
    port_paths = ["packaging/void", "security/void-beta27", "LICENSE"]
    if current:
        port_paths.extend(["security/void-beta29", "docs/void/BETA27-5-DECK-IMAGE-CREDITS.md",
                           "docs/void/notices/Roboto-3.015-OFL.txt",
                           "experiments/beta29-icons/generate.py",
                           "experiments/beta29-icons/build.sh",
                           "experiments/beta29-icons/TABLER-LICENSE.txt"])
    port_names = subprocess.check_output(["git", "ls-files", "-z", "--", *port_paths], cwd=ROOT).decode().split("\0")
    subprocess.run(["git", "diff", "--exit-code", "HEAD", "--", *port_paths],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    port_commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    paths = sorted(suite.rglob('*'))
    if any(p.is_symlink() for p in paths):
        raise ValueError('Source symlink requires review')
    inputs = [('suite/'+str(p.relative_to(suite)),p) for p in paths if not p.is_dir()]
    rebuild = ROOT / ("security/void-beta29/README.md" if current else "docs/void/SOURCE-REBUILD.md")
    inputs += [("sources.json", receipt), ("REBUILD.md", rebuild)]
    inputs += [("native-ffmpeg/" + path.name, path) for path in native_inputs]
    inputs += [('void-port/'+name,ROOT/name) for name in port_names if name]
    if not current and VERSION in ('1.0.0beta27_6', '1.0.0beta27_7'):
        for name in ('BETA27-5-DECK-IMAGE-CREDITS.md', 'notices/Roboto-3.015-OFL.txt',
                     'notices/Iced-MIT.txt', 'BETA27-5-FONT-ICON-CLOSURE.md'):
            path = ROOT/'docs/void'/name
            inputs.append(('void-port/docs/void/'+name, path))
    output.mkdir(mode=0o700, parents=False)
    archive = output/'corresponding-source.tar.xz'
    files = []
    with tarfile.open(archive,'w:xz',preset=1) as tar:
        for name, path in inputs:
            safe_path(name)
            if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o6000:
                raise ValueError('Unexpected source file type/mode: '+name)
            item = tarfile.TarInfo(name)
            item.size = path.stat().st_size
            item.mode = stat.S_IMODE(path.stat().st_mode)
            item.mtime = epoch
            with path.open('rb') as stream:
                tar.addfile(item,stream)
            files.append({'path':name,'sha256':digest(path),'bytes':item.size,'mode':item.mode})
        manifest = {'schema':1,'package_version':version,'files':files,
                    'registry_packages_verified':len(registry),'source_provenance':provenance,'port_commit':port_commit,
                    'distribution_approved':False,'legal_approval':False,
                    'note':'Vendor metadata and file hashes checked; not a fresh independent crates.io authentication or binary build.'}
        data = (json.dumps(manifest,indent=2)+'\n').encode()
        item = tarfile.TarInfo('SOURCE-FILES.json'); item.size=len(data); item.mode=0o644; item.mtime=epoch
        tar.addfile(item,io.BytesIO(data))
    # Verify the actual archive, not just its input inventory.
    expected = {row['path']:row for row in files}
    seen = set()
    with tarfile.open(archive,'r:xz') as tar:
        for item in tar:
            if item.name == 'SOURCE-FILES.json':
                if tar.extractfile(item).read() != data: raise ValueError('Embedded manifest mismatch')
                continue
            row = expected[item.name]
            if item.name in seen or not item.isfile() or item.mode != row['mode']:
                raise ValueError('Archive entry mismatch')
            seen.add(item.name)
            if hashlib.file_digest(tar.extractfile(item),'sha256').hexdigest() != row['sha256']:
                raise ValueError('Archive bytes mismatch')
    if seen != set(expected): raise ValueError('Missing archive files')
    (output/'SOURCE-FILES.json').write_bytes(data)
    result = {'archive':archive.name,'archive_sha256':digest(archive),'archive_bytes':archive.stat().st_size,
              'manifest_sha256':hashlib.sha256(data).hexdigest(),'files':len(files),
              'archive_verified':True,'distribution_approved':False,'legal_approval':False}
    (output/'SOURCE-RECEIPT.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite',type=Path); parser.add_argument('output',type=Path)
    parser.add_argument("--beta29-native-notices", type=Path)
    args=parser.parse_args()
    print(json.dumps(prepare(args.suite.absolute(), args.output.absolute(), args.beta29_native_notices), indent=2))
