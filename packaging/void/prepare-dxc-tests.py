#!/usr/bin/env python3
"""Extract the exact upstream CI DXC into a new test-only directory."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('build_directory', type=Path)
parser.add_argument('archive', type=Path)
args = parser.parse_args()
policy = Path(__file__).resolve().parents[2] / 'security/void-beta27/test-inputs.json'
pin = json.loads(policy.read_text())['dxc']
if args.archive.stat().st_size != pin['archive_bytes']:
    raise ValueError('Wrong DXC archive size')
with args.archive.open('rb') as source:
    if hashlib.file_digest(source, 'sha256').hexdigest() != pin['sha256']:
        raise ValueError('Wrong DXC archive checksum')
destination = args.build_directory / 'test-inputs/dxc'
if destination.exists() or destination.is_symlink():
    raise ValueError('DXC destination must be new')
with tarfile.open(args.archive) as archive:
    for member in archive.getmembers():
        path = PurePosixPath(member.name)
        if (path.is_absolute() or '..' in path.parts
                or not (member.isfile() or member.isdir())):
            raise ValueError('Unexpected DXC archive member')
    destination.mkdir(parents=True)
    archive.extractall(destination, filter='data')
print(destination)
