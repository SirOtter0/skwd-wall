import importlib.util,pathlib,tempfile,hashlib,unittest
p=pathlib.Path(__file__).resolve().parents[1]/'prepare-source.py';s=importlib.util.spec_from_file_location('ffmpeg_prepare',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class FFmpegInputs(unittest.TestCase):
 def pin(self):return {'version':'test','url':'https://invalid.example/no-download','path':'vendor-ffmpeg/source.tar.xz','sha256':hashlib.sha256(b'source').hexdigest()}
 def test_missing_source_refuses_offline_fallback(self):
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaisesRegex(ValueError,'FFmpeg source missing'):m.prepare_ffmpeg(pathlib.Path(t),self.pin(),False)
 def test_modified_source_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=pathlib.Path(t);f=root/self.pin()['path'];f.parent.mkdir();f.write_bytes(b'changed')
   with self.assertRaisesRegex(ValueError,'checksum mismatch'):m.prepare_ffmpeg(root,self.pin(),False)
 def test_verified_existing_source_needs_no_network(self):
  with tempfile.TemporaryDirectory() as t:
   root=pathlib.Path(t);f=root/self.pin()['path'];f.parent.mkdir();f.write_bytes(b'source');r=m.prepare_ffmpeg(root,self.pin(),False);self.assertEqual(r['sha256'],self.pin()['sha256'])
if __name__=='__main__':unittest.main()
