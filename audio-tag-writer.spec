# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Audio Tag Writer
# Build: pyinstaller audio-tag-writer.spec

import os

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('CHANGELOG.md', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'mutagen',
        'mutagen.mp3',
        'mutagen.wave',
        'mutagen.oggvorbis',
        'mutagen.flac',
        'mutagen.id3',
        'mutagen._util',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='audio-tag-writer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    # A relative runtime_tmpdir (e.g. '.') is resolved against the CURRENT WORKING
    # DIRECTORY at launch, not the exe's own folder. Explorer's "Open with" / right-click
    # context-menu launch can set the CWD to the target file's directory (read-only media,
    # a network share, a protected folder, etc.), which made extraction fail there with
    # "Could not create a temporary directory!" (issue #6). %LOCALAPPDATA% is always
    # writable per-user and independent of how/where the exe was launched from, and since
    # it's not cleaned up, we still avoid the original AV-lock-on-delete error (v0.7.7).
    runtime_tmpdir=r'%LOCALAPPDATA%\audio-tag-writer\runtime',
    console=False,           # no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join('assets', 'ICON_atw.ico'),
    version='version_info.txt',
)
