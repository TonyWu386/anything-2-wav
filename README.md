# anything-2-wav
This tool converts files of any type into valid and playable wav audio files

Copyright (c) 2018 [Tony Wu], All Right Reserved

License: GNU GPL v3.0

Features:

- Authenticated encryption via passcode or keyfile

- Adjustable bitrate target (affects playback duration)

- Adjustable number of audio channels

All output wav files sound like static. This is intentional, and indicates the encryption is working. Authenticated encryption (AEAD) is provided by ChaCha20-Poly1305 from the pycryptodome library. Key derivation is provided by Scrypt. This system prevents extraction of the original file without the correct passcode/keyfile.

```
sh-4.4$ file img_file.png
img_file.png: PNG image data, 1241 x 1241, 8-bit/color RGBA, non-interlaced

sh-4.4$ python3 anything2wav.py -e -r 256 -c 2 -o legit_wav_file.wav img_file.png
no keyfile provided - asking for passcode instead
enter passcode:

sh-4.4$ file legit_wav_file.wav
legit_wav_file.wav: RIFF (little-endian) data, WAVE audio, Microsoft PCM, 8 bit, stereo 16036 Hz

sh-4.4$ ffprobe legit_wav_file.wav
...
Input #0, wav, from 'legit_wav_file.wav':
  Duration: 00:00:52.93, bitrate: 256 kb/s
    Stream #0:0: Audio: pcm_u8 ([1][0][0][0] / 0x0001), 16036 Hz, 2 channels, u8, 256 kb/s

sh-4.4$ python3 anything2wav.py -d -o back_again.png legit_wav_file.wav
no keyfile provided - asking for passcode instead
enter passcode:

sh-4.4$ file back_again.png
back_again.png: PNG image data, 1241 x 1241, 8-bit/color RGBA, non-interlaced
```
