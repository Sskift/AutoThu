import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from thu_learn_client import ThuLearnClient, SessionExpired
from mac_login import decrypt
import session_keepalive as keep
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

class SessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'session.json'
        self.path.write_text(json.dumps({'cookies': {'JSESSIONID': 'old', 'XSRF-TOKEN': 'xsrf'}}))
    def tearDown(self):
        self.tmp.cleanup()
    def test_modern_chrome_domain_prefix(self):
        key = b'x' * 16
        host = 'learn.tsinghua.edu.cn'
        plain = hashlib.sha256(host.encode()).digest() + b'test-value'
        padder = padding.PKCS7(128).padder()
        cipher = Cipher(algorithms.AES(key), modes.CBC(b' ' * 16)).encryptor()
        encrypted = b'v10' + cipher.update(padder.update(plain) + padder.finalize()) + cipher.finalize()
        self.assertEqual(decrypt(encrypted, key, host, 24), 'test-value')
        with self.assertRaises(RuntimeError):
            decrypt(encrypted, key, '.learn.tsinghua.edu.cn', 24)
    def test_cookie_rotation_and_concurrent_refresh(self):
        c = ThuLearnClient.from_session_file(self.path)
        c.session.cookies.set('JSESSIONID', 'new', domain='learn.tsinghua.edu.cn', path='/')
        self.assertTrue(c.persist())
        self.assertEqual(ThuLearnClient.from_session_file(self.path).session.cookies.get('JSESSIONID'), 'new')
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        updated = '{"cookies":{"JSESSIONID":"newer"}}'
        self.path.write_text(updated)
        self.assertFalse(c.persist())
        self.assertEqual(self.path.read_text(), updated)
    def test_network_failure_preserves_file_and_last_success(self):
        previous = self.path.read_bytes()
        with patch.object(ThuLearnClient, 'get_current_semester', side_effect=TimeoutError):
            result = keep.once(self.path)
        self.assertEqual(result['state'], 'unavailable')
        self.assertEqual(self.path.read_bytes(), previous)
    def test_login_page_is_not_success(self):
        r = Mock(status_code=200)
        r.json.side_effect = ValueError('HTML')
        with self.assertRaises(SessionExpired):
            ThuLearnClient._json(r)
    def test_expired_recovery_is_throttled_and_never_launches_browser(self):
        with patch.object(ThuLearnClient, 'get_current_semester', side_effect=SessionExpired), patch('session_keepalive.sys.platform','darwin'), patch('mac_login.import_chrome_cookies', side_effect=RuntimeError) as imp, patch('mac_login.browser_login_cookies') as browser:
            self.assertEqual(keep.once(self.path, True)['state'], 'expired')
            self.assertEqual(keep.once(self.path, True)['state'], 'expired')
            imp.assert_called_once()
            browser.assert_not_called()
    def test_success_persists_updated_cookie(self):
        c = ThuLearnClient.from_session_file(self.path)
        c.session.cookies.set('JSESSIONID','rotated',domain='learn.tsinghua.edu.cn',path='/')
        with patch.object(ThuLearnClient,'from_session_file', return_value=c), patch.object(c,'get_current_semester'), patch.object(c,'list_courses',return_value=[]):
            result = keep.once(self.path)
        self.assertEqual(result['state'],'valid')
        self.assertEqual(ThuLearnClient.from_session_file(self.path).session.cookies.get('JSESSIONID'),'rotated')
    def test_cookie_scope_and_csrf_rotation(self):
        c = ThuLearnClient.from_session_file(self.path)
        c.session.cookies.set('XSRF-TOKEN','id-token',domain='id.tsinghua.edu.cn',path='/')
        c.session.cookies.set('XSRF-TOKEN','rotated',domain='learn.tsinghua.edu.cn',path='/')
        self.assertEqual(c._csrf_params(),{'_csrf':'rotated'})
        self.assertEqual(c.session.headers['X-XSRF-TOKEN'],'rotated')

if __name__ == '__main__':
    unittest.main()
