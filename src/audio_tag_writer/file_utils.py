"""
Audio Tag Writer - Audio file scanning utilities.
"""

import os
import logging

from .constants import AUDIO_EXTENSIONS

logger = logging.getLogger(__name__)


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
