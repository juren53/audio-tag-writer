"""
Audio Tag Writer - Audio file scanning utilities.
"""

import os
import logging

from .constants import AUDIO_EXTENSIONS

logger = logging.getLogger(__name__)


def backup_file(file_path: str) -> str | None:
    """Create a timestamped backup copy of file_path; return the backup path or None on failure."""
    if not os.path.exists(file_path):
        return None

    backup_path = f"{file_path}_backup"
    counter = 1
    while os.path.exists(backup_path):
        backup_path = f"{file_path}_backup{counter}"
        counter += 1

    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        return backup_path
    except Exception as e:
        logger.error(f"Error creating backup of '{file_path}': {e}")
        return None


def get_audio_files(directory: str) -> list:
    """Return a sorted list of audio file paths in directory."""
    if not directory or not os.path.exists(directory):
        return []

    audio_files = []
    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_file(follow_symlinks=False):
                    _, ext = os.path.splitext(entry.name)
                    if ext.lower() in AUDIO_EXTENSIONS:
                        audio_files.append(entry.path)
        audio_files.sort(key=lambda x: os.path.basename(x).lower())
        return audio_files
    except Exception as e:
        logger.error(f"Error scanning directory '{directory}': {e}")
        return []
