"""
Regenerate tests/fixtures/archival_sample.mp3 — the small committed MP3 the test suite
uses when the HSTL test corpus is not available (e.g. on GitHub Actions CI).

It is a 3-second mono 440 Hz tone (MP3, 64 kbps) carrying an HSTL-style Archival
Recording tag set written as ID3v2.3, so the real-file tests (load, save/reload,
ID3v2.3, JSON export/import, stream info) exercise the same code paths as on a real
archival recording.

Usage (needs an ffmpeg with libmp3lame on PATH, or pass its path):
    python tests/fixtures/make_sample_mp3.py [path\\to\\ffmpeg.exe]
"""

import os
import shutil
import subprocess
import sys

from mutagen.id3 import ID3, TIT2, TIT3, TALB, TPE1, TCON, TCOP, TRDA, TYER, TXXX, COMM, IPLS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'archival_sample.mp3')


def main():
    ffmpeg = sys.argv[1] if len(sys.argv) > 1 else shutil.which('ffmpeg')
    if not ffmpeg:
        raise SystemExit('ffmpeg not found — pass its path as the first argument.')
    subprocess.run([ffmpeg, '-v', 'error', '-y',
                    '-f', 'lavfi', '-i', 'sine=frequency=440:duration=3',
                    '-ac', '1', '-c:a', 'libmp3lame', '-b:a', '64k',
                    '-map_metadata', '-1', '-id3v2_version', '0', '-write_xing', '0', OUT],
                   check=True)

    tags = ID3()
    tags['TIT2'] = TIT2(encoding=3, text=['Sample Archival Recording'])
    tags['TIT3'] = TIT3(encoding=3, text=['Synthetic 440 Hz tone used by the ATW test suite.'])
    tags['TALB'] = TALB(encoding=3, text=['SR00-000'])
    tags['TPE1'] = TPE1(encoding=3, text=['Harry S. Truman Library'])
    tags['TCON'] = TCON(encoding=3, text=['speech'])
    tags['TCOP'] = TCOP(encoding=3, text=['None'])
    tags['TRDA'] = TRDA(encoding=3, text=['1948-05-03'])
    tags['TYER'] = TYER(encoding=3, text=['1948'])
    tags['TXXX:TLOC'] = TXXX(encoding=3, desc='TLOC', text=['Independence, MO'])
    tags['COMM::eng'] = COMM(encoding=3, lang='eng', desc='', text=['Test fixture'])
    tags['IPLS'] = IPLS(encoding=3, people=[['speaker', 'Test Speaker']])
    tags.save(OUT, v2_version=3)
    print(f'Wrote {OUT}  ({os.path.getsize(OUT):,} bytes)')


if __name__ == '__main__':
    main()
