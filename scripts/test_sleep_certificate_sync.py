"""Certificate rotation failures must preserve the working pair."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('sync_certificate', Path(__file__).resolve().parents[1] / 'deploy/sync_certificate.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


@unittest.skipUnless(shutil.which('openssl'), 'OpenSSL is required for certificate checks')
class CertificateRotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        root = Path(cls.temp.name)
        for name in ['first', 'second']:
            subprocess.run([
                'openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                '-subj', '/CN=sleep.example.test', '-addext', 'subjectAltName=DNS:sleep.example.test',
                '-days', '30', '-keyout', str(root / (name + '.key')),
                '-out', str(root / (name + '.pem')),
            ], capture_output=True, check=True)
        cls.certificate = (root / 'first.pem').read_bytes()
        cls.key = (root / 'first.key').read_bytes()
        cls.wrong_key = (root / 'second.key').read_bytes()
        cls.trust = patch.dict(os.environ, {'SSL_CERT_FILE': str(root / 'first.pem')})
        cls.trust.start()

    @classmethod
    def tearDownClass(cls):
        cls.trust.stop()
        cls.temp.cleanup()

    def setUp(self):
        self.output = tempfile.TemporaryDirectory()
        self.root = Path(self.output.name)
        sync.install_bundle(self.certificate, self.key, self.root, 'sleep.example.test')
        self.before = (self.root / 'current').readlink()

    def tearDown(self):
        self.output.cleanup()

    def test_matching_repeat_is_idempotent_and_private(self):
        result = sync.install_bundle(self.certificate, self.key, self.root, 'sleep.example.test')
        self.assertEqual(result['status'], 'unchanged')
        self.assertEqual((self.root / 'current').readlink(), self.before)
        self.assertEqual((self.root / 'current/key.pem').stat().st_mode & 0o777, 0o600)

    def test_wrong_hostname_preserves_working_pair(self):
        with self.assertRaises(RuntimeError):
            sync.install_bundle(self.certificate, self.key, self.root, 'wrong.example.test')
        self.assertEqual((self.root / 'current').readlink(), self.before)
        self.assertEqual((self.root / 'current/key.pem').read_bytes(), self.key)

    def test_mismatched_key_preserves_working_pair(self):
        with self.assertRaises(ValueError):
            sync.install_bundle(self.certificate, self.wrong_key, self.root, 'sleep.example.test')
        self.assertEqual((self.root / 'current').readlink(), self.before)
        self.assertEqual((self.root / 'current/key.pem').read_bytes(), self.key)


if __name__ == '__main__':
    unittest.main()
