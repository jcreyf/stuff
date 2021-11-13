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
from bs4 import BeautifulSoup

class AES_256_CBC(object):
  """ This class will encrypt/decrypt using the aes-256-cbc cipher.
  """
  
  def __init__(self, key: str, verbose: bool = False) -> None:
    """ Constructor, setting the encryption key.
    If we have a secondary "special key" on the system, then that secondary key
    will be used to encrypt the encryption key.  That encrypted key then becomes the
    actual key to encrypt and decrypt secrets.

    Arguments:
      key (str): the encryption key;
      verbose (bool): level of log messages;
    """
    self.verbose=verbose
    self.block_size=AES.block_size
    # Set the secondary optional "special key" (if we have one):
    try:
      self.log("Fetching special key...")
      with open("key.txt","r") as f:
        _specialKey=f.readline()
      f.close()
      # Remove potential newline characters from the string:
      _specialKey=_specialKey.replace("\n", "")
    except:
      # Ignore any and all exceptions to truly make the "special key" optional.
      _specialKey=""

    if _specialKey == "":
      # Use the given key if we don't have a "special key":
      self.key = hashlib.sha256(key.encode()).digest()
    else:
      # Aha!  We have a secondary key to make things "special".
      self.key=hashlib.sha256(_specialKey.encode()).digest()
      self.log(f"special key: {self.key}")
      _bytes=self.encrypt(key, special=True)
      self.log(f"encrypted: {_bytes}")
      self.key=hashlib.sha256(_bytes.encode("utf-8")).digest()


  def log(self, msg: str) -> None:
    """ Method to log messages.

    Arguments:
      msg (str): the message to log
    """
    if self.verbose:
      print(msg)


  def encrypt(self, txt: str, special: bool = False) -> str:
    """ Encrypt a string and return it as a Base64 encoded string.

    Arguments:
      txt (str): the string to encrypt;
      special (bool): (optional) flag to indicate if the string is the secondary key;

    Returns:
      str: the return value is a Base64 encoded string;
    
    Raises:
      multiple potential exceptions during either the encryption or encoding process;
    """
    # Make sure the text is at the correct length:
    txt=self._pad(txt)
    # This method is also called to encrypt the "special key" (optional secondary key).
    # That optional key needs to get encrypted with the same exact seed every single
    # time to make sure it doesn't change.
    # Secrets encrypted with both the key and secondary key will no longer be decryptable
    # if not the exact same key is used that was used to encrypt the extra key.
    if special:
      # Use a fixed seed:
      iv=b"\xf4\r\xb7\x1b\xbb7\x0e`CX&\x0c\xf7O1\x08"
    else:
      # Generate a random seed based on AES block size (16 bytes in our case):
      iv=Random.new().read(self.block_size)

    # Initialize the cipher:
    cipher=AES.new(self.key, AES.MODE_CBC, iv)
    encoded=base64.b64encode(iv+cipher.encrypt(txt.encode()))
    # We now have a byte object with the encryted string.
    # Encode it as Base64 if not the special key:
    if not special:
          encoded=base64.b64encode(encoded)
    # Return it as a string:
    return encoded.decode("utf-8")


  def decrypt(self, txt: str) -> str:
    """ Decrypt a string

    Arguments:
      txt (str): the string to decrypt;

    Returns:
      str: the return value is the decrypted string;

    Raises:
      multiple potential exceptions during either the decoding or decryption process;
    """
    txt_bytes=txt.encode("utf-8")
    decode_bytes=base64.b64decode(txt_bytes)
    decode_txt=decode_bytes.decode("utf-8")
    txt=base64.b64decode(decode_txt)
    iv=txt[:AES.block_size]
    cipher=AES.new(self.key, AES.MODE_CBC, iv)
    decrypt_txt=self._unpad(cipher.decrypt(txt[AES.block_size:]))
    return decrypt_txt.decode('utf-8')


  def _pad(self, txt: str) -> str:
    """ Append characters to the string to make sure it's the correct length for the block size in the AES encryption.

    Arguments:
      txt (str): the text to pad
    
    Returns:
      str: the padded text
    """
    return txt + \
           (self.block_size - len(txt) % self.block_size) * \
           chr(self.block_size - len(txt) % self.block_size)


  @staticmethod
  def _unpad(s):
    return s[:-ord(s[len(s)-1:])]

# ------

if __name__ == "__main__":
  VERBOSE=False
  def verbose(str):
    """ Only print the message if the Verbose-flag is set. """
    if VERBOSE:
      print(str)

  def processFile(file, encode=True):
    """ Method to encrypt or decrypt all values between <PWD> tags in some HTML-file. """
    print(f"Processing file: {file}")
    # This works to find all passwords (between <PWD> tags):
    html = BeautifulSoup(open(file).read(), "html.parser")
    # Loop through them all:
    for pwd in html.findAll("pwd"):
      txt=pwd.contents[0]
      verbose(f"'{txt}' on line: {pwd.sourceline}, col: {pwd.sourcepos}")
      if encode:
        secret=cipher.encrypt(txt)
      else:
        secret=cipher.decrypt(txt)
      verbose(f" {txt}  ->  {secret}")
      new_tag=html.new_tag("PWD")
      new_tag.string=secret
      pwd.replace_with(new_tag)
    # Write the new html doc:
    new_file=f"{file}_new.html"
    print(f"Writing updates to: {new_file}")
    f=open(new_file, "w")
    f.write(str(html))
    f.close()


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
                        required=False, \
                        metavar="<string>", \
                        help="the string to encrypt/decrypt")
  parser.add_argument("-f", "--file", \
                        dest="__FILE", \
                        required=False, \
                        metavar="<file uri>", \
                        help="file to process html <PWD>-tags")

  # Now parse the command-line arguments and automatically take care of handling some of the usage requests:
  __ARGS=parser.parse_args()

  # Do some argument validations:
  if (__ARGS.__ENCRYPT or __ARGS.__DECRYPT)==False:
    sys.exit("Need to use the '-e' (encrypt) or '-d' (decrypt) flag!")
  if (__ARGS.__ENCRYPT and __ARGS.__DECRYPT)==True:
    sys.exit("Can't use both the '-e' (encrypt) and '-d' (decrypt) flags at the same time!")
  if __ARGS.__PWD == None and __ARGS.__FILE == None:
    sys.exit("Need to provide a password (-p) or file (-f) to process!")
  if __ARGS.__PWD != None and __ARGS.__FILE != None:
    sys.exit("Can't provide both a password (-p) and a file (-f) to process at the same time!")

  # Pull out the values that we want:
  VERBOSE=__ARGS.__VERBOSE
  verbose(__ARGS)
  pwd=__ARGS.__PWD
  ENCRYPT=__ARGS.__ENCRYPT

  cipher=AES_256_CBC(key=__ARGS.__KEY, verbose=VERBOSE)

  if __ARGS.__FILE != None:
    # We need to process a file:
    processFile(__ARGS.__FILE, ENCRYPT)
  else:
    # No file processing.  Just a single encrypt/decrypt:
    if ENCRYPT:
      secret=cipher.encrypt(pwd)
      print(f"{secret}")
    else:
      try:
        secret=cipher.decrypt(pwd)
      except BaseException as err:
        sys.exit(f"Failed to decrypt!!! -> {str(err)} ({err.__class__})")
      # We may get an empty decrypted string if for example a secondary key was used to generate the
      # encrypted string and are now trying to decrypt without that secondary key!
      if secret != "":
        print(f"{secret}")
      else:
        sys.exit("The secret decrypted into an empty string!")
