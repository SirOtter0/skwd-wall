#!/usr/bin/env python3
"""Copy only the verified test SDK runtime; do not modify vendor or package it."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('build_directory', type=Path)
parser.add_argument('archive', type=Path)
args = parser.parse_args()
policy = Path(__file__).resolve().parents[2] / 'security/void-beta27'
pin = json.loads((policy / 'test-inputs.json').read_text())['steamworks']
suite = json.loads((policy / 'sources.json').read_text())
if args.archive.stat().st_size != pin['archive_bytes']:
    raise ValueError('Wrong Steamworks companion size')
with args.archive.open('rb') as source:
    if hashlib.file_digest(source, 'sha256').hexdigest() != pin['sha256']:
        raise ValueError('Wrong Steamworks companion checksum')
root = 'skwd-deck-steamworks-1.0.0-beta.27/'
with tarfile.open(args.archive) as archive:
    manifest = json.load(archive.extractfile(root + 'companion-manifest.json'))
    if (manifest['version'] != suite['version']
            or manifest['deck_revision'] != suite['commits']['deck']
            or manifest['paper_revision'] != suite['commits']['paper']):
        raise ValueError('Wrong coordinated Steamworks revisions')
    name = root + 'vendor/steamworks-sys-0.13.0/lib/steam/redistributable_bin/linux64/libsteam_api.so'
    member = archive.getmember(name)
    if not member.isfile():
        raise ValueError('Runtime must be a regular file')
    data = archive.extractfile(member).read()
    if hashlib.sha256(data).hexdigest() != pin['runtime_sha256']:
        raise ValueError('Wrong Steamworks runtime checksum')
destination = args.build_directory / 'test-inputs/steam-sdk/redistributable_bin/linux64/libsteam_api.so'
destination.parent.mkdir(parents=True, exist_ok=True)
with destination.open('xb') as output:
    output.write(data)
print(destination)
