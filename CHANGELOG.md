# Changelog

Todos los cambios relevantes de **Steam Command Gen** quedan documentados en este archivo.

---

## [2.0.0] - 2026-09-14

### 🚀 Nuevas funcionalidades

* Añadido soporte para **tres tecnologías de escalado de Gamescope**:

  * **FSR**
  * **NIS**
  * **NEAREST**
* Las tecnologías de escalado son **mutuamente excluyentes**, evitando generar comandos con varias tecnologías activas simultáneamente.
* Añadidos controles independientes de nitidez para:

  * FSR
  * NIS
* Añadido soporte para detectar automáticamente la tecnología de escalado utilizada en las `LaunchOptions` existentes.
* Añadida restauración automática de la configuración detectada al seleccionar un juego.
* Añadidas nuevas resoluciones:

  * 450p — `800x450`
  * 576p — `1024x576`
  * 720p — `1280x720`
  * 900p — `1600x900`
  * 1080p — `1920x1080`
  * 1440p — `2560x1440`
  * 4K — `3840x2160`
* Las resoluciones de entrada y salida utilizan ahora el mismo conjunto de opciones.
* Añadido soporte para `--nis-sharpness`.
* Añadida gestión específica del estado de los sliders de FSR y NIS.
* Añadida detección y restauración de:

  * FSR
  * NIS
  * NEAREST
  * HDR
  * VRR
  * Immediate Flips
  * `WINEDLLOVERRIDES`

---

### 🔧 Cambios

#### Escalado Gamescope

En V1 FSR estaba activado automáticamente en todos los comandos generados.

En V2 el escalado se genera únicamente cuando el usuario lo selecciona:

```text
-F fsr
-F nis
-F nearest
```

Esto permite generar comandos sin escalado o utilizar cualquiera de las tres tecnologías disponibles.

---

#### FSR

* FSR ya no está activado por defecto.
* El slider de FSR permanece desactivado hasta activar FSR.
* El rango del slider continúa siendo de `0` a `5`.
* Se mantiene la conversión del valor del slider al parámetro `--fsr-sharpness` de Gamescope.

---

#### NIS

* Añadido nuevo slider de nitidez NIS.
* Rango de interfaz: `0–5`.
* El valor de la interfaz se convierte al rango utilizado por Gamescope (`0.0–1.0`).
* El slider permanece desactivado hasta activar NIS.

---

#### NEAREST

* Añadido soporte para:

```text
-F nearest
```

* No requiere slider de nitidez.
* Se desactiva automáticamente FSR y NIS cuando NEAREST es seleccionado.

---

### 🖥️ Interfaz gráfica

* Añadidos controles independientes para seleccionar:

  * `Activar FSR`
  * `Activar NIS`
  * `Activar NEAREST`
* Los controles de escalado son mutuamente excluyentes.
* Los sliders asociados se activan y desactivan automáticamente según la tecnología seleccionada.
* Añadida exclusión mutua entre:

  * VRR
  * Immediate Flips
* Immediate Flips deja de estar activado por defecto.
* La interfaz ahora refleja correctamente las opciones encontradas en las `LaunchOptions` existentes.
* Al no seleccionar ningún juego, el campo de comando se limpia automáticamente.
* Después de aplicar correctamente un comando, este se muestra inmediatamente en la interfaz.

---

### 🛠️ Mejoras en Steam

* Centralizada la búsqueda de `localconfig.vdf`.
* Añadidas las funciones:

  * `find_localconfig()`
  * `load_localconfig()`
* Eliminada la duplicación de código utilizada anteriormente para localizar `localconfig.vdf`.
* Mejorada la detección de las bibliotecas de Steam.
* Las bibliotecas duplicadas se eliminan automáticamente.
* Se comprueba que las rutas existan antes de procesarlas.

---

### 🧩 Mejoras en lectura de archivos VDF

Se ha mejorado la tolerancia ante archivos VDF corruptos o que no puedan ser leídos.

Ahora se gestionan errores al procesar:

* `libraryfolders.vdf`
* Archivos `.acf`
* `localconfig.vdf`

Los juegos cuyo archivo `.acf` no pueda procesarse correctamente se ignoran en lugar de provocar un error en toda la aplicación.

---

### 🔍 Mejoras en la detección de juegos

* Se mantienen las búsquedas recursivas de archivos `.acf`.
* Se ignoran automáticamente entradas inválidas.
* Se evita añadir varias veces el mismo juego mediante su AppID.
* Se mantiene la detección del ejecutable de mayor tamaño dentro del directorio del juego.

---

### 🌐 Mejoras de red

Se sustituye la creación de múltiples instancias de `QNetworkAccessManager` por una única instancia compartida:

```python
self.network_manager
```

Esto permite centralizar las peticiones utilizadas para cargar:

* Iconos de juegos.
* Imágenes.
* Carátulas.

---

### 🧠 Mejoras en el procesamiento de LaunchOptions

El parser de Gamescope ha sido ampliado para reconocer:

```text
-F fsr
--fsr-sharpness

-F nis
--nis-sharpness

-F nearest
```

También mantiene el reconocimiento de:

```text
-W
-H
-w
-h
-HDR
--hdr-enabled
--immediate-flips
--adaptive-sync
WINEDLLOVERRIDES
```

La configuración detectada se transforma posteriormente en el estado correspondiente de la interfaz gráfica.

---

### 🛡️ Robustez

Se han añadido comprobaciones adicionales para evitar errores cuando:

* No existe una biblioteca de Steam.
* Una biblioteca no es accesible.
* Un archivo VDF está corrupto.
* No existe `localconfig.vdf`.
* Un juego tiene información incompleta.
* Una resolución no puede ser determinada.
* Steam no puede cerrarse mediante `pkill`.

También se han añadido comprobaciones para evitar errores al restaurar valores de resolución o sliders.

---

### ⚙️ Mejoras internas

* Añadido `re` como dependencia de la biblioteca estándar.
* `subprocess` pasa a importarse a nivel global.
* Mejorada la organización interna del código.
* Separación más clara entre:

  * Detección de Steam.
  * Detección de bibliotecas.
  * Lectura de juegos.
  * Gestión de `localconfig.vdf`.
  * Generación de comandos.
  * Análisis de comandos.
  * Interfaz gráfica.

---

### 🐛 Correcciones

Se corrigen o reducen varios problemas presentes en V1:

* Búsqueda duplicada de `localconfig.vdf`.
* Errores al leer archivos VDF defectuosos.
* Posibles `KeyError` al analizar `LaunchOptions`.
* Restauración incorrecta o incompleta de los controles de escalado.
* Falta de exclusión entre FSR, NIS y NEAREST.
* Falta de exclusión entre VRR e Immediate Flips.
* El comando mostrado en pantalla no se actualizaba inmediatamente después de aplicar la configuración.
* Posibles errores al trabajar con resoluciones inexistentes.
* Creación repetida de `QNetworkAccessManager`.
* Falta de control de errores al cerrar Steam.

---

## [1.0.0]

### Funcionalidades principales

* Detección automática de Steam.
* Detección de bibliotecas de Steam.
* Escaneo automático de juegos instalados.
* Lectura de archivos `.acf`.
* Detección de ejecutables.
* Carga de iconos y carátulas.
* Generación de comandos Gamescope.
* Selección de resolución de entrada.
* Selección de resolución de salida.
* Soporte para FSR.
* Control de nitidez FSR.
* Soporte para HDR.
* Soporte para VRR.
* Soporte para Immediate Flips.
* Soporte para `WINEDLLOVERRIDES`.
* Lectura de las `LaunchOptions` actuales de Steam.
* Restauración de la configuración existente en la interfaz.
* Aplicación de `LaunchOptions`.
* Eliminación de `LaunchOptions`.
* Copiado de comandos al portapapeles.
* Cierre de Steam desde la aplicación.
* Integración como aplicación de escritorio Linux mediante PyQt6.

---

## 📌 Resumen de V2.0.0

La versión **2.0.0** supone una ampliación importante respecto a V1.

Las principales novedades son:

**V1**

```text
FSR
HDR
VRR
Immediate Flips
WINEDLLOVERRIDES
```

**V2**

```text
FSR
NIS
NEAREST
HDR
VRR
Immediate Flips
WINEDLLOVERRIDES
```

Además, V2 mejora considerablemente la gestión de Steam, la lectura de configuraciones existentes, la gestión de errores y la sincronización entre las `LaunchOptions` y la interfaz gráfica.

---

## ⚠️ Notas de actualización

* Las configuraciones existentes con FSR pueden seguir siendo detectadas por V2.
* V2 ya no activa FSR automáticamente al generar un comando.
* El usuario debe seleccionar explícitamente la tecnología de escalado que desea utilizar.
* VRR e Immediate Flips son ahora opciones mutuamente excluyentes.
* No se introduce ningún paso específico de migración de datos en el código de V2.
