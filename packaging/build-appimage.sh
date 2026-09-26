#!/usr/bin/env bash
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
version="3.2.7"
out="${1:-$repo/dist}"
mkdir -p "$out"
out="$(cd "$out" && pwd -P)"
if [[ "$(uname -m)" != x86_64 ]]; then
    echo "Este AppImage se construye para x86_64." >&2; exit 1
fi
tool="${APPIMAGETOOL:-}"
if [[ -z "$tool" ]] || [[ ! -x "$tool" ]]; then
    echo "Define APPIMAGETOOL con la ruta a appimagetool (ejecutable)." >&2; exit 1
fi
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
"${PYTHON_FOR_APPIMAGE:-python3.14}" -m venv "$tmp/venv"
"$tmp/venv/bin/python" -m pip install --disable-pip-version-check \
    'pyinstaller==6.22.3' 'vdf==3.4' \
    'PyQt6==6.11.0' 'PyQt6-Qt6==6.11.2' 'PyQt6-sip==13.12.0'
"$tmp/venv/bin/pyinstaller" --noconfirm --clean --onedir \
    --name SteamCommandGen \
    --add-data "$repo/src/SteamCommandGen:SteamCommandGen" \
    --distpath "$tmp/dist" --workpath "$tmp/build" --specpath "$tmp" \
    "$repo/src/SteamCommandGen.py"
appdir="$tmp/SteamCommandGen.AppDir"
mkdir -p "$appdir/usr/bin"
cp -a "$tmp/dist/SteamCommandGen" "$appdir/usr/bin/"
install -m644 "$repo/src/SteamCommandGen.png" "$appdir/SteamCommandGen.png"
cat > "$appdir/SteamCommandGen.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=SteamCommandGen
Exec=SteamCommandGen
Icon=SteamCommandGen
Categories=Utility;Game;
Terminal=false
EOF
cat > "$appdir/AppRun" <<'EOF'
#!/usr/bin/env bash
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
# Ignore inherited system/venv plugin paths; PyInstaller includes its matching Qt plugins.
unset PYTHONPATH PYTHONHOME QT_PLUGIN_PATH QT_QPA_PLATFORM_PLUGIN_PATH
exec "$here/usr/bin/SteamCommandGen/SteamCommandGen" "$@"
EOF
chmod +x "$appdir/AppRun"
# Refuse to ship the old kind of AppImage whose interpreter points to /usr/bin/python3.
find "$appdir/usr/bin/SteamCommandGen/_internal" -maxdepth 1 -name 'libpython3*.so*' | grep -q . || \
    { echo "No se ha incluido el runtime Python." >&2; exit 1; }
ARCH=x86_64 "$tool" "$appdir" "$out/SteamCommandGen-${version}-x86_64.AppImage"
