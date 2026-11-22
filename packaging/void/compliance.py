"""Carry verified beta27_2 notices into rebuilt packages; refresh native facts."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile
import tomllib

ROOT = Path(__file__).resolve().parents[2]

def refresh_revision4(destination, suite, component):
    """Refresh only the reviewed crate/source delta; preserve historic notices."""
    dependencies = json.loads((destination / 'DEPENDENCIES.json').read_text())
    for entry in dependencies:
        if entry['package'] == 'rustix-1.1.4':
            source = suite / 'vendor/rustix-1.1.6'
            target = destination / 'crates/rustix-1.1.6'
            target.mkdir(parents=True)
            for notice in entry['notices']:
                old = destination / notice['path']
                new = source / old.name
                # License text was reviewed as unchanged; reject unreviewed drift.
                if digest(new) != notice['sha256']:
                    raise ValueError('Unexpected rustix notice change: ' + new.name)
                shutil.copyfile(new, target / old.name)
                notice['path'] = 'crates/rustix-1.1.6/' + old.name
            shutil.rmtree(destination / 'crates/rustix-1.1.4')
            entry['package'] = 'rustix-1.1.6'
        if entry['package'] == 'libsqlite3-sys-0.30.1' and component == 'deck':
            entry['downstream_source'] = 'skwd-deck/vendor/libsqlite3-sys'
            entry['downstream_patch'] = 'sqlite-wal-initialize.patch'
    (destination / 'DEPENDENCIES.json').write_text(json.dumps(dependencies, indent=2)+'\n')
    notice = destination / 'NOTICE.txt'
    notice.write_text(notice.read_text().replace('rustix-1.1.4', 'rustix-1.1.6'))
    revision = ROOT / 'security/void-beta27/revision4'
    shutil.copyfile(revision / 'proposal.json', destination / 'SECURITY-REVISION4.json')
    if component == 'deck':
        proposal = json.loads((revision / 'proposal.json').read_text())
        local = suite / 'skwd-deck/vendor/libsqlite3-sys'
        if digest(local/'sqlite3/sqlite3.c') != proposal['patched_sqlite3_c_sha256']:
            raise ValueError('SQLite override differs from reviewed backport')
        target = destination / 'local-overrides/libsqlite3-sys-0.30.1'
        target.mkdir(parents=True)
        for name in ['LICENSE', 'Cargo.toml']:
            shutil.copyfile(local/name, target/name)
        shutil.copyfile(revision/'patches/sqlite-wal-initialize.patch', target/'sqlite-wal-initialize.patch')
        (target/'SOURCE.txt').write_text(
            'Path-patched libsqlite3-sys 0.30.1, bundled SQLite 3.46.0.\n'
            'Exact source: suite/skwd-deck/vendor/libsqlite3-sys in corresponding-source.tar.xz.\n'
            'Original registry source remains separately in suite/vendor/libsqlite3-sys-0.30.1.\n'
            'WAL initialization backport: SQLite commit e5bf119821f25be1d7f10ef0a2edbe175289166e.\n'
            'No registry version or advisory clearance is claimed by this patch.\n')

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def validate_revision7_wall(suite):
    wall = suite / 'skwd-wall'
    lock = tomllib.loads((wall / 'Cargo.lock').read_text())['package']
    lru = [entry for entry in lock if entry['name'] == 'lru']
    checksum = '5d2f2f9b4ba7e6b24d95e7e899329d35be83bcded72c8540cdd5368932d1d90a'
    if len(lru) != 1 or (lru[0]['version'], lru[0].get('checksum')) != ('0.18.2', checksum):
        raise ValueError('Unexpected lru lock resolution')
    if [entry for entry in lock if entry['name'] == 'cryoglyph'] != [{
        'name': 'cryoglyph', 'version': '0.1.0',
        'dependencies': ['cosmic-text', 'etagere', 'lru', 'rustc-hash 2.1.2', 'wgpu'],
    }]:
        raise ValueError('Unexpected cryoglyph lock resolution')
    manifest = tomllib.loads((wall / 'Cargo.toml').read_text())
    override = 'vendor-patches/cryoglyph-0.1.0'
    if manifest['patch']['crates-io'].get('cryoglyph') != {'path': override}:
        raise ValueError('Unexpected cryoglyph override')
    local = wall / override
    paths = sorted(local.rglob('*'))
    if any(p.is_symlink() for p in paths):
        raise ValueError('Unexpected symlink in cryoglyph source')
    contents = {p.relative_to(local).as_posix(): digest(p) for p in paths if p.is_file()}
    if hashlib.sha256(json.dumps(contents, sort_keys=True).encode()).hexdigest() != (
            'eae0ef0c92415c52a7f5bca999d06b2a965dfda95c83a5d754c03fd773c00532'):
        raise ValueError('Unreviewed cryoglyph source')
    return local


def refresh_revision7_wall(destination, suite):
    local = validate_revision7_wall(suite)
    path = destination / 'DEPENDENCIES.json'
    dependencies = json.loads(path.read_text())
    lru = next(entry for entry in dependencies if entry['package'] == 'lru-0.16.4')
    for notice in lru['notices']:
        filename = Path(notice['path']).name
        if digest(suite / 'vendor/lru-0.18.2' / filename) != notice['sha256']:
            raise ValueError('Unexpected lru notice change')
        notice['path'] = 'crates/lru-0.18.2/' + filename
    (destination / 'crates/lru-0.16.4').rename(destination / 'crates/lru-0.18.2')
    lru['package'] = 'lru-0.18.2'
    cryoglyph = next(entry for entry in dependencies if entry['package'] == 'cryoglyph-0.1.0')
    cryoglyph['downstream_source'] = 'skwd-wall/vendor-patches/cryoglyph-0.1.0'
    cryoglyph['downstream_commit'] = 'a18bea27afd50e1841e56e167d3bb892a8d366bc'
    path.write_text(json.dumps(dependencies, indent=2) + '\n')
    notice = destination / 'NOTICE.txt'
    notice.write_text(notice.read_text().replace('lru-0.16.4', 'lru-0.18.2'))
    target = destination / 'local-overrides/cryoglyph-0.1.0'
    target.mkdir(parents=True)
    for filename in ('Cargo.toml', 'LICENSE-APACHE', 'LICENSE-MIT', 'LICENSE-ZLIB'):
        shutil.copyfile(local / filename, target / filename)
    (target / 'SOURCE.txt').write_text(
        'Cryoglyph 0.1.0 with the upstream dependency change from iced-rs/cryoglyph#5.\n'
        'Wall pins the corrected lru 0.18.2 with default features disabled.\n'
        'Source: suite/skwd-wall/vendor-patches/cryoglyph-0.1.0 in corresponding-source.tar.xz.\n')


def add_redistribution_notices(suite, component, licenses):
    """Stage portable notices when an authorized later package opts in."""
    docs = ROOT / "docs/void"
    if component == "deck":
        manifest = suite / "skwd-deck/crates/skwd-walld/assets/outdoors/sources.json"
        if digest(manifest) != "5eaa5fa2f55295abf4863539d7e2527f5f69aa39c49247f76f9b33d37307e891":
            raise ValueError("Deck outdoor attribution manifest changed")
        shutil.copyfile(manifest, licenses / "OUTDOOR-IMAGE-SOURCES.json")
        shutil.copyfile(docs / "BETA27-5-DECK-IMAGE-CREDITS.md",
                        licenses / "OUTDOOR-IMAGE-CREDITS.md")
    elif component == "paper":
        notice = docs / "notices/Roboto-3.015-OFL.txt"
        if digest(notice) != "061402327a96aadb0bfb694a960ed289ecd38d383e396243831ab81feb109c41":
            raise ValueError("Exact Roboto notice changed")
        shutil.copyfile(notice, licenses / "Roboto-3.015-OFL.txt")


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
    package_version = json.loads((suite / 'release-manifest.json').read_text()).get('void_package_version', '1.0.0beta27_3')
    is_revision4 = package_version in ('1.0.0beta27_4', '1.0.0beta27_5', '1.0.0beta27_6', '1.0.0beta27_7')
    if is_revision4:
        refresh_revision4(destination, suite, component)
    if package_version == '1.0.0beta27_7' and component == 'wall':
        refresh_revision7_wall(destination, suite)
    # The Rust lockfiles and build features stay fixed. Require exact version sets
    # before reusing the conservative runtime/build notice closure.
    lock = tomllib.loads((suite / ('skwd-' + component) / 'Cargo.lock').read_text())
    packages = {p['name'] + '-' + p['version'] for p in lock['package']}
    for entry in json.loads((destination / 'DEPENDENCIES.json').read_text()):
        if entry['package'] not in packages:
            raise ValueError('Historical notice closure no longer matches lockfile')
    if is_revision4:
        offer = destination / 'SOURCE-OFFER.txt'
        offer.write_text(offer.read_text() + '\nVoid revision 1.0.0beta27_4: rustix 1.1.6 sources are in suite/vendor/rustix-1.1.6.\nThe suite also includes Deck\'s path-patched SQLite in suite/skwd-deck/vendor/libsqlite3-sys.\nExact patches and source hashes accompany corresponding-source.tar.xz; no publication approval.\n')
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
    if package_version in ('1.0.0beta27_5', '1.0.0beta27_6', '1.0.0beta27_7') and component == 'paper':
        patches = suite / 'vendor-ffmpeg/security-patches'
        shutil.copytree(patches, licenses / 'ffmpeg/security-patches')
        description = destination / 'FFMPEG.md'
        previous = 'ffmpeg-source-changes.diff is empty: no source patch\nwas applied.'
        contents = description.read_text()
        if previous not in contents:
            raise ValueError('Expected the original FFmpeg source-change statement')
        description.write_text(contents.replace(previous,
            'Four upstream FFmpeg changes are recorded in ../ffmpeg/security-patches.\n'
            'The build recipe applies them to the exact 9.0.2 archive.'))
        (destination / 'ffmpeg-source-changes.diff').write_bytes(
            b''.join(path.read_bytes() for path in sorted(patches.glob('*.patch'))))
        offer = destination / 'SOURCE-OFFER.txt'
        offer.write_text(offer.read_text() + '\nFFmpeg 9.0.2 has upstream security backports. Exact patch texts are in suite/vendor-ffmpeg/security-patches and are reproduced with the native library notices.\n')
    revision = package_version.rsplit('_', 1)[-1]
    (destination / ('REVISION' + revision + '.txt')).write_text(
        'beta27_' + revision + ': retains verified historical notices; private FFmpeg 9.0.2.\n' +
        ('Revision4 updates rustix to 1.1.6 and carries a source-patched SQLite override.\n' if is_revision4 else '') +
        'Historical attribution review records are provenance, not new binary acceptance.\n'
        'No distribution approval. New binaries, source delivery, closure and licenses require review.\n')
