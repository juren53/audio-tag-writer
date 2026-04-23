"""
Tests for audio_tag_writer.metadata (MetadataManager)
"""

import json
import os
import pytest

from audio_tag_writer.metadata import MetadataManager
from audio_tag_writer.mutagen_utils import AudioFileError


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

@pytest.fixture
def mgr():
    """Fresh MetadataManager in Archival Recording mode."""
    return MetadataManager()


# ------------------------------------------------------------------
# _sanitize_value
# ------------------------------------------------------------------

def test_sanitize_strips_whitespace(mgr):
    assert mgr._sanitize_value('  hello  ') == 'hello'


def test_sanitize_strips_null_bytes(mgr):
    assert mgr._sanitize_value('hel\x00lo') == 'hello'


def test_sanitize_normalizes_crlf(mgr):
    result = mgr._sanitize_value('line1\r\nline2\rline3')
    assert '\r' not in result
    assert result == 'line1\nline2\nline3'


def test_sanitize_caps_at_max_chars(mgr):
    long_str = 'x' * 3000
    result = mgr._sanitize_value(long_str, max_chars=2000)
    assert len(result) == 2000


def test_sanitize_non_string_returns_empty(mgr):
    assert mgr._sanitize_value(None) == ''
    assert mgr._sanitize_value(42) == ''
    assert mgr._sanitize_value(['list']) == ''


# ------------------------------------------------------------------
# load_from_file
# ------------------------------------------------------------------

def test_load_from_file_returns_false_for_missing(mgr, tmp_path):
    result = mgr.load_from_file(str(tmp_path / 'ghost.mp3'))
    assert result is False


def test_load_from_file_returns_true_for_real_mp3(mgr, real_mp3):
    assert mgr.load_from_file(real_mp3) is True


def test_load_from_file_sets_current_path(mgr, real_mp3):
    mgr.load_from_file(real_mp3)
    assert mgr.current_path == real_mp3


def test_load_from_file_populates_title(mgr, real_mp3):
    mgr.load_from_file(real_mp3)
    title = mgr.get_field('Title')
    assert isinstance(title, str)   # may be empty if tag absent, but must be a string


# ------------------------------------------------------------------
# _read_frame — IPLS flattening (in-memory tags)
# ------------------------------------------------------------------

def test_read_ipls_flattens_to_string(mgr, tagged_id3):
    raw = mgr._read_frame(tagged_id3, 'IPLS')
    assert 'Jane Smith' in raw
    assert 'John Doe' in raw


def test_read_ipls_falls_back_to_tipl(mgr):
    """Mutagen may present IPLS as TIPL after v2.4 normalisation."""
    from mutagen.id3 import ID3, TIPL
    tags = ID3()
    tags['TIPL'] = TIPL(encoding=3, people=[['producer', 'Alice']])
    raw = mgr._read_frame(tags, 'IPLS')
    assert 'Alice' in raw


def test_read_frame_none_tags_returns_empty(mgr):
    assert mgr._read_frame(None, 'TIT2') == ''


# ------------------------------------------------------------------
# save_to_file — raises for unsupported formats
# ------------------------------------------------------------------

def test_save_raises_for_ogg(mgr, tmp_path):
    path = str(tmp_path / 'test.ogg')
    open(path, 'w').close()
    with pytest.raises(AudioFileError, match='OGG'):
        mgr.save_to_file(path)


def test_save_raises_for_flac(mgr, tmp_path):
    path = str(tmp_path / 'test.flac')
    open(path, 'w').close()
    with pytest.raises(AudioFileError, match='FLAC'):
        mgr.save_to_file(path)


# ------------------------------------------------------------------
# save_to_file — MP3 write/read roundtrip
# ------------------------------------------------------------------

def test_save_and_reload_title(mp3_copy):
    mgr = MetadataManager()
    mgr.load_from_file(mp3_copy)
    mgr.set_field('Title', 'Roundtrip Test Title')
    mgr.save_to_file(mp3_copy)

    mgr2 = MetadataManager()
    mgr2.load_from_file(mp3_copy)
    assert mgr2.get_field('Title') == 'Roundtrip Test Title'


def test_save_uses_id3v23(mp3_copy):
    """Saved file must use ID3v2.3 (v2_version=3) for archival compatibility."""
    mgr = MetadataManager()
    mgr.load_from_file(mp3_copy)
    mgr.set_field('Title', 'Version Check')
    mgr.save_to_file(mp3_copy)

    import mutagen.mp3
    audio = mutagen.mp3.MP3(mp3_copy)
    assert audio.tags.version[0] == 2
    assert audio.tags.version[1] == 3


def test_save_and_reload_description(mp3_copy):
    mgr = MetadataManager()
    mgr.load_from_file(mp3_copy)
    mgr.set_field('Description', 'A test description for COMM frame.')
    mgr.save_to_file(mp3_copy)

    mgr2 = MetadataManager()
    mgr2.load_from_file(mp3_copy)
    assert mgr2.get_field('Description') == 'A test description for COMM frame.'


def test_save_and_reload_txxx_field(mp3_copy):
    mgr = MetadataManager()
    mgr.load_from_file(mp3_copy)
    mgr.set_field('Credit', 'HSTL Test Credit')
    mgr.save_to_file(mp3_copy)

    mgr2 = MetadataManager()
    mgr2.load_from_file(mp3_copy)
    assert mgr2.get_field('Credit') == 'HSTL Test Credit'


# ------------------------------------------------------------------
# JSON export / import roundtrip
# ------------------------------------------------------------------

def test_export_creates_json_file(mgr, real_mp3, tmp_path):
    mgr.load_from_file(real_mp3)
    out = str(tmp_path / 'meta.json')
    assert mgr.export_to_json(out) is True
    assert os.path.isfile(out)


def test_export_json_contains_metadata_key(mgr, real_mp3, tmp_path):
    mgr.load_from_file(real_mp3)
    out = str(tmp_path / 'meta.json')
    mgr.export_to_json(out)
    with open(out) as f:
        data = json.load(f)
    assert 'metadata' in data
    assert 'mode' in data
    assert 'filename' in data


def test_import_from_json_restores_values(mgr, real_mp3, tmp_path):
    mgr.load_from_file(real_mp3)
    mgr.set_field('Title', 'Export Test')
    out = str(tmp_path / 'meta.json')
    mgr.export_to_json(out)

    mgr2 = MetadataManager()
    mgr2.load_from_file(real_mp3)
    mgr2.import_from_json(out)
    assert mgr2.get_field('Title') == 'Export Test'


def test_json_roundtrip_preserves_all_fields(mgr, real_mp3, tmp_path):
    mgr.load_from_file(real_mp3)
    mgr.set_field('Title', 'RT Title')
    mgr.set_field('Description', 'RT Desc')
    out = str(tmp_path / 'rt.json')
    mgr.export_to_json(out)

    mgr2 = MetadataManager()
    mgr2.load_from_file(real_mp3)
    mgr2.import_from_json(out)

    assert mgr2.get_field('Title') == 'RT Title'
    assert mgr2.get_field('Description') == 'RT Desc'
