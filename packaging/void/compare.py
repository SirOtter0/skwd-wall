#!/usr/bin/env python3
"""Compare two independent package outputs; equivalence is not functional validation."""
import argparse,hashlib,json,pathlib,plistlib,tarfile

def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def properties(path):
 with tarfile.open(path,'r:*') as archive:
  members=[m for m in archive.getmembers() if pathlib.PurePosixPath(m.name).name=='props.plist']
  if len(members)!=1:raise ValueError('Expected exactly one XBPS props.plist')
  props=plistlib.loads(archive.extractfile(members[0]).read())
  headers={m.name.lstrip('./'):{'mode':m.mode,'uid':m.uid,'gid':m.gid,'type':m.type.hex(),'link':m.linkname} for m in archive.getmembers() if pathlib.PurePosixPath(m.name).name not in ['props.plist','files.plist']}
  times={m.name:m.mtime for m in archive.getmembers()}
  payload={};elf={}
  for member in archive.getmembers():
   name=member.name.removeprefix('./')
   if member.isdir() or name in ['props.plist','files.plist']:continue
   if pathlib.PurePosixPath(name).is_absolute() or '..' in pathlib.PurePosixPath(name).parts:raise ValueError('Unsafe archive path: '+name)
   if member.issym():payload['/'+name]=(None,member.linkname)
   elif member.isfile():
    stream=archive.extractfile(member);prefix=stream.read(4);digest=hashlib.sha256(prefix)
    while data:=stream.read(1024*1024):digest.update(data)
    payload['/'+name]=(digest.hexdigest(),None)
    if prefix==b'\x7fELF':elf['/'+name]=digest.hexdigest()
   else:raise ValueError('Unexpected archive entry: '+name)
  return props,headers,times,payload,elf

def inventory(root):
 result={}
 for p in json.loads((root/'packages.json').read_text()):
  file=root/'repository'/pathlib.Path(p['archive']).name
  actual=sha(file)
  if actual!=p['archive_sha256']:raise ValueError('Package changed since inventory: '+file.name)
  props,headers,times,payload,elf=properties(file)
  if payload!={r['path']:(r['sha256'],r['symlink']) for r in p['payload']}:raise ValueError('Payload disagrees with inventory: '+file.name)
  if elf!={r['path']:r['sha256'] for r in p['elf']}:raise ValueError('ELF inventory disagrees with archive: '+file.name)
  if sorted(props.get('run_depends',[]))!=sorted(p['dependencies']):raise ValueError('Dependencies disagree with inventory: '+file.name)
  result[p['name']]={'file_metadata':headers,'timestamps':times,'payload':payload,'dependencies':sorted(p['dependencies']),'elf':elf,'archive_sha256':actual,'properties':props}
 return result

def compare(a,b):
 if set(a)!=set(b):raise ValueError('Different package sets')
 rows=[]
 for name in sorted(a):
  x,y=a[name],b[name]
  keys=set(x['properties'])|set(y['properties'])
  rows.append({'package':name,'payload_equal':x['payload']==y['payload'] and x.get('file_metadata',{})==y.get('file_metadata',{}),'dependencies_equal':x['dependencies']==y['dependencies'],'elf_equal':x['elf']==y['elf'],'archive_equal':x['archive_sha256']==y['archive_sha256'],'timestamp_differences':sum(x.get('timestamps',{}).get(k)!=y.get('timestamps',{}).get(k) for k in set(x.get('timestamps',{}))|set(y.get('timestamps',{}))),'metadata_differences':sorted(k for k in keys if x['properties'].get(k)!=y['properties'].get(k))})
 return {'packages':rows,'content_and_dependencies_equal':all(x['payload_equal'] and x['dependencies_equal'] for x in rows),'elf_byte_identical':all(x['elf_equal'] for x in rows),'xbps_byte_identical':all(x['archive_equal'] for x in rows),'functional_validation':'Must be established separately by installation/runtime tests'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('first',type=pathlib.Path);p.add_argument('second',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path);a=p.parse_args()
 result=compare(inventory(a.first),inventory(a.second));text=json.dumps(result,indent=2)+'\n'
 if a.output:a.output.write_text(text)
 print(text,end='')
 return 0 if result['content_and_dependencies_equal'] else 1

if __name__=='__main__':raise SystemExit(main())
