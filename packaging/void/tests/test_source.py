import importlib.util,io,pathlib,tarfile,tempfile,unittest
P=pathlib.Path(__file__).resolve().parents[1]/'prepare-source.py'
spec=importlib.util.spec_from_file_location('prepare_source',P);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class ArchiveTests(unittest.TestCase):
 def check_member(self,name,kind=None,root='crate-1'):
  with tempfile.TemporaryDirectory() as work:
   p=pathlib.Path(work);a=p/'source.tar'
   with tarfile.open(a,'w') as t:
    i=tarfile.TarInfo(name)
    if kind is not None:i.type=kind;i.linkname='/etc/passwd'
    else:i.size=2
    t.addfile(i,io.BytesIO(b'ok') if kind is None else None)
   module.extract(a,p/'output',root)
   return (p/'output/crate-1/file').read_bytes()
 def test_safe_file(self):self.assertEqual(self.check_member('crate-1/file'),b'ok')
 def test_traversal(self):
  with self.assertRaises(ValueError):self.check_member('../escape')
 def test_absolute(self):
  with self.assertRaises(ValueError):self.check_member('/escape')
 def test_wrong_root(self):
  with self.assertRaises(ValueError):self.check_member('other/file')
 def test_symlink(self):
  with self.assertRaises(ValueError):self.check_member('crate-1/file',tarfile.SYMTYPE)
 def test_hardlink(self):
  with self.assertRaises(ValueError):self.check_member('crate-1/file',tarfile.LNKTYPE)
if __name__=='__main__':unittest.main()
