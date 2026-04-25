"""
Audio Tag Writer - MetadataManager for ID3 tag operations.
"""

import os
import json
import logging
from datetime import datetime

import mutagen
from mutagen.id3 import (
    ID3, ID3NoHeaderError,
    TIT1, TIT2, TIT3, TALB, TPE1, TPE2, TCON, TCOM, TRCK, TDRC, TPUB, TCOP,
    TOFN, TRDA, TXXX, COMM, IPLS, TEXT, TYER, TORY, TDAT,
)

from .config import config
from .mutagen_utils import open_audio, safe_get_text, AudioFileError

logger = logging.getLogger(__name__)


class MetadataManager:
    """Manages audio metadata read/write using Mutagen."""

    def __init__(self):
        self._values = {}       # label -> str value
        self._field_specs = []  # list of spec dicts from active mode
        self.current_path = None
        self._rebuild_from_mode()

    # ------------------------------------------------------------------
    # Mode support
    # ------------------------------------------------------------------

    def _rebuild_from_mode(self, mode_name=None):
        """Rebuild field list from the given (or active) mode spec."""
        self._field_specs = config.get_mode_fields(mode_name)
        self._values = {}
        for spec in self._field_specs:
            label = spec['label']
            if spec.get('widget') == 'hidden':
                self._values[label] = spec.get('auto_value', '')
            else:
                self._values[label] = ''

    def reload_mode(self, mode_name=None):
        """Switch to a different mode, clearing current values."""
        self._rebuild_from_mode(mode_name)
        self.current_path = None

    def get_field_specs(self):
        return list(self._field_specs)

    # ------------------------------------------------------------------
    # Field access
    # ------------------------------------------------------------------

    def get_field(self, label, default=''):
        return self._values.get(label, default)

    def set_field(self, label, value):
        self._values[label] = value

    def get_all_fields(self):
        return dict(self._values)

    def clear(self):
        self._rebuild_from_mode()
        self.current_path = None

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def load_from_file(self, path: str) -> bool:
        """Load ID3 tags from an audio file into the field store."""
        if not os.path.exists(path):
            logger.error(f"File not found: {path}")
            return False

        self.clear()
        self.current_path = path

        try:
            audio = open_audio(path)
            tags = audio.tags

            for spec in self._field_specs:
                label = spec['label']
                frame_id = spec['frame_id']
                max_chars = spec.get('max_chars', 2000)

                # Hidden fields are auto-generated on save; skip reading from file.
                if spec.get('widget') == 'hidden':
                    continue

                raw = self._read_frame(tags, frame_id)

                # Alias fallback: try each alias in order if primary frame is empty.
                if not raw:
                    for alias in spec.get('aliases', []):
                        raw = self._read_frame(tags, alias)
                        if raw:
                            break

                self._values[label] = self._sanitize_value(raw, max_chars)

            logger.info(f"Loaded metadata from '{path}'")
            return True

        except AudioFileError as e:
            logger.error(f"AudioFileError loading '{path}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error loading '{path}': {e}")
            return False

    # Mutagen converts these ID3v2.3 frames to v2.4 equivalents on load.
    _V23_TO_V24 = {
        'TRDA': 'TDRC',  # Recording Dates → Recording Time
        'TORY': 'TDOR',  # Original Release Year → Original Release Time
    }

    def _read_frame(self, tags, frame_id: str) -> str:
        """Read a single frame value from an ID3 tag object."""
        if tags is None:
            return ''

        try:
            # IPLS — Involved People List; flatten to "role: name; ..." string.
            # Mutagen's default translate-to-v2.4 on load converts IPLS → TIPL,
            # so check both frame IDs.
            if frame_id == 'IPLS':
                frame = tags.get('IPLS') or tags.get('TIPL')
                if frame and hasattr(frame, 'people'):
                    parts = [
                        f"{p[0]}: {p[1]}" if p[0] else p[1]
                        for p in frame.people
                    ]
                    return '; '.join(parts)
                return ''

            raw = safe_get_text(tags, frame_id)
            # Fall back to v2.4 equivalent if mutagen converted the v2.3 frame.
            if not raw and frame_id in self._V23_TO_V24:
                raw = safe_get_text(tags, self._V23_TO_V24[frame_id])
            return raw

        except Exception as e:
            logger.warning(f"Error reading frame '{frame_id}': {e}")
            return ''

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save_to_file(self, path: str) -> bool:
        """Write current field values back to the audio file as ID3 tags."""
        ext = os.path.splitext(path)[1].lower()
        if ext not in ('.mp3', '.wav'):
            logger.error(f"ID3 write not supported for format: {ext}")
            raise AudioFileError(
                f"Metadata writing is only supported for MP3 and WAV files.\n"
                f"'{os.path.basename(path)}' is a {ext.lstrip('.').upper()} file."
            )

        try:
            audio = open_audio(path)
        except AudioFileError:
            raise

        if audio.tags is None:
            audio.add_tags()

        tags = audio.tags

        for spec in self._field_specs:
            label = spec['label']
            frame_id = spec['frame_id']

            if spec.get('widget') == 'hidden':
                auto_val = spec.get('auto_value', '')
                if auto_val == '__app_version__':
                    from .constants import APP_NAME, APP_VERSION
                    value = f"{APP_NAME} v{APP_VERSION}"
                else:
                    value = auto_val
            else:
                value = self._values.get(label, '').strip()

            self._write_frame(tags, frame_id, value)

            for alias in spec.get('aliases', []):
                self._write_frame(tags, alias, value)

            if spec.get('date_field'):
                self._write_date_derived(tags, value)

        # Enforce ID3v2.3 — TRDA, TDAT, TYER, TORY, IPLS are v2.3-only frames.
        tags.update_to_v23()
        audio.save(v2_version=3)

        logger.info(f"Saved metadata to '{path}'")
        return True

    # Standard frame classes keyed by frame ID
    _SIMPLE_FRAME_MAP = {
        'TIT1': TIT1, 'TIT2': TIT2, 'TIT3': TIT3,
        'TALB': TALB, 'TPE1': TPE1, 'TPE2': TPE2,
        'TCON': TCON, 'TCOM': TCOM, 'TRCK': TRCK, 'TDRC': TDRC,
        'TPUB': TPUB, 'TCOP': TCOP, 'TOFN': TOFN,
        'TRDA': TRDA, 'TEXT': TEXT,
        'TYER': TYER, 'TORY': TORY, 'TDAT': TDAT,
    }

    def _write_frame(self, tags, frame_id: str, value: str):
        """Set or delete a single ID3 frame based on value."""
        if frame_id == 'IPLS':
            self._write_ipls(tags, value)
            return

        if frame_id == 'COMM':
            self._write_comm(tags, value)
            return

        if frame_id.startswith('TXXX:'):
            desc = frame_id[5:]
            key = f'TXXX:{desc}'
            if value:
                tags[key] = TXXX(encoding=3, desc=desc, text=[value])
            else:
                tags.delall(key)
            return

        frame_cls = self._SIMPLE_FRAME_MAP.get(frame_id)
        if frame_cls is None:
            logger.warning(f"Unknown frame ID '{frame_id}' — skipped")
            return

        if value:
            tags[frame_id] = frame_cls(encoding=3, text=[value])
        else:
            tags.delall(frame_id)

    def _write_comm(self, tags, value: str):
        """Write or delete the COMM frame (lang=eng, desc='')."""
        key = 'COMM::eng'
        if value:
            tags[key] = COMM(encoding=3, lang='eng', desc='', text=[value])
        else:
            tags.delall('COMM')

    def _write_ipls(self, tags, value: str):
        """
        Write IPLS from a 'role: name; role: name' display string.
        Pairs without a colon are stored as ('', name).
        """
        if not value:
            tags.delall('IPLS')
            return

        people = []
        for part in value.split(';'):
            part = part.strip()
            if ':' in part:
                role, name = part.split(':', 1)
                people.append([role.strip(), name.strip()])
            elif part:
                people.append(['', part])

        if people:
            tags['IPLS'] = IPLS(encoding=3, people=people)
        else:
            tags.delall('IPLS')

    def _write_date_derived(self, tags, date_str: str):
        """
        Write auxiliary ID3v2.3 date frames derived from date_str.
        Expects ISO format (YYYY, YYYY-MM, or YYYY-MM-DD); skips derived
        frames gracefully if the value doesn't parse.
        """
        for fid in ('TYER', 'TORY', 'TDAT'):
            tags.delall(fid)
        tags.delall('TXXX:ICRD')

        if not date_str:
            return

        parts = [p.strip() for p in date_str.split('-')]
        year  = parts[0] if len(parts) > 0 and parts[0].isdigit() and len(parts[0]) == 4 else ''
        month = parts[1] if len(parts) > 1 and parts[1].isdigit() else ''
        day   = parts[2] if len(parts) > 2 and parts[2].isdigit() else ''

        if year:
            tags['TYER'] = TYER(encoding=3, text=[year])
            tags['TORY'] = TORY(encoding=3, text=[year])

        if month and day:
            tags['TDAT'] = TDAT(encoding=3, text=[day.zfill(2) + month.zfill(2)])

        tags['TXXX:ICRD'] = TXXX(encoding=3, desc='ICRD', text=[date_str])

    # ------------------------------------------------------------------
    # Export / Import
    # ------------------------------------------------------------------

    def export_to_json(self, path: str) -> bool:
        try:
            data = {
                'filename':    os.path.basename(self.current_path or ''),
                'export_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'mode':        config.get_active_mode(),
                'metadata':    self._values,
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info(f"Exported metadata to '{path}'")
            return True
        except Exception as e:
            logger.error(f"Error exporting metadata: {e}")
            return False

    def import_from_json(self, path: str) -> bool:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            imported = data.get('metadata', data)
            for label in self._values:
                if label in imported:
                    self._values[label] = self._sanitize_value(str(imported[label]))
            logger.info(f"Imported metadata from '{path}'")
            return True
        except Exception as e:
            logger.error(f"Error importing metadata: {e}")
            return False

    # ------------------------------------------------------------------
    # Sanitization
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize_value(value, max_chars: int = 2000) -> str:
        if not isinstance(value, str):
            return ''
        value = value.replace('\x00', '')
        value = value.replace('\r\n', '\n').replace('\r', '\n')
        value = value.strip()
        if len(value) > max_chars:
            value = value[:max_chars]
        return value
