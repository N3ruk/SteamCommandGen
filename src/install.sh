#!/bin/bash

echo "========================================"
echo "  Instalador de SteamCommandGen"
echo "========================================"

# Detectar distro
detect_distro() {
    if command -v apt >/dev/null 2>&1; then
        echo "debian"
    elif command -v pacman >/dev/null 2>&1; then
        echo "arch"
    elif command -v dnf >/dev/null 2>&1; then
        echo "fedora"
    else
        echo "unknown"
    fi
}

DISTRO=$(detect_distro)

echo "Detectando dependencias..."

# Función para comprobar módulos Python
check_python_module() {
    python3 - <<EOF
import importlib
try:
    importlib.import_module("$1")
except ImportError:
    exit(1)
EOF
}

# Dependencias requeridas
NEED_PYQT6=false
NEED_VDF=false

# Comprobar Python3
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Python3 no está instalado."
    INSTALL_PYTHON=true
else
    echo "✔ Python3 OK"
fi

# Comprobar PyQt6
if ! check_python_module PyQt6; then
    echo "❌ Falta PyQt6"
    NEED_PYQT6=true
else
    echo "✔ PyQt6 OK"
fi

# Comprobar vdf
if ! check_python_module vdf; then
    echo "❌ Falta módulo vdf"
    NEED_VDF=true
else
    echo "✔ vdf OK"
fi

echo ""
echo "========================================"
echo "  Instalando dependencias faltantes"
echo "========================================"

case $DISTRO in
    debian)
        echo "→ Sistema basado en Debian detectado"
        sudo apt update

        [ "$INSTALL_PYTHON" = true ] && sudo apt install -y python3
        [ "$NEED_PYQT6" = true ] && sudo apt install -y python3-pyqt6
        [ "$NEED_VDF" = true ] && sudo apt install -y python3-pip && pip3 install vdf
        ;;
    arch)
        echo "→ Sistema basado en Arch detectado"
        sudo pacman -Sy --noconfirm

        [ "$INSTALL_PYTHON" = true ] && sudo pacman -S --noconfirm python
        [ "$NEED_PYQT6" = true ] && sudo pacman -S --noconfirm python-pyqt6
        [ "$NEED_VDF" = true ] && sudo pacman -S --noconfirm python-pip && pip install vdf
        ;;
    fedora)
        echo "→ Sistema basado en Fedora detectado"
        sudo dnf install -y python3 python3-pip

        [ "$NEED_PYQT6" = true ] && sudo dnf install -y python3-qt5 python3-qt6
        [ "$NEED_VDF" = true ] && pip3 install vdf
        ;;
    *)
        echo "⚠ Distro desconocida. Instala manualmente:"
        echo "   python3, PyQt6, vdf"
        ;;
esac

echo ""
echo "========================================"
echo "  Instalando SteamCommandGen"
echo "========================================"

# Crear carpetas
mkdir -p ~/.local/bin
mkdir -p ~/.local/share/applications
mkdir -p ~/.local/share/icons/hicolor/256x256/apps

# Copiar archivos
cp SteamCommanderGen.py ~/.local/bin/
cp SteamCommandGen.desktop ~/.local/share/applications/
cp SteamCommandGen.png ~/.local/share/icons/hicolor/256x256/apps/

# Permisos
chmod +x ~/.local/bin/SteamCommanderGen.py

# Actualizar caché de iconos
gtk-update-icon-cache ~/.local/share/icons/hicolor

echo ""
echo "========================================"
echo "  Instalación completada"
echo "========================================"
echo "Puedes ejecutar SteamCommandGen desde el menú de aplicaciones."

