"""
Audio Tag Writer - Configuration and single instance management.
"""

import os
import sys
import json
import logging
import tempfile

from .constants import (APP_VERSION, APP_TIMESTAMP,
                        DEFAULT_MODES, DEFAULT_DETECT_FRAMES, DEFAULT_DETECT_DEFAULT)

logger = logging.getLogger(__name__)

if sys.platform.startswith('win'):
    import msvcrt
else:
    import fcntl


class SingleInstanceChecker:
    """Ensures only one instance of the application runs at a time."""

    def __init__(self, app_name="audio-tag-writer"):
        self.app_name = app_name
        self.lock_file_path = os.path.join(tempfile.gettempdir(), f"{app_name}.lock")
        self.lock_file = None
        self.is_locked = False

    def is_already_running(self):
        try:
            self.lock_file = open(self.lock_file_path, 'w')
            if sys.platform.startswith('win'):
                try:
                    msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    self.is_locked = True
                    self.lock_file.write(str(os.getpid()))
                    self.lock_file.flush()
                    return False
                except (OSError, IOError):
                    return True
            else:
                try:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.is_locked = True
                    self.lock_file.write(str(os.getpid()))
                    self.lock_file.flush()
                    return False
                except (OSError, IOError):
                    return True
        except Exception as e:
            logger.error(f"Error checking for running instance: {e}")
            return False

    def release(self):
        if self.is_locked and self.lock_file:
            try:
                if sys.platform.startswith('win'):
                    try:
                        msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                    except Exception:
                        pass
                else:
                    try:
                        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                    except Exception:
                        pass
                self.lock_file.close()
                self.is_locked = False
                try:
                    if os.path.exists(self.lock_file_path):
                        os.remove(self.lock_file_path)
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Error releasing lock: {e}")

    def __del__(self):
        self.release()


class Config:
    """Global configuration and state management."""

    def __init__(self):
        self.app_version = APP_VERSION
        self.app_timestamp = APP_TIMESTAMP

        self.selected_file = None
        self.last_directory = None
        self.recent_files = []
        self.recent_directories = []
        self.directory_audio_files = []
        self.current_file_index = -1

        self.dark_mode = False
        self.ui_zoom_factor = 1.0
        self.current_theme = 'Default Light'
        self.window_geometry = None
        self.window_maximized = False

        self.auto_check_updates = False
        self.last_update_check = None
        self.skipped_versions = []
        self.update_check_frequency = 86400

        # Mode state — seeded from DEFAULT_MODES on first run
        self.active_mode = "Archival Recording"
        self.modes = {name: list(fields) for name, fields in DEFAULT_MODES.items()}

        # Auto-detect mode settings
        self.auto_detect_mode = True
        self.mode_detect_frames = dict(DEFAULT_DETECT_FRAMES)
        self.mode_detect_default = DEFAULT_DETECT_DEFAULT

        self.config_file = os.path.join(os.path.expanduser("~"), ".audio_tag_writer_config.json")
        self.load_config()

    # ------------------------------------------------------------------
    # Recent files / directories
    # ------------------------------------------------------------------

    def add_recent_file(self, file_path):
        if file_path and os.path.exists(file_path):
            if file_path in self.recent_files:
                self.recent_files.remove(file_path)
            self.recent_files.insert(0, file_path)
            self.recent_files = self.recent_files[:10]
            self.save_config()

    def add_recent_directory(self, directory_path):
        if directory_path and os.path.exists(directory_path) and os.path.isdir(directory_path):
            if directory_path in self.recent_directories:
                self.recent_directories.remove(directory_path)
            self.recent_directories.insert(0, directory_path)
            self.recent_directories = self.recent_directories[:10]
            self.save_config()

    # ------------------------------------------------------------------
    # Mode helpers
    # ------------------------------------------------------------------

    def get_active_mode(self):
        return self.active_mode

    def set_active_mode(self, mode_name):
        if mode_name in self.modes:
            self.active_mode = mode_name
            self.save_config()

    def get_mode_fields(self, mode_name=None):
        name = mode_name or self.active_mode
        return list(self.modes.get(name, self.modes["Archival Recording"]))

    def reset_mode_to_default(self, mode_name):
        if mode_name in DEFAULT_MODES:
            self.modes[mode_name] = list(DEFAULT_MODES[mode_name])
            self.save_config()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_config(self):
        try:
            data = {
                'selected_file': self.selected_file,
                'last_directory': self.last_directory,
                'recent_files': self.recent_files,
                'recent_directories': self.recent_directories,
                'dark_mode': self.dark_mode,
                'ui_zoom_factor': self.ui_zoom_factor,
                'current_theme': self.current_theme,
                'window_geometry': self.window_geometry,
                'window_maximized': self.window_maximized,
                'auto_check_updates': self.auto_check_updates,
                'last_update_check': self.last_update_check,
                'skipped_versions': self.skipped_versions,
                'update_check_frequency': self.update_check_frequency,
                'active_mode': self.active_mode,
                'modes': self.modes,
                'auto_detect_mode': self.auto_detect_mode,
                'mode_detect_frames': self.mode_detect_frames,
                'mode_detect_default': self.mode_detect_default,
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    def load_config(self):
        try:
            if not os.path.exists(self.config_file):
                return
            with open(self.config_file, 'r') as f:
                data = json.load(f)

            self.selected_file = data.get('selected_file')
            self.last_directory = data.get('last_directory')
            self.recent_files = [f for f in data.get('recent_files', []) if os.path.exists(f)]
            self.recent_directories = [
                d for d in data.get('recent_directories', [])
                if os.path.exists(d) and os.path.isdir(d)
            ]
            self.dark_mode = data.get('dark_mode', False)
            self.ui_zoom_factor = data.get('ui_zoom_factor', 1.0)
            self.current_theme = data.get('current_theme', 'Default Light')
            self.window_geometry = data.get('window_geometry')
            self.window_maximized = data.get('window_maximized', False)
            self.auto_check_updates = data.get('auto_check_updates', False)
            self.last_update_check = data.get('last_update_check')
            self.skipped_versions = data.get('skipped_versions', [])
            self.update_check_frequency = data.get('update_check_frequency', 86400)
            self.active_mode = data.get('active_mode', 'Archival Recording')
            self.auto_detect_mode = data.get('auto_detect_mode', True)
            self.mode_detect_frames = data.get('mode_detect_frames', dict(DEFAULT_DETECT_FRAMES))
            self.mode_detect_default = data.get('mode_detect_default', DEFAULT_DETECT_DEFAULT)

            # Always use current DEFAULT_MODES for built-in modes so frame-ID changes
            # (schema migrations) take effect immediately.  User-added custom modes
            # (not present in DEFAULT_MODES) are preserved from the saved config.
            saved_modes = data.get('modes', {})
            for name, fields in DEFAULT_MODES.items():
                saved_modes[name] = list(fields)
            self.modes = saved_modes

            logger.debug(f"Configuration loaded from {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")


config = Config()
