#!/usr/bin/env python3
"""Verify an untouched copied build tree; never launch a compiler or delete data."""
import hashlib,json,pathlib,stat,sys

def inventory(root):
    if root.is_symlink() or not root.is_dir():raise ValueError('Invalid source tree')
    rows={}
    for p in root.rglob('*'):
        rel=str(p.relative_to(root));mode=stat.S_IMODE(p.lstat().st_mode)
        if p.is_symlink():raise ValueError('Unexpected symlink: '+str(p))
        if p.is_file():rows[rel]=('file',mode,hashlib.file_digest(p.open('rb'),'sha256').hexdigest())
        elif p.is_dir():rows[rel]=('dir',mode)
        else:raise ValueError('Unexpected special file: '+str(p))
    return rows

def verify(suite,build):
    if not build.is_dir() or build.is_symlink():raise ValueError('Invalid build directory')
    if {p.name for p in build.iterdir()}-{'suite','cargo','build.log'}:
        raise ValueError('Build has unexpected outputs; do not restart automatically')
    if (build/'target').exists() or any((build/'cargo').iterdir()):
        raise ValueError('Compiler outputs/cache exist; separate resume review required')
    if (build/'build.log').read_text().strip()!='bwrap: loopback: Failed to create NETLINK_ROUTE socket: Operation not permitted':
        raise ValueError('Unexpected prior failure')
    original=inventory(suite);copied=inventory(build/'suite')
    if original!=copied:raise ValueError('Copied source tree changed; refuse reuse')
    return {'status':'PASS','files_and_directories':len(original),'copied_tree_matches_prepared_source':True,'compiler_outputs_present':False}

if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('Usage: verify-unstarted-build.py PREPARED-SUITE EXISTING-BUILD')
    print(json.dumps(verify(pathlib.Path(sys.argv[1]).resolve(),pathlib.Path(sys.argv[2]).resolve())))
