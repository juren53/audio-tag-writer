"""
Shared pytest fixtures for audio-tag-writer tests.
"""

import os
import sys
import shutil
import platform
from datetime import datetime
from collections import defaultdict

import pytest

# Ensure src/ is on the import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

_PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))

# ── Report generation hooks ───────────────────────────────────────────────────

_module_results: dict[str, dict[str, int]] = defaultdict(lambda: {'passed': 0, 'failed': 0, 'skipped': 0})
_session_start: datetime | None = None


def pytest_sessionstart(session):
    global _session_start
    _session_start = datetime.now()


def pytest_runtest_logreport(report):
    if report.when != 'call' and not (report.when == 'setup' and report.skipped):
        return
    module = os.path.basename(report.fspath) if report.fspath else 'unknown'
    if report.passed:
        _module_results[module]['passed'] += 1
    elif report.failed:
        _module_results[module]['failed'] += 1
    elif report.skipped:
        _module_results[module]['skipped'] += 1


def pytest_sessionfinish(session, exitstatus):
    now = datetime.now()
    stamp = now.strftime('%Y-%m-%d-%H%M')
    filename = f'REPORT_ATW-acceptance-test-{stamp}.txt'
    reports_dir = os.path.join(_PROJECT_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, filename)

    total_passed  = sum(v['passed']  for v in _module_results.values())
    total_failed  = sum(v['failed']  for v in _module_results.values())
    total_skipped = sum(v['skipped'] for v in _module_results.values())
    total = total_passed + total_failed + total_skipped

    duration = (now - _session_start).total_seconds() if _session_start else 0.0

    try:
        import pytest as _pytest
        pytest_ver = _pytest.__version__
    except Exception:
        pytest_ver = 'unknown'

    try:
        sys.path.insert(0, os.path.join(_PROJECT_ROOT, 'src'))
        from audio_tag_writer.constants import APP_VERSION
    except Exception:
        APP_VERSION = 'unknown'

    win_ver  = platform.version()
    py_ver   = platform.python_version()
    os_label = f'Windows {platform.release()} {win_ver}' if sys.platform == 'win32' else platform.platform()

    overall = 'PASS' if total_failed == 0 and total > 0 else ('FAIL' if total_failed > 0 else 'NO TESTS')

    col_w = max((len('tests/' + m) for m in _module_results), default=30)
    col_w = max(col_w, len('Module'))
    header_line = '-' * (col_w + 16)

    rows = []
    for module in sorted(_module_results):
        r = _module_results[module]
        count = r['passed'] + r['failed'] + r['skipped']
        status = 'PASS' if r['failed'] == 0 else 'FAIL'
        if r['skipped'] and r['passed'] == 0 and r['failed'] == 0:
            status = 'SKIP'
        rows.append(f"  {'tests/' + module:<{col_w}}  {count:>5}    {status}")

    rows_str   = '\n'.join(rows)
    total_line = f"  {'TOTAL':<{col_w}}  {total:>5}    {total_passed} passed"
    if total_failed:
        total_line += f', {total_failed} failed'
    if total_skipped:
        total_line += f', {total_skipped} skipped'
    total_line += f' in {duration:.2f}s'

    report = f"""\
{filename}
{'=' * max(len(filename), 48)}
Audio Tag Writer v{APP_VERSION} — Acceptance Test Report
Date/Time: {now.strftime('%Y-%m-%d %H:%M')}
Platform:  {os_label}, Python {py_ver}
{'=' * max(len(filename), 48)}

AUTOMATED TEST SUITE
--------------------
Runner:    pytest {pytest_ver}
Rootdir:   {_PROJECT_ROOT}
Collected: {total} tests

  {'Module':<{col_w}}  Tests    Result
  {header_line}
{rows_str}
  {header_line}
{total_line}

OVERALL RESULT: {overall}
"""

    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f'\nReport saved: {filename}')
    except Exception as exc:
        print(f'\nWarning: could not write test report: {exc}')

# Real MP3s from the HSTL test corpus (available on dev machine, skipped on CI)
_TEST_MP3_DIR = r'C:\Users\juren\Projects\HST-Metadata\Audio\Test-mp3s'
_TEST_MP3 = os.path.join(_TEST_MP3_DIR, 'sr65-11-1.mp3')


@pytest.fixture
def real_mp3():
    """Path to a real, tagged HST MP3 file. Skip if not available (e.g. CI)."""
    if not os.path.isfile(_TEST_MP3):
        pytest.skip(f'Real MP3 not available: {_TEST_MP3}')
    return _TEST_MP3


@pytest.fixture
def mp3_copy(tmp_path, real_mp3):
    """Writable copy of the real test MP3 in a temp directory."""
    dest = tmp_path / 'test_copy.mp3'
    shutil.copy2(real_mp3, dest)
    return str(dest)


@pytest.fixture
def tagged_id3():
    """An in-memory ID3 tag object populated with sample values."""
    from mutagen.id3 import ID3, TIT2, TALB, COMM, TXXX, IPLS
    tags = ID3()
    tags['TIT2'] = TIT2(encoding=3, text=['Test Title'])
    tags['TALB'] = TALB(encoding=3, text=['SR59-001'])
    tags['COMM::eng'] = COMM(encoding=3, lang='eng', desc='', text=['A test description.'])
    tags['TXXX:Credit'] = TXXX(encoding=3, desc='Credit', text=['HSTL'])
    tags['IPLS'] = IPLS(encoding=3, people=[['interviewer', 'Jane Smith'], ['subject', 'John Doe']])
    return tags
