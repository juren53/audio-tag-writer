"""
Generate version_info.txt for PyInstaller Windows EXE Properties/Details tab.
Run before building: python generate_version_info.py
"""

import re
import sys
import os

CONSTANTS_PATH = os.path.join(os.path.dirname(__file__), 'src', 'audio_tag_writer', 'constants.py')
OUTPUT_PATH    = os.path.join(os.path.dirname(__file__), 'version_info.txt')


def read_version() -> str:
    with open(CONSTANTS_PATH, encoding='utf-8') as f:
        text = f.read()
    m = re.search(r'^APP_VERSION\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
    if not m:
        raise RuntimeError("APP_VERSION not found in constants.py")
    return m.group(1)


def version_tuple(v: str) -> tuple:
    parts = [int(x) for x in v.split('.')]
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


def write_version_info(version: str):
    vt = version_tuple(version)
    content = f"""\
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={vt},
    prodvers={vt},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'CompanyName',      u'SynchroSoft'),
           StringStruct(u'FileDescription',  u'Audio Tag Writer'),
           StringStruct(u'FileVersion',      u'{version}'),
           StringStruct(u'InternalName',     u'audio-tag-writer'),
           StringStruct(u'LegalCopyright',   u'Copyright (c) 2026 SynchroSoft'),
           StringStruct(u'OriginalFilename', u'audio-tag-writer.exe'),
           StringStruct(u'ProductName',      u'Audio Tag Writer'),
           StringStruct(u'ProductVersion',   u'{version}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [0x0409, 1200])])
  ]
)
"""
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"version_info.txt written  ({version} -> {vt})")


if __name__ == '__main__':
    v = read_version()
    write_version_info(v)
