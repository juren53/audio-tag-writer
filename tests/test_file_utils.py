"""
Tests for audio_tag_writer.file_utils
"""

import os
import pytest

from audio_tag_writer.file_utils import get_audio_files


def _touch(directory, filename):
    path = os.path.join(directory, filename)
    open(path, 'w').close()
    return path


# ------------------------------------------------------------------
# Basic behaviour
# ------------------------------------------------------------------

def test_returns_empty_list_for_nonexistent_dir(tmp_path):
    result = get_audio_files(str(tmp_path / 'no_such_dir'))
    assert result == []


def test_returns_empty_list_for_none():
    assert get_audio_files(None) == []


def test_returns_empty_list_for_empty_string():
    assert get_audio_files('') == []


def test_returns_empty_for_directory_with_no_audio(tmp_path):
    _touch(str(tmp_path), 'readme.txt')
    _touch(str(tmp_path), 'image.jpg')
    assert get_audio_files(str(tmp_path)) == []


# ------------------------------------------------------------------
# Extension filtering
# ------------------------------------------------------------------

def test_finds_mp3_files(tmp_path):
    _touch(str(tmp_path), 'track.mp3')
    result = get_audio_files(str(tmp_path))
    assert any('track.mp3' in p for p in result)


def test_finds_wav_files(tmp_path):
    _touch(str(tmp_path), 'recording.wav')
    result = get_audio_files(str(tmp_path))
    assert any('recording.wav' in p for p in result)


def test_finds_ogg_files(tmp_path):
    _touch(str(tmp_path), 'audio.ogg')
    result = get_audio_files(str(tmp_path))
    assert any('audio.ogg' in p for p in result)


def test_finds_flac_files(tmp_path):
    _touch(str(tmp_path), 'lossless.flac')
    result = get_audio_files(str(tmp_path))
    assert any('lossless.flac' in p for p in result)


def test_excludes_non_audio_files(tmp_path):
    _touch(str(tmp_path), 'track.mp3')
    _touch(str(tmp_path), 'cover.jpg')
    _touch(str(tmp_path), 'notes.txt')
    result = get_audio_files(str(tmp_path))
    assert len(result) == 1
    assert result[0].endswith('.mp3')


def test_extension_matching_is_case_insensitive(tmp_path):
    _touch(str(tmp_path), 'upper.MP3')
    _touch(str(tmp_path), 'mixed.Wav')
    result = get_audio_files(str(tmp_path))
    assert len(result) == 2


# ------------------------------------------------------------------
# Sorting
# ------------------------------------------------------------------

def test_results_are_sorted_case_insensitively(tmp_path):
    for name in ('Charlie.mp3', 'alpha.mp3', 'Beta.mp3'):
        _touch(str(tmp_path), name)
    result = get_audio_files(str(tmp_path))
    basenames = [os.path.basename(p).lower() for p in result]
    assert basenames == sorted(basenames)


def test_returns_full_paths(tmp_path):
    _touch(str(tmp_path), 'track.mp3')
    result = get_audio_files(str(tmp_path))
    assert os.path.isabs(result[0])
