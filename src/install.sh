#!/usr/bin/env bash
set -euo pipefail

if (( EUID == 0 )); then
    echo "Ejecuta este instalador como usuario, sin sudo." >&2
    exit 1
fi

source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
python_bin="$(command -v python3 || true)"
if [[ -z "$python_bin" ]]; then
    echo "Falta Python 3. Instálalo con el gestor de paquetes de tu distribución." >&2
    exit 1
fi

app_root="$HOME/.local/share/SteamCommandGen"
launcher="$HOME/.local/bin/SteamCommanderGen"
desktop="$HOME/.local/share/applications/SteamCommandGen.desktop"
icon="$HOME/.local/share/icons/hicolor/256x256/apps/SteamCommandGen.png"

for file in SteamCommanderGen.py SteamCommandGen.desktop SteamCommandGen.png; do
    [[ -f "$source_dir/$file" ]] || { echo "Falta $source_dir/$file" >&2; exit 1; }
done
for folder in BOTONES scaling; do
    [[ -d "$source_dir/SteamCommandGen/$folder" ]] || { echo "Falta $folder" >&2; exit 1; }
done

# Prepare dependencies first so a failed pip download does not replace a working install.
mkdir -p "$app_root" "$(dirname "$launcher")" "$(dirname "$desktop")" "$(dirname "$icon")"
if [[ ! -x "$app_root/venv/bin/python" ]]; then
    "$python_bin" -m venv "$app_root/venv" || {
        echo "No se pudo crear el entorno Python. Instala python3-venv o el paquete equivalente." >&2
        exit 1
    }
fi
"$app_root/venv/bin/python" -m pip install --disable-pip-version-check \
    'vdf==3.4' 'PyQt6==6.7.1' 'PyQt6-Qt6==6.7.3'
"$app_root/venv/bin/python" -c 'import vdf; from PyQt6 import QtCore, QtGui, QtWidgets, QtNetwork'

mkdir -p "$app_root/app"
cp -- "$source_dir/SteamCommanderGen.py" "$app_root/app/SteamCommanderGen.py"
cp -a -- "$source_dir/SteamCommandGen/." "$app_root/"
cp -- "$source_dir/SteamCommandGen.png" "$icon"

cat > "$launcher" <<EOF
#!/usr/bin/env bash
exec "$app_root/venv/bin/python" "$app_root/app/SteamCommanderGen.py" "\$@"
EOF
chmod +x "$launcher"
rm -f -- "$HOME/.local/bin/SteamCommanderGen.py"

cat > "$desktop" <<EOF
[Desktop Entry]
Type=Application
Name=SteamCommandGen
Comment=Generador de comandos para Steam
Exec="$launcher"
Icon=SteamCommandGen
Terminal=false
Categories=Utility;Game;
StartupNotify=true
StartupWMClass=SteamCommandGen
EOF

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi
echo "SteamCommandGen instalado en $app_root"
