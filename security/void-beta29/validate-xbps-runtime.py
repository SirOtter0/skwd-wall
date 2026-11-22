"""Headless tests for the installed beta.29 programs inside the disposable guest."""

import hashlib
import json
import os
from pathlib import Path
import select
import struct
import subprocess
import sys
import time

media, scratch = map(Path, sys.argv[1:])
os.umask(0o077)
for variable in ("HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME",
                 "XDG_STATE_HOME", "XDG_RUNTIME_DIR"):
    isolated = scratch / variable
    isolated.mkdir()
    os.environ[variable] = str(isolated)
if Path("/sys/class/drm/card0").exists() or Path("/dev/dri/renderD128").exists():
    raise RuntimeError("Expected a headless guest without a GPU")
library = scratch / "library"
library.mkdir()
(library / "synthetic.png").write_bytes((media / "fixtures/synthetic.png").read_bytes())
configuration = Path(os.environ["XDG_CONFIG_HOME"]) / "skwd-wall-v2"
configuration.mkdir()
(configuration / "config.json").write_text(json.dumps({"paths": {"wallpaper": str(library)}}))
cache = Path(os.environ["XDG_CACHE_HOME"]) / "skwd-wall-v2/thumbs"
cache.mkdir(parents=True)


def run(*args):
    return subprocess.run(args, capture_output=True, timeout=25)


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=4)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


catalogue_ok = False
with (scratch / "daemon.log").open("wb") as log:
    daemon = subprocess.Popen(["skwd-walld"], stdout=log, stderr=log)
    try:
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            result = run("skwd-helm", "list", "--json")
            if result.returncode == 0 and "synthetic.png" in result.stdout.decode():
                print("PASS Deck startup and catalogue over IPC", flush=True)
                catalogue_ok = True
                break
            if daemon.poll() is not None:
                raise RuntimeError("Deck exited before IPC was ready")
            time.sleep(0.2)
        else:
            print("FAIL Deck catalogue", result.returncode, result.stdout.decode(), result.stderr.decode(), flush=True)
    finally:
        stop(daemon)
        print((scratch / "daemon.log").read_text(), flush=True)
        scanner = Path(os.environ["XDG_CACHE_HOME"]) / "skwd-wall-v2/skwd-wall-scan.log"
        if scanner.is_file():
            print(scanner.read_text(errors="replace"), flush=True)
        print(f"Deck stop status {daemon.returncode}", flush=True)

for command in (("skwd-wall-v2", "--help"), ("skwd-paper-v2", "--help"),
                ("skwd-lens", "--list-packs", "--models-dir", str(scratch / "models"))):
    result = run(*command)
    if result.returncode:
        raise RuntimeError((command, result.returncode, result.stderr.decode()))
    print(f"PASS installed CLI {command[0]}", flush=True)

valid = ("h264-1080.mkv", "hevc-1080.mkv", "av1-360.ivf")
invalid = ("empty.mkv", "truncated.mkv")
for file in valid + invalid:
    source = media / "fixtures" / file
    output = cache / f"{source.stem}.webp"
    result = run("skwd-wall-scan", "--tall", str(source), str(output), "--video")
    print(result.stderr.decode(), flush=True)
    thumbnail = output.with_suffix(".tall.webp")
    if file in valid:
        head = thumbnail.read_bytes()[:12]
        assert result.returncode == 0 and head.startswith(b"RIFF") and head[8:12] == b"WEBP", file
    else:
        assert result.returncode == 0 and not thumbnail.exists() and result.stderr, file
    print(f"PASS Deck scan {file}", flush=True)

driver = media / "software-icd"
probe = subprocess.run(["ldd", str(driver / "libvulkan_lvp.so")],
                       capture_output=True, text=True,
                       env=dict(os.environ, LD_LIBRARY_PATH=str(driver)), timeout=10)
if probe.returncode or "not found" in probe.stdout:
    print("BLOCKED Paper software renderer ICD dependencies", probe.stdout, probe.stderr, flush=True)
    sys.exit(0 if catalogue_ok else 1)
descriptor = scratch / "lvp.json"
descriptor.write_text(json.dumps({"file_format_version": "1.0.1",
    "ICD": {"api_version": "1.4.354", "library_arch": "64", "library_path": str(driver / "libvulkan_lvp.so")}}))
env = dict(os.environ, VK_DRIVER_FILES=str(descriptor), LD_LIBRARY_PATH=str(driver), RUST_LOG="info")
for file in valid:
    with (scratch / "paper.log").open("wb") as log:
        paper = subprocess.Popen(["skwd-wall-vk", "--video-stream", str(media / "fixtures" / file),
                                  "--stream-size", "160x90", "--stream-fps", "12"],
                                 env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log)
        try:
            deadline = time.monotonic() + 25
            data = bytearray()
            size = 160 * 90 * 4
            while len(data) < 12 + size * 4:
                remaining = deadline - time.monotonic()
                assert remaining > 0 and select.select([paper.stdout], [], [], remaining)[0], file
                chunk = os.read(paper.stdout.fileno(), 12 + size * 4 - len(data))
                assert chunk, file
                data.extend(chunk)
            assert struct.unpack("<4sII", data[:12]) == (b"SKWP", 160, 90)
            assert len({hashlib.sha256(data[i:i+size]).digest()
                        for i in range(12, len(data), size)}) > 1
        finally:
            stop(paper)
            print((scratch / "paper.log").read_text(), flush=True)
    print(f"PASS Paper software stream {file} stop={paper.returncode}", flush=True)

for file in invalid:
    result = subprocess.run(
        ["skwd-wall-vk", "--video-stream", str(media / "fixtures" / file),
         "--stream-size", "160x90"],
        env=env, input=b"", capture_output=True, timeout=25)
    assert result.returncode == 1 and not result.stdout and result.stderr, file
    print(f"PASS Paper rejects {file}", flush=True)

if not catalogue_ok:
    sys.exit(1)
