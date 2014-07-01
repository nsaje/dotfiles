from Crypto.Cipher import AES
from Crypto.Util import Counter


def aes_encrypt(message, secret_key):
    counter = Counter.new(128)
    aes = AES.new(secret_key, AES.MODE_CTR, counter=counter)
    return aes.encrypt(message)


def aes_decrypt(cipher_text, secret_key):
    counter = Counter.new(128)
    aes = AES.new(secret_key, AES.MODE_CTR, counter=counter)
    return aes.decrypt(cipher_text)
