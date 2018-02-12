import unittest

from utils import encryption_helpers


class EncryptionHelperTestCase(unittest.TestCase):

    def setUp(self):
        self.secret_key = b'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        self.message = b'This is a secret message.'
        self.cipher_text = b'~\xe9C1\xd8M\xe9\xfdT\\\xa6\xc7\x8f;+$\xb5y\xd5\xc2\x9b\xdc[\x9d_'

    def test_aes_encrypt(self):
        encrypted = encryption_helpers.aes_encrypt(self.message, self.secret_key)
        self.assertEqual(encrypted, self.cipher_text)

    def test_aes_decrypt(self):
        decrypted = encryption_helpers.aes_decrypt(self.cipher_text, self.secret_key)
        self.assertEqual(decrypted, self.message)
