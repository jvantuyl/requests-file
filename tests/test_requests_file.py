import os
import unittest
import urllib
import requests
from requests_file.adapters import FileAdapter

class RELAdapter(FileAdapter):
    def __init__(self, path):
        self.path = path

    def resolve_host(self, host, fname):
        if host and host == "REL":
            return os.path.join(self.path, fname)
        return super(RELAdapter, self).resolve_host(host, fname)

class TestFileAdapter(unittest.TestCase):
    def setUp(self):
        self.s = requests.Session()
        self.s.mount('file://', FileAdapter())

    def test_file_get(self):
        """method GET -> 200 for file-scheme"""
        r = self.s.get('file://' + __file__)
        self.assertEqual(r.status_code, 200)
        self.assertTrue("magic_signature_text" in r.content)

    def test_file_missing(self):
        """method GET -> 404 for file-scheme"""
        r = self.s.get('file:///this/file/does/not/exist')
        self.assertEqual(r.status_code, 404)

    def test_file_dir_index(self):
        """method GET for file-scheme with index"""
        r = self.s.get('file://' + urllib.quote(os.path.dirname(__file__)))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(os.path.basename(__file__) in r.content)

    def test_resolve_host(self):
        """Allow for hostnames to be resolved"""
        self.s.mount('file://', RELAdapter(os.path.dirname(__file__)))
        print __file__
        r = self.s.get('file://REL/' + os.path.basename(__file__))
        self.assertEqual(r.status_code, 200)
        self.assertTrue("magic_signature_text" in r.content)
