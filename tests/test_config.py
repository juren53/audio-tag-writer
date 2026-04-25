"""
Tests for audio_tag_writer.config (Config class)
"""

import json
import os
import pytest

from audio_tag_writer.constants import DEFAULT_MODES


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def make_config(tmp_path):
    """Create a fresh Config instance backed by a temp config file."""
    from audio_tag_writer.config import Config
    cfg = Config()
    cfg.config_file = str(tmp_path / 'test_config.json')
    return cfg


# ------------------------------------------------------------------
# Default values
# ------------------------------------------------------------------

def test_default_active_mode(tmp_path):
    cfg = make_config(tmp_path)
    # After construction the active mode is either from disk or the default
    assert cfg.active_mode in cfg.modes


def test_all_default_modes_present(tmp_path):
    cfg = make_config(tmp_path)
    for mode_name in DEFAULT_MODES:
        assert mode_name in cfg.modes


def test_default_theme_is_string(tmp_path):
    cfg = make_config(tmp_path)
    assert isinstance(cfg.current_theme, str)


# ------------------------------------------------------------------
# add_recent_file
# ------------------------------------------------------------------

def test_add_recent_file_appends(tmp_path):
    cfg = make_config(tmp_path)
    cfg.recent_files = []
    mp3 = tmp_path / 'a.mp3'
    mp3.write_bytes(b'')
    cfg.add_recent_file(str(mp3))
    assert str(mp3) in cfg.recent_files


def test_add_recent_file_deduplicates_to_front(tmp_path):
    cfg = make_config(tmp_path)
    cfg.recent_files = []
    f1, f2 = tmp_path / 'a.mp3', tmp_path / 'b.mp3'
    f1.write_bytes(b'')
    f2.write_bytes(b'')
    cfg.add_recent_file(str(f1))
    cfg.add_recent_file(str(f2))
    cfg.add_recent_file(str(f1))   # duplicate — should move to front
    assert cfg.recent_files[0] == str(f1)
    assert len(cfg.recent_files) == 2


def test_add_recent_file_capped_at_10(tmp_path):
    cfg = make_config(tmp_path)
    cfg.recent_files = []
    files = []
    for i in range(12):
        p = tmp_path / f'file_{i}.mp3'
        p.write_bytes(b'')
        files.append(str(p))
    for f in files:
        cfg.add_recent_file(f)
    assert len(cfg.recent_files) <= 10


def test_add_recent_file_ignores_nonexistent(tmp_path):
    cfg = make_config(tmp_path)
    cfg.recent_files = []
    cfg.add_recent_file(str(tmp_path / 'ghost.mp3'))
    assert cfg.recent_files == []


# ------------------------------------------------------------------
# Mode helpers
# ------------------------------------------------------------------

def test_get_mode_fields_returns_list(tmp_path):
    cfg = make_config(tmp_path)
    fields = cfg.get_mode_fields('Archival Recording')
    assert isinstance(fields, list)
    assert len(fields) > 0


def test_get_mode_fields_each_has_label_and_frame_id(tmp_path):
    cfg = make_config(tmp_path)
    for mode in DEFAULT_MODES:
        for spec in cfg.get_mode_fields(mode):
            assert 'label' in spec
            assert 'frame_id' in spec


def test_set_active_mode(tmp_path):
    cfg = make_config(tmp_path)
    cfg.set_active_mode('Music')
    assert cfg.active_mode == 'Music'


def test_reset_mode_to_default_restores_fields(tmp_path):
    cfg = make_config(tmp_path)
    # Corrupt the Archival Recording mode
    cfg.modes['Archival Recording'] = [{'label': 'JUNK', 'frame_id': 'JUNK', 'widget': 'line'}]
    cfg.reset_mode_to_default('Archival Recording')
    assert cfg.modes['Archival Recording'] == DEFAULT_MODES['Archival Recording']


# ------------------------------------------------------------------
# Save / load roundtrip
# ------------------------------------------------------------------

def test_save_load_roundtrip(tmp_path):
    cfg = make_config(tmp_path)
    cfg.current_theme = 'Dark'
    cfg.active_mode = 'Music'
    cfg.save_config()

    cfg2 = make_config(tmp_path)   # same temp config_file
    cfg2.load_config()
    assert cfg2.current_theme == 'Dark'
    assert cfg2.active_mode == 'Music'


def test_builtin_modes_overwrite_stale_frame_ids(tmp_path):
    """Saved config with stale TLOC frame_id is replaced by DEFAULT_MODES on load."""
    stale = {
        'modes': {
            'Archival Recording': [
                {'label': 'Location', 'frame_id': 'TLOC', 'widget': 'line', 'max_chars': 2000}
            ]
        }
    }
    config_path = tmp_path / 'stale.json'
    config_path.write_text(json.dumps(stale))

    from audio_tag_writer.config import Config
    cfg = Config()
    cfg.config_file = str(config_path)
    cfg.load_config()

    loc = next(
        f for f in cfg.modes['Archival Recording'] if f['label'] == 'Location'
    )
    assert loc['frame_id'] == 'TXXX:TLOC'


def test_custom_mode_preserved_on_load(tmp_path):
    """User-added modes that are not in DEFAULT_MODES survive a load cycle."""
    saved = {
        'modes': {
            'Custom Mode': [
                {'label': 'MyField', 'frame_id': 'TXXX:MyField', 'widget': 'line'}
            ],
            **{name: list(fields) for name, fields in DEFAULT_MODES.items()}
        }
    }
    config_path = tmp_path / 'custom.json'
    config_path.write_text(json.dumps(saved))

    from audio_tag_writer.config import Config
    cfg = Config()
    cfg.config_file = str(config_path)
    cfg.load_config()

    assert 'Custom Mode' in cfg.modes
