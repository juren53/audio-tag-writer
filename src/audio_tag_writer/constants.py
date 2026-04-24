"""
Audio Tag Writer - Constants, version info, and default mode definitions.
"""

APP_NAME = "Audio Tag Writer"
APP_VERSION = "0.7.4"
APP_TIMESTAMP = "2026-04-23 19:48"
APP_ORGANIZATION = "SynchroSoft"
APP_USER_MODEL_ID = "SynchroSoft.AudioTagWriter.ATW.0.7.4"
GITHUB_REPO = "juren53/audio-tag-writer"

AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg', '.flac']

# Detection rules: ordered dict of {mode_name: frame_id}.
# First mode whose frame_id is non-empty and present in the file wins.
# Modes with no frame_id are never matched by the rule loop.
DEFAULT_DETECT_FRAMES = {
    "Scientific":         "TXXX:Equipment",
    "Music":              "TRCK",      # Track Number — unique to music; TPE1 is unreliable
    "Archival Recording": "",          # no discriminating frame — use as default
}
# TPE1 (Artist) was the original Music discriminator but HSTL archival files
# have TPE1 = "Harry S. Truman Library" set by the batch pipeline, causing
# false Music matches.  TRCK (Track Number) is safe: archival and scientific
# recordings never carry a track number.
DEFAULT_DETECT_DEFAULT = "Archival Recording"

DEFAULT_MODES = {
    "Archival Recording": [
        {"label": "Title",                "frame_id": "TIT2",            "widget": "line", "max_chars": 2000},
        {"label": "Description",          "frame_id": "COMM",            "widget": "text", "max_chars": 1000},
        {"label": "Accession Number",     "frame_id": "TALB",            "widget": "line", "max_chars": 2000},
        {"label": "Speakers",             "frame_id": "IPLS",            "widget": "line", "max_chars": 2000},
        {"label": "Date Recorded",        "frame_id": "TXXX:DateRecorded","widget": "line", "max_chars": 2000},
        {"label": "Restrictions",         "frame_id": "TCOP",            "widget": "line", "max_chars": 2000},
        {"label": "Location",             "frame_id": "TXXX:Location",   "widget": "line", "max_chars": 2000},
        {"label": "Production/Copyright", "frame_id": "TPUB",            "widget": "line", "max_chars": 2000},
        {"label": "Original Filename",    "frame_id": "TOFN",            "widget": "line", "max_chars": 2000},
        {"label": "Credit",               "frame_id": "TXXX:Credit",     "widget": "line", "max_chars": 2000},
    ],
    "Music": [
        {"label": "Title",        "frame_id": "TIT2",        "widget": "line", "max_chars": 2000},
        {"label": "Artist",       "frame_id": "TPE1",        "widget": "line", "max_chars": 2000},
        {"label": "Album",        "frame_id": "TALB",        "widget": "line", "max_chars": 2000},
        {"label": "Track Number", "frame_id": "TRCK",        "widget": "line", "max_chars": 2000},
        {"label": "Year",         "frame_id": "TDRC",        "widget": "line", "max_chars": 2000},
        {"label": "Genre",        "frame_id": "TCON",        "widget": "line", "max_chars": 2000},
        {"label": "Comment",      "frame_id": "COMM",        "widget": "text", "max_chars": 1000},
        {"label": "Composer",     "frame_id": "TCOM",        "widget": "line", "max_chars": 2000},
        {"label": "Album Artist", "frame_id": "TPE2",        "widget": "line", "max_chars": 2000},
        {"label": "Credit",       "frame_id": "TXXX:Credit", "widget": "line", "max_chars": 2000},
    ],
    "Scientific": [
        {"label": "Title",          "frame_id": "TIT2",             "widget": "line", "max_chars": 2000},
        {"label": "Description",    "frame_id": "COMM",             "widget": "text", "max_chars": 1000},
        {"label": "Researcher",     "frame_id": "TXXX:Researcher",  "widget": "line", "max_chars": 2000},
        {"label": "Date Recorded",  "frame_id": "TXXX:DateRecorded","widget": "line", "max_chars": 2000},
        {"label": "Location",       "frame_id": "TXXX:Location",    "widget": "line", "max_chars": 2000},
        {"label": "Subject/Species","frame_id": "TXXX:Subject",     "widget": "line", "max_chars": 2000},
        {"label": "Equipment",      "frame_id": "TXXX:Equipment",   "widget": "line", "max_chars": 2000},
        {"label": "Collection",     "frame_id": "TIT1",             "widget": "line", "max_chars": 2000},
        {"label": "Credit",         "frame_id": "TXXX:Credit",      "widget": "line", "max_chars": 2000},
    ],
}
