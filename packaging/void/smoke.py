#!/usr/bin/env python3
"""Run only from smoke.sh's isolated filesystem and network namespace."""
import json
import os
from pathlib import Path
import signal
import struct
import subprocess
import time
import zlib


def run(name, arguments):
    result = subprocess.run(arguments, capture_output=True, text=True, timeout=15)
    (Path('/evidence') / (name + '.json')).write_text(json.dumps({
        'command': arguments, 'exit_code': result.returncode,
        'stdout': result.stdout, 'stderr': result.stderr,
    }, indent=2) + '\n')
    return result


def main():
    for key in ('HOME', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_DATA_HOME',
                'XDG_STATE_HOME', 'XDG_RUNTIME_DIR'):
        Path(os.environ[key]).mkdir(mode=0o700, parents=True, exist_ok=True)
    images = Path('/tmp/images')
    images.mkdir()
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', 32, 32, 8, 2, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress((b'\0' + b'\x24\x80\xc0' * 32) * 32))
           + chunk(b'IEND', b''))
    (images / 'synthetic.png').write_bytes(png)
    config = Path(os.environ['XDG_CONFIG_HOME']) / 'skwd-wall-v2'
    config.mkdir()
    (config / 'config.json').write_text(json.dumps({
        'paths': {'wallpaper': str(images)},
        'library': {'folders': [str(images)]},
        'pickOnlyMode': True,
    }))
    checks = [
        ('wall-version', ['skwd-wall', '--version']),
        ('deck-version', ['skwd-walld', '--version']),
        ('helm-help', ['skwd-helm', '--help']),
        ('paper-help', ['skwd-paper', '--help']),
        ('lens-empty-packs', ['skwd-lens', '--list-packs', '--models-dir', '/tmp/models']),
    ]
    results = {name: run(name, arguments).returncode == 0 for name, arguments in checks}
    draw = run('draw-requires-pack', ['skwd-wall-draw', '--check'])
    results['draw-requires-pack'] = draw.returncode == 1 and '--pack is required' in draw.stderr
    with Path('/evidence/daemon.log').open('w') as log:
        daemon = subprocess.Popen(['skwd-walld'], stdout=log, stderr=subprocess.STDOUT,
                                  start_new_session=True)
        try:
            deadline = time.monotonic() + 45
            listed = False
            thumbnails = False
            while time.monotonic() < deadline and daemon.poll() is None:
                response = run('catalogue', ['skwd-helm', 'list', '--json'])
                if response.returncode == 0:
                    catalogue = json.loads(response.stdout)
                    for item in catalogue.get('wallpapers', []):
                        if item.get('key') != 'static:synthetic.png':
                            continue
                        listed = True
                        paths = [Path(item[key]) for key in ('thumb', 'thumb_sm') if item.get(key)]
                        thumbnails = len(paths) == 2 and all(
                            path.is_file() and path.read_bytes()[:4] == b'RIFF'
                            and path.read_bytes()[8:12] == b'WEBP' for path in paths)
                    if listed and thumbnails:
                        break
                time.sleep(0.25)
            results['daemon-ipc-synthetic-catalogue'] = listed
            results['synthetic-webp-thumbnails'] = thumbnails
        finally:
            if daemon.poll() is None:
                os.killpg(daemon.pid, signal.SIGTERM)
            try:
                daemon.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(daemon.pid, signal.SIGKILL)
                daemon.wait()
    Path('/evidence/summary.json').write_text(json.dumps(results, indent=2) + '\n')
    raise SystemExit(0 if all(results.values()) else 1)


if __name__ == '__main__':
    main()
