# Changelog

Todos los cambios relevantes de **Steam Command Gen** quedan documentados en este archivo.

---

## [3.2.8] - 2026-09-26

* Corregido el crecimiento de la ventana tras cargar juegos y mostrar los controles de nitidez FSR/NIS. Las rutas largas y los títulos largos ya no fuerzan el tamaño de la ventana.
* Los controles y botones permanecen visibles dentro del área útil de 720p al cambiar de tecnología de reescalado, sin superposiciones.
* Notas de las releases en inglés primero y español después. Sin cambios en la generación de comandos.

---

## [3.2.7] - 2026-09-26

* La ventana se abre dentro del área útil del escritorio y cabe en resoluciones de 720p.
* Imágenes, botones y separaciones se adaptan al tamaño de la ventana; las acciones se distribuyen en dos filas cuando falta anchura, sin barras de desplazamiento.
* La lista de juegos deja de fijar la anchura de la ventana según el título más largo. Las carátulas conservan su proporción al redimensionar.
* Sin cambios en la lógica de los comandos ni en la instalación de Ubuntu y SteamOS.

---

## [3.2.6] - 2026-09-25

* Homogeneizado el archivo principal como `SteamCommandGen.py` y actualizados instalador, `.deb` y AppImage.
* AppImage reconstruido con Python 3.14 y Qt 6.11, igualando el entorno de la versión 3.2.5 que funcionaba en Ubuntu, pero incluyendo el intérprete en el paquete.
* Lanzador del `.deb` con `/usr/bin/steamcommandgen` absoluto y alias temporal para el comando de 3.2.5, que desaparecía al actualizar.
* Instalador SteamOS/Linux de usuario con entorno Python propio para PyQt6 y `vdf`, independiente del Python global. Genera un `.desktop` con ruta absoluta y resuelve sus archivos según la ubicación del script.
* Recursos gráficos accesibles desde el código fuente, instalaciones y AppImage; se corrigen los botones sin iconos.
* Nuevo proceso de empaquetado AppImage que incluye su intérprete Python; el anterior enlazaba con `/usr/bin/python3` del equipo y fallaba al importar `PyQt6.sip` si la versión difería.
* Nuevo empaquetado `.deb` con `vdf` incluido y PyQt6 como dependencia de Debian/Ubuntu.

---

## [3.2.5] - 2026-09-21

> Cambios acumulados desde **2.0.0**.  
> El historial de las versiones anteriores se conserva íntegramente más abajo.

### 🚀 Nuevas funcionalidades

#### 🥭 Integración de MangoHud

* Añadido soporte para activar MangoHud directamente desde SteamCommandGen mediante:

```text
--mangoapp
```

* Añadido un botón gráfico independiente para activar o desactivar MangoHud por juego.
* Añadido un **configurador gráfico de MangoHud** integrado en SteamCommandGen.
* SteamCommandGen puede leer y editar el archivo global:

```text
~/.config/MangoHud/MangoHud.conf
```

* Se añade una configuración predeterminada cuando todavía no existe `MangoHud.conf`.
* El editor permite activar o desactivar individualmente indicadores como:

  * FPS
  * Frametime
  * Uso de CPU
  * Uso de GPU
  * Temperatura de CPU
  * Temperatura de GPU
  * RAM
  * VRAM
  * Motor gráfico
  * Wine
  * Batería
  * Carga por núcleo
  * Frecuencia de GPU
  * Frecuencia de VRAM
  * Potencia de GPU
  * Potencia de CPU
  * Temperatura RAM
  * Resolución
  * Frecuencia de pantalla
  * Present mode
  * Red
  * GameMode
  * HDR
  * FSR

* Añadida selección de posición del HUD:

  * Arriba izquierda
  * Arriba derecha
  * Abajo izquierda
  * Abajo derecha

* Añadida selección de distribución:

  * Vertical
  * Horizontal

* Añadido ajuste fino de posición mediante desplazamiento horizontal y vertical.
* Añadidos controles direccionales para mover MangoHud en incrementos de 5 píxeles.
* Añadida personalización de color para:

  * FPS
  * Carga de GPU
  * Carga de CPU

* Añadida configuración de la combinación de teclas utilizada para mostrar u ocultar MangoHud.
* Se valida el formato de la combinación de teclas antes de guardar.
* Las opciones de `MangoHud.conf` que no están representadas en la interfaz se conservan al volver a guardar el archivo.

---

#### 👁️ Vista previa de MangoHud

* Añadido sistema de **vista previa en vivo** de la configuración de MangoHud.
* La vista previa utiliza `mangohud` junto con:

  * `vkcube`, si está disponible.
  * `pascube` como alternativa.

* Cuando se utiliza `vkcube`, la vista previa se abre a `1280x720` para disponer de espacio suficiente para configuraciones horizontales.
* Los cambios realizados desde el editor se aplican automáticamente a la configuración utilizada por la vista previa.
* SteamCommandGen captura los errores del proceso de vista previa y los muestra dentro del propio configurador.
* Al cerrar la vista previa, el proceso se termina de forma controlada.

---

#### 💾 Gestión segura de `MangoHud.conf`

* Añadida escritura atómica mediante `QSaveFile`.
* SteamCommandGen conserva una instantánea del archivo antes de comenzar a editarlo.
* Si se pulsa **Cancelar**, se restaura automáticamente el archivo anterior.
* Si el archivo no existía antes de abrir el editor, Cancelar elimina el archivo creado durante la edición.
* Añadido botón para crear manualmente:

```text
MangoHud.conf.bak
```

* Añadido botón para abrir directamente la carpeta que contiene `MangoHud.conf`.
* Se evita reescribir el archivo si el contenido generado no ha cambiado.
* La configuración global de MangoHud ya no se incrusta dentro de las `LaunchOptions`; MangoHud utiliza directamente su archivo de configuración.

---

### 🎮 Nuevo sistema visual de FSR / NIS / NEAREST

* Los antiguos checkbox de escalado han sido sustituidos por **botones gráficos dedicados**.
* Añadidos recursos visuales para:

  * FSR
  * NIS
  * NEAREST

* Los botones son seleccionables y reflejan visualmente el escalador activo.
* Se introduce el estado interno `scaling_mode` para controlar de forma centralizada la tecnología seleccionada.
* FSR, NIS y NEAREST continúan siendo mutuamente excluyentes.
* Añadida una función común para reiniciar completamente el estado del escalado.
* Los controles de nitidez solo aparecen cuando corresponden:

  * FSR muestra su slider.
  * NIS muestra su slider.
  * NEAREST no muestra slider.

---

### ⚙️ Cambios en la sintaxis de Gamescope

#### FSR

El comando generado pasa de:

```text
-F fsr --fsr-sharpness N
```

a:

```text
-F fsr --sharpness N
```

#### NIS

El comando generado pasa de:

```text
-F nis --nis-sharpness N
```

a:

```text
-F nis --sharpness N
```

* FSR y NIS utilizan ahora el mismo parámetro `--sharpness`.
* La generación utiliza una única cadena de decisión para evitar incluir más de un escalador a la vez.

---

### 🎚️ Nuevo comportamiento de nitidez

La interfaz mantiene un rango sencillo de `0–5`, pero SteamCommandGen lo convierte automáticamente al rango utilizado por `--sharpness`:

| Interfaz | Gamescope |
| ---: | ---: |
| 0 | 20 |
| 1 | 16 |
| 2 | 12 |
| 3 | 8 |
| 4 | 4 |
| 5 | 0 |

* FSR y NIS utilizan ahora la misma conversión.
* Eliminada la conversión antigua de NIS al rango `0.0–1.0`.
* Al cargar una configuración existente, el valor de `--sharpness` vuelve a convertirse automáticamente al valor correspondiente del slider.

---

### 🖥️ Interfaz gráfica renovada

* Añadido un estilo general inspirado en la interfaz de Steam.
* Nueva paleta oscura basada en tonos azul oscuro.
* Rediseñados visualmente:

  * Ventana principal
  * Paneles
  * `QGroupBox`
  * `QComboBox`
  * `QLineEdit`
  * `QPlainTextEdit`
  * `QListWidget`
  * `QCheckBox`
  * `QSlider`

* Añadidos estados visuales de selección para los botones de escalado.
* Añadido botón gráfico dedicado a MangoHud.
* Añadido botón independiente para abrir la configuración de MangoHud.
* Si el recurso gráfico del botón de configuración de MangoHud no está instalado, SteamCommandGen puede generar un icono alternativo mediante Qt.
* Se reorganizan y agrupan mejor las opciones de escalado, pantalla y MangoHud.

---

### 🖥️ Selección de resolución mejorada

* Las resoluciones base y de salida ya no comienzan con una resolución real seleccionada automáticamente.
* Los dos desplegables comienzan ahora en:

```text
Seleccionar resolución...
```

* El usuario debe elegir explícitamente:

  * Resolución base.
  * Resolución de salida.

* SteamCommandGen impide generar o aplicar el comando si falta alguna de las dos resoluciones.
* Se muestran avisos específicos indicando qué resolución falta.
* Se evita así generar accidentalmente un comando utilizando la resolución mínima por defecto.

---

### ⚡ Escaneo de Steam optimizado

#### Búsqueda de manifiestos `.acf`

* Eliminado el recorrido recursivo de toda la carpeta `steamapps`.
* Los manifiestos se buscan ahora directamente mediante `os.scandir()`.
* Esto evita recorrer innecesariamente directorios como:

  * `compatdata`
  * `shadercache`
  * contenido interno de los juegos

* El cambio reduce considerablemente el trabajo realizado al escanear bibliotecas grandes.

#### Escaneo en segundo hilo

* Añadido `GameScanWorker`.
* El escaneo de juegos se ejecuta fuera del hilo principal mediante `QThread`.
* La interfaz permanece disponible mientras SteamCommandGen analiza las bibliotecas.
* Durante el escaneo:

  * El botón **Buscar juegos** se desactiva.
  * El texto cambia temporalmente a `Buscando…`.

* Al finalizar se restaura automáticamente el estado del botón.
* Añadido manejo independiente de errores producidos durante el escaneo.

---

### 🧹 Filtrado de aplicaciones que no son juegos

SteamCommandGen deja de mostrar como juegos determinadas herramientas internas de Steam.

Se filtran automáticamente nombres que contienen:

```text
proton
steam linux runtime
lossless scaling
steamworks common redistributables
```

Esto reduce el ruido en la lista de títulos detectados.

---

### 🔍 Mejoras en la detección de juegos

* Se valida que cada entrada tenga:

  * AppID.
  * Nombre.
  * Directorio de instalación.

* Los AppID ya detectados se almacenan en un `set`, evitando duplicados de forma más eficiente.
* Los juegos se ordenan alfabéticamente antes de mostrarse.
* La lista muestra directamente el nombre del juego.
* El ancho de la lista se calcula automáticamente a partir del nombre más largo.
* Se establece un límite mínimo y máximo para evitar que la interfaz quede demasiado estrecha o demasiado ancha.

---

### 🛡️ Detección de ejecutables más robusta

* Se mantiene el comportamiento de seleccionar el `.exe` o `.sh` de mayor tamaño situado en el directorio raíz del juego.
* Añadido control de errores al listar el directorio.
* Añadido control de errores al consultar el tamaño de cada archivo.
* Un archivo inaccesible ya no interrumpe necesariamente el escaneo completo.

---

### 📚 Mejoras en la gestión de bibliotecas y usuarios de Steam

* Validación más estricta de las entradas de `libraryfolders.vdf`.
* Las entradas que no sean diccionarios válidos se ignoran.
* Las entradas sin ruta se ignoran.
* La biblioteca principal de Steam continúa añadiéndose automáticamente.
* Se mantiene la prevención de bibliotecas duplicadas.
* Los directorios numéricos de `userdata` se ordenan antes de buscar `localconfig.vdf`.
* Se mantiene un sistema de fallback para localizar la configuración cuando la ruta inicialmente detectada no existe.

---

### 🧩 Refactorización de `localconfig.vdf`

* Añadida la función:

```python
get_steam_apps_dict()
```

* Esta función centraliza el acceso a:

```text
UserLocalConfigStore
└── Software
    └── Valve
        └── Steam
            └── apps
```

* Se reduce la duplicación entre:

  * Escritura de `LaunchOptions`.
  * Borrado de `LaunchOptions`.
  * Lectura de `LaunchOptions`.

---

### 🧠 Parser de LaunchOptions actualizado

El parser reconoce ahora la sintaxis utilizada por la versión actual:

```text
-F fsr
-F nis
-F nearest
--sharpness
--hdr-enabled
--adaptive-sync
--immediate-flips
--mangoapp
WINEDLLOVERRIDES
```

También continúa restaurando:

```text
-w
-h
-W
-H
```

#### `WINEDLLOVERRIDES`

* Se amplía la detección para aceptar valores:

  * Entre comillas dobles.
  * Entre comillas simples.
  * Sin comillas.

* Al generar un nuevo comando se utiliza `shlex.quote()` para escapar el valor de forma más segura.

---

### 🔄 Restauración y aislamiento de la configuración de cada juego

Al seleccionar un juego, SteamCommandGen reinicia primero el estado de la interfaz antes de cargar sus `LaunchOptions`.

Se reinician:

* Resolución base.
* Resolución de salida.
* FSR.
* NIS.
* NEAREST.
* Sliders de nitidez.
* HDR.
* VRR.
* Immediate Flips.
* MangoHud.
* `WINEDLLOVERRIDES`.

Después se analiza la configuración del juego seleccionado y se restauran únicamente las opciones encontradas.

Esto evita arrastrar opciones visuales pertenecientes al juego seleccionado anteriormente.

---

### 🧹 Mejoras en “Limpiar propiedades”

Después de borrar las `LaunchOptions`, SteamCommandGen también reinicia la configuración mostrada en la interfaz:

* Resolución base.
* Resolución de salida.
* Escalado.
* Nitidez.
* HDR.
* VRR.
* Immediate Flips.
* MangoHud.
* `WINEDLLOVERRIDES`.

---

### 🌐 Mejoras en la carga de imágenes

* Se mantiene una única instancia compartida de `QNetworkAccessManager`.
* Añadido manejo explícito de `QNetworkReply`.
* Se comprueba que la imagen recibida pueda convertirse correctamente en `QPixmap`.
* La imagen principal del juego utiliza escalado suave.
* Antes de asignar una cápsula descargada se comprueba que el elemento continúe perteneciendo a la lista.

---

### 🔁 VRR e Immediate Flips

* VRR e Immediate Flips continúan siendo mutuamente excluyentes.
* Durante la desactivación automática de la opción incompatible se bloquean temporalmente las señales de Qt.
* Esto evita ejecutar callbacks innecesarios mientras la aplicación sincroniza los controles.

---

### 🧯 Cierre de Steam más preciso

El cierre de Steam cambia de:

```text
pkill -f steam
```

a:

```text
pkill -x steam
```

* Se utiliza ahora una coincidencia exacta del nombre del proceso.
* Se reduce el riesgo de terminar accidentalmente otros procesos cuyo comando simplemente contenga la palabra `steam`.
* La ejecución se realiza mediante `subprocess.run()` y mantiene manejo explícito de errores.

---

### 🛠️ Mejoras internas

* Añadido `shlex` para construir de forma más segura variables de entorno incluidas en las Launch Options.
* Añadido `shutil` para localizar ejecutables y gestionar la copia de seguridad de MangoHud.
* Añadido uso explícito de `QNetworkReply`.
* Añadidas rutas centralizadas para recursos gráficos:

```text
/usr/local/share/SteamCommandGen/scaling
/usr/local/share/SteamCommandGen/BOTONES
```

* Añadida separación más clara entre:

  * Detección de Steam.
  * Bibliotecas.
  * Manifiestos `.acf`.
  * Juegos.
  * Gestión de `localconfig.vdf`.
  * Generación de comandos.
  * Configuración de MangoHud.
  * Escaneo en segundo hilo.
  * Interfaz.
  * Restauración de configuraciones.

* Añadido manejo de más errores de sistema de archivos.
* Reducida la duplicación de código.
* Mejor sincronización entre el estado interno y los controles gráficos.

---

### 🐛 Correcciones

* Corregida la sintaxis de nitidez de FSR y NIS para utilizar `--sharpness`.
* Eliminada la conversión antigua de NIS al rango `0.0–1.0`.
* Evitado que los desplegables de resolución seleccionen automáticamente la resolución mínima.
* Evitado que la configuración del juego anterior permanezca activa al seleccionar otro.
* Mejorado el aislamiento entre FSR, NIS y NEAREST.
* Evitados callbacks innecesarios al cambiar entre VRR e Immediate Flips.
* Reducidos bloqueos de interfaz durante el escaneo de bibliotecas.
* Evitado el recorrido recursivo innecesario de `steamapps`.
* Filtradas herramientas de Steam que anteriormente podían aparecer mezcladas con los juegos.
* Mejorado el tratamiento de rutas y archivos inaccesibles durante el escaneo.
* Mejorado el tratamiento de `WINEDLLOVERRIDES`.
* Mejorado el cierre de Steam para utilizar una coincidencia exacta del proceso.
* Añadida restauración segura de `MangoHud.conf` cuando se cancela una edición.

---

### ⚠️ Notas de actualización desde 2.0.0

* Las configuraciones nuevas de FSR y NIS utilizan:

```text
--sharpness
```

en lugar de:

```text
--fsr-sharpness
--nis-sharpness
```

* NIS deja de utilizar la conversión de interfaz `0–5` → `0.0–1.0` documentada en 2.0.0.
* Las resoluciones deben seleccionarse explícitamente antes de generar un comando.
* MangoHud puede activarse mediante `--mangoapp` y configurarse desde la propia aplicación.
* El histórico de 2.0.0 y 1.0.0 se conserva a continuación para documentar el comportamiento de esas versiones.

---

### 📌 Resumen de 3.2.5

La versión **3.2.5** amplía considerablemente SteamCommandGen respecto a 2.0.0.

Las principales incorporaciones son:

```text
Interfaz gráfica renovada
Botones gráficos FSR / NIS / NEAREST
FSR/NIS mediante --sharpness
Integración --mangoapp
Configurador gráfico de MangoHud
Vista previa de MangoHud en vivo
Gestión segura de MangoHud.conf
Escaneo de Steam mediante QThread
Escaneo directo de manifiestos .acf
Filtrado de herramientas que no son juegos
Selección explícita de resoluciones
Parser de LaunchOptions actualizado
Mejor restauración del estado por juego
Cierre de Steam más preciso
```

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
