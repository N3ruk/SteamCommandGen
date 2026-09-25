#!/usr/bin/env bash
set -euo pipefail
if (( EUID == 0 )); then
    echo "Ejecuta este desinstalador sin sudo." >&2
    exit 1
fi
rm -f -- "$HOME/.local/bin/SteamCommandGen" \
    "$HOME/.local/bin/SteamCommanderGen" \
    "$HOME/.local/bin/SteamCommanderGen.py" \
    "$HOME/.local/bin/SteamCommandGen.py" \
    "$HOME/.local/share/applications/SteamCommandGen.desktop" \
    "$HOME/.local/share/icons/hicolor/256x256/apps/SteamCommandGen.png"
rm -rf -- "$HOME/.local/share/SteamCommandGen"
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi
echo "SteamCommandGen desinstalado."
