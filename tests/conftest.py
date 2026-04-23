"""
Shared pytest fixtures for audio-tag-writer tests.
"""

import os
import sys
import shutil

import pytest

# Ensure src/ is on the import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Real MP3s from the HSTL test corpus (available on dev machine, skipped on CI)
_TEST_MP3_DIR = r'C:\Users\juren\Projects\HST-Metadata\Audio\Test-mp3s'
_TEST_MP3 = os.path.join(_TEST_MP3_DIR, 'sr65-11-1.mp3')


@pytest.fixture
def real_mp3():
    """Path to a real, tagged HST MP3 file. Skip if not available (e.g. CI)."""
    if not os.path.isfile(_TEST_MP3):
        pytest.skip(f'Real MP3 not available: {_TEST_MP3}')
    return _TEST_MP3


@pytest.fixture
def mp3_copy(tmp_path, real_mp3):
    """Writable copy of the real test MP3 in a temp directory."""
    dest = tmp_path / 'test_copy.mp3'
    shutil.copy2(real_mp3, dest)
    return str(dest)


@pytest.fixture
def tagged_id3():
    """An in-memory ID3 tag object populated with sample values."""
    from mutagen.id3 import ID3, TIT2, TALB, COMM, TXXX, IPLS
    tags = ID3()
    tags['TIT2'] = TIT2(encoding=3, text=['Test Title'])
    tags['TALB'] = TALB(encoding=3, text=['SR59-001'])
    tags['COMM::eng'] = COMM(encoding=3, lang='eng', desc='', text=['A test description.'])
    tags['TXXX:Credit'] = TXXX(encoding=3, desc='Credit', text=['HSTL'])
    tags['IPLS'] = IPLS(encoding=3, people=[['interviewer', 'Jane Smith'], ['subject', 'John Doe']])
    return tags
