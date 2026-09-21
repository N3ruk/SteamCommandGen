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

SteamCommandGen genera comandos con la sintaxis:

```text
-F fsr --sharpness N
```

### NIS

SteamCommandGen genera comandos con la sintaxis:

```text
-F nis --sharpness N
```

### NEAREST

```text
-F nearest
```

Los controles de nitidez de FSR y NIS utilizan una escala sencilla de **0 a 5** en la interfaz. SteamCommandGen realiza internamente la conversión necesaria al valor utilizado por Gamescope.

---

## 🥭 Integración con MangoHud

SteamCommandGen v3.2.5 incorpora integración directa con **MangoHud**.

MangoHud puede activarse desde la interfaz y se añade al comando Gamescope mediante:

```text
--mangoapp
```

Además, SteamCommandGen incluye un configurador gráfico para:

* FPS y frametime.
* Uso de CPU y GPU.
* Temperaturas.
* RAM y VRAM.
* Frecuencias y consumo.
* Resolución y frecuencia de pantalla.
* Estado de HDR, FSR y GameMode.
* Posición del HUD.
* Diseño vertical u horizontal.
* Ajuste fino de posición.
* Colores.
* Tecla para mostrar u ocultar el HUD.

La configuración se guarda en:

```text
~/.config/MangoHud/MangoHud.conf
```

El editor incluye gestión segura del archivo de configuración, creación de copia `.bak` y restauración de los cambios al cancelar.

SteamCommandGen también puede mostrar una **vista previa de MangoHud** cuando existe una aplicación Vulkan compatible para utilizar como ventana de prueba.

---

## 🖥️ Resoluciones

Actualmente se pueden seleccionar las siguientes resoluciones:

* **450p** — 800×450
* **576p** — 1024×576
* **720p** — 1280×720
* **900p** — 1600×900
* **1080p** — 1920×1080
* **1440p** — 2560×1440
* **4K** — 3840×2160

Las resoluciones de entrada y salida comienzan **sin ningún valor preseleccionado**, evitando generar accidentalmente un comando con una resolución que el usuario no haya elegido.

---

## 🔄 Restauración de LaunchOptions

Al seleccionar un juego, SteamCommandGen analiza sus `LaunchOptions` existentes e intenta restaurar automáticamente en la interfaz:

* Resolución de entrada.
* Resolución de salida.
* FSR.
* NIS.
* NEAREST.
* Nitidez.
* HDR.
* VRR / Adaptive Sync.
* Immediate Flips.
* MangoHud.
* `WINEDLLOVERRIDES`.

Al cambiar de juego, el estado de la interfaz se reinicia antes de cargar la configuración del nuevo título, evitando mezclar opciones entre juegos diferentes.

---

## 🎮 Gestión de Steam

SteamCommandGen detecta automáticamente las bibliotecas configuradas en Steam y lee sus manifiestos `.acf`.

El escaneo actual está optimizado para consultar directamente los manifiestos situados en `steamapps`, evitando recorrer recursivamente directorios que no son necesarios.

Además, se filtran automáticamente aplicaciones y componentes que no deberían aparecer como videojuegos, entre ellos:

* Proton.
* Steam Linux Runtime.
* Steamworks Common Redistributables.
* Lossless Scaling.

Los juegos duplicados entre bibliotecas se identifican mediante su **AppID**.

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

> **VRR / Adaptive Sync** e **Immediate Flips** se gestionan como opciones mutuamente excluyentes desde la interfaz.

---

# 📦 Instalación

SteamCommandGen puede instalarse de diferentes formas dependiendo de las preferencias del usuario.

La versión más reciente y los archivos descargables están disponibles en la sección **Releases** de GitHub.

## 🟩 Opción 1: Paquete `.deb`

Descarga el paquete `.deb` correspondiente a la versión que quieras instalar desde **Releases** y ejecuta:

```bash
sudo apt install ./SteamCommandGen_x.x.x_amd64.deb
```

---

## 🟩 Opción 2: Script instalador

Descarga el `.zip` desde **Releases**, descomprímelo y ejecuta:

```bash
chmod +x install.sh
./install.sh
```

El instalador se encargará de realizar la instalación de la aplicación.

---

## 🟩 Opción 3: AppImage

Descarga la versión AppImage desde **Releases** y ejecuta:

```bash
chmod +x SteamCommandGen-x86_64.AppImage
./SteamCommandGen-x86_64.AppImage
```

No es necesario realizar una instalación tradicional para utilizar la versión AppImage.

---

# 🛠️ Requisitos

## Requisitos principales

* Linux.
* Steam.
* Gamescope.

## Ejecución desde código fuente

Para ejecutar directamente el programa en Python también son necesarios:

* Python 3.x.
* PyQt6.
* Módulo Python `vdf`.

## Funciones opcionales

Para utilizar las funciones relacionadas con MangoHud:

* MangoHud.

Para utilizar la vista previa del HUD debe existir además una aplicación Vulkan compatible utilizada por SteamCommandGen para mostrar la prueba.

Las versiones empaquetadas pueden incluir parte de las dependencias necesarias dependiendo del formato utilizado.

---

# 📋 Changelog

Puedes consultar el historial completo de cambios de **SteamCommandGen**, incluyendo las versiones 1.0.0, 2.0.0 y 3.2.5, en:

**[CHANGELOG.md](CHANGELOG.md)**

---

# 🚀 Releases

Las versiones oficiales y sus archivos descargables están disponibles en:

**[Releases](../../releases)**

---

# 📄 Licencia

Consulta el archivo **[LICENSE](https://github.com/neruk123-droid/SteamCommandGen/blob/main/LICENSE)** incluido en este repositorio para conocer las condiciones de uso y distribución del proyecto.
