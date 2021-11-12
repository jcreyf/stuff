#!/usr/bin/env python3
#
# We're using this Crypto implementation for the AES 256bit CBC cipher logic:
#   pip install pycryptodome
#   https://stackoverflow.com/questions/12524994/encrypt-decrypt-using-pycrypto-aes-256
#
import sys
import argparse
import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES

class AES_256_CBC_Cipher(object):
  """
    This class will encrypt/decrypt using the aes-256-cbc cipher.
    Initial version cloned from:
      https://stackoverflow.com/questions/12524994/encrypt-decrypt-using-pycrypto-aes-256
  """

  def __init__(self, key):
    """
      Constructor, setting the encryption key.
      If we have a secondary "special key" on the system, then that secondary key
      will be used to encrypt the encryption key.  That encrypted key then becomes the
      actual key to encrypt and decrypt secrets.
    """
    self.bs=AES.block_size
    # Set the secondary optional "special key" (if we have one):
    try:
      with open("key.txt","r") as f:
        _specialKey=f.readline()
      f.close()
      # Remove potential newline characters from the string:
      _specialKey=_specialKey.replace("\n", "")
#      print(f"Special: '{_specialKey}'")
    except:
      # Ignore any and all exceptions to truly make the "special key" optional.
      _specialKey=""

    if _specialKey == "":
      # Use the given key if we don't have a "special key":
      self.key = hashlib.sha256(key.encode()).digest()
    else:
      # Aha!  We have a secondary key to make things "special".
      self.key=hashlib.sha256(_specialKey.encode()).digest()
#      print(f"special key: {self.key}")
      _bytes=self.encrypt(key, special=True)
#      print(f"encrypted: {_bytes}")
      self.key=hashlib.sha256(_bytes).digest()


  def encrypt(self, raw, special=False):
    raw = self._pad(raw)
    # This method is also called to encrypt the "special key" (optional secondary key).
    # That optional key needs to get encrypted with the same exact seed every single
    # time to make sure it doesn't change.
    # Secrets encrypted with both the key and secondary key will no longer be decryptable
    # if not the exact same key is used that was used to encrypt the extra key.
    if special:
      iv = b"\xf4\r\xb7\x1b\xbb7\x0e`CX&\x0c\xf7O1\x08"
    else:
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

# ------

if __name__ == "__main__":
  VERBOSE=False
  def verbose(str):
    if VERBOSE:
      print(str)

  # Define the command-line arguments that the app supports:
  parser=argparse.ArgumentParser(description="Encrypt or Decrypt secrets.")
  parser.add_argument("--version", \
                        action="version", \
                        version="%(prog)s 1.0")
  parser.add_argument("-v", "--verbose", \
                        dest="__VERBOSE", \
                        required=False, \
                        default=False, \
                        action="store_true", \
                        help="show verbose level output")
  parser.add_argument("-e", "--encrypt", \
                        dest="__ENCRYPT", \
                        required=False, \
                        default=False, \
                        action="store_true", \
                        help="encrypt the string")
  parser.add_argument("-d", "--decrypt", \
                        dest="__DECRYPT", \
                        required=False, \
                        default=False, \
                        action="store_true", \
                        help="decrypt the string")
  parser.add_argument("-k", "--key", \
                        dest="__KEY", \
                        required=True, \
                        metavar="<string>", \
                        help="encryption key")
  parser.add_argument("-p", "--password", \
                        dest="__PWD", \
                        required=True, \
                        metavar="<string>", \
                        help="the string to encrypt/decrypt")

  # Now parse the command-line arguments and automatically take care of handling some of the usage requests:
  __ARGS=parser.parse_args()

  # Do some argument validations:
  if (__ARGS.__ENCRYPT or __ARGS.__DECRYPT)==False:
    sys.exit("Need to use the '-e' (encrypt) or '-d' (decrypt) flag!")
  if (__ARGS.__ENCRYPT and __ARGS.__DECRYPT)==True:
    sys.exit("Can't use both the '-e' (encrypt) and '-d' (decrypt) flags at the same time!")

  # Pull out the values that we want:
  VERBOSE=__ARGS.__VERBOSE
  verbose(__ARGS)
  key=__ARGS.__KEY
  pwd=__ARGS.__PWD
  ENCRYPT=__ARGS.__ENCRYPT

  enc=AES_256_CBC_Cipher(key)

  if ENCRYPT:
    # Encrypt and convert to string:
    secret_bytes=enc.encrypt(pwd)
    secret=secret_bytes.decode("utf-8")
    verbose(secret)
    # Convert to bytes and decrypt:
    secret_bytes=secret.encode("utf-8")
    verbose(enc.decrypt(secret_bytes))
    # Encode encrypted password:
    base_pwd=secret
    base_bytes=base_pwd.encode("utf-8")
    encode_bytes=base64.b64encode(base_bytes)
    encode_txt=encode_bytes.decode("utf-8")
    print(encode_txt)
  else:
    # Decrypt:
    try:
      encode_bytes=pwd.encode("utf-8")
      base_bytes=base64.b64decode(encode_bytes)
      base_txt=base_bytes.decode("utf-8")
      secret=base_txt
      verbose(secret)
      print(enc.decrypt(secret))
    except BaseException as err:
      sys.exit(f"Failed to decrypt!!! -> {str(err)} ({err.__class__})")
