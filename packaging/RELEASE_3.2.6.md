# SteamCommandGen v3.2.6

## English

Fixes SteamOS installation and the distributed packages.

**Package update:** the main file is now named `SteamCommandGen.py`.

The 3.2.5 AppImage scanned games correctly on Ubuntu when Python 3.14 was installed on the host. The first 3.2.6 build switched from Python 3.14/Qt 6.11 to Python 3.12/Qt 6.7; this updated build restores Python 3.14/Qt 6.11 and bundles them in the AppImage. The `.deb` launcher uses an absolute path and retains the old command name as an alias for upgrades from 3.2.5.

### What was broken

- The per-user `.desktop` file invoked `SteamCommanderGen.py` by name, but Plasma does not always include `~/.local/bin` in its `PATH`.
- The installer copied files from the current working directory and mixed the system's `pip` with the Python interpreter that ran the application. On SteamOS, `vdf` could be missing from the interpreter actually used.
- The application only looked for FSR, NIS, NEAREST, and MangoHud icons in one particular installation structure; buttons had no images when run from source.
- The 3.2.5 AppImage contained PyQt6 packages for Python 3.14, but `usr/bin/python3` was an absolute link to the host's Python. On Python 3.12, for example, importing `PyQt6.sip` failed.

### What was fixed

- Per-user installer with its own Python environment, pinned PyQt6 versions, and import checks. Run `./install.sh` from `src/` without `sudo`; it does not modify system packages.
- Plasma launcher with an absolute path, independent of `PATH`. The installer works from any working directory.
- Asset lookup for the source tree, user and system installations, and the PyInstaller binary.
- AppImage built with PyInstaller and a bundled Python runtime. The `.deb` includes `vdf` and uses Debian/Ubuntu's `python3-pyqt6` package.

Downloads: `SteamCommandGen-3.2.6-x86_64.AppImage` (Linux x86_64), `SteamCommandGen_3.2.6_amd64.deb` (Debian/Ubuntu), and the source ZIP. On SteamOS, use the AppImage or the per-user installer, not the `.deb`.

---

## Español

Corrección de instalación en SteamOS y de los paquetes distribuidos.

**Actualización del paquete:** el archivo principal se llama ahora `SteamCommandGen.py`.

El AppImage 3.2.5 buscaba juegos correctamente en Ubuntu cuando encontraba Python 3.14 en el sistema. La primera compilación de 3.2.6 cambió Python 3.14/Qt 6.11 por Python 3.12/Qt 6.7; esta actualización recupera Python 3.14/Qt 6.11 y los incluye en el propio AppImage. El `.deb` usa una ruta absoluta en el lanzador y proporciona el nombre antiguo como alias para instalaciones actualizadas desde 3.2.5.

### Qué estaba roto

- El `.desktop` de la instalación de usuario ejecutaba `SteamCommanderGen.py` por nombre, y Plasma no siempre incluye `~/.local/bin` en su `PATH`.
- El instalador copiaba los archivos desde el directorio actual y mezclaba `pip` del sistema con el Python que luego ejecutaba la aplicación. En SteamOS, `vdf` podía quedar sin instalar en el intérprete correcto.
- El programa buscaba los iconos de FSR, NIS, NEAREST y MangoHud sólo bajo una estructura de instalación concreta; al ejecutarlo desde el código fuente los botones salían sin imágenes.
- El AppImage 3.2.5 contenía paquetes PyQt6 para Python 3.14, pero `usr/bin/python3` era un enlace absoluto al Python del equipo anfitrión. Con Python 3.12, por ejemplo, falla al importar `PyQt6.sip`.

### Qué se ha corregido

- Instalador por usuario con entorno Python propio, versiones PyQt6 fijadas y comprobación de importaciones. Ejecutar `./install.sh` desde `src/`, sin `sudo`; no modifica paquetes del sistema.
- Lanzador de Plasma con ruta absoluta, independiente del `PATH`. El instalador funciona desde cualquier directorio.
- Búsqueda de recursos en árbol fuente, instalaciones de usuario o sistema y binario PyInstaller.
- AppImage generado con PyInstaller y runtime Python incluido. El `.deb` incluye `vdf` y utiliza `python3-pyqt6` de Debian/Ubuntu.

Descargas: `SteamCommandGen-3.2.6-x86_64.AppImage` (Linux x86_64), `SteamCommandGen_3.2.6_amd64.deb` (Debian/Ubuntu) y archivo fuente ZIP. En SteamOS usar el AppImage o el instalador de usuario, no el `.deb`.
