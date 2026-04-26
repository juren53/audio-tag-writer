# Audio Tag Writer

A desktop application for reading and editing ID3 metadata tags in audio files. Designed for archivists, researchers, and musicians who need accurate, repeatable metadata workflows across large audio collections.

## Features

- **Three built-in modes** — Archival Recording, Music, and Scientific, each with purpose-specific field sets
- **Full HSTL archival metadata profile** — Archival Recording mode writes the complete ID3v2.3 frame set used by the HSTL FFmpeg tagging pipeline, including cross-schema alias frames for iTunes, XMP, and Windows Media compatibility
- **Read and write ID3v2.3 metadata** — enforces v2.3 compatibility so all frames survive across tools
- **Auto-detect mode on load** — automatically switches to the correct mode (Archival, Music, Scientific) based on frame content; toggle from toolbar or View menu
- **Directory navigation** — open a folder and step through files with Prev / Next (or ↑ ↓ keys)
- **Album art display** — shows embedded APIC frames; music-note placeholder when none present
- **Technical audio info panel** — displays duration, bitrate, bitrate mode (CBR/VBR), sample rate, channels, stereo mode, MPEG version, compression mode, file size, and modification date
- **Export / Import JSON** — dump and reload all field values for bulk or scripted workflows
- **View All Tags** — searchable table of every raw ID3 frame in the current file
- **Rename File** — rename the current audio file in-place with automatic backup
- **Play button** — hands the file off to the OS default audio player
- **Copy FQFN to Clipboard** — copies the fully qualified file name to the clipboard (Ctrl+Shift+C)
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

Switch modes from the toolbar Mode selector or the mode combo. Each mode presents a fixed set of fields tailored to a specific use case. Auto-detect mode (toggle with the **Auto Detect** toolbar button) switches automatically when a file is opened.

### Archival Recording

Full HSTL metadata profile — compatible with iTunes, Windows Media Player, XMP-aware catalog tools, and FFmpeg-tagged archives.

| Field | Primary Frame | Also Written To |
|---|---|---|
| Title | TIT2 | |
| Description | TIT3 | COMM, TXXX:COMM, TXXX:ISBJ, TXXX:dc:description, TXXX:xmpDM:logComment, TXXX:©cmt |
| Accession Number | TALB | TXXX:IPRD |
| Speakers | IPLS | TXXX:IPLS |
| Date Recorded | TRDA | TYER, TORY, TDAT (DDMM), TXXX:ICRD |
| Restrictions | TCOP | |
| Location | TXXX:TLOC | |
| Production/Copyright | TPUB | TXXX:©pub, TXXX:dc:publisher |
| Original Filename | TOFN | |
| Collection | TXXX:grouping | |
| Source URL | TXXX:WOAS | |
| NAC URL | TXXX:WXXX | |
| Institution ID | TXXX:ISRC | |
| *(Artist — hidden)* | TPE1 | auto: "Harry S. Truman Library" |
| *(Genre — hidden)* | TCON | auto: "speech" |
| *(Tagging Software — hidden)* | TEXT | auto: "Audio Tag Writer vX.X.X" |

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
| ↑ / ↓ | Previous / Next file in directory |
| F2 | Rename file |
| F5 | Refresh (reload from disk) |
| Ctrl+O | Open file |
| Ctrl+S | Save metadata |
| Ctrl+L | Clear all fields |
| Ctrl+T | View all tags |
| Ctrl+D | Toggle dark mode |
| Ctrl+Shift+C | Copy FQFN to clipboard |
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
│           └── audio_panel.py       # Album art + technical info panel
├── generate_version_info.py         # Generates version_info.txt for PyInstaller
├── version_info.txt                 # Windows EXE Properties/Details metadata
├── audio-tag-writer.spec            # PyInstaller build spec
├── build_exe.ps1                    # Build script — generates version info then runs PyInstaller
├── run.sh                           # Bash launcher (Linux/macOS)
├── run.ps1                          # PowerShell launcher (Windows)
├── requirements.txt
└── CHANGELOG.md
```

## Configuration

App state (last open file, recent history, window geometry, active mode, auto-detect setting) is persisted to `~/.audio_tag_writer_config.json`. Delete this file to reset to defaults.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the full release history.
