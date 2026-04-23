"""
Audio Tag Writer - Constants, version info, and default mode definitions.
"""

APP_NAME = "Audio Tag Writer"
APP_VERSION = "0.6.3"
APP_TIMESTAMP = "2026-04-23 09:55"
APP_ORGANIZATION = "SynchroSoft"
APP_USER_MODEL_ID = "SynchroSoft.AudioTagWriter.ATW.0.6.3"
GITHUB_REPO = "juren53/audio-tag-writer"

AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg', '.flac']

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
        {"label": "Accession Number","frame_id": "TALB",            "widget": "line", "max_chars": 2000},
        {"label": "Researcher",     "frame_id": "TXXX:Researcher",  "widget": "line", "max_chars": 2000},
        {"label": "Date Recorded",  "frame_id": "TXXX:DateRecorded","widget": "line", "max_chars": 2000},
        {"label": "Location",       "frame_id": "TXXX:Location",    "widget": "line", "max_chars": 2000},
        {"label": "Subject/Species","frame_id": "TXXX:Subject",     "widget": "line", "max_chars": 2000},
        {"label": "Equipment",      "frame_id": "TXXX:Equipment",   "widget": "line", "max_chars": 2000},
        {"label": "Collection",     "frame_id": "TIT1",             "widget": "line", "max_chars": 2000},
        {"label": "Credit",         "frame_id": "TXXX:Credit",      "widget": "line", "max_chars": 2000},
    ],
}
