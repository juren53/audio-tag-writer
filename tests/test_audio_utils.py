"""
Tests for audio_tag_writer.audio_utils
"""

import os
import pytest

from audio_tag_writer.audio_utils import get_audio_info


# ------------------------------------------------------------------
# Edge cases that don't require a real audio file
# ------------------------------------------------------------------

def test_returns_dict_with_expected_keys(tmp_path):
    """get_audio_info returns a dict even for a nonexistent file."""
    result = get_audio_info(str(tmp_path / 'ghost.mp3'))
    for key in ('filename', 'duration', 'bitrate', 'sample_rate', 'channels',
                'format', 'file_size', 'modified'):
        assert key in result


def test_missing_file_returns_dashes(tmp_path):
    result = get_audio_info(str(tmp_path / 'ghost.mp3'))
    assert result['duration'] == '--'
    assert result['bitrate'] == '--'
    assert result['file_size'] == '--'


def test_format_detected_from_extension(tmp_path):
    # Format is derived from extension, not audio stream content
    p = tmp_path / 'track.wav'
    p.write_bytes(b'\x00' * 10)
    result = get_audio_info(str(p))
    assert result['format'] == 'WAV'


def test_unknown_extension_gives_dash(tmp_path):
    p = tmp_path / 'track.xyz'
    p.write_bytes(b'\x00' * 10)
    result = get_audio_info(str(p))
    assert result['format'] == '--'


def test_filename_is_basename(tmp_path):
    p = tmp_path / 'my_track.mp3'
    p.write_bytes(b'\x00' * 10)
    result = get_audio_info(str(p))
    assert result['filename'] == 'my_track.mp3'


def test_file_size_bytes(tmp_path):
    p = tmp_path / 'tiny.mp3'
    p.write_bytes(b'\x00' * 100)
    result = get_audio_info(str(p))
    assert result['file_size'].endswith('B')


def test_file_size_kilobytes(tmp_path):
    p = tmp_path / 'medium.mp3'
    p.write_bytes(b'\x00' * 2048)
    result = get_audio_info(str(p))
    assert result['file_size'].endswith('KB')


def test_file_size_megabytes(tmp_path):
    p = tmp_path / 'large.mp3'
    p.write_bytes(b'\x00' * (2 * 1024 * 1024))
    result = get_audio_info(str(p))
    assert result['file_size'].endswith('MB')


# ------------------------------------------------------------------
# Integration tests against a real tagged MP3
# ------------------------------------------------------------------

def test_real_mp3_has_duration(real_mp3):
    result = get_audio_info(real_mp3)
    assert result['duration'] != '--'
    # Duration should be in M:SS format
    parts = result['duration'].split(':')
    assert len(parts) == 2
    assert len(parts[1]) == 2        # zero-padded seconds


def test_real_mp3_has_bitrate(real_mp3):
    result = get_audio_info(real_mp3)
    assert result['bitrate'] != '--'
    assert result['bitrate'].endswith('kbps')


def test_real_mp3_has_sample_rate(real_mp3):
    result = get_audio_info(real_mp3)
    assert result['sample_rate'] != '--'
    assert 'Hz' in result['sample_rate']


def test_real_mp3_channels(real_mp3):
    result = get_audio_info(real_mp3)
    assert result['channels'] in ('Mono', 'Stereo') or result['channels'].endswith('ch')


def test_real_mp3_format_is_mp3(real_mp3):
    result = get_audio_info(real_mp3)
    assert result['format'] == 'MP3'
