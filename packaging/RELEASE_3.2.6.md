# SteamCommandGen v3.2.6

Corrección de instalación en SteamOS y de los paquetes distribuidos.

## Qué estaba roto

- El `.desktop` de la instalación de usuario ejecutaba `SteamCommanderGen.py` por nombre, y Plasma no siempre incluye `~/.local/bin` en su `PATH`.
- El instalador copiaba los archivos desde el directorio actual y mezclaba `pip` del sistema con el Python que luego ejecutaba la aplicación. En SteamOS, `vdf` podía quedar sin instalar en el intérprete correcto.
- El programa buscaba los iconos de FSR, NIS, NEAREST y MangoHud sólo bajo una estructura de instalación concreta; al ejecutarlo desde el código fuente los botones salían sin imágenes.
- El AppImage 3.2.5 contenía paquetes PyQt6 para Python 3.14, pero `usr/bin/python3` era un enlace absoluto al Python del equipo anfitrión. Con Python 3.12, por ejemplo, falla al importar `PyQt6.sip`.

## Qué se ha corregido

- Instalador por usuario con entorno Python propio, versiones PyQt6 fijadas y comprobación de importaciones. Ejecutar `./install.sh` desde `src/`, sin `sudo`; no modifica paquetes del sistema.
- Lanzador de Plasma con ruta absoluta, independiente del `PATH`. El instalador funciona desde cualquier directorio.
- Búsqueda de recursos en árbol fuente, instalaciones de usuario o sistema y binario PyInstaller.
- AppImage generado con PyInstaller y runtime Python incluido. El `.deb` incluye `vdf` y utiliza `python3-pyqt6` de Debian/Ubuntu.

Descargas: `SteamCommandGen-3.2.6-x86_64.AppImage` (Linux x86_64), `SteamCommandGen_3.2.6_amd64.deb` (Debian/Ubuntu) y archivo fuente ZIP. En SteamOS usar el AppImage o el instalador de usuario, no el `.deb`.
