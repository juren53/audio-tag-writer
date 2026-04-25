# Audio Tag Writer

A desktop application for reading and editing ID3 metadata tags in audio files. Designed for archivists, researchers, and musicians who need accurate, repeatable metadata workflows across large audio collections.

## Features

- **Three built-in modes** — Archival Recording, Music, and Scientific, each with purpose-specific field sets
- **Read and write ID3v2.3 metadata** — enforces v2.3 compatibility so all frames survive across tools
- **Directory navigation** — open a folder and step through files with Prev / Next (or ← → keys)
- **Album art display** — shows embedded APIC frames; music-note placeholder when none present
- **Export / Import JSON** — dump and reload all field values for bulk or scripted workflows
- **View All Tags** — searchable table of every raw ID3 frame in the current file
- **Play button** — hands the file off to the OS default audio player
- **Recent files and directories** — quick access from the File menu
- **Single-instance guard** — prevents duplicate launches
- **Persistent window geometry** — size and position restored on each launch

## Requirements

- Python 3.8+
- PyQt6 ≥ 6.4.2
- mutagen ≥ 1.47.0

All dependencies are installed automatically by the launcher scripts.

## Quick Start

### Windows (PowerShell)

Windows 11 executable is available at:

https://github.com/juren53/audio-tag-writer/releases

```powershell
git clone https://github.com/juren53/audio-tag-writer.git
cd audio-tag-writer
.\run.ps1
```

### Linux / macOS

```bash
git clone https://github.com/juren53/audio-tag-writer.git
cd audio-tag-writer
./run.sh
```

The launcher will locate Python, create a virtual environment under `venv/`, install dependencies, and start the app. Dependencies are only reinstalled when `requirements.txt` changes.

You can open a file directly from the command line:

```bash
./run.sh path/to/recording.mp3
```

## Supported Formats

| Format | Read | Write |
|--------|------|-------|
| MP3    | ✓    | ✓     |
| WAV    | ✓    | ✓     |
| OGG    | ✓    | —     |
| FLAC   | ✓    | —     |

Write support is limited to ID3-capable containers (MP3 and WAV). OGG and FLAC tags can be viewed but not saved.

## Modes

Switch modes from the metadata panel. Each mode presents a fixed set of fields tailored to a specific use case.

### Archival Recording

| Field | ID3 Frame |
|---|---|
| Title | TIT2 |
| Description | COMM |
| Accession Number | TALB |
| Speakers | IPLS |
| Date Recorded | TXXX:DateRecorded |
| Restrictions | TCOP |
| Location | TXXX:Location |
| Production/Copyright | TPUB |
| Original Filename | TOFN |
| Credit | TXXX:Credit |

### Music

| Field | ID3 Frame |
|---|---|
| Title | TIT2 |
| Artist | TPE1 |
| Album | TALB |
| Track Number | TRCK |
| Year | TDRC |
| Genre | TCON |
| Comment | COMM |
| Composer | TCOM |
| Album Artist | TPE2 |
| Credit | TXXX:Credit |

### Scientific

| Field | ID3 Frame |
|---|---|
| Title | TIT2 |
| Description | COMM |
| Accession Number | TALB |
| Researcher | TXXX:Researcher |
| Date Recorded | TXXX:DateRecorded |
| Location | TXXX:Location |
| Subject / Species | TXXX:Subject |
| Equipment | TXXX:Equipment |
| Collection | TIT1 |
| Credit | TXXX:Credit |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| ← / → | Previous / Next file in directory |
| F5 | Refresh (reload from disk) |
| Ctrl+O | Open file |
| Ctrl+S | Save metadata |
| Ctrl+L | Clear all fields |
| Ctrl+T | View all tags |
| Ctrl+Shift+C | Copy file path to clipboard |
| Ctrl+Q | Quit |

## Project Structure

```
audio-tag-writer/
├── src/
│   ├── main.py                      # Entry point; MainWindow
│   └── audio_tag_writer/
│       ├── constants.py             # App metadata, DEFAULT_MODES, AUDIO_EXTENSIONS
│       ├── config.py                # Config singleton, SingleInstanceChecker
│       ├── metadata.py              # MetadataManager — ID3 read/write, JSON export/import
│       ├── audio_utils.py           # Stream info (duration, bitrate, sample rate, …)
│       ├── file_utils.py            # Directory scan for audio files
│       ├── mutagen_utils.py         # Mutagen wrappers and error types
│       ├── navigation.py            # NavigationMixin — open, prev/next, load_file
│       ├── file_ops.py              # FileOpsMixin — save, export, import, view tags
│       ├── menu.py                  # MenuMixin — menu bar and toolbar
│       ├── window.py                # WindowMixin — key events, geometry, close
│       ├── platform.py              # Windows taskbar integration
│       └── widgets/
│           ├── metadata_panel.py    # Dynamic ID3 form
│           └── audio_panel.py       # Album art + file info panel
├── run.sh                           # Bash launcher (Linux/macOS)
├── run.ps1                          # PowerShell launcher (Windows)
├── requirements.txt
└── CHANGELOG.md
```

## Configuration

App state (last open file, recent history, window geometry, active mode) is persisted to `~/.audio_tag_writer_config.json`. Delete this file to reset to defaults.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full release history.
