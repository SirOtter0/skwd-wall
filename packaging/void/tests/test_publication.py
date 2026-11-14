import hashlib
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[3]


class PublicationBoundary(unittest.TestCase):
    def test_experiments_are_not_in_publication_payload(self):
        for name in ('noctalia-hook','noctalia-bridge'):
            self.assertFalse((ROOT/'packaging/void'/name).exists())
        self.assertNotIn('work/beta27_3/continuation', (ROOT/'packaging/void/test.sh').read_text())
        self.assertIn('SKWD_TEST_INPUTS:?', (ROOT/'packaging/void/test.sh').read_text())

    def test_complete_notice_import_remains_byte_identical(self):
        data=json.loads((ROOT/'security/void-beta27/BETA27-2-IMPORT.json').read_text())
        self.assertEqual(len(data['preserved_compliance_files']),1889)
        for row in data['preserved_compliance_files']:
            path=ROOT/row['path']
            self.assertFalse(path.is_symlink())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),row['sha256'])

    def test_pin_and_recipe_coherence(self):
        sources=json.loads((ROOT/'security/void-beta27/sources.json').read_text())
        recipes=json.loads((ROOT/'packaging/void/recipes.json').read_text())
        self.assertEqual(recipes['version'],'1.0.0beta27_3')
        self.assertEqual(sources['ffmpeg']['version'],'9.0.2')
        self.assertEqual(sources['ffmpeg']['sha256'],'8c3850283eb25fa026482078a04051e0be17347b09ef81a0849bec15a96e002e')
        self.assertEqual(set(recipes['components']),{'wall','deck','lens','paper'})
        for name in sources['patches']:
            self.assertTrue((ROOT/'security/void-beta27/patches'/name).is_file())
