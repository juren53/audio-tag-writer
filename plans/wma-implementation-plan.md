# WMA (ASF) Format Support — Implementation Plan

**Issue:** [#1 — Add WMA (ASF) audio format support](https://github.com/juren53/audio-tag-writer/issues/1)  
**Priority:** Low (HSTL workflow is MP3-only; this broadens format coverage)  
**Dependencies:** None — mutagen already supports ASF via `mutagen.asf`

---

## Background

WMA files use the ASF (Advanced Systems Format) container. Their tag model is completely different from ID3:

| Dimension | ID3 (MP3/WAV) | ASF (WMA) |
|---|---|---|
| Tag object | `mutagen.id3.ID3` | `mutagen.asf.ASFTags` |
| Key type | Frame ID (`TIT2`, `TXXX:Credit`) | String key (`Title`, `WM/AlbumTitle`) |
| Value type | Frame object (`.text[0]`) | `ASFValue` list (`.value`) |
| Save call | `audio.save(v2_version=3)` after `update_to_v23()` | `audio.save()` — no version dance |
| Album art frame | `APIC` | `WM/Picture` with different byte layout |

mutagen detects ASF automatically: `mutagen.File(path)` returns a `mutagen.asf.ASF` instance for WMA files.

---

## ASF ↔ ID3 Field Mapping

### Archival Recording Mode

| Label | ID3 frame | ASF key |
|---|---|---|
| Title | `TIT2` | `Title` |
| Description | `TIT3` + aliases | `Description` |
| Accession Number | `TALB` | `WM/AlbumTitle` |
| Speakers | `IPLS` | `WM/Composer` *(closest approximation)* |
| Date Recorded | `TRDA` | `WM/Year` |
| Restrictions | `TCOP` | `Copyright` |
| Location | `TXXX:TLOC` | `WM/ContentDistributor` *(or free-form key)* |
| Production/Copyright | `TPUB` | `WM/Publisher` |
| Original Filename | `TOFN` | `WM/TrackNumber` *(skip — no good equivalent)* |
| Collection | `TXXX:grouping` | `WM/AlbumArtistSortOrder` *(or free-form)* |
| Source URL | `TXXX:WOAS` | `WM/UniqueFileIdentifier` *(or free-form)* |
| NAC URL | `TXXX:WXXX` | *(free-form key)* |
| Institution ID | `TXXX:ISRC` | `WM/Provider` |
| Credit | `TXXX:Credit` | `WM/Lyrics` *(or free-form key)* |

> **Note:** ASF supports free-form string keys, so fields without a clean WM/ standard
> equivalent can use their ID3 frame name as the ASF key (e.g. `TXXX:Credit` stays as-is).
> This avoids information loss and is consistent with what Windows Media Player and
> other tools do for non-standard fields.

### Music Mode

| Label | ID3 frame | ASF key |
|---|---|---|
| Title | `TIT2` | `Title` |
| Artist | `TPE1` | `Author` |
| Album | `TALB` | `WM/AlbumTitle` |
| Track Number | `TRCK` | `WM/TrackNumber` |
| Year | `TDRC` | `WM/Year` |
| Genre | `TCON` | `WM/Genre` |
| Comment | `COMM` | `Description` |
| Composer | `TCOM` | `WM/Composer` |
| Album Artist | `TPE2` | `WM/AlbumArtist` |
| Credit | `TXXX:Credit` | `WM/Lyrics` |

### Scientific Mode

| Label | ID3 frame | ASF key |
|---|---|---|
| Title | `TIT2` | `Title` |
| Description | `COMM` | `Description` |
| Researcher | `TXXX:Researcher` | `WM/Researcher` *(free-form)* |
| Date Recorded | `TXXX:DateRecorded` | `WM/Year` |
| Location | `TXXX:Location` | `WM/ContentDistributor` |
| Subject/Species | `TXXX:Subject` | `WM/Subject` *(free-form)* |
| Equipment | `TXXX:Equipment` | `WM/Equipment` *(free-form)* |
| Collection | `TIT1` | `WM/AlbumArtistSortOrder` |
| Credit | `TXXX:Credit` | `WM/Lyrics` |

---

## Files to Change

### 1. `src/audio_tag_writer/constants.py`

**a) Extend `AUDIO_EXTENSIONS`** (line 12):
```python
# before
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg', '.flac']

# after
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg', '.flac', '.wma']
```

**b) Add `asf_key` to every field spec** in `DEFAULT_MODES`.

Each field dict gains an optional `"asf_key"` entry. Fields without a meaningful
ASF equivalent can either be omitted or mapped to a free-form key.

Example for Archival Recording mode:
```python
{"label": "Title",            "frame_id": "TIT2",    "asf_key": "Title",          "widget": "line", ...},
{"label": "Description",      "frame_id": "TIT3",    "asf_key": "Description",    "widget": "text", ...},
{"label": "Accession Number", "frame_id": "TALB",    "asf_key": "WM/AlbumTitle",  "widget": "line", ...},
{"label": "Date Recorded",    "frame_id": "TRDA",    "asf_key": "WM/Year",        "widget": "line", ...},
{"label": "Restrictions",     "frame_id": "TCOP",    "asf_key": "Copyright",      "widget": "line", ...},
{"label": "Production/Copyright","frame_id":"TPUB",  "asf_key": "WM/Publisher",   "widget": "line", ...},
{"label": "Credit",           "frame_id": "TXXX:Credit","asf_key":"WM/Lyrics",    "widget": "line", ...},
# fields with no clean ASF equivalent get asf_key=None or a free-form key:
{"label": "Speakers",         "frame_id": "IPLS",    "asf_key": "WM/Composer",    "widget": "line", ...},
{"label": "Location",         "frame_id": "TXXX:TLOC","asf_key":"WM/ContentDistributor","widget":"line",...},
```

---

### 2. `src/audio_tag_writer/audio_utils.py`

**a) Extend `_FORMAT_MAP`** (line 11):
```python
_FORMAT_MAP = {'.mp3': 'MP3', '.wav': 'WAV', '.ogg': 'OGG', '.flac': 'FLAC', '.wma': 'WMA'}
```

**b) Extend compression detection** (line 30):
```python
'compression': (
    'Lossless' if ext in ('.flac', '.wav') else
    'Lossy'    if ext in ('.mp3', '.ogg', '.wma') else
    '--'
),
```

No changes needed to the stream-info loop — `hasattr` checks already handle
differences between formats generically. WMA `info` exposes `length`, `bitrate`,
`channels`, and `sample_rate` through the same attribute names.

---

### 3. `src/audio_tag_writer/navigation.py`

**Extend `_AUDIO_FILTER`** (lines 20–27):
```python
_AUDIO_FILTER = (
    "Audio Files (*.mp3 *.wav *.ogg *.flac *.wma);;"
    "MP3 Files (*.mp3);;"
    "WAV Files (*.wav);;"
    "OGG Files (*.ogg);;"
    "FLAC Files (*.flac);;"
    "WMA Files (*.wma);;"
    "All Files (*)"
)
```

---

### 4. `src/audio_tag_writer/mutagen_utils.py`

Add a format-detection helper so other modules can branch cleanly without
importing `mutagen.asf` everywhere:

```python
def is_asf_audio(audio) -> bool:
    """Return True if the mutagen object is an ASF/WMA file."""
    try:
        from mutagen.asf import ASF
        return isinstance(audio, ASF)
    except ImportError:
        return False
```

Add an ASF-aware text reader (parallel to `safe_get_text` for ID3):

```python
def safe_get_asf_text(tags, asf_key: str, default: str = '') -> str:
    """Return the string value of an ASF tag key, or default if absent."""
    if tags is None or not asf_key:
        return default
    try:
        values = tags.get(asf_key)
        if not values:
            return default
        val = values[0]
        # ASFValue exposes .value; plain strings are also accepted by mutagen
        text = val.value if hasattr(val, 'value') else str(val)
        return str(text) if text is not None else default
    except Exception as e:
        logger.warning(f"Error reading ASF key '{asf_key}': {e}")
        return default
```

Update `detect_mode()` to short-circuit for ASF files (mode detection rules
are ID3-centric; defaulting to Archival Recording for WMA is safe for now):

```python
def detect_mode(tags, detect_frames: dict, default: str, audio=None) -> str:
    # ASF tags don't carry ID3 frame IDs; skip detection and use the default.
    if audio is not None and is_asf_audio(audio):
        return default
    if tags is not None:
        for mode_name, frame_id in detect_frames.items():
            if frame_id and safe_get_text(tags, frame_id):
                return mode_name
    return default
```

> The `audio=None` default keeps the signature backward-compatible with the
> existing callers until they are updated to pass `audio`.

---

### 5. `src/audio_tag_writer/metadata.py`

This file needs the most changes. The strategy is a **dispatcher pattern**:
`load_from_file()` and `save_to_file()` detect the format once and call the
appropriate read/write helpers.

#### 5a. Import additions (top of file)
```python
from .mutagen_utils import open_audio, safe_get_text, safe_get_asf_text, is_asf_audio, AudioFileError
```

#### 5b. `load_from_file()` — add format branch

```python
def load_from_file(self, path: str) -> bool:
    if not os.path.exists(path):
        logger.error(f"File not found: {path}")
        return False

    self.clear()
    self.current_path = path

    try:
        audio = open_audio(path)
        tags  = audio.tags
        asf   = is_asf_audio(audio)           # ← new

        for spec in self._field_specs:
            label    = spec['label']
            max_chars = spec.get('max_chars', 2000)

            if spec.get('widget') == 'hidden':
                continue

            if asf:                            # ← new branch
                raw = self._read_asf_field(tags, spec)
            else:
                frame_id = spec['frame_id']
                raw = self._read_frame(tags, frame_id)
                if not raw:
                    for alias in spec.get('aliases', []):
                        raw = self._read_frame(tags, alias)
                        if raw:
                            break

            self._values[label] = self._sanitize_value(raw, max_chars)

        logger.info(f"Loaded metadata from '{path}'")
        return True

    except AudioFileError as e:
        logger.error(f"AudioFileError loading '{path}': {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error loading '{path}': {e}")
        return False
```

#### 5c. New `_read_asf_field()` method

```python
def _read_asf_field(self, tags, spec: dict) -> str:
    """Read one field from an ASF tag dict using the spec's asf_key."""
    asf_key = spec.get('asf_key')
    if not asf_key:
        return ''
    return safe_get_asf_text(tags, asf_key)
```

#### 5d. `save_to_file()` — add WMA branch

```python
def save_to_file(self, path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    if ext not in ('.mp3', '.wav', '.wma'):        # ← add .wma
        logger.error(f"Tag write not supported for format: {ext}")
        raise AudioFileError(
            f"Metadata writing is only supported for MP3, WAV, and WMA files.\n"
            f"'{os.path.basename(path)}' is a {ext.lstrip('.').upper()} file."
        )

    try:
        audio = open_audio(path)
    except AudioFileError:
        raise

    asf = is_asf_audio(audio)                     # ← new

    if asf:
        self._save_asf(audio, path)
    else:
        self._save_id3(audio, path)

    return True
```

Extract the existing ID3 save body into a private `_save_id3()` method:

```python
def _save_id3(self, audio, path: str):
    if audio.tags is None:
        audio.add_tags()
    tags = audio.tags

    for spec in self._field_specs:
        label    = spec['label']
        frame_id = spec['frame_id']

        if spec.get('widget') == 'hidden':
            auto_val = spec.get('auto_value', '')
            if auto_val == '__app_version__':
                from .constants import APP_NAME, APP_VERSION
                value = f"{APP_NAME} v{APP_VERSION}"
            else:
                value = auto_val
        else:
            value = self._values.get(label, '').strip()

        self._write_frame(tags, frame_id, value)

        for alias in spec.get('aliases', []):
            self._write_frame(tags, alias, value)

        if spec.get('date_field'):
            self._write_date_derived(tags, value)

    tags.update_to_v23()
    audio.save(v2_version=3)
    logger.info(f"Saved ID3 metadata to '{path}'")
```

Add the new `_save_asf()` method:

```python
def _save_asf(self, audio, path: str):
    from mutagen.asf import ASFValue, UNICODE as ASF_UNICODE

    if audio.tags is None:
        audio.add_tags()
    tags = audio.tags

    for spec in self._field_specs:
        label   = spec['label']
        asf_key = spec.get('asf_key')
        if not asf_key:
            continue

        if spec.get('widget') == 'hidden':
            auto_val = spec.get('auto_value', '')
            if auto_val == '__app_version__':
                from .constants import APP_NAME, APP_VERSION
                value = f"{APP_NAME} v{APP_VERSION}"
            else:
                value = auto_val
        else:
            value = self._values.get(label, '').strip()

        if value:
            tags[asf_key] = [ASFValue(value, ASF_UNICODE)]
        elif asf_key in tags:
            del tags[asf_key]

    audio.save()                    # no v2_version arg for ASF
    logger.info(f"Saved ASF metadata to '{path}'")
```

---

### 6. `widgets/audio_panel.py` — Album Art (WM/Picture)

This is a secondary deliverable. Album art for WMA files is stored in the
`WM/Picture` ASF tag as an `ASFByteArrayAttribute` (or `ASFValue` with picture
data). The structure differs from ID3 `APIC`.

The relevant changes are in whichever method currently loads `APIC` for display.
Extend it to:

```python
# Pseudo-code — adapt to the actual picture-loading method
if is_asf_audio(audio):
    pic_values = audio.tags.get("WM/Picture", [])
    for v in pic_values:
        # v.value is the raw picture data (bytes) for newer mutagen versions
        # or access v.data depending on the mutagen.asf API version
        data = getattr(v, 'value', None) or getattr(v, 'data', None)
        if data:
            # load pixmap from bytes
            ...
            break
else:
    # existing APIC logic
```

> Defer album-art support to a follow-up if it adds significant complexity.

---

## Test Strategy

### New test file: `tests/test_wma_support.py`

The test corpus must include at least one WMA file with known tags. Place it at
`tests/corpus/sample.wma` (create with FFmpeg: `ffmpeg -i sample.mp3 sample.wma`).

**Test cases:**

| Test | Purpose |
|---|---|
| `test_wma_in_audio_extensions` | `.wma` appears in `AUDIO_EXTENSIONS` |
| `test_wma_format_map` | `get_audio_info()` returns `format='WMA'`, `compression='Lossy'` |
| `test_wma_file_filter_string` | `_AUDIO_FILTER` contains `*.wma` |
| `test_is_asf_audio_true` | `is_asf_audio()` returns `True` for WMA file |
| `test_is_asf_audio_false` | `is_asf_audio()` returns `False` for MP3 file |
| `test_safe_get_asf_text_present` | Reads a known ASF key |
| `test_safe_get_asf_text_absent` | Returns `''` for missing key |
| `test_load_wma_reads_title` | `MetadataManager.load_from_file()` populates Title from WMA |
| `test_save_wma_writes_title` | `save_to_file()` round-trips Title through a WMA file |
| `test_save_wma_does_not_call_update_to_v23` | ASF save skips ID3 version dance |
| `test_detect_mode_asf_returns_default` | `detect_mode()` returns default for WMA tags |

---

## Implementation Order

Work in this sequence to keep the app functional at each stage:

1. **`constants.py`** — add `.wma` to `AUDIO_EXTENSIONS` and `asf_key` to field specs  
   *Result: WMA files appear in directory listings.*

2. **`audio_utils.py`** — extend `_FORMAT_MAP` and compression detection  
   *Result: Audio panel shows correct format/compression for WMA.*

3. **`navigation.py`** — extend `_AUDIO_FILTER`  
   *Result: File-open dialog shows WMA files.*

4. **`mutagen_utils.py`** — add `is_asf_audio()`, `safe_get_asf_text()`, update `detect_mode()`  
   *Result: Low-level ASF detection and read helpers available.*

5. **`metadata.py`** — add ASF read/write branches  
   *Result: WMA tags can be loaded and saved.*

6. **Tests** — add `test_wma_support.py`  
   *Result: Acceptance suite covers WMA.*

7. **`audio_panel.py`** — album art for WMA *(optional / follow-up)*

---

## Acceptance Criteria

- [ ] `.wma` files appear in directory file list alongside MP3/FLAC/OGG
- [ ] File-open dialog includes a "WMA Files (*.wma)" filter entry
- [ ] Audio panel shows correct duration, bitrate, sample rate, channels for WMA
- [ ] Audio panel shows `Format: WMA`, `Compression: Lossy`
- [ ] Loading a tagged WMA populates Archival Recording fields correctly
- [ ] Saving edits to a WMA file persists through a reload
- [ ] Loading an untagged WMA does not crash; fields are blank
- [ ] Attempting to save a `.ogg` or `.flac` file still raises `AudioFileError`
- [ ] All existing tests (72/72) continue to pass
- [ ] New WMA-specific tests pass

---

## Known Risks / Edge Cases

| Risk | Mitigation |
|---|---|
| Some ASF keys hold non-Unicode `ASFValue` types (e.g. integers) | Cast to `str()` in `safe_get_asf_text`; guard with `try/except` |
| WMA files created by Windows Media Player may have tags in varying encodings | mutagen normalises to Python `str` on read; no extra handling needed |
| Mode auto-detect always defaults to Archival Recording for WMA | Acceptable given current use case; revisit if Music mode WMA support is needed |
| `IPLS` (Speakers) has no exact ASF equivalent | Map to `WM/Composer` as a best-effort; document in field tooltip |
| Album art byte layout differs between mutagen versions | Wrap in `try/except`; log a warning if art fails to load |
