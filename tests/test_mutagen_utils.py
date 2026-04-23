"""
Tests for audio_tag_writer.mutagen_utils
"""

import pytest
from mutagen.id3 import ID3, TIT2, TALB, TXXX, COMM

from audio_tag_writer.mutagen_utils import (
    AudioFileError, check_mutagen_available, open_audio, safe_get_text,
)


# ------------------------------------------------------------------
# check_mutagen_available
# ------------------------------------------------------------------

def test_check_mutagen_available_succeeds():
    """mutagen is installed — should not raise."""
    check_mutagen_available()


# ------------------------------------------------------------------
# open_audio
# ------------------------------------------------------------------

def test_open_audio_returns_object(real_mp3):
    audio = open_audio(real_mp3)
    assert audio is not None


def test_open_audio_raises_on_missing_file(tmp_path):
    with pytest.raises(AudioFileError):
        open_audio(str(tmp_path / 'nonexistent.mp3'))


def test_open_audio_raises_on_non_audio_file(tmp_path):
    txt = tmp_path / 'not_audio.txt'
    txt.write_text('hello world')
    with pytest.raises(AudioFileError):
        open_audio(str(txt))


# ------------------------------------------------------------------
# safe_get_text — standard frames
# ------------------------------------------------------------------

def test_safe_get_text_standard_frame():
    tags = ID3()
    tags['TIT2'] = TIT2(encoding=3, text=['Hello'])
    assert safe_get_text(tags, 'TIT2') == 'Hello'


def test_safe_get_text_returns_default_for_missing_frame():
    tags = ID3()
    assert safe_get_text(tags, 'TIT2') == ''
    assert safe_get_text(tags, 'TIT2', default='N/A') == 'N/A'


def test_safe_get_text_none_tags():
    assert safe_get_text(None, 'TIT2') == ''
    assert safe_get_text(None, 'TIT2', default='X') == 'X'


# ------------------------------------------------------------------
# safe_get_text — TXXX frames
# ------------------------------------------------------------------

def test_safe_get_text_txxx_frame():
    tags = ID3()
    tags['TXXX:Credit'] = TXXX(encoding=3, desc='Credit', text=['HSTL'])
    assert safe_get_text(tags, 'TXXX:Credit') == 'HSTL'


def test_safe_get_text_txxx_missing_desc():
    tags = ID3()
    tags['TXXX:Credit'] = TXXX(encoding=3, desc='Credit', text=['HSTL'])
    assert safe_get_text(tags, 'TXXX:Location') == ''


# ------------------------------------------------------------------
# safe_get_text — COMM frames
# ------------------------------------------------------------------

def test_safe_get_text_comm_frame():
    tags = ID3()
    tags['COMM::eng'] = COMM(encoding=3, lang='eng', desc='', text=['A description'])
    assert safe_get_text(tags, 'COMM') == 'A description'


def test_safe_get_text_comm_missing():
    tags = ID3()
    assert safe_get_text(tags, 'COMM') == ''
