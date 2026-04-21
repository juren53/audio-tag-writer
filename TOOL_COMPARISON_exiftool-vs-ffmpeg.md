# Audio Metadata Tool Comparison: ExifTool vs FFmpeg vs Mutagen

## Why This Decision Matters

The `audio-tag-writer` project needs a metadata backend for two distinct operations:

1. **Single-file editing (GUI)** — Read current tags from one file, let a user edit them,
   write the changes back in place without touching the audio stream.
2. **Batch embedding (HSTL Audio Framework CLI)** — Read ~3,757 rows from a CSV, embed ID3
   tags *and* a custom thumbnail into each MP3 in one pipeline pass.

These operations have different requirements. The right tool for the batch pipeline is not
necessarily the right tool for the GUI editor. This document covers all three serious
candidates so an informed choice can be made for each context.

---

## The Three Candidates

| | ExifTool | FFmpeg | Mutagen |
|--|----------|--------|---------|
| **Type** | Metadata read/write utility | Multimedia transcoder + mux/demux | Python library (no binary) |
| **Primary purpose** | Metadata for images, audio, video | Audio/video encoding, muxing, streaming | Audio tag read/write |
| **Author** | Phil Harvey | FFmpeg community (Fabrice Bellard origin) | Joe Wreschnig, Michael Urman et al. |
| **Language** | Perl (CLI binary) | C | Python |
| **Python binding** | PyExifTool (subprocess wrapper) | subprocess (no official binding) | Native Python import |
| **Installation** | Standalone EXE (~3 MB, bundle-able) | Standalone EXE (~100 MB full build) | `pip install mutagen` (~1 MB) |
| **License** | GPL/Artistic | LGPL/GPL | GPL v2 |
| **Active development** | Yes (v12.x, 2024) | Yes (heavily) | Yes (v1.47, 2024) |

---

## Detailed Comparison

### 1. Reading Audio Metadata

**ExifTool**
- Reads virtually every tag format: ID3v1, ID3v2.2/2.3/2.4, APEv2, Vorbis Comment, FLAC
  native, MP4/M4A, WMA, AIFF, BWF (Broadcast Wave)
- Returns structured JSON: `exiftool -j -ID3:all file.mp3`
- Also reads technical audio properties: duration, bitrate, sample rate, channels
- Output is flat — all tags from all tag namespaces merged into one dict
- Handles malformed/partial tags gracefully

**FFmpeg**
- `ffprobe -v quiet -print_format json -show_format -show_streams file.mp3` returns
  streams + format metadata
- Metadata fields appear under `format.tags{}` — only the tags the muxer recognises
- Technical properties (codec, bitrate, sample rate) are thorough and accurate
- Does not expose raw ID3 frame names (TIT2, TALB, etc.) — normalises them to generic
  keys like `title`, `album`, `artist`; non-standard frames may be dropped silently
- Not designed for tag inspection; `ffprobe` output varies by codec/container

**Mutagen**
- `mutagen.mp3.MP3('file.mp3')` gives direct access to every ID3 frame object by tag ID
  (TIT2, TALB, COMM, APIC, etc.)
- Also exposes audio stream info: `audio.info.length`, `.bitrate`, `.sample_rate`, `.channels`
- Frame-level access: can distinguish ID3v2.3 vs v2.4, read multiple COMM frames by language
- Raises `MutagenError` on corrupt files rather than silently returning partial data
- Format-specific: `mutagen.mp3.MP3` for MP3, `mutagen.flac.FLAC` for FLAC, etc. (or use
  `mutagen.File()` for auto-detection)

---

### 2. Writing Audio Metadata

This is the most important distinction for the GUI use case.

**ExifTool**
- Writes ID3 tags in-place with `-overwrite_original`; no re-encoding, no re-muxing
- Original file is backed up as `.mp3_original` unless `-overwrite_original` is used
- Example: `exiftool -ID3:TIT2="New Title" -ID3:TALB="SR60-59" -overwrite_original file.mp3`
- Can write individual tags or all at once
- Does NOT embed cover art (APIC frames) — this is a known ExifTool limitation for audio
- ID3v2.4 writing has had historical edge-case bugs; `-use_id3v2_version=3` recommended
- Safe: never touches the audio stream

**FFmpeg**
- Writing metadata requires full demux/remux: `ffmpeg -i in.mp3 -metadata TIT2="x" -c copy out.mp3`
- `-c copy` copies the audio stream without re-encoding — fast and lossless
- BUT: outputs to a *new file*; you must replace the original yourself (or use a temp file)
- Cover art embedding is native and reliable: add `-i thumb.jpg -map 0 -map 1`
- Two-pass approach needed for combined metadata + thumbnail (as in `audio-tags-09.py`)
- FFmpeg normalises tag names via its ID3 muxer — non-standard frames (IPLS, TOFN, TLOC)
  may not survive a `-c copy` pass depending on FFmpeg version and the `-id3v2_version` flag
- Risk of silent tag loss if a frame ID isn't recognised by FFmpeg's ID3 muxer
- Verified working in prototype: `audio-tags-09.py` v0.09 embeds all 22 tags successfully

**Mutagen**
- In-place write: `audio.tags['TIT2'] = TIT2('encoding=3, text="New Title"')`; `audio.save()`
- No re-encoding, no temp files, no shell subprocess — pure Python file I/O
- Full ID3 frame support: can write any valid ID3v2 frame including APIC (cover art)
- Can force ID3v2.3 or ID3v2.4 on save: `audio.tags.update_to_v23(); audio.save(v2_version=3)`
- Atomically replaces the tag block in the file — audio stream bytes never modified
- Cover art: `audio.tags['APIC'] = APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=img_bytes)`

---

### 3. Cover Art / Thumbnail Embedding

| | ExifTool | FFmpeg | Mutagen |
|--|----------|--------|---------|
| Read existing cover art | Yes (extracts APIC) | Yes (via ffprobe streams) | Yes (APIC frame object) |
| Write/embed cover art | **No** (cannot write APIC) | **Yes** (primary strength) | **Yes** (APIC frame) |
| Overlay text on thumbnail | No | **Yes** (drawtext filter) | No (use Pillow separately) |

This is the decisive difference. For the HSTL workflow, thumbnail embedding with text overlay
is a core requirement — FFmpeg is the only tool that handles the full pipeline in one step.

---

### 4. Python Integration

**ExifTool via PyExifTool**
- Subprocess-based: Python calls `exiftool.exe` as a persistent process
- Returns JSON; Python parses it into dicts
- I/O overhead per call; mitigated by keeping process alive (already done in tag-writer)
- Well-tested in tag-writer; `PersistentExifTool` pattern is production-proven
- External binary must exist on disk; bundled for distribution

**FFmpeg via subprocess**
- No official Python binding; all calls are `subprocess.run(['ffmpeg', ...args])`
- Each write creates a new process (can't keep alive like ExifTool)
- Large binary (~100 MB with all codecs); bundling in a PyInstaller EXE is expensive
- For the GUI, spawning ffmpeg for every tag-save would be slow and heavyweight
- Fine for batch processing where per-file overhead is amortised

**Mutagen**
- Pure `import mutagen` — no external process, no binary, no subprocess
- Reads and writes happen entirely in Python memory
- Fastest option for single-file operations in a GUI
- Excellent PyPI package: `pip install mutagen`; ~1 MB installed
- No bundling concerns for PyInstaller (pure Python wheels)

---

### 5. Format Support Matrix

| Format | ExifTool (read) | ExifTool (write) | FFmpeg | Mutagen |
|--------|----------------|-----------------|--------|---------|
| MP3 / ID3v2 | ✓ | ✓ | ✓ | ✓ |
| MP3 / ID3v1 | ✓ | ✓ | ✓ | ✓ |
| WAV (INFO chunk) | ✓ | ✓ | ✓ | ✓ |
| WAV / BWF chunk | ✓ | ✓ | Partial | ✗ |
| FLAC | ✓ | ✓ | ✓ | ✓ |
| OGG Vorbis | ✓ | ✓ | ✓ | ✓ |
| MP4 / M4A | ✓ | ✓ | ✓ | ✓ |
| AIFF | ✓ | ✓ | ✓ | ✓ |
| Cover art embed | ✗ (read only) | ✗ | ✓ | ✓ |

---

### 6. Risk Assessment

**ExifTool**
- Low risk for read; moderate risk for audio write in edge cases
- Cannot embed cover art — a blocking limitation if thumbnails are needed in the GUI
- Already proven in tag-writer; team knows the API
- Smaller binary to bundle

**FFmpeg**
- High risk of silent tag loss for non-standard ID3 frames during remux
  (IPLS, TOFN, TLOC are not in FFmpeg's standard tag mapping)
- Every write requires a full remux pass — adds latency in a GUI context
- Large binary; awkward to bundle in a PyInstaller EXE for a desktop app
- Best-in-class for thumbnail generation and embedding — no other tool matches it here

**Mutagen**
- Low risk: frame-level access means no normalisation surprises
- All 22 ID3 frames from `audio-tags-09.py` are writable without loss
- No binary dependency; simplest deployment story
- Cover art requires Pillow for thumbnail generation (text overlay), but write is native
- Less battle-tested in this project — would need new integration code

---

## Recommendation by Use Case

### HSTL Audio Framework (Batch CLI)

**Use FFmpeg** — it is already proven in the prototype, handles the thumbnail text-overlay
requirement natively, and the per-file subprocess cost is acceptable when processing 3,757
files in a batch. The key concern about silent tag loss for non-standard frames should be
verified with a tag readback validation step (Step 5 in the framework plan).

### audio-tag-writer (Single-file GUI)

**Use Mutagen** as the primary metadata backend.

Reasoning:
- No subprocess latency — critical for a responsive UI
- In-place writes — no temp files, no replace-original dance
- Full ID3 frame fidelity — all 22 HSTL tag fields survive without normalisation loss
- Cover art read/write native — no blocking limitation
- Tiny footprint — `pip install mutagen`; no binary to bundle
- Pure Python — PyInstaller EXE is smaller and simpler

**Keep ExifTool for audio technical info** (duration, bitrate, sample rate, channels) if
already bundled, OR use `mutagen.mp3.MP3().info` which provides the same properties without
a second tool. The mutagen `.info` object covers: `length`, `bitrate`, `sample_rate`,
`channels`, `mode` (mono/stereo/joint stereo). This eliminates the ExifTool dependency
entirely for the audio-tag-writer GUI.

### Summary Table

| Context | Recommended tool | Reason |
|---------|-----------------|--------|
| Batch tag embedding (CLI) | FFmpeg | Proven; handles thumbnail+metadata in one pass |
| Thumbnail text overlay | FFmpeg (only option) | `drawtext` filter; no Python alternative |
| Single-file GUI tag editing | Mutagen | In-place, fast, full frame fidelity, no binary |
| Audio stream info in GUI | Mutagen `.info` | Same data, no extra dependency |
| Read all tags for inspection | Mutagen or ExifTool | Either works; mutagen preferred if already present |

---

## Impact on audio-tag-writer Development Plan

If Mutagen is adopted:

1. **Remove ExifTool dependency** from `audio-tag-writer` entirely (or keep for "View All Tags"
   as a power-user feature only)
2. **Replace** `exiftool_utils.py` with `mutagen_utils.py` — thin wrapper around Mutagen
   with consistent error handling
3. **Replace** `audio_utils.py` ExifTool calls with `mutagen.mp3.MP3(path).info` attributes
4. **Simplify** `metadata.py` — direct frame dict manipulation instead of subprocess JSON
5. **Add** `pip install mutagen` to `requirements.txt`; **remove** `PyExifTool` and bundled
   `exiftool.exe` from the project
6. Cover art (APIC) embedding becomes available in the GUI with no additional tool

The mixin architecture, Config singleton, ThemeManager, and all UI code remain unchanged.
The substitution is confined to the metadata and audio_utils layers.

---

## References

- ExifTool audio tag support: https://exiftool.org/TagNames/ID3.html
- FFmpeg metadata docs: https://ffmpeg.org/ffmpeg-formats.html#Metadata-1
- Mutagen docs: https://mutagen.readthedocs.io/
- Mutagen ID3 frames: https://mutagen.readthedocs.io/en/latest/api/id3_frames.html
- PyExifTool: https://sylikc.github.io/pyexiftool/

---

Created: 2026-04-20
