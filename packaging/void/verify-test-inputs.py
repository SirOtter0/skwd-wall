#!/usr/bin/env python3
"""Validate fixed test inputs before executing any test; no system CLI fallback."""
import hashlib,json,pathlib,sys
root=pathlib.Path(__file__).resolve().parents[2]
def sha(path):return hashlib.file_digest(path.open('rb'),'sha256').hexdigest()
def verify(directory):
 pins=json.loads((root/'security/void-beta27/test-inputs-beta27-3.json').read_text())
 for row in pins['files']:
  relative=pathlib.PurePosixPath(row['path'])
  if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe test input')
  path=directory/relative
  if path.is_symlink() or not path.is_file() or sha(path)!=row['sha256']:raise ValueError('Missing or changed fixed test input: '+str(path))
 source=json.loads((root/'security/void-beta27/sources.json').read_text())['ffmpeg']
 if pins['ffmpeg_reference']['source_sha256']!=source['sha256'] or pins['ffmpeg_reference']['version']!='9.0.2':raise ValueError('Reference source mismatch')
 print('PASS fixed FFmpeg9.0.2/DXC/Steamworks test inputs; no fallback')
if __name__=='__main__':verify(pathlib.Path(sys.argv[1]).resolve())
