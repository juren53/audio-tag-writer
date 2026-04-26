"""
Audio Tag Writer - Audio stream info utilities.
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

_FORMAT_MAP = {'.mp3': 'MP3', '.wav': 'WAV', '.ogg': 'OGG', '.flac': 'FLAC'}


def get_audio_info(path: str) -> dict:
    """
    Return a dict of human-readable audio file properties.
    All values are strings; '--' is used when a value is unavailable.
    """
    ext = os.path.splitext(path)[1].lower()
    result = {
        'filename':     os.path.basename(path),
        'duration':     '--',
        'bitrate':      '--',
        'bitrate_mode': '--',
        'sample_rate':  '--',
        'channels':     '--',
        'stereo_mode':  '--',
        'mpeg_version': '--',
        'format':       _FORMAT_MAP.get(ext, '--'),
        'compression':  'Lossless' if ext in ('.flac', '.wav') else ('Lossy' if ext in ('.mp3', '.ogg') else '--'),
        'file_size':    '--',
        'modified':     '--',
    }

    # File system stats (no mutagen needed)
    try:
        stat = os.stat(path)
        size = stat.st_size
        if size < 1024:
            result['file_size'] = f"{size} B"
        elif size < 1024 * 1024:
            result['file_size'] = f"{size / 1024:.1f} KB"
        else:
            result['file_size'] = f"{size / (1024 * 1024):.1f} MB"
        result['modified'] = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d')
    except Exception as e:
        logger.warning(f"Error reading file stats for '{path}': {e}")

    # Audio stream properties via mutagen
    try:
        import mutagen
        audio = mutagen.File(path)
        if audio is None:
            return result

        info = audio.info
        if not info:
            return result

        if hasattr(info, 'length') and info.length:
            secs = int(info.length)
            result['duration'] = f"{secs // 60}:{secs % 60:02d}"

        if hasattr(info, 'bitrate') and info.bitrate:
            result['bitrate'] = f"{info.bitrate // 1000} kbps"

        if hasattr(info, 'sample_rate') and info.sample_rate:
            result['sample_rate'] = f"{info.sample_rate:,} Hz"

        if hasattr(info, 'channels') and info.channels:
            result['channels'] = (
                'Mono' if info.channels == 1
                else 'Stereo' if info.channels == 2
                else f"{info.channels} ch"
            )

        # MP3-specific fields
        if hasattr(info, 'bitratemode'):
            from mutagen.mp3 import BitrateMode
            mode_map = {
                BitrateMode.CBR: 'CBR',
                BitrateMode.VBR: 'VBR',
                BitrateMode.ABR: 'ABR',
            }
            bm = mode_map.get(info.bitratemode, '')
            if bm:
                result['bitrate_mode'] = bm

        if hasattr(info, 'version') and info.version is not None:
            result['mpeg_version'] = f"MPEG {info.version}"

        if hasattr(info, 'mode') and info.mode is not None:
            from mutagen.mp3 import STEREO, JOINTSTEREO, DUALCHANNEL, MONO
            stereo_map = {STEREO: 'Stereo', JOINTSTEREO: 'Joint Stereo',
                          DUALCHANNEL: 'Dual Channel', MONO: 'Mono'}
            result['stereo_mode'] = stereo_map.get(info.mode, str(info.mode))

    except Exception as e:
        logger.warning(f"Error reading audio stream info for '{path}': {e}")

    return result
