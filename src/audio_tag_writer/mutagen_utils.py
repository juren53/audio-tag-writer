"""
Audio Tag Writer - Mutagen wrapper with consistent error handling.
"""

import logging

logger = logging.getLogger(__name__)


class AudioFileError(Exception):
    """Raised when an audio file cannot be opened or parsed."""


def check_mutagen_available():
    """Pre-flight check; raises AudioFileError with install hint if mutagen is missing."""
    try:
        import mutagen  # noqa: F401
    except ImportError:
        raise AudioFileError(
            "The 'mutagen' library is not installed.\n\n"
            "Install it with:  pip install mutagen"
        )


def open_audio(path: str):
    """
    Open any supported audio file and return a mutagen FileType object.
    Raises AudioFileError on failure.
    """
    try:
        import mutagen
        audio = mutagen.File(path)
        if audio is None:
            raise AudioFileError(f"Unsupported or unrecognised audio format: {path}")
        return audio
    except AudioFileError:
        raise
    except Exception as e:
        raise AudioFileError(f"Could not open audio file '{path}': {e}") from e


def safe_get_text(tags, frame_id: str, default: str = '') -> str:
    """
    Return the first text value from an ID3 frame, or default if the frame is absent.
    Handles both standard frames (e.g. 'TIT2') and TXXX frames (e.g. 'TXXX:Credit').
    """
    if tags is None:
        return default
    try:
        if frame_id.startswith('TXXX:'):
            desc = frame_id[5:]
            for key, frame in tags.items():
                if key.startswith('TXXX') and getattr(frame, 'desc', '') == desc:
                    text = frame.text
                    return text[0] if text else default
            return default

        if frame_id == 'COMM':
            # Return the first COMM frame regardless of language/description
            for key, frame in tags.items():
                if key.startswith('COMM'):
                    text = frame.text
                    return text[0] if text else default
            return default

        frame = tags.get(frame_id)
        if frame is None:
            return default
        text = getattr(frame, 'text', None)
        if text:
            return text[0] if isinstance(text, list) else str(text)
        return default
    except Exception as e:
        logger.warning(f"Error reading frame '{frame_id}': {e}")
        return default
