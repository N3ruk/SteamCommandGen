#!/usr/bin/env python3

import os
import sys
import re
import subprocess
import vdf

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest


# ============================================================
# DETECCIÓN DE STEAM
# ============================================================

def detect_steam_paths():
    candidates = [
        os.path.expanduser("~/.steam/steam"),
        os.path.expanduser("~/.local/share/Steam"),
    ]

    for base in candidates:
        if not os.path.isdir(base):
            continue

        userdata = os.path.join(base, "userdata")

        if not os.path.isdir(userdata):
            continue

        users = [u for u in os.listdir(userdata) if u.isdigit()]
        steamid = users[0] if users else "0"

        return {
            "root": base,
            "steamapps": os.path.join(base, "steamapps"),
            "libraryfolders": os.path.join(
                base,
                "steamapps",
                "libraryfolders.vdf"
            ),
            "localconfig": os.path.join(
                base,
                "userdata",
                steamid,
                "config",
                "localconfig.vdf"
            ),
        }

    return None


STEAM = detect_steam_paths()

if STEAM is None:
    print("No se encontró Steam.")
    sys.exit(1)


# ============================================================
# ESCANEO DE BIBLIOTECAS Y JUEGOS
# ============================================================

def get_libraries():
    libs = []
    lf_path = STEAM["libraryfolders"]

    # Si no existe libraryfolders.vdf, utilizar la biblioteca
    # principal de Steam.
    if not os.path.isfile(lf_path):
        return [STEAM["steamapps"]]

    try:
        with open(
            lf_path,
            encoding="utf-8",
            errors="ignore"
        ) as f:
            data = vdf.load(f)
    except Exception:
        return [STEAM["steamapps"]]

    lf = data.get("libraryfolders", {})

    for value in lf.values():
        if isinstance(value, dict) and "path" in value:
            steamapps = os.path.join(
                value["path"],
                "steamapps"
            )

            if steamapps not in libs:
                libs.append(steamapps)

    # Asegurar que la biblioteca principal siempre está incluida.
    if STEAM["steamapps"] not in libs:
        libs.append(STEAM["steamapps"])

    return libs


def find_acf_files(path):
    acf_list = []

    if not os.path.isdir(path):
        return acf_list

    for root, dirs, files in os.walk(path):
        for filename in files:
            if filename.endswith(".acf"):
                acf_list.append(os.path.join(root, filename))

    return acf_list


def parse_acf(path):
    try:
        with open(
            path,
            encoding="utf-8",
            errors="ignore"
        ) as f:
            data = vdf.load(f)
    except Exception:
        return None

    app = data.get("AppState", {})

    return {
        "appid": app.get("appid"),
        "name": app.get("name"),
        "install_dir": app.get("installdir"),
        "acf_path": path,
    }


def find_executables(game_dir):
    """
    Busca ejecutables en el directorio raíz del juego.

    Se mantiene el comportamiento original:
    devuelve únicamente el ejecutable de mayor tamaño.
    """

    if not os.path.isdir(game_dir):
        return []

    exes = []

    for filename in os.listdir(game_dir):
        full = os.path.join(game_dir, filename)

        if (
            os.path.isfile(full)
            and filename.lower().endswith((".exe", ".sh"))
        ):
            exes.append(full)

    if not exes:
        return []

    exes.sort(
        key=lambda path: os.path.getsize(path),
        reverse=True
    )

    return [exes[0]]


def scan_games():
    games = []

    for lib in get_libraries():
        for acf in find_acf_files(lib):

            info = parse_acf(acf)

            if not info:
                continue

            if not info["install_dir"]:
                continue

            game_dir = os.path.join(
                lib,
                "common",
                info["install_dir"]
            )

            info["game_dir"] = game_dir
            info["executables"] = find_executables(game_dir)

            # Evitar juegos duplicados entre bibliotecas.
            if not any(
                game["appid"] == info["appid"]
                for game in games
            ):
                games.append(info)

    return games


# ============================================================
# LOCALCONFIG DE STEAM
# ============================================================

def find_localconfig():
    """
    Localiza el localconfig.vdf del usuario de Steam.

    Se mantiene independiente de detect_steam_paths()
    para poder utilizarla también si existen varias
    bibliotecas o configuraciones.
    """

    bases = [
        os.path.expanduser("~/.steam/steam/userdata"),
        os.path.expanduser("~/.local/share/Steam/userdata"),
    ]

    # Primero intentar utilizar la configuración detectada.
    detected = STEAM.get("localconfig")

    if detected and os.path.isfile(detected):
        return detected

    # Fallback: buscar entre los usuarios de Steam.
    for base in bases:

        if not os.path.isdir(base):
            continue

        for user in os.listdir(base):

            if not user.isdigit():
                continue

            path = os.path.join(
                base,
                user,
                "config",
                "localconfig.vdf"
            )

            if os.path.isfile(path):
                return path

    return None


def load_localconfig():
    cfg_path = find_localconfig()

    if not cfg_path:
        raise FileNotFoundError(
            "No se encontró localconfig.vdf"
        )

    with open(
        cfg_path,
        encoding="utf-8",
        errors="ignore"
    ) as f:
        data = vdf.load(f)

    return cfg_path, data


# ============================================================
# GENERADOR DE COMANDO GAMESCOPE
# ============================================================

def build_gamescope_command(opts):
    cmd = [
        "gamescope",
        f"-w {opts['res_w']}",
        f"-h {opts['res_h']}",
        f"-W {opts['out_w']}",
        f"-H {opts['out_h']}",
    ]

    if opts["hdr"]:
        cmd.append("--hdr-enabled")

    if opts["vrr"]:
        cmd.append("--adaptive-sync")

    if opts["immediate"]:
        cmd.append("--immediate-flips")

    if opts.get("fsr_enabled"):
        cmd.append("-F fsr")
        cmd.append(
            f"--fsr-sharpness {opts['sharpness']}"
        )

    if opts.get("nis_enabled"):
        cmd.append("-F nis")
        cmd.append(
            f"--nis-sharpness {opts['nis_sharpness']}"
        )

    if opts.get("nearest_enabled"):
        cmd.append("-F nearest")

    cmd.append("-f")
    cmd.append("-- %command%")

    final = " ".join(cmd)

    if opts["winedll"]:
        return (
            f'WINEDLLOVERRIDES="{opts["winedll"]}" '
            f"{final}"
        )

    return final


# ============================================================
# ESCRITURA DE LAUNCH OPTIONS
# ============================================================

def write_launch_options(appid, cmd):
    cfg_path, data = load_localconfig()

    ulcs = data.setdefault(
        "UserLocalConfigStore",
        {}
    )

    software = ulcs.setdefault(
        "Software",
        {}
    )

    valve = software.setdefault(
        "Valve",
        {}
    )

    steam = valve.setdefault(
        "Steam",
        {}
    )

    apps = steam.setdefault(
        "apps",
        {}
    )

    apps.setdefault(str(appid), {})[
        "LaunchOptions"
    ] = cmd

    with open(
        cfg_path,
        "w",
        encoding="utf-8",
        errors="ignore"
    ) as f:
        vdf.dump(data, f, pretty=False)


# ============================================================
# BORRADO DE LAUNCH OPTIONS
# ============================================================

def clear_launch_options(appid):
    cfg_path, data = load_localconfig()

    ulcs = data.setdefault(
        "UserLocalConfigStore",
        {}
    )

    software = ulcs.setdefault(
        "Software",
        {}
    )

    valve = software.setdefault(
        "Valve",
        {}
    )

    steam = valve.setdefault(
        "Steam",
        {}
    )

    apps = steam.setdefault(
        "apps",
        {}
    )

    # Dejar LaunchOptions vacío.
    apps.setdefault(str(appid), {})[
        "LaunchOptions"
    ] = ""

    with open(
        cfg_path,
        "w",
        encoding="utf-8",
        errors="ignore"
    ) as f:
        vdf.dump(data, f, pretty=False)


# ============================================================
# OBTENER LAUNCH OPTIONS ACTUALES
# ============================================================

def get_active_launch_options(appid):
    cfg_path = find_localconfig()

    if not cfg_path:
        return ""

    try:
        with open(
            cfg_path,
            encoding="utf-8",
            errors="ignore"
        ) as f:
            data = vdf.load(f)
    except Exception:
        return ""

    ulcs = data.get(
        "UserLocalConfigStore",
        {}
    )

    software = ulcs.get(
        "Software",
        {}
    )

    valve = software.get(
        "Valve",
        {}
    )

    steam = valve.get(
        "Steam",
        {}
    )

    apps = steam.get(
        "apps",
        {}
    )

    return apps.get(
        str(appid),
        {}
    ).get(
        "LaunchOptions",
        ""
    )


# ============================================================
# GUI PRINCIPAL
# ============================================================

class GamescopeManager(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        # ====================================================
        # CONFIGURACIÓN DE VENTANA
        # ====================================================

        app_icon = QtGui.QIcon.fromTheme(
            "SteamCommandGen"
        )

        self.setWindowIcon(app_icon)
        self.resize(1200, 700)

        self.games = []
        self.current_game = None

        # Un único gestor de red para toda la aplicación.
        self.network_manager = QNetworkAccessManager(self)

        # ====================================================
        # LISTA DE JUEGOS
        # ====================================================

        self.game_list = QtWidgets.QListWidget()
        self.game_list.setIconSize(
            QtCore.QSize(120, 45)
        )

        # ====================================================
        # IMAGEN DEL JUEGO
        # ====================================================

        self.img_label = QtWidgets.QLabel()
        self.img_label.setFixedHeight(200)
        self.img_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignCenter
        )

        # ====================================================
        # PANEL DE OPCIONES
        # ====================================================

        self.details_widget = QtWidgets.QWidget()

        self.details_layout = QtWidgets.QFormLayout(
            self.details_widget
        )

        # ====================================================
        # RESOLUCIONES
        # ====================================================

        resolutions = {
            "450p (800x450)": (800, 450),
            "576p (1024x576)": (1024, 576),
            "720p (1280x720)": (1280, 720),
            "900p (1600x900)": (1600, 900),
            "1080p (1920x1080)": (1920, 1080),
            "1440p (2560x1440)": (2560, 1440),
            "4K (3840x2160)": (3840, 2160),
        }

        self.base_res_combo = QtWidgets.QComboBox()

        for label, res in resolutions.items():
            self.base_res_combo.addItem(
                label,
                res
            )

        self.out_res_combo = QtWidgets.QComboBox()

        for label, res in resolutions.items():
            self.out_res_combo.addItem(
                label,
                res
            )

        # ====================================================
        # SLIDER FSR
        # ====================================================

        self.sharpness_slider = QtWidgets.QSlider(
            QtCore.Qt.Orientation.Horizontal
        )

        self.sharpness_slider.setRange(0, 5)
        self.sharpness_slider.setValue(0)
        self.sharpness_slider.setTickInterval(1)
        self.sharpness_slider.setTickPosition(
            QtWidgets.QSlider.TickPosition.TicksBelow
        )

        self.sharpness_slider.setEnabled(False)

        self.sharpness_slider.setStyleSheet("""
        QSlider::groove:horizontal:disabled {
            background: #2a2a2a;
        }
        """)

        self.sharpness_label = QtWidgets.QLabel("0")

        self.sharpness_slider.valueChanged.connect(
            lambda value:
            self.sharpness_label.setText(
                str(value)
            )
        )

        sharpness_box = QtWidgets.QHBoxLayout()
        sharpness_box.addWidget(
            self.sharpness_slider
        )
        sharpness_box.addWidget(
            self.sharpness_label
        )

        # ====================================================
        # SLIDER NIS
        # ====================================================

        self.nis_slider = QtWidgets.QSlider(
            QtCore.Qt.Orientation.Horizontal
        )

        self.nis_slider.setRange(0, 5)
        self.nis_slider.setValue(0)
        self.nis_slider.setTickInterval(1)
        self.nis_slider.setTickPosition(
            QtWidgets.QSlider.TickPosition.TicksBelow
        )

        self.nis_slider.setEnabled(False)

        self.nis_slider.setStyleSheet("""
        QSlider::groove:horizontal:disabled {
            background: #2a2a2a;
        }
        """)

        self.nis_label = QtWidgets.QLabel("0")

        self.nis_slider.valueChanged.connect(
            lambda value:
            self.nis_label.setText(
                str(value)
            )
        )

        nis_box = QtWidgets.QHBoxLayout()
        nis_box.addWidget(
            self.nis_slider
        )
        nis_box.addWidget(
            self.nis_label
        )

        # ====================================================
        # WINEDLLOVERRIDES
        # ====================================================

        self.txt_winedll = QtWidgets.QLineEdit()

        self.txt_winedll.setPlaceholderText(
            "WINEDLLOVERRIDES= (opcional)"
        )

        self.details_layout.addRow(
            "WINEDLLOVERRIDES:",
            self.txt_winedll
        )

        # ====================================================
        # CHECKBOXES
        # ====================================================

        self.chk_fsr = QtWidgets.QCheckBox(
            "Activar FSR"
        )

        self.chk_fsr.setChecked(False)

        self.chk_nis = QtWidgets.QCheckBox(
            "Activar NIS"
        )

        self.chk_nis.setChecked(False)

        self.chk_nearest = QtWidgets.QCheckBox(
            "Activar NEAREST"
        )

        self.chk_nearest.setChecked(False)

        self.chk_hdr = QtWidgets.QCheckBox(
            "HDR"
        )

        self.chk_vrr = QtWidgets.QCheckBox(
            "VRR (Adaptive Sync)"
        )

        self.chk_immediate = QtWidgets.QCheckBox(
            "Modo Baja Latencia"
        )

        # VRR y modo baja latencia son incompatibles.
        self.chk_vrr.stateChanged.connect(
            self.vrr_changed
        )

        self.chk_immediate.stateChanged.connect(
            self.immediate_changed
        )

        # FSR, NIS y NEAREST son mutuamente excluyentes.
        self.chk_fsr.stateChanged.connect(
            self.fsr_changed
        )

        self.chk_nis.stateChanged.connect(
            self.nis_changed
        )

        self.chk_nearest.stateChanged.connect(
            self.nearest_changed
        )

        # ====================================================
        # RUTA DEL JUEGO
        # ====================================================

        self.lbl_game_dir = QtWidgets.QLabel("")

        # ====================================================
        # EJECUTABLES
        # ====================================================

        self.exec_list = QtWidgets.QListWidget()

        # ====================================================
        # COMANDO GENERADO
        # ====================================================

        self.cmd_text = QtWidgets.QPlainTextEdit()
        self.cmd_text.setReadOnly(True)

        # ====================================================
        # BOTONES
        # ====================================================

        self.btn_scan = QtWidgets.QPushButton(
            "Buscar juegos"
        )

        self.btn_scan.setStyleSheet("""
            QPushButton {
                background-color: #E67E22;
                color: black;
                padding: 8px;
                border-radius: 10px;
            }

            QPushButton:hover {
                background-color: #F39C12;
            }
        """)

        self.btn_preview = QtWidgets.QPushButton(
            "Generar comando"
        )

        self.btn_preview.setStyleSheet("""
            QPushButton {
                background-color: #1E90FF;
                color: black;
                padding: 8px;
                border-radius: 10px;
            }

            QPushButton:hover {
                background-color: #3AA0FF;
            }
        """)

        self.btn_copy = QtWidgets.QPushButton(
            "Copiar comando"
        )

        self.btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #F1C40F;
                color: black;
                padding: 8px;
                border-radius: 10px;
            }

            QPushButton:hover {
                background-color: #F4D03F;
            }
        """)

        self.btn_apply = QtWidgets.QPushButton(
            "Aplicar a Steam"
        )

        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: black;
                padding: 8px;
                border-radius: 10px;
            }

            QPushButton:hover {
                background-color: #2ECC71;
            }
        """)

        self.btn_clear = QtWidgets.QPushButton(
            "Limpiar Propiedades"
        )

        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #C0392B;
                color: black;
                padding: 8px;
                border-radius: 10px;
            }

            QPushButton:hover {
                background-color: #E74C3C;
            }
        """)

        self.btn_kill_steam = QtWidgets.QPushButton(
            "Cerrar Steam"
        )

        self.btn_kill_steam.setStyleSheet("""
            QPushButton {
                background-color: #000000;
                color: white;
                padding: 8px;
                border-radius: 10px;
            }

            QPushButton:hover {
                background-color: #1A1A1A;
            }
        """)

        # ====================================================
        # LAYOUT PRINCIPAL
        # ====================================================

        main_widget = QtWidgets.QWidget()

        main_layout = QtWidgets.QHBoxLayout(
            main_widget
        )

        # ----------------------------------------------------
        # IZQUIERDA
        # ----------------------------------------------------

        left = QtWidgets.QVBoxLayout()

        left.addWidget(
            QtWidgets.QLabel("Juegos detectados")
        )

        left.addWidget(
            self.game_list
        )

        left.addWidget(
            self.btn_scan
        )

        # ----------------------------------------------------
        # DERECHA
        # ----------------------------------------------------

        right = QtWidgets.QVBoxLayout()

        right.addWidget(
            QtWidgets.QLabel("Imagen del juego")
        )

        right.addWidget(
            self.img_label
        )

        right.addWidget(
            QtWidgets.QLabel("Configuración")
        )

        right.addWidget(
            self.details_widget
        )

        right.addWidget(
            QtWidgets.QLabel("Ruta del juego")
        )

        right.addWidget(
            self.lbl_game_dir
        )

        right.addWidget(
            QtWidgets.QLabel("Ejecutables")
        )

        right.addWidget(
            self.exec_list
        )

        right.addWidget(
            QtWidgets.QLabel("Comando")
        )

        right.addWidget(
            self.cmd_text
        )

        # ----------------------------------------------------
        # BOTONES
        # ----------------------------------------------------

        btns = QtWidgets.QHBoxLayout()

        btns.addWidget(
            self.btn_preview
        )

        btns.addWidget(
            self.btn_copy
        )

        btns.addWidget(
            self.btn_apply
        )

        btns.addWidget(
            self.btn_clear
        )

        btns.addWidget(
            self.btn_kill_steam
        )

        right.addLayout(btns)

        # ----------------------------------------------------
        # PROPORCIONES
        # ----------------------------------------------------

        main_layout.addLayout(
            left,
            2
        )

        main_layout.addLayout(
            right,
            3
        )

        self.setCentralWidget(
            main_widget
        )

        # ====================================================
        # OPCIONES DEL PANEL
        # ====================================================

        self.details_layout.addRow(
            "Resolución base:",
            self.base_res_combo
        )

        self.details_layout.addRow(
            "Resolución salida:",
            self.out_res_combo
        )

        self.details_layout.addRow(
            self.chk_fsr
        )

        self.details_layout.addRow(
            "Nitidez FSR (0–5):",
            sharpness_box
        )

        self.details_layout.addRow(
            self.chk_nis
        )

        self.details_layout.addRow(
            "Nitidez NIS (0–5):",
            nis_box
        )

        self.details_layout.addRow(
            self.chk_nearest
        )

        self.details_layout.addRow(
            self.chk_hdr
        )

        self.details_layout.addRow(
            self.chk_vrr
        )

        self.details_layout.addRow(
            self.chk_immediate
        )

        # ====================================================
        # CONEXIONES
        # ====================================================

        self.btn_scan.clicked.connect(
            self.scan_clicked
        )

        self.game_list.currentItemChanged.connect(
            self.game_selected
        )

        self.btn_preview.clicked.connect(
            self.generate_command
        )

        self.btn_copy.clicked.connect(
            self.copy_command
        )

        self.btn_apply.clicked.connect(
            self.apply_command
        )

        self.btn_clear.clicked.connect(
            self.clear_command
        )

        self.btn_kill_steam.clicked.connect(
            self.kill_steam
        )

        # ====================================================
        # AVISO
        # ====================================================

        QtWidgets.QMessageBox.information(
            self,
            "Aviso importante",
            "SteamCommandGen requiere que Steam esté "
            "cerrado para aplicar o borrar LaunchOptions.\n"
            "Si Steam está abierto, los cambios no se "
            "guardarán.\n\n"
            "Cierre Steam antes de continuar."
        )

    # ============================================================
    # CARGA DE IMÁGENES
    # ============================================================

    def load_image(self, appid):
        url = (
            f"https://steamcdn-a.akamaihd.net/"
            f"steam/apps/{appid}/header.jpg"
        )

        req = QNetworkRequest(
            QtCore.QUrl(url)
        )

        reply = self.network_manager.get(req)

        def done():
            if (
                reply.error()
                == reply.NetworkError.NoError
            ):
                pix = QtGui.QPixmap()

                pix.loadFromData(
                    reply.readAll()
                )

                self.img_label.setPixmap(
                    pix.scaledToWidth(400)
                )

            reply.deleteLater()

        reply.finished.connect(done)

    def load_icon(self, appid, item):
        url = (
            f"https://steamcdn-a.akamaihd.net/"
            f"steam/apps/{appid}/capsule_231x87.jpg"
        )

        req = QNetworkRequest(
            QtCore.QUrl(url)
        )

        reply = self.network_manager.get(req)

        def done():
            if (
                reply.error()
                == reply.NetworkError.NoError
            ):
                pix = QtGui.QPixmap()

                pix.loadFromData(
                    reply.readAll()
                )

                # Comprobar que el item sigue existiendo
                # en la lista antes de asignar el icono.
                if item.listWidget() is not None:
                    item.setIcon(
                        QtGui.QIcon(pix)
                    )

            reply.deleteLater()

        reply.finished.connect(done)

    # ============================================================
    # LÓGICA DE COMPATIBILIDAD DE OPCIONES
    # ============================================================

    def vrr_changed(self, _state):
        # Si VRR se activa, desactivar modo baja latencia.
        if self.chk_vrr.isChecked():
            self.chk_immediate.setChecked(False)

    def immediate_changed(self, _state):
        # Si modo baja latencia se activa, desactivar VRR.
        if self.chk_immediate.isChecked():
            self.chk_vrr.setChecked(False)

    def fsr_changed(self, _state):
        enabled = self.chk_fsr.isChecked()

        if enabled:
            self.chk_nis.setChecked(False)
            self.chk_nearest.setChecked(False)

        self.sharpness_slider.setEnabled(
            enabled
        )

        if enabled:
            self.nis_slider.setEnabled(False)

    def nis_changed(self, _state):
        enabled = self.chk_nis.isChecked()

        if enabled:
            self.chk_fsr.setChecked(False)
            self.chk_nearest.setChecked(False)

        self.nis_slider.setEnabled(
            enabled
        )

        if enabled:
            self.sharpness_slider.setEnabled(False)

    def nearest_changed(self, _state):
        enabled = self.chk_nearest.isChecked()

        if enabled:
            self.chk_fsr.setChecked(False)
            self.chk_nis.setChecked(False)

        self.sharpness_slider.setEnabled(False)
        self.nis_slider.setEnabled(False)

    # ============================================================
    # PARSEAR GAMESCOPE
    # ============================================================

    def parse_gamescope_command(self, cmd):

        # Todas las claves quedan inicializadas para evitar
        # KeyError al cargar comandos que no contienen
        # determinadas opciones.

        result = {
            "res_w": None,
            "res_h": None,
            "out_w": None,
            "out_h": None,

            "sharpness": None,
            "nis_sharpness": None,

            "hdr": False,
            "vrr": False,
            "immediate": False,

            "winedll": "",

            "fsr_enabled": False,
            "nis_enabled": False,
            "nearest_enabled": False,
        }

        # --------------------------------------------------------
        # WINEDLLOVERRIDES
        # --------------------------------------------------------

        m = re.search(
            r'WINEDLLOVERRIDES="([^"]+)"',
            cmd
        )

        if m:
            result["winedll"] = m.group(1)

        # --------------------------------------------------------
        # RESOLUCIÓN BASE
        # --------------------------------------------------------

        m = re.search(
            r'-w (\d+)',
            cmd
        )

        if m:
            result["res_w"] = int(
                m.group(1)
            )

        m = re.search(
            r'-h (\d+)',
            cmd
        )

        if m:
            result["res_h"] = int(
                m.group(1)
            )

        # --------------------------------------------------------
        # RESOLUCIÓN DE SALIDA
        # --------------------------------------------------------

        m = re.search(
            r'-W (\d+)',
            cmd
        )

        if m:
            result["out_w"] = int(
                m.group(1)
            )

        m = re.search(
            r'-H (\d+)',
            cmd
        )

        if m:
            result["out_h"] = int(
                m.group(1)
            )

        # --------------------------------------------------------
        # FSR
        # --------------------------------------------------------

        if (
            "--fsr-sharpness" in cmd
            or "-F fsr" in cmd
        ):
            result["fsr_enabled"] = True

        m = re.search(
            r'--fsr-sharpness (\d+)',
            cmd
        )

        if m:
            result["sharpness"] = int(
                m.group(1)
            )

        # --------------------------------------------------------
        # NIS
        # --------------------------------------------------------

        if (
            "-F nis" in cmd
            or "--nis-sharpness" in cmd
        ):
            result["nis_enabled"] = True

        m = re.search(
            r'--nis-sharpness ([0-9.]+)',
            cmd
        )

        if m:
            result["nis_sharpness"] = float(
                m.group(1)
            )

        # --------------------------------------------------------
        # NEAREST
        # --------------------------------------------------------

        if "-F nearest" in cmd:
            result["nearest_enabled"] = True

        # --------------------------------------------------------
        # FLAGS
        # --------------------------------------------------------

        result["hdr"] = (
            "--hdr-enabled" in cmd
        )

        result["vrr"] = (
            "--adaptive-sync" in cmd
        )

        result["immediate"] = (
            "--immediate-flips" in cmd
        )

        return result

    # ============================================================
    # APLICAR OPCIONES PARSEADAS A LA GUI
    # ============================================================

    def apply_parsed_options(self, opts):

        # --------------------------------------------------------
        # RESOLUCIÓN BASE
        # --------------------------------------------------------

        if (
            opts["res_w"] is not None
            and opts["res_h"] is not None
        ):
            for i in range(
                self.base_res_combo.count()
            ):
                w, h = (
                    self.base_res_combo.itemData(i)
                )

                if (
                    w == opts["res_w"]
                    and h == opts["res_h"]
                ):
                    self.base_res_combo.setCurrentIndex(i)
                    break

        # --------------------------------------------------------
        # RESOLUCIÓN SALIDA
        # --------------------------------------------------------

        if (
            opts["out_w"] is not None
            and opts["out_h"] is not None
        ):
            for i in range(
                self.out_res_combo.count()
            ):
                w, h = (
                    self.out_res_combo.itemData(i)
                )

                if (
                    w == opts["out_w"]
                    and h == opts["out_h"]
                ):
                    self.out_res_combo.setCurrentIndex(i)
                    break

        # --------------------------------------------------------
        # NITIDEZ FSR
        # --------------------------------------------------------

        if opts["sharpness"] is not None:
            slider_val = (
                20 - opts["sharpness"]
            ) // 4

            slider_val = max(
                0,
                min(5, slider_val)
            )

            self.sharpness_slider.setValue(
                slider_val
            )

        # --------------------------------------------------------
        # NITIDEZ NIS
        # --------------------------------------------------------

        if opts["nis_sharpness"] is not None:
            slider_val = int(
                opts["nis_sharpness"] * 5
            )

            slider_val = max(
                0,
                min(5, slider_val)
            )

            self.nis_slider.setValue(
                slider_val
            )

        # --------------------------------------------------------
        # FLAGS
        # --------------------------------------------------------

        self.chk_hdr.setChecked(
            opts["hdr"]
        )

        self.chk_vrr.setChecked(
            opts["vrr"]
        )

        self.chk_immediate.setChecked(
            opts["immediate"]
        )

        self.chk_fsr.setChecked(
            opts["fsr_enabled"]
        )

        self.chk_nis.setChecked(
            opts["nis_enabled"]
        )

        self.chk_nearest.setChecked(
            opts["nearest_enabled"]
        )

        # --------------------------------------------------------
        # ESTADO DE SLIDERS
        # --------------------------------------------------------

        self.sharpness_slider.setEnabled(
            opts["fsr_enabled"]
        )

        self.nis_slider.setEnabled(
            opts["nis_enabled"]
        )

        # NEAREST no utiliza slider.
        if opts["nearest_enabled"]:
            self.sharpness_slider.setEnabled(False)
            self.nis_slider.setEnabled(False)

        # --------------------------------------------------------
        # WINEDLLOVERRIDES
        # --------------------------------------------------------

        self.txt_winedll.setText(
            opts["winedll"]
        )

    # ============================================================
    # ESCANEAR JUEGOS
    # ============================================================

    def scan_clicked(self):

        self.games = scan_games()

        self.game_list.clear()

        for game in self.games:

            item = QtWidgets.QListWidgetItem(
                f"{game['name']} "
                f"(appid {game['appid']})"
            )

            item.setData(
                QtCore.Qt.ItemDataRole.UserRole,
                game
            )

            self.game_list.addItem(item)

            self.load_icon(
                game["appid"],
                item
            )

    # ============================================================
    # JUEGO SELECCIONADO
    # ============================================================

    def game_selected(
        self,
        current,
        _previous
    ):

        if current is None:

            self.current_game = None

            self.lbl_game_dir.setText("")

            self.exec_list.clear()

            self.img_label.clear()

            self.cmd_text.clear()

            return

        game = current.data(
            QtCore.Qt.ItemDataRole.UserRole
        )

        self.current_game = game

        self.lbl_game_dir.setText(
            game["game_dir"]
        )

        self.exec_list.clear()

        for exe in game["executables"]:
            self.exec_list.addItem(exe)

        self.load_image(
            game["appid"]
        )

        # ========================================================
        # DETECTAR COMANDO ACTIVO
        # ========================================================

        active_cmd = get_active_launch_options(
            game["appid"]
        )

        if active_cmd.strip():

            self.cmd_text.setPlainText(
                active_cmd
            )

            parsed = self.parse_gamescope_command(
                active_cmd
            )

            self.apply_parsed_options(
                parsed
            )

        else:

            self.cmd_text.clear()

    # ============================================================
    # RECOGER OPCIONES
    # ============================================================

    def collect_options(self):

        base_w, base_h = (
            self.base_res_combo.currentData()
        )

        out_w, out_h = (
            self.out_res_combo.currentData()
        )

        # --------------------------------------------------------
        # FSR
        # Slider 0–5 -> valor Gamescope 20–0
        # --------------------------------------------------------

        slider_val = (
            self.sharpness_slider.value()
        )

        sharpness_real = (
            20 - (slider_val * 4)
        )

        # --------------------------------------------------------
        # NIS
        # Slider 0–5 -> valor 0.0–1.0
        # --------------------------------------------------------

        nis_slider_val = (
            self.nis_slider.value()
        )

        nis_real = (
            nis_slider_val / 5
        )

        return {
            "res_w": base_w,
            "res_h": base_h,

            "out_w": out_w,
            "out_h": out_h,

            "sharpness": (
                sharpness_real
                if self.chk_fsr.isChecked()
                else None
            ),

            "nis_sharpness": (
                nis_real
                if self.chk_nis.isChecked()
                else None
            ),

            "hdr": self.chk_hdr.isChecked(),
            "vrr": self.chk_vrr.isChecked(),
            "immediate": self.chk_immediate.isChecked(),

            "winedll": (
                self.txt_winedll.text().strip()
            ),

            "fsr_enabled": (
                self.chk_fsr.isChecked()
            ),

            "nis_enabled": (
                self.chk_nis.isChecked()
            ),

            "nearest_enabled": (
                self.chk_nearest.isChecked()
            ),
        }

    # ============================================================
    # GENERAR COMANDO
    # ============================================================

    def generate_command(self):

        opts = self.collect_options()

        cmd = build_gamescope_command(
            opts
        )

        self.cmd_text.setPlainText(
            cmd
        )

    # ============================================================
    # COPIAR COMANDO
    # ============================================================

    def copy_command(self):

        cmd = (
            self.cmd_text
            .toPlainText()
            .strip()
        )

        if not cmd:

            QtWidgets.QMessageBox.warning(
                self,
                "Sin comando",
                "Genera el comando primero."
            )

            return

        QtWidgets.QApplication.clipboard().setText(
            cmd
        )

        QtWidgets.QMessageBox.information(
            self,
            "Copiado",
            "Comando copiado al portapapeles."
        )

    # ============================================================
    # APLICAR A STEAM
    # ============================================================

    def apply_command(self):

        if self.current_game is None:

            QtWidgets.QMessageBox.warning(
                self,
                "Sin juego",
                "Selecciona un juego."
            )

            return

        opts = self.collect_options()

        cmd = build_gamescope_command(
            opts
        )

        appid = self.current_game["appid"]

        try:

            write_launch_options(
                appid,
                cmd
            )

        except Exception as e:

            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                "No se pudo escribir "
                f"LaunchOptions:\n{e}"
            )

            return

        self.cmd_text.setPlainText(
            cmd
        )

        QtWidgets.QMessageBox.information(
            self,
            "Aplicado",
            f"LaunchOptions aplicadas "
            f"para appid {appid}."
        )

    # ============================================================
    # LIMPIAR PROPIEDADES
    # ============================================================

    def clear_command(self):

        if self.current_game is None:

            QtWidgets.QMessageBox.warning(
                self,
                "Sin juego",
                "Selecciona un juego."
            )

            return

        appid = self.current_game["appid"]
        name = self.current_game["name"]

        try:

            clear_launch_options(
                appid
            )

        except Exception as e:

            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                "No se pudo limpiar "
                f"LaunchOptions:\n{e}"
            )

            return

        self.cmd_text.clear()

        QtWidgets.QMessageBox.information(
            self,
            "Comando eliminado",
            "Se han borrado las LaunchOptions de:\n\n"
            f"{name}\n\n"
            f"(appid {appid})"
        )

    # ============================================================
    # CERRAR STEAM
    # ============================================================

    def kill_steam(self):

        try:

            subprocess.call(
                ["pkill", "-f", "steam"]
            )

        except Exception as e:

            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"No se pudo cerrar Steam:\n{e}"
            )

            return

        QtWidgets.QMessageBox.information(
            self,
            "Steam cerrado",
            "Steam ha sido cerrado correctamente."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    # Integración con el escritorio Linux/Wayland.
    QtGui.QGuiApplication.setDesktopFileName(
        "SteamCommandGen"
    )

    app = QtWidgets.QApplication(
        sys.argv
    )

    app.setApplicationName(
        "SteamCommandGen"
    )

    app.setApplicationDisplayName(
        "Steam Command Gen V2.0.0"
    )

    win = GamescopeManager()

    win.show()

    sys.exit(
        app.exec()
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
