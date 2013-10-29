import os.path
import unittest
import urllib
import requests
from requests_file.adapters import FileAdapter

class TestFileAdapter(unittest.TestCase):
    def test_file_get(self):
        """method GET -> 200 for file-scheme"""
        s = requests.Session()
        s.mount('file://', FileAdapter())
        r = s.get('file://' + __file__)
        print(r.content)
        self.assertEqual(r.status_code, 200)
        self.assertTrue("magic_signature_text" in r.content)

    def test_file_missing(self):
        """method GET -> 404 for file-scheme"""
        s = requests.Session()
        s.mount('file://', FileAdapter())
        r = s.get('file:///this/file/does/not/exist')
        print(r.content)
        self.assertEqual(r.status_code, 404)

    def test_file_dir_index(self):
        """method GET for file-scheme with index"""
        s = requests.Session()
        s.mount('file://', FileAdapter())
        r = s.get('file://' + urllib.quote(os.path.dirname(__file__)))
        print(r.content)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(os.path.basename(__file__) in r.content)

