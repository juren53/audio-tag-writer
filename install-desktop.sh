#!/usr/bin/env bash
# Install (or remove) the Audio Tag Writer entry in the Linux System Menu.
# User-level install — no sudo. Tested on LMDE / Cinnamon.

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DESKTOP="$PROJECT_DIR/assets/ATW.desktop"
APPS_DIR="$HOME/.local/share/applications"
DEST_DESKTOP="$APPS_DIR/atw.desktop"

uninstall() {
    rm -f "$DEST_DESKTOP"
    update-desktop-database "$APPS_DIR" 2>/dev/null || true
    echo "Removed $DEST_DESKTOP"
    exit 0
}

[[ "${1:-}" == "--uninstall" ]] && uninstall

[[ -f "$SRC_DESKTOP" ]] || { echo "Missing $SRC_DESKTOP" >&2; exit 1; }

chmod +x "$PROJECT_DIR/run.sh"
mkdir -p "$APPS_DIR"

# Rewrite the hard-coded paths in assets/ATW.desktop to this checkout's location.
sed "s|/home/juren/Projects/audio-tag-writer|$PROJECT_DIR|g" "$SRC_DESKTOP" > "$DEST_DESKTOP"
chmod 644 "$DEST_DESKTOP"

command -v desktop-file-validate >/dev/null 2>&1 && desktop-file-validate "$DEST_DESKTOP" || true
update-desktop-database "$APPS_DIR" 2>/dev/null || true
gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor/" 2>/dev/null || true

echo "Installed $DEST_DESKTOP"
echo "Audio Tag Writer should now appear in the System Menu (Sound & Video / Accessories)."
echo "If it does not show immediately, restart Cinnamon (Ctrl+Alt+Esc) or log out and back in."
