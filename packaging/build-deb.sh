#!/usr/bin/env bash
set -euo pipefail
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
version="3.2.8"
out="${1:-$repo/dist}"
mkdir -p "$out"
out="$(cd "$out" && pwd -P)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
pkg="$tmp/pkg"
install -Dm644 "$repo/src/SteamCommandGen.py" "$pkg/usr/lib/steamcommandgen/SteamCommandGen.py"
install -Dm644 "$repo/src/SteamCommandGen.png" "$pkg/usr/share/icons/hicolor/256x256/apps/SteamCommandGen.png"
cp -a "$repo/src/SteamCommandGen" "$pkg/usr/share/SteamCommandGen"
mkdir -p "$pkg/usr/lib/steamcommandgen/vendor" "$pkg/usr/bin" "$pkg/usr/share/applications" "$pkg/DEBIAN"
python3 -m pip install --disable-pip-version-check --no-deps --target "$pkg/usr/lib/steamcommandgen/vendor" 'vdf==3.4'
find "$pkg/usr/lib/steamcommandgen/vendor" -name '__pycache__' -type d -prune -exec rm -rf {} +
cat > "$pkg/usr/bin/steamcommandgen" <<'EOF'
#!/usr/bin/env bash
export PYTHONPATH="/usr/lib/steamcommandgen/vendor${PYTHONPATH:+:$PYTHONPATH}"
exec /usr/bin/python3 /usr/lib/steamcommandgen/SteamCommandGen.py "$@"
EOF
chmod +x "$pkg/usr/bin/steamcommandgen"
ln -s steamcommandgen "$pkg/usr/bin/SteamCommanderGen.py"
cat > "$pkg/usr/share/applications/SteamCommandGen.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=SteamCommandGen
Comment=Generador de comandos para Steam
Exec=/usr/bin/steamcommandgen
Icon=SteamCommandGen
Terminal=false
Categories=Utility;Game;
StartupNotify=true
StartupWMClass=SteamCommandGen
EOF
cat > "$pkg/DEBIAN/control" <<EOF
Package: steamcommandgen
Version: $version
Section: games
Priority: optional
Architecture: amd64
Maintainer: N3ruk
Depends: python3 (>= 3.10), python3-pyqt6
Description: Steam launch options generator with Gamescope and MangoHud
 Graphical launch options editor for Steam games.
EOF
install -m755 "$repo/packaging/debian/postinst" "$pkg/DEBIAN/postinst"
install -m755 "$repo/packaging/debian/postrm" "$pkg/DEBIAN/postrm"
chmod -R a+rX "$pkg"
dpkg-deb --root-owner-group --build "$pkg" "$out/SteamCommandGen_${version}_amd64.deb"
