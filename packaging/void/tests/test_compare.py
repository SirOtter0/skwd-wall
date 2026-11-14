import importlib.util,pathlib,unittest,copy,tempfile,tarfile,io,plistlib,json,hashlib
p=pathlib.Path(__file__).resolve().parents[1]/'compare.py';s=importlib.util.spec_from_file_location('compare_packages',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class ComparisonTests(unittest.TestCase):
 def baseline(self):return {'package':{'payload':{'/usr/bin/app':('abc',None)},'dependencies':['glibc>=1'],'elf':{'/usr/bin/app':'abc'},'archive_sha256':'archive-a','properties':{'pkgver':'package-1_1','build-date':'day1'}}}
 def test_metadata_drift_is_not_binary_drift(self):
  a=self.baseline();b=copy.deepcopy(a);b['package']['properties']['build-date']='day2';b['package']['archive_sha256']='archive-b';r=m.compare(a,b)
  self.assertTrue(r['content_and_dependencies_equal']);self.assertTrue(r['elf_byte_identical']);self.assertFalse(r['xbps_byte_identical']);self.assertEqual(r['packages'][0]['metadata_differences'],['build-date'])
 def test_changed_binary_is_not_equivalent(self):
  a=self.baseline();b=copy.deepcopy(a);b['package']['elf']['/usr/bin/app']='def';b['package']['payload']['/usr/bin/app']=('def',None);r=m.compare(a,b)
  self.assertFalse(r['content_and_dependencies_equal']);self.assertFalse(r['elf_byte_identical'])
 def test_missing_package_is_error(self):
  with self.assertRaises(ValueError):m.compare(self.baseline(),{})
 def test_archive_payload_must_match_inventory(self):
  with tempfile.TemporaryDirectory() as directory:
   root=pathlib.Path(directory);(root/'repository').mkdir();archive=root/'repository/test.xbps'
   with tarfile.open(archive,'w') as t:
    for name,data in [('props.plist',plistlib.dumps({'run_depends':[]})),('usr/bin/app',b'actual')]:
     member=tarfile.TarInfo(name);member.size=len(data);t.addfile(member,io.BytesIO(data))
   (root/'packages.json').write_text(json.dumps([{'name':'test','archive':str(archive),'archive_sha256':m.sha(archive),'dependencies':[],'elf':[],'payload':[{'path':'/usr/bin/app','sha256':hashlib.sha256(b'incorrect').hexdigest(),'symlink':None}]}]))
   with self.assertRaisesRegex(ValueError,'Payload disagrees'):m.inventory(root)
if __name__=='__main__':unittest.main()
