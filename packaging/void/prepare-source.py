#!/usr/bin/env python3
"""Prepare pinned suite sources; builds are separate. Never run as root."""
import argparse,hashlib,json,os,pathlib,subprocess,tarfile,tomllib,urllib.request
P=pathlib.Path(__file__).resolve().parents[2]/'security/void-beta26'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def extract(archive,dest,root=None):
 with tarfile.open(archive) as t:
  members=t.getmembers()
  for m in members:
   n=pathlib.PurePosixPath(m.name)
   if n.is_absolute() or '..' in n.parts or m.issym() or m.islnk() or not (m.isfile() or m.isdir()):raise ValueError('Unexpected archive member: '+m.name)
   if root and n.parts[0]!=root:raise ValueError('Unexpected archive root')
  t.extractall(dest,filter='data')
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('archive',type=pathlib.Path);a.add_argument('destination',type=pathlib.Path);a.add_argument('--fetch-missing-crates',action='store_true',help='Allow exact lockfile crates from static.crates.io; checksum verified before extraction');x=a.parse_args()
 assert os.getuid()!=0,'Do not run as root'
 pins=json.loads((P/'sources.json').read_text());assert sha(x.archive)==pins['original_archive_sha256'],'Wrong official suite archive'
 dest=x.destination.absolute();assert not dest.exists() and not dest.is_symlink();dest.parent.mkdir(parents=True,exist_ok=True);dest.mkdir(mode=0o700)
 extract(x.archive,dest);roots=list(dest.iterdir());assert len(roots)==1 and roots[0].is_dir();suite=dest/'suite';roots[0].rename(suite)
 for comp in ['deck','paper','lens']:
  patch=P/'patches'/('skwd-'+comp+'.patch')
  subprocess.run(['patch','--batch','--forward','--dry-run','-p1','-i',str(patch)],cwd=suite/('skwd-'+comp),check=True)
  subprocess.run(['patch','--batch','--forward','-p1','-i',str(patch)],cwd=suite/('skwd-'+comp),check=True)
 vendor=suite/'vendor';packages={}
 for comp in ['wall','deck','lens','paper']:
  for pkg in tomllib.loads((suite/('skwd-'+comp)/'Cargo.lock').read_text())['package']:
   if pkg.get('source','').startswith('registry+'):
    key=(pkg['name'],pkg['version']);assert key not in packages or packages[key]==pkg['checksum'];packages[key]=pkg['checksum']
 downloads=dest/'crates';downloads.mkdir()
 for (name,version),checksum in sorted(packages.items()):
  folder=vendor/(name+'-'+version)
  if folder.exists():
   meta=json.loads((folder/'.cargo-checksum.json').read_text());assert meta['package']==checksum,(name,version)
   for rel,h in meta['files'].items():assert sha(folder/rel)==h,(name,rel)
   continue
  assert x.fetch_missing_crates,'Missing '+name+' '+version+'; rerun into a NEW destination with --fetch-missing-crates'
  archive=downloads/(name+'-'+version+'.crate');url=f'https://static.crates.io/crates/{name}/{name}-{version}.crate'
  with urllib.request.urlopen(url,timeout=60) as response,archive.open('xb') as output:
   while chunk:=response.read(1024*1024):output.write(chunk)
  assert sha(archive)==checksum,'Crate checksum mismatch: '+name
  extract(archive,vendor,name+'-'+version)
  files={str(f.relative_to(folder)):sha(f) for f in folder.rglob('*') if f.is_file() and f.name!='.cargo-checksum.json'}
  (folder/'.cargo-checksum.json').write_text(json.dumps({'package':checksum,'files':files}))
 manifest={'original_archive_sha256':pins['original_archive_sha256'],'commits':pins['commits'],'locks':{c:sha(suite/('skwd-'+c)/'Cargo.lock') for c in ['wall','deck','lens','paper']},'patches':{p.name:sha(p) for p in (P/'patches').glob('*.patch')}}
 (dest/'sources.json').write_text(json.dumps(manifest,indent=2)+'\n');print(suite)
if __name__=='__main__':main()
