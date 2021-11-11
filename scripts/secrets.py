#!/usr/bin/env python3
# This is using:
##   pip3 install pyOpenSSL
#   pip3 install pyca
#       https://cryptography.io/en/latest/
#

#from cryptography import fernet     # Symmetric encryption

#import os
#from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

#echo "${_pwd}" | openssl enc -e -aes-256-cbc -a -k "${ENCRYPTION_KEY}" | base64

#_key=b"JoCreyf"
#_key=fernet.Fernet.generate_key()
# This generates something like: b'EglhCZ5Itpac6yNg4vQ05-FeRxueOe52e_F5ag7l500='
#print("Key: "+str(_key))

#_pwd=b"ThisIsATest"
#print("Encrypting: "+str(_pwd))

#encryptor=fernet.Fernet(_key)
#_encrypted=encryptor.encrypt(_pwd)

# https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption/#cryptography.hazmat.primitives.ciphers.Cipher
#key = os.urandom(32)
#key=b"1234567890123456"
#iv = os.urandom(16)
# https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption/#algorithms
# https://cryptography.io/en/latest/hazmat/primitives/symmetric-encryption/#module-cryptography.hazmat.primitives.ciphers.modes
#cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
#encryptor = cipher.encryptor()
#ct = encryptor.update(_pwd) + encryptor.finalize()
#decryptor = cipher.decryptor()
#decryptor.update(ct) + decryptor.finalize()


#print("encrypted: "+str(_encrypted))

#_decrypted=encryptor.decrypt(_encrypted)
#print("Decrypted: "+str(_decrypted))

# https://stackoverflow.com/questions/12524994/encrypt-decrypt-using-pycrypto-aes-256
import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES

class AESCipher(object):

    def __init__(self, key): 
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode()))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]


enc=AESCipher("mycipher")
pwd="mypwd"
secret=enc.encrypt(pwd)
secret="VTJGc2RHVmtYMStaRnROV2ZmMG4xSUxLTm1WY2RFS2RzdEZaK0dTMXFXQT0K"
print(secret)
print(enc.decrypt(secret))

print(enc.decrypt("VTJGc2RHVmtYMS9kUWlmMHliYkFzWWErZ2tXaU8veFFQdG1SREpuKzh0QT0K"))