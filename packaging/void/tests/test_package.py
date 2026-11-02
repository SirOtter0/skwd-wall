import importlib.util,pathlib,tempfile,unittest,os
p=pathlib.Path(__file__).resolve().parents[1]/'package.py';s=importlib.util.spec_from_file_location('void_package',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class PackageTimestamps(unittest.TestCase):
 def test_normalization_preserves_bytes_links_and_modes(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);sub=root/'usr';sub.mkdir();file=sub/'payload';file.write_bytes(b'unchanged');file.chmod(0o755);link=sub/'link';link.symlink_to('payload')
   m.normalize_timestamps(root,1792079636)
   for p in [root,sub,file,link]:self.assertEqual(p.lstat().st_mtime,1792079636)
   self.assertEqual(file.read_bytes(),b'unchanged');self.assertEqual(file.stat().st_mode&0o777,0o755);self.assertEqual(os.readlink(link),'payload')
 def test_negative_epoch_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):m.normalize_timestamps(pathlib.Path(d),-1)
if __name__=='__main__':unittest.main()
