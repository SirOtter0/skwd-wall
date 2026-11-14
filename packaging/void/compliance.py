"""Carry verified beta27_2 notices into rebuilt packages; refresh native facts."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[2]

def digest(path):
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()

def add_compliance(stage, component, package, suite, licenses, pins):
    receipt = json.loads((ROOT / 'security/void-beta27/BETA27-2-IMPORT.json').read_text())
    rows = [row for row in receipt['preserved_compliance_files'] if row['package'] == package]
    if not rows:
        raise ValueError('Missing beta27_2 compliance input')
    base = ROOT / 'packaging/void/compliance-beta27_2' / package
    destination = licenses / 'compliance'
    for row in rows:
        source = ROOT / row['path']
        if source.is_symlink() or digest(source) != row['sha256']:
            raise ValueError('Changed beta27_2 notice: ' + row['path'])
        target = destination / source.relative_to(base)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    # The Rust lockfiles and build features stay fixed. Require exact version sets
    # before reusing the conservative runtime/build notice closure.
    import tomllib
    lock = tomllib.loads((suite / ('skwd-' + component) / 'Cargo.lock').read_text())
    packages = {p['name'] + '-' + p['version'] for p in lock['package']}
    for entry in json.loads((destination / 'DEPENDENCIES.json').read_text()):
        if entry['package'] not in packages:
            raise ValueError('Historical notice closure no longer matches lockfile')
    ffmpeg = pins['ffmpeg']
    for name in ['SOURCE-OFFER.txt', 'FFMPEG.md']:
        path = destination / name
        if path.exists():
            text = path.read_text().replace('9.0.1', ffmpeg['version'])
            text = text.replace('cf38e0e28c7e5605942c4a77755349b0145804a397af37eb1fb4c77cb237f635', ffmpeg['sha256'])
            if name == 'FFMPEG.md':
                text = text.replace('checked against the\nstring embedded in the validated libavutil', 'checked below against the\nconfiguration embedded in this rebuilt libavutil')
            path.write_text(text)
    if component == 'paper':
        runtime = suite / '.skwd-package/ffmpeg'
        library = list((runtime / 'lib').glob('libavutil.so.*.*.*'))
        if len(library) != 1:
            raise ValueError('Expected one rebuilt libavutil')
        expected = (destination / 'ffmpeg-configure.txt').read_text().strip().removeprefix('./configure ')
        if expected.encode() not in library[0].read_bytes().split(b'\0'):
            raise ValueError('FFmpeg configuration differs from reviewed flags')
        archive = suite / ffmpeg['path']
        if digest(archive) != ffmpeg['sha256']:
            raise ValueError('FFmpeg source mismatch')
        with tarfile.open(archive) as tar:
            notices = []
            for name in ['libavcodec/jfdctfst.c','libavcodec/jfdctint_template.c','libavcodec/jrevdct.c']:
                text = tar.extractfile('ffmpeg-' + ffmpeg['version'] + '/' + name).read().decode()
                notices.append(name + '\n' + text[:text.index('*/')+2] + '\n')
            (destination / 'JPEG-SOURCE-NOTICES.txt').write_text('\n'.join(notices))
        (destination / 'FFMPEG-RECIPE-CHANGES.patch').write_bytes(
            (ROOT / 'security/void-beta27/patches/skwd-paper.patch').read_bytes())
    (destination / 'REVISION3.txt').write_text(
        'beta27_3: retains verified beta27_2 notices; rebuilds against FFmpeg 9.0.2.\n'
        'Historical attribution review records are provenance, not new binary acceptance.\n'
        'No distribution approval. New binaries, source delivery, closure and licenses require review.\n')
