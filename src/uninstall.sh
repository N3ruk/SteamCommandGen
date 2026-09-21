#!/bin/bash

echo "========================================"
echo "  Desinstalador de SteamCommandGen"
echo "========================================"

# Rutas
BIN_PATH="$HOME/.local/bin/SteamCommanderGen.py"
DESKTOP_PATH="$HOME/.local/share/applications/SteamCommandGen.desktop"
ICON_PATH="$HOME/.local/share/icons/hicolor/256x256/apps/SteamCommandGen.png"
RESOURCES_PATH="$HOME/.local/share/SteamCommandGen"

echo "Eliminando archivos..."

# Eliminar binario
if [ -f "$BIN_PATH" ]; then
    rm "$BIN_PATH"
    echo "✔ Eliminado: $BIN_PATH"
else
    echo "⚠ No encontrado: $BIN_PATH"
fi

# Eliminar .desktop
if [ -f "$DESKTOP_PATH" ]; then
    rm "$DESKTOP_PATH"
    echo "✔ Eliminado: $DESKTOP_PATH"
else
    echo "⚠ No encontrado: $DESKTOP_PATH"
fi

# Eliminar icono
if [ -f "$ICON_PATH" ]; then
    rm "$ICON_PATH"
    echo "✔ Eliminado: $ICON_PATH"
else
    echo "⚠ No encontrado: $ICON_PATH"
fi

# Eliminar recursos de la aplicación
if [ -d "$RESOURCES_PATH" ]; then
    rm -rf "$RESOURCES_PATH"
    echo "✔ Eliminados recursos: $RESOURCES_PATH"
else
    echo "⚠ Recursos no encontrados: $RESOURCES_PATH"
fi

echo ""
echo "Actualizando caché de iconos..."
gtk-update-icon-cache "$HOME/.local/share/icons/hicolor"

echo ""
echo "========================================"
echo "  Desinstalación completada"
echo "========================================"
echo "SteamCommandGen ha sido eliminado del sistema."
