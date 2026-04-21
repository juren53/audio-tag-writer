"""
Audio Tag Writer - MetadataManager for ID3 tag operations.
"""

import os
import json
import logging
from datetime import datetime

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
        self._values = {spec['label']: '' for spec in self._field_specs}

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
        self._values = {spec['label']: '' for spec in self._field_specs}
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

                raw = self._read_frame(tags, frame_id)
                self._values[label] = self._sanitize_value(raw, max_chars)

            logger.info(f"Loaded metadata from '{path}'")
            return True

        except AudioFileError as e:
            logger.error(f"AudioFileError loading '{path}': {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error loading '{path}': {e}")
            return False

    def _read_frame(self, tags, frame_id: str) -> str:
        """Read a single frame value from an ID3 tag object."""
        if tags is None:
            return ''

        try:
            # IPLS — Involved People List; flatten to "role: name; ..." string
            if frame_id == 'IPLS':
                frame = tags.get('IPLS')
                if frame and hasattr(frame, 'people'):
                    parts = [
                        f"{p[0]}: {p[1]}" if p[0] else p[1]
                        for p in frame.people
                    ]
                    return '; '.join(parts)
                return ''

            return safe_get_text(tags, frame_id)

        except Exception as e:
            logger.warning(f"Error reading frame '{frame_id}': {e}")
            return ''

    # ------------------------------------------------------------------
    # Write (Phase 3)
    # ------------------------------------------------------------------

    def save_to_file(self, path: str) -> bool:
        """Write current field values back to the audio file as ID3 tags."""
        # Implemented in Phase 3
        logger.warning("save_to_file() not yet implemented (Phase 3)")
        return False

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
