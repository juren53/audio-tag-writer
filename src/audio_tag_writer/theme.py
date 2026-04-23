"""
Audio Tag Writer - ThemeManager class and theme dictionaries.
"""

import logging

logger = logging.getLogger(__name__)


class ThemeManager:
    """Manages application themes and styling."""

    def __init__(self):
        self.themes = {
            'Default Light': {
                'name': 'Default Light',
                'background': '#fafafa',
                'text': '#2d3748',
                'selection_bg': '#4299e1',
                'selection_text': '#ffffff',
                'menubar_bg': '#f7fafc',
                'menubar_text': '#2d3748',
                'toolbar_bg': '#f7fafc',
                'statusbar_bg': '#edf2f7',
                'statusbar_text': '#4a5568',
                'button_bg': '#e2e8f0',
                'button_text': '#2d3748',
                'button_hover': '#cbd5e0',
                'border': '#cbd5e0'
            },
            'Warm Light': {
                'name': 'Warm Light',
                'background': '#eee9e0',
                'text': '#504741',
                'selection_bg': '#6699cc',
                'selection_text': '#ffffff',
                'menubar_bg': '#e6e1d7',
                'menubar_text': '#504741',
                'toolbar_bg': '#f0ebe2',
                'statusbar_bg': '#e1dcd2',
                'statusbar_text': '#504741',
                'button_bg': '#e6e1d7',
                'button_text': '#504741',
                'button_hover': '#ddd8cf',
                'border': '#b4aa9a'
            },
            'Dark': {
                'name': 'Dark',
                'background': '#2b2b2b',
                'text': '#ffffff',
                'selection_bg': '#4a9eff',
                'selection_text': '#ffffff',
                'menubar_bg': '#3c3c3c',
                'menubar_text': '#ffffff',
                'toolbar_bg': '#404040',
                'statusbar_bg': '#333333',
                'statusbar_text': '#ffffff',
                'button_bg': '#454545',
                'button_text': '#ffffff',
                'button_hover': '#555555',
                'border': '#555555'
            },
            'Solarized Light': {
                'name': 'Solarized Light',
                'background': '#fdf6e3',
                'text': '#657b83',
                'selection_bg': '#268bd2',
                'selection_text': '#fdf6e3',
                'menubar_bg': '#eee8d5',
                'menubar_text': '#657b83',
                'toolbar_bg': '#f5f0e7',
                'statusbar_bg': '#eee8d5',
                'statusbar_text': '#657b83',
                'button_bg': '#eee8d5',
                'button_text': '#657b83',
                'button_hover': '#e8e2d4',
                'border': '#d3cbb7'
            },
            'Solarized Dark': {
                'name': 'Solarized Dark',
                'background': '#002b36',
                'text': '#839496',
                'selection_bg': '#268bd2',
                'selection_text': '#002b36',
                'menubar_bg': '#073642',
                'menubar_text': '#839496',
                'toolbar_bg': '#0a3c47',
                'statusbar_bg': '#073642',
                'statusbar_text': '#839496',
                'button_bg': '#073642',
                'button_text': '#839496',
                'button_hover': '#0c4956',
                'border': '#586e75'
            },
            'High Contrast': {
                'name': 'High Contrast',
                'background': '#000000',
                'text': '#ffffff',
                'selection_bg': '#ffff00',
                'selection_text': '#000000',
                'menubar_bg': '#000000',
                'menubar_text': '#ffffff',
                'toolbar_bg': '#000000',
                'statusbar_bg': '#000000',
                'statusbar_text': '#ffffff',
                'button_bg': '#333333',
                'button_text': '#ffffff',
                'button_hover': '#555555',
                'border': '#ffffff'
            },
            'Monokai': {
                'name': 'Monokai',
                'background': '#272822',
                'text': '#f8f8f2',
                'selection_bg': '#49483e',
                'selection_text': '#f8f8f2',
                'menubar_bg': '#3e3d32',
                'menubar_text': '#f8f8f2',
                'toolbar_bg': '#414339',
                'statusbar_bg': '#3e3d32',
                'statusbar_text': '#f8f8f2',
                'button_bg': '#49483e',
                'button_text': '#f8f8f2',
                'button_hover': '#5a594d',
                'border': '#75715e'
            },
            'GitHub Dark': {
                'name': 'GitHub Dark',
                'background': '#0d1117',
                'text': '#c9d1d9',
                'selection_bg': '#388bfd',
                'selection_text': '#ffffff',
                'menubar_bg': '#161b22',
                'menubar_text': '#c9d1d9',
                'toolbar_bg': '#21262d',
                'statusbar_bg': '#161b22',
                'statusbar_text': '#c9d1d9',
                'button_bg': '#21262d',
                'button_text': '#c9d1d9',
                'button_hover': '#30363d',
                'border': '#30363d'
            }
        }
        self.current_theme = 'Default Light'

    def get_theme_names(self):
        return list(self.themes.keys())

    def get_theme(self, theme_name):
        return self.themes.get(theme_name, self.themes['Default Light'])

    def is_dark_theme(self, theme_name=None):
        if theme_name is None:
            theme_name = self.current_theme
        dark_themes = ['Dark', 'Solarized Dark', 'High Contrast', 'Monokai', 'GitHub Dark']
        return theme_name in dark_themes

    def generate_stylesheet(self, theme_name):
        """Generate QSS stylesheet for the given theme."""
        theme = self.get_theme(theme_name)

        return f"""
        QMainWindow {{
            background-color: {theme['background']};
            color: {theme['text']};
        }}

        QTextEdit, QPlainTextEdit {{
            background-color: {theme['background']};
            color: {theme['text']};
            selection-background-color: {theme['selection_bg']};
            selection-color: {theme['selection_text']};
            border: 1px solid {theme['border']};
        }}

        QMenuBar {{
            background-color: {theme['menubar_bg']};
            color: {theme['menubar_text']};
            border-bottom: 1px solid {theme['border']};
        }}

        QMenuBar::item {{
            background-color: transparent;
            padding: 4px 8px;
        }}

        QMenuBar::item:selected {{
            background-color: {theme['selection_bg']};
            color: {theme['selection_text']};
        }}

        QMenu {{
            background-color: {theme['menubar_bg']};
            color: {theme['menubar_text']};
            border: 1px solid {theme['border']};
        }}

        QMenu::item {{
            background-color: transparent;
            padding: 6px 12px;
        }}

        QMenu::item:selected {{
            background-color: {theme['selection_bg']};
            color: {theme['selection_text']};
        }}

        QMenu::separator {{
            height: 1px;
            background-color: {theme['border']};
            margin: 2px 0;
        }}

        QToolBar {{
            background-color: {theme['toolbar_bg']};
            color: {theme['text']};
            border: 1px solid {theme['border']};
            spacing: 2px;
        }}

        QToolBar::separator {{
            background-color: {theme['border']};
            width: 1px;
            margin: 2px;
        }}

        QStatusBar {{
            background-color: {theme['statusbar_bg']};
            color: {theme['statusbar_text']};
            border-top: 1px solid {theme['border']};
        }}

        QPushButton {{
            background-color: {theme['button_bg']};
            color: {theme['button_text']};
            border: 1px solid {theme['border']};
            border-radius: 3px;
            padding: 6px 12px;
            min-width: 80px;
        }}

        QPushButton:hover {{
            background-color: {theme['button_hover']};
        }}

        QPushButton:pressed {{
            background-color: {theme['selection_bg']};
            color: {theme['selection_text']};
        }}

        QPushButton:disabled {{
            background-color: {theme['border']};
            color: {theme['statusbar_text']};
        }}

        QLabel {{
            background-color: transparent;
            color: {theme['text']};
        }}

        QLineEdit {{
            background-color: {theme['background']};
            color: {theme['text']};
            border: 1px solid {theme['border']};
            border-radius: 3px;
            padding: 4px;
            selection-background-color: {theme['selection_bg']};
            selection-color: {theme['selection_text']};
        }}

        QLineEdit:focus {{
            border: 2px solid {theme['selection_bg']};
        }}

        QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px solid {theme['selection_bg']};
        }}

        QWidget {{
            background-color: {theme['background']};
            color: {theme['text']};
        }}

        QScrollArea {{
            background-color: {theme['background']};
            color: {theme['text']};
            border: 1px solid {theme['border']};
        }}

        QScrollArea > QWidget > QWidget {{
            background-color: {theme['background']};
        }}

        QFrame {{
            background-color: {theme['background']};
            color: {theme['text']};
        }}

        QDialog {{
            background-color: {theme['background']};
            color: {theme['text']};
        }}

        QSplitter::handle {{
            background-color: {theme['border']};
            width: 2px;
        }}

        QSplitter::handle:hover {{
            background-color: {theme['selection_bg']};
        }}

        QComboBox {{
            background-color: {theme['button_bg']};
            color: {theme['button_text']};
            border: 1px solid {theme['border']};
            border-radius: 3px;
            padding: 4px 8px;
            min-width: 100px;
        }}

        QComboBox:hover {{
            background-color: {theme['button_hover']};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}

        QComboBox::down-arrow {{
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {theme['text']};
        }}

        QComboBox QAbstractItemView {{
            background-color: {theme['menubar_bg']};
            color: {theme['menubar_text']};
            selection-background-color: {theme['selection_bg']};
            selection-color: {theme['selection_text']};
            border: 1px solid {theme['border']};
        }}

        QTableWidget {{
            background-color: {theme['background']};
            color: {theme['text']};
            selection-background-color: {theme['selection_bg']};
            selection-color: {theme['selection_text']};
            border: 1px solid {theme['border']};
        }}

        QTableWidget::item {{
            border-bottom: 1px solid {theme['border']};
            padding: 4px;
        }}

        QHeaderView::section {{
            background-color: {theme['toolbar_bg']};
            color: {theme['text']};
            border: 1px solid {theme['border']};
            padding: 4px;
        }}

        QScrollBar:vertical {{
            background-color: {theme['background']};
            width: 16px;
            border: 1px solid {theme['border']};
        }}

        QScrollBar::handle:vertical {{
            background-color: {theme['button_bg']};
            border: 1px solid {theme['selection_bg']};
            border-radius: 3px;
            min-height: 20px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {theme['selection_bg']};
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            background-color: {theme['toolbar_bg']};
            border: 1px solid {theme['border']};
            height: 16px;
            subcontrol-origin: margin;
        }}

        QScrollBar::add-line:vertical:hover, QScrollBar::sub-line:vertical:hover {{
            background-color: {theme['button_hover']};
        }}

        QScrollBar::up-arrow:vertical {{
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 6px solid {theme['text']};
        }}

        QScrollBar::down-arrow:vertical {{
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid {theme['text']};
        }}

        QScrollBar:horizontal {{
            background-color: {theme['background']};
            height: 16px;
            border: 1px solid {theme['border']};
        }}

        QScrollBar::handle:horizontal {{
            background-color: {theme['button_bg']};
            border: 1px solid {theme['selection_bg']};
            border-radius: 3px;
            min-width: 20px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {theme['selection_bg']};
        }}

        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            background-color: {theme['toolbar_bg']};
            border: 1px solid {theme['border']};
            width: 16px;
            subcontrol-origin: margin;
        }}

        QScrollBar::add-line:horizontal:hover, QScrollBar::sub-line:horizontal:hover {{
            background-color: {theme['button_hover']};
        }}

        QScrollBar::left-arrow:horizontal {{
            border-top: 4px solid transparent;
            border-bottom: 4px solid transparent;
            border-right: 6px solid {theme['text']};
        }}

        QScrollBar::right-arrow:horizontal {{
            border-top: 4px solid transparent;
            border-bottom: 4px solid transparent;
            border-left: 6px solid {theme['text']};
        }}

        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: transparent;
        }}
        """
