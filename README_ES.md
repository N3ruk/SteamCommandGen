# SteamCommandGen

**SteamCommandGen** es una herramienta gráfica para **Linux** diseñada para generar, aplicar y gestionar opciones de lanzamiento de Steam utilizando **Gamescope**.

Permite configurar de forma sencilla y visual resoluciones, tecnologías de escalado, nitidez, HDR, VRR, baja latencia, `WINEDLLOVERRIDES` y MangoHud, generando automáticamente las `LaunchOptions` necesarias para cada juego.

> Versión actual: **SteamCommandGen v3.2.5**

![SteamCommandGen Screenshot](assets/screenshots/main.png)

---

## ✨ Características

* 🎮 Detección automática de juegos y bibliotecas de Steam.
* ⚡ Escaneo optimizado de bibliotecas sin recorrer innecesariamente `compatdata`, `shadercache` u otras carpetas.
* 🧵 Escaneo de juegos en segundo plano para evitar bloquear la interfaz.
* ⚙️ Generación automática de comandos **Gamescope**.
* 🖥️ Interfaz gráfica desarrollada con **PyQt6**.
* 🔴 Soporte para **AMD FSR**.
* 🟢 Soporte para **NVIDIA NIS**.
* 🔵 Soporte para **NEAREST**.
* 🎚️ Control de nitidez para FSR y NIS.
* 🥭 Integración con **MangoHud** mediante `--mangoapp`.
* 🛠️ Configurador gráfico integrado para `MangoHud.conf`.
* 👁️ Vista previa de MangoHud.
* 🖥️ Resoluciones desde **450p hasta 4K**.
* 🌈 Soporte para **HDR**.
* ⚡ Soporte para **VRR / Adaptive Sync**.
* 🚀 Soporte para **Immediate Flips / baja latencia**.
* 🔧 Soporte para `WINEDLLOVERRIDES`.
* 🔄 Lectura y restauración automática de las **Steam LaunchOptions** existentes.
* 🧹 Limpieza de LaunchOptions desde la propia aplicación.
* 📋 Copiado de comandos al portapapeles.
* 🖼️ Carga de iconos y carátulas de los juegos.
* 🚫 Filtrado automático de herramientas de Steam que no son juegos.
* 📦 Disponible como **AppImage**, **paquete `.deb`** y **script instalador**.

---

## 🎮 Tecnologías de escalado

SteamCommandGen permite seleccionar entre diferentes tecnologías de escalado disponibles en Gamescope:

| Tecnología | Descripción |
| --- | --- |
| **FSR** | AMD FidelityFX Super Resolution |
| **NIS** | NVIDIA Image Scaling |
| **NEAREST** | Escalado mediante vecino más cercano |

Las tecnologías de escalado son **mutuamente excluyentes**. La aplicación mantiene sincronizado el estado de la interfaz y genera automáticamente el parámetro correspondiente de Gamescope.

### FSR

```text
-F fsr --sharpness N
```

### NIS

```text
-F nis --sharpness N
```

### NEAREST

```text
-F nearest
```

Los controles de nitidez de FSR y NIS utilizan una escala sencilla de **0 a 5** en la interfaz.

---

## 🥭 Integración con MangoHud

SteamCommandGen v3.2.5 incorpora integración directa con **MangoHud** mediante `--mangoapp` y un configurador gráfico para `MangoHud.conf`.

La configuración se guarda en:

```text
~/.config/MangoHud/MangoHud.conf
```

El editor incluye copia `.bak`, restauración al cancelar y vista previa cuando existe una aplicación Vulkan compatible.

---

## 🖥️ Resoluciones

* **450p** — 800×450
* **576p** — 1024×576
* **720p** — 1280×720
* **900p** — 1600×900
* **1080p** — 1920×1080
* **1440p** — 2560×1440
* **4K** — 3840×2160

Las resoluciones de entrada y salida comienzan sin ningún valor preseleccionado.

---

## 🔄 Restauración de LaunchOptions

SteamCommandGen intenta restaurar automáticamente desde las opciones existentes:

* Resolución de entrada y salida.
* FSR, NIS y NEAREST.
* Nitidez.
* HDR.
* VRR / Adaptive Sync.
* Immediate Flips.
* MangoHud.
* `WINEDLLOVERRIDES`.

---

## 🎮 Gestión de Steam

SteamCommandGen detecta bibliotecas de Steam y lee sus manifiestos `.acf`, filtra herramientas que no son juegos y evita duplicados usando el AppID.

---

## ⚙️ Ejemplos de comandos

### FSR

```text
gamescope -w 1920 -h 1080 -W 2560 -H 1440 -F fsr --sharpness 0 -f -- %command%
```

### NIS + MangoHud

```text
gamescope -w 1920 -h 1080 -W 2560 -H 1440 -F nis --sharpness 0 --mangoapp -f -- %command%
```

### HDR + VRR

```text
gamescope -w 1920 -h 1080 -W 2560 -H 1440 --hdr-enabled --adaptive-sync -f -- %command%
```

> **VRR / Adaptive Sync** e **Immediate Flips** se gestionan como opciones mutuamente excluyentes.

---

# 📦 Instalación

La versión más reciente está en **[Releases](../../releases)**.

## Paquete `.deb`

```bash
sudo apt install ./SteamCommandGen_x.x.x_amd64.deb
```

## Script instalador

```bash
chmod +x install.sh
./install.sh
```

## AppImage

```bash
chmod +x SteamCommandGen-x86_64.AppImage
./SteamCommandGen-x86_64.AppImage
```

---

# 🛠️ Requisitos

* Linux.
* Steam.
* Gamescope.

Desde código fuente:

* Python 3.x.
* PyQt6.
* Módulo Python `vdf`.

Opcional:

* MangoHud.

---

# 📋 Changelog

Consulta **[CHANGELOG.md](CHANGELOG.md)**.

# 🚀 Releases

Descargas oficiales: **[Releases](../../releases)**.

# 📄 Licencia

Consulta **[LICENSE](LICENSE)**.
