# ----------------------------------------------------------------------------
# Anything2Wav
#
# Copyright (c) 2018 [Tony Wu], All Right Reserved
# github.com/TonyWu386
#
# License: GNU GPL v3.0
#
# Requires Python3, pycryptodome, and wave
# ----------------------------------------------------------------------------

from Crypto.Cipher import ChaCha20_Poly1305
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import scrypt

from getpass import getpass
from collections import namedtuple
import wave


SCRYPT_ITER = 131072


def getCrypter(keyRaw, kdfSalt, nonce):
    ''' (bytes, bytes, bytes) -> ChaCha20_Poly1305
    Derives the encryption key from provided parameters
    Sets up and returns a ChaCha20_Poly1305 instance
    '''

    keyDerived = scrypt(password = keyRaw, salt = kdfSalt, key_len = 32, \
    N = SCRYPT_ITER, r=8, p=1)

    return ChaCha20_Poly1305.new(key = keyDerived, nonce = nonce)


def encode(keyRaw, inputFile, outputFile, bitrate, channels):
    ''' (bytes, str, str, float, int) -> None
    Encodes the inputFile into a wav file based on parameters
    '''

    # Set up encryption
    kdfSalt = get_random_bytes(32)
    nonce_rfc7539 = get_random_bytes(12)
    crypter = getCrypter(keyRaw, kdfSalt, nonce_rfc7539)

    with open(inputFile, 'rb') as f:
        data = f.read()

    cipherbytes, authData = crypter.encrypt_and_digest(data)

    # Calculate and set up wav header
    wp = namedtuple('_wave_params', ['nchannels', 'sampwidth', 'framerate', \
    'nframes', 'comptype', 'compname'])
    nframes = 1 + len(kdfSalt + nonce_rfc7539 + authData + cipherbytes)
    framerate = (125.284 * bitrate) / channels
    header = wp(channels, 1, framerate, nframes, 'NONE', 'not compressed')

    # The WAV format truncates frame data to multiples of the channel quantity
    # Padding may be required in this case
    paddingCount = 0
    if (channels > 1):
        if (nframes % channels > 0):
            paddingCount = channels - (nframes % channels)

    # Write new wav file to disk
    with wave.open(outputFile, 'wb') as w:
        w.setparams(header)

        # 1B padding count, 32B salt, 12B nonce, 16B auth, ciphertext, padding
        w.writeframes(paddingCount.to_bytes(1, 'big') + kdfSalt + \
        nonce_rfc7539 + authData + cipherbytes + bytes(paddingCount))

    return None


def decode(keyRaw, inputFile, outputFile):
    ''' (bytes, str, str) -> None
    Decodes the inputFile back into its original format
    '''

    # Extract data from wav file
    with wave.open(inputFile, 'rb') as w:
        header = w.getparams()
        data = w.readframes(header[3])

    # 1B padding count
    paddingCount = data[0]
    # 32B salt for KDF
    kdfSalt = data[1:33]
    # 12B nonce for CHACHA20
    nonce_rfc7539 = data[33:45]
    # 16B auth data for POLY1305
    authData = data[45:61]

    # Get ciphertext without any padding, if it was added
    if (paddingCount is 0):
        paddingCount = None
    else:
        paddingCount *= -1

    cipherbytes = data[61: paddingCount]

    # Decrypt extracted data
    crypter = getCrypter(keyRaw, kdfSalt, nonce_rfc7539)
    try:
        plainbytes = crypter.decrypt_and_verify(cipherbytes, authData)
    except ValueError:
        print("Poly1305 Authentication Failed!\n")
        print("If you're sure the passcode/keyfile was correct, then " + \
        "the wav file was tampered with post-encryption.\n")
        print("Aborting...")
        sys.exit(2)

    # Write original file back to disk
    with open(outputFile, 'wb') as f:
        f.write(plainbytes)

    return None


if __name__ == "__main__":

    import os, sys, getopt

    def usage():
        print ('Usage:    ' + os.path.basename(__file__) + \
        ' options input_file ')
        print ('Options:')
        print ('\t -e, --encode')
        print ('\t -d, --decode')
        print ('\t -r, --bitrate')
        print ('\t -c, --channels')
        print ('\t -k key_file, --key=key_file')
        print ('\t -o output_file, --output=output_file')
        sys.exit(2)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hedr:c:k:o:", ["help", \
        "encode", "decode", "bitrate=", "channels=", "key=", "output="])
    except getopt.GetoptError as err:
        print(err)
        usage()

    # Command line parsing
    mode = None
    bitrate = None
    keyFile = None
    outputFile = None
    channels = None
    inputFile = args[0] if len(args) > 0 else None
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-e", "--encode"):
            mode = "encode"
        elif opt in ("-d", "--decode"):
            mode = "decode"
        elif opt in ("-r", "--bitrate"):
            bitrate = arg
        elif opt in ("-c", "--channels"):
            channels = arg
        elif opt in ("-k", "--key"):
            keyFile = arg
        elif opt in ("-o", "--output"):
            outputFile = arg

    # Command line verification
    if (mode is None):
        print('encode/decode option is missing\n')
        usage()

    if (bitrate is None and mode is "encode"):
        print('bitrate option is missing and mode is encode\n')
        usage()
    if (bitrate is not None and mode is "decode"):
        print('bitrate option is present and mode is decode\n')
        usage()
    if (bitrate is not None):
        if (not bitrate.replace('.','',1).isdigit()):
            print('bitrate must be a positive number\n')
            usage()
        else:
            bitrate = float(bitrate)

    if (channels is None and mode is "encode"):
        print('channel option is missing and mode is encode\n')
        usage()
    if (channels is not None and mode is "decode"):
        print('channel option is present and mode is decode\n')
        usage()
    if (channels is not None):
        if (not channels.isdigit()):
            print('channels must be a positive integer\n')
            usage()
        else:
            channels = int(channels)

    if (keyFile is None):
        print('no keyfile provided - asking for passcode instead')
        keyRaw = getpass(prompt = "enter passcode: ").encode()
    else:
        with open(keyFile, 'rb') as f:
            keyRaw = f.read()

    if (outputFile is None):
        print('output option is missing\n')
        usage()
    if (inputFile is None):
        print('input_file is missing\n')
        usage()

    if (mode is "encode"):
        encode(keyRaw, inputFile, outputFile, bitrate, channels)
    else:
        decode(keyRaw, inputFile, outputFile)
