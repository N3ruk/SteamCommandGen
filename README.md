# SteamCommandGen

SteamCommandGen es una herramienta gráfica para **Linux** diseñada para generar y gestionar opciones de lanzamiento de Steam utilizando **Gamescope**.

Permite configurar de forma sencilla y visual resoluciones, tecnologías de escalado, nitidez y diferentes parámetros de rendimiento, generando automáticamente las opciones de lanzamiento que pueden utilizarse con los juegos de Steam.

![SteamCommandGen Screenshot](assets/screenshots/main.png)

---

## ✨ Características

* 🎮 Detección automática de juegos y bibliotecas de Steam.
* ⚙️ Generación automática de comandos **Gamescope**.
* 🖥️ Interfaz gráfica desarrollada con **PyQt6**.
* 🔴 Soporte para **AMD FSR**.
* 🟢 Soporte para **NVIDIA NIS**.
* 🔵 Soporte para **NEAREST**.
* 🎚️ Control de nitidez para FSR y NIS.
* 🖥️ Resoluciones desde **450p hasta 4K**.
* 🌈 Soporte para **HDR**.
* ⚡ Soporte para **VRR / Adaptive Sync**.
* 🚀 Soporte para **Immediate Flips**.
* 🔧 Soporte para `WINEDLLOVERRIDES`.
* 🔄 Lectura y restauración de las **Steam LaunchOptions** existentes.
* 📋 Copiado de comandos al portapapeles.
* 🛠️ Aplicación y eliminación de LaunchOptions desde la aplicación.
* 🖼️ Carga de iconos y carátulas de los juegos.
* 📦 Disponible como **AppImage**, **paquete `.deb`** y **script instalador**.

---

## 🎮 Tecnologías de escalado

SteamCommandGen permite seleccionar entre diferentes tecnologías de escalado disponibles en Gamescope:

| Tecnología  | Descripción                          |
| ----------- | ------------------------------------ |
| **FSR**     | AMD FidelityFX Super Resolution      |
| **NIS**     | NVIDIA Image Scaling                 |
| **NEAREST** | Escalado mediante vecino más cercano |

Las tecnologías de escalado son mutuamente excluyentes y la aplicación genera automáticamente el parámetro correspondiente de Gamescope.

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

Descarga el `.zip` desde **Releases`, descomprímelo y ejecuta:

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

# 📋 Changelog

Puedes consultar todos los cambios y novedades de cada versión en:

**[CHANGELOG.md](CHANGELOG.md)**

---

# 🚀 Releases

Las versiones oficiales y sus archivos descargables están disponibles en:

**[Releases](../../releases)**

---

# 🛠️ Requisitos

* Linux
* Steam
* Gamescope
* Python 3.x para ejecutar el programa directamente desde el código fuente
* PyQt6

Las versiones empaquetadas como **AppImage** o **.deb** no requieren ejecutar manualmente el código Python.

---

# 📄 Licencia

Consulta el archivo **[License](https://github.com/neruk123-droid/SteamCommandGen/blob/main/LICENSE)** incluido en este repositorio para conocer las condiciones de uso y distribución del proyecto.
