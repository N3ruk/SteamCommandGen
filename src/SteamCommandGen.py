#!/usr/bin/env python3

import os
import sys
import re
import shlex
import shutil
import subprocess

import vdf

from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkRequest,
    QNetworkReply,
)


# ============================================================
# RECURSOS DE LA APLICACIÓN
# ============================================================

def find_resources_dir():
    """Locate bundled assets in source, user/system installs and AppImage."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = []
    if getattr(sys, "_MEIPASS", None):
        candidates.append(os.path.join(sys._MEIPASS, "SteamCommandGen"))
    candidates.extend((
        os.path.join(script_dir, "SteamCommandGen"),
        os.path.dirname(script_dir),
        os.path.join(script_dir, "..", "share", "SteamCommandGen"),
        os.path.join(script_dir, "..", "..", "share", "SteamCommandGen"),
    ))
    for candidate in candidates:
        if all(os.path.isdir(os.path.join(candidate, name))
               for name in ("scaling", "BOTONES")):
            return os.path.abspath(candidate)
    raise FileNotFoundError("Faltan los recursos de SteamCommandGen (scaling/BOTONES)")


RESOURCES_DIR = find_resources_dir()
SCALING_DIR = os.path.join(RESOURCES_DIR, "scaling")
BUTTONS_DIR = os.path.join(RESOURCES_DIR, "BOTONES")


def create_mangohud_config_icon():
    """Genera el icono de configuración si el recurso SVG no está instalado."""

    pixmap = QtGui.QPixmap(256, 256)
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)

    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(
        QtGui.QPainter.RenderHint.Antialiasing
    )

    gradient = QtGui.QLinearGradient(0, 0, 256, 256)
    gradient.setColorAt(0, QtGui.QColor("#FFE600"))
    gradient.setColorAt(1, QtGui.QColor("#FF7800"))

    painter.setPen(
        QtGui.QPen(
            QtGui.QBrush(gradient),
            12,
            QtCore.Qt.PenStyle.SolidLine,
            QtCore.Qt.PenCapStyle.RoundCap,
            QtCore.Qt.PenJoinStyle.RoundJoin,
        )
    )
    painter.setBrush(QtGui.QColor("#101820"))
    painter.drawRoundedRect(18, 18, 220, 220, 32, 32)

    painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
    for y in (76, 128, 180):
        painter.drawLine(62, y, 194, y)

    painter.setBrush(QtGui.QColor("#101820"))
    for x, y in ((108, 76), (164, 128), (94, 180)):
        painter.drawEllipse(x - 17, y - 17, 34, 34)

    painter.end()
    return QtGui.QIcon(pixmap)


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

        users = sorted(
            u for u in os.listdir(userdata)
            if u.isdigit()
        )

        steamid = users[0] if users else "0"

        return {
            "root": base,
            "steamapps": os.path.join(
                base,
                "steamapps"
            ),
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
# ESCANEO DE BIBLIOTECAS
# ============================================================

def get_libraries():
    libs = []
    lf_path = STEAM["libraryfolders"]

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

    libraryfolders = data.get(
        "libraryfolders",
        {}
    )

    for value in libraryfolders.values():

        if not isinstance(value, dict):
            continue

        path = value.get("path")

        if not path:
            continue

        steamapps = os.path.join(
            path,
            "steamapps"
        )

        if steamapps not in libs:
            libs.append(steamapps)

    if STEAM["steamapps"] not in libs:
        libs.append(STEAM["steamapps"])

    return libs


# ============================================================
# BUSCAR ARCHIVOS ACF
# ============================================================

def find_acf_files(path):
    if not os.path.isdir(path):
        return []

    # Los manifiestos de Steam están directamente en steamapps. Recorrer
    # toda la biblioteca (compatdata, shadercache, etc.) bloquea la GUI y
    # puede tardar varios segundos en bibliotecas grandes.
    try:
        return [
            entry.path
            for entry in os.scandir(path)
            if entry.is_file() and entry.name.lower().endswith(".acf")
        ]
    except OSError:
        return []


# ============================================================
# PARSEAR ACF
# ============================================================

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

    app = data.get(
        "AppState",
        {}
    )

    return {
        "appid": app.get("appid"),
        "name": app.get("name"),
        "install_dir": app.get("installdir"),
        "acf_path": path,
    }


# ============================================================
# EJECUTABLES
# ============================================================

def find_executables(game_dir):
    """
    Busca ejecutables en el directorio raíz del juego.

    Mantiene el comportamiento original:
    devuelve únicamente el ejecutable de mayor tamaño.
    """

    if not os.path.isdir(game_dir):
        return []

    exes = []

    try:
        filenames = os.listdir(game_dir)
    except OSError:
        return []

    for filename in filenames:

        full_path = os.path.join(
            game_dir,
            filename
        )

        if not os.path.isfile(full_path):
            continue

        if not filename.lower().endswith(
            (".exe", ".sh")
        ):
            continue

        try:
            size = os.path.getsize(full_path)
        except OSError:
            continue

        exes.append(
            (full_path, size)
        )

    if not exes:
        return []

    exes.sort(
        key=lambda item: item[1],
        reverse=True
    )

    return [exes[0][0]]


# ============================================================
# APLICACIONES DE STEAM QUE NO SON VIDEOJUEGOS
# ============================================================

NON_GAME_APP_KEYWORDS = (
    "proton",
    "steam linux runtime",
    "lossless scaling",
    "steamworks common redistributables",
)


# ============================================================
# ESCANEAR JUEGOS
# ============================================================

def scan_games():
    games = []
    seen_appids = set()

    for library in get_libraries():

        for acf_path in find_acf_files(library):

            info = parse_acf(acf_path)

            if not info:
                continue

            appid = info.get("appid")
            name = (
                info.get("name")
                or ""
            ).strip()

            if not appid:
                continue

            if not name:
                continue

            name_lower = name.lower()

            if any(
                keyword in name_lower
                for keyword in NON_GAME_APP_KEYWORDS
            ):
                continue

            install_dir = info.get(
                "install_dir"
            )

            if not install_dir:
                continue

            if appid in seen_appids:
                continue

            game_dir = os.path.join(
                library,
                "common",
                install_dir
            )

            info["game_dir"] = game_dir
            info["executables"] = find_executables(
                game_dir
            )

            games.append(info)
            seen_appids.add(appid)

    return games


# ============================================================
# LOCALCONFIG DE STEAM
# ============================================================

def find_localconfig():

    detected = STEAM.get(
        "localconfig"
    )

    if (
        detected
        and os.path.isfile(detected)
    ):
        return detected

    bases = [
        os.path.expanduser(
            "~/.steam/steam/userdata"
        ),
        os.path.expanduser(
            "~/.local/share/Steam/userdata"
        ),
    ]

    for base in bases:

        if not os.path.isdir(base):
            continue

        users = sorted(
            user
            for user in os.listdir(base)
            if user.isdigit()
        )

        for user in users:

            path = os.path.join(
                base,
                user,
                "config",
                "localconfig.vdf"
            )

            if os.path.isfile(path):
                return path

    return None


# ============================================================
# CARGAR LOCALCONFIG
# ============================================================

def load_localconfig():

    cfg_path = find_localconfig()

    if not cfg_path:
        raise FileNotFoundError(
            "No se encontró localconfig.vdf."
        )

    with open(
        cfg_path,
        encoding="utf-8",
        errors="ignore"
    ) as f:

        data = vdf.load(f)

    return cfg_path, data


# ============================================================
# OBTENER ESTRUCTURA STEAM/APPS
# ============================================================

def get_steam_apps_dict(data):

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

    return apps


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

    # --------------------------------------------------------
    # HDR
    # --------------------------------------------------------

    if opts.get("hdr"):
        cmd.append(
            "--hdr-enabled"
        )

    # --------------------------------------------------------
    # VRR
    # --------------------------------------------------------

    if opts.get("vrr"):
        cmd.append(
            "--adaptive-sync"
        )

    # --------------------------------------------------------
    # BAJA LATENCIA
    # --------------------------------------------------------

    if opts.get("immediate"):
        cmd.append(
            "--immediate-flips"
        )

    # --------------------------------------------------------
    # ESCALADO
    # --------------------------------------------------------

    if opts.get("fsr_enabled"):

        cmd.append(
            "-F fsr"
        )

        cmd.append(
            f"--sharpness {opts['sharpness']}"
        )

    elif opts.get("nis_enabled"):

        cmd.append(
            "-F nis"
        )

        cmd.append(
            f"--sharpness {opts['nis_sharpness']}"
        )

    elif opts.get("nearest_enabled"):

        cmd.append(
            "-F nearest"
        )

    # --------------------------------------------------------
    # MANGOHUD
    # --------------------------------------------------------

    if opts.get("mangohud"):
        cmd.append(
            "--mangoapp"
        )

    # --------------------------------------------------------
    # FULLSCREEN
    # --------------------------------------------------------

    cmd.append(
        "-f"
    )

    # --------------------------------------------------------
    # STEAM COMMAND
    # --------------------------------------------------------

    cmd.append(
        "-- %command%"
    )

    final = " ".join(cmd)

    # MangoHud lee su configuración de ~/.config/MangoHud/MangoHud.conf.
    # No incrustar MANGOHUD_CONFIG: además de hacer enorme el comando,
    # sustituiría la configuración central del usuario.
    env_prefix = []

    # --------------------------------------------------------
    # WINEDLLOVERRIDES
    # --------------------------------------------------------

    winedll = (
        opts.get("winedll", "")
        .strip()
    )

    if winedll:
        env_prefix.insert(
            0,
            f'WINEDLLOVERRIDES={shlex.quote(winedll)}'
        )

    if env_prefix:
        return f"{' '.join(env_prefix)} {final}"

    return final


# ============================================================
# ESCRIBIR LAUNCH OPTIONS
# ============================================================

def write_launch_options(
    appid,
    cmd
):

    cfg_path, data = load_localconfig()

    apps = get_steam_apps_dict(
        data
    )

    apps.setdefault(
        str(appid),
        {}
    )["LaunchOptions"] = cmd

    with open(
        cfg_path,
        "w",
        encoding="utf-8"
    ) as f:

        vdf.dump(
            data,
            f,
            pretty=False
        )


# ============================================================
# BORRAR LAUNCH OPTIONS
# ============================================================

def clear_launch_options(appid):

    cfg_path, data = load_localconfig()

    apps = get_steam_apps_dict(
        data
    )

    apps.setdefault(
        str(appid),
        {}
    )["LaunchOptions"] = ""

    with open(
        cfg_path,
        "w",
        encoding="utf-8"
    ) as f:

        vdf.dump(
            data,
            f,
            pretty=False
        )


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

    apps = (
        data
        .get("UserLocalConfigStore", {})
        .get("Software", {})
        .get("Valve", {})
        .get("Steam", {})
        .get("apps", {})
    )

    return (
        apps
        .get(str(appid), {})
        .get("LaunchOptions", "")
    )


# ============================================================
# CONFIGURACIÓN DE MANGOHUD
# ============================================================

DEFAULT_MANGOHUD_CONFIG = (
    "fps,frame_timing,cpu_stats,gpu_stats,cpu_temp,gpu_temp,ram,vram"
)
MANGOHUD_CONFIG_FILE = os.path.expanduser(
    "~/.config/MangoHud/MangoHud.conf"
)


def load_mangohud_config_file():
    """Carga MangoHud.conf y lo adapta al formato de MANGOHUD_CONFIG."""

    if not os.path.isfile(MANGOHUD_CONFIG_FILE):
        return DEFAULT_MANGOHUD_CONFIG

    values = []
    try:
        with open(
            MANGOHUD_CONFIG_FILE,
            encoding="utf-8",
            errors="ignore",
        ) as config_file:
            for raw_line in config_file:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                if "=" not in line:
                    values.append(line)
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # En MANGOHUD_CONFIG la coma separa opciones; MangoHud
                # permite usar '+' para conservar listas como 50,90.
                if key in {
                    "gpu_load_value",
                    "gpu_load_color",
                    "cpu_load_value",
                    "cpu_load_color",
                    "fps_color",
                    "fps_value",
                }:
                    value = value.replace(",", "+")

                value = value.replace(",", r"\,")
                values.append(f"{key}={value}")
    except OSError:
        return DEFAULT_MANGOHUD_CONFIG

    return ",".join(values) or DEFAULT_MANGOHUD_CONFIG


def config_value(config, key, default=""):
    prefix = f"{key}="
    for item in re.split(r"(?<!\\),", config):
        item = item.strip()
        if item.startswith(prefix):
            return item[len(prefix):]
    return default


class MangoHudConfigDialog(QtWidgets.QDialog):

    def __init__(self, config="", parent=None):

        super().__init__(parent)

        self.config_path = os.path.realpath(MANGOHUD_CONFIG_FILE)
        self.original_bytes = None
        self.snapshot_error = None
        try:
            with open(self.config_path, "rb") as source:
                self.original_bytes = source.read()
        except FileNotFoundError:
            pass
        except OSError as error:
            self.snapshot_error = str(error)
        self.last_written = self.original_bytes
        self.live_dirty = False
        self.preview_process = QtCore.QProcess(self)
        self.preview_process.setProcessChannelMode(
            QtCore.QProcess.ProcessChannelMode.MergedChannels
        )
        self.preview_output = ""
        self.preview_process.readyReadStandardOutput.connect(self.read_preview_output)
        self.preview_process.errorOccurred.connect(self.preview_failed)
        self.preview_process.finished.connect(self.preview_finished)
        self.live_timer = QtCore.QTimer(self)
        self.live_timer.setSingleShot(True)
        self.live_timer.setInterval(300)
        self.live_timer.timeout.connect(self.save_global_config)

        self.setWindowTitle("Configurar MangoHud")
        self.setObjectName("mangohudDialog")
        self.setStyleSheet("""
            QDialog#mangohudDialog { background: #171D25; }
            QGroupBox {
                background: #1B2838; border: 1px solid #2A475E;
                border-radius: 8px; margin-top: 10px; padding: 0px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 12px;
                padding: 0 4px; color: #66C0F4;
            }
            QCheckBox { spacing: 7px; padding: 2px 0; background: transparent; }
            QCheckBox::indicator {
                width: 16px; height: 16px; border: 1px solid #547087;
                border-radius: 3px; background: #101820;
            }
            QCheckBox::indicator:checked { background: #1A9FFF; border-color: #66C0F4; }
            QPushButton { padding: 6px 12px; }
        """)

        config = config.strip() or load_mangohud_config_file()

        current = {
            item.strip()
            for item in re.split(r"(?<!\\),", config)
            if item.strip()
        }

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        columns_layout = QtWidgets.QHBoxLayout()
        columns_layout.setSpacing(14)
        layout.addLayout(columns_layout, 1)

        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        right_panel = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)

        columns_layout.addWidget(left_panel, 2)
        columns_layout.addWidget(right_panel, 1)

        info = QtWidgets.QLabel(
            "Selecciona los indicadores que aparecerán en la superposición."
        )
        info.setWordWrap(True)
        layout.insertWidget(0, info)

        metrics_box = QtWidgets.QGroupBox("Indicadores")
        metrics_layout = QtWidgets.QGridLayout(metrics_box)
        metrics_layout.setContentsMargins(12, 20, 12, 12)
        metrics_layout.setHorizontalSpacing(20)
        metrics_layout.setVerticalSpacing(4)

        self.metric_checks = {}
        metrics = [
            ("fps", "FPS"),
            ("frame_timing", "Frametime"),
            ("cpu_stats", "Uso de CPU"),
            ("gpu_stats", "Uso de GPU"),
            ("cpu_temp", "Temperatura CPU"),
            ("gpu_temp", "Temperatura GPU"),
            ("ram", "RAM"),
            ("vram", "VRAM"),
            ("engine_version", "Motor gráfico"),
            ("wine", "Wine"),
            ("battery", "Batería"),
            ("core_load", "Carga por núcleo"),
            ("gpu_core_clock", "Reloj GPU"),
            ("gpu_mem_clock", "Reloj VRAM"),
            ("gpu_power", "Potencia GPU"),
            ("cpu_power", "Potencia CPU"),
            ("ram_temp", "Temperatura RAM"),
            ("resolution", "Resolución"),
            ("refresh_rate", "Frecuencia pantalla"),
            ("present_mode", "Present mode"),
            ("network", "Red"),
            ("gamemode", "Estado GameMode"),
            ("hdr", "Estado HDR"),
            ("fsr", "Estado FSR"),
        ]

        for index, (key, label) in enumerate(metrics):
            check = QtWidgets.QCheckBox(label)
            check.setChecked(key in current or f"{key}=1" in current)
            check.ensurePolished()
            check.setMinimumWidth(check.sizeHint().width() + 12)
            self.metric_checks[key] = check
            metrics_layout.addWidget(check, index // 2, index % 2)

        left_layout.addWidget(metrics_box)

        try:
            self.offset_x = int(config_value(config, "offset_x", "0"))
        except ValueError:
            self.offset_x = 0
        try:
            self.offset_y = int(config_value(config, "offset_y", "0"))
        except ValueError:
            self.offset_y = 0

        offset_box = QtWidgets.QGroupBox("Ajuste fino de posición")
        offset_layout = QtWidgets.QGridLayout(offset_box)
        offset_layout.setContentsMargins(12, 20, 12, 12)
        offset_layout.setHorizontalSpacing(8)
        offset_layout.setVerticalSpacing(4)
        offset_layout.addWidget(QtWidgets.QLabel("Mover HUD:"), 1, 0)

        def add_move_button(text, row, column, dx=0, dy=0):
            button = QtWidgets.QPushButton(text)
            button.setFixedSize(42, 32)
            button.setAutoDefault(False)
            button.setToolTip("Mover MangoHud 5 píxeles")
            button.clicked.connect(
                lambda _checked=False, x=dx, y=dy: self.move_hud(x, y)
            )
            offset_layout.addWidget(button, row, column)

        add_move_button("↑", 0, 2, dy=-5)
        add_move_button("←", 1, 1, dx=-5)
        add_move_button("→", 1, 3, dx=5)
        add_move_button("↓", 2, 2, dy=5)
        left_layout.addWidget(offset_box)
        left_layout.addStretch(1)

        placement_box = QtWidgets.QGroupBox("Distribución")
        form = QtWidgets.QFormLayout(placement_box)
        form.setContentsMargins(12, 20, 12, 12)
        form.setVerticalSpacing(10)
        form.setRowWrapPolicy(QtWidgets.QFormLayout.RowWrapPolicy.WrapAllRows)

        self.position_combo = QtWidgets.QComboBox()
        positions = [
            ("Arriba izquierda", "top-left"),
            ("Arriba derecha", "top-right"),
            ("Abajo izquierda", "bottom-left"),
            ("Abajo derecha", "bottom-right"),
        ]
        for label, value in positions:
            self.position_combo.addItem(label, value)

        position = config_value(config, "position", "top-left")
        position_index = self.position_combo.findData(position)
        if position_index >= 0:
            self.position_combo.setCurrentIndex(position_index)

        form.addRow("Posición:", self.position_combo)
        self.layout_type = QtWidgets.QComboBox()
        self.layout_type.addItem("Vertical", "vertical")
        self.layout_type.addItem("Horizontal", "horizontal")
        self.layout_type.setCurrentIndex(
            1 if "horizontal" in current or "horizontal=1" in current else 0
        )
        form.addRow("Tipo de diseño:", self.layout_type)
        right_layout.addWidget(placement_box)

        colors_box = QtWidgets.QGroupBox("Colores")
        colors_layout = QtWidgets.QFormLayout(colors_box)
        colors_layout.setContentsMargins(12, 20, 12, 12)
        colors_layout.setVerticalSpacing(10)
        self.color_values = {}
        self.color_buttons = {}

        color_groups = [
            ("fps_color", "FPS", "008000+FFFF00+FF0000"),
            ("gpu_load_color", "Carga GPU", "FFFFFF+FFFFFF+FFFFFF"),
            ("cpu_load_color", "Carga CPU", "FFFFFF+FFFFFF+FFFFFF"),
        ]

        for key, label, default in color_groups:
            configured = config_value(config, key, default)
            colors = [
                color.strip().lstrip("#").upper()
                for color in configured.split("+")
                if color.strip()
            ]
            color = colors[0] if colors else default.split("+")[0]
            colors = [color]
            self.color_values[key] = colors

            row = QtWidgets.QWidget()
            row_layout = QtWidgets.QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(6)
            self.color_buttons[key] = []

            button = QtWidgets.QPushButton()
            button.setFixedSize(42, 30)
            button.setToolTip("Seleccionar color")
            button.clicked.connect(
                lambda _checked=False, group=key:
                self.choose_color(group)
            )
            self.color_buttons[key].append(button)
            row_layout.addWidget(button)
            self.update_color_button(key)

            row_layout.addStretch(1)
            colors_layout.addRow(label + ":", row)

        right_layout.addWidget(colors_box)
        shortcut_box = QtWidgets.QGroupBox("Mostrar / ocultar HUD")
        shortcut_layout = QtWidgets.QVBoxLayout(shortcut_box)
        shortcut_layout.setContentsMargins(12, 20, 12, 12)
        self.toggle_key = QtWidgets.QLineEdit(
            config_value(config, "toggle_hud", "Shift_R+F12")
        )
        self.toggle_key.setPlaceholderText("F1 o Shift_R+F12")
        self.toggle_key.setToolTip("Nombre de tecla de MangoHud, por ejemplo F1 o Shift_R+F12")
        self.toggle_key.setValidator(QtGui.QRegularExpressionValidator(
            QtCore.QRegularExpression(r"[A-Za-z0-9_]+(?:\+[A-Za-z0-9_]+)*"), self
        ))
        shortcut_layout.addWidget(self.toggle_key)
        right_layout.addWidget(shortcut_box)
        right_layout.addStretch(1)

        represented = set(self.metric_checks) | {
            "position",
            "horizontal",
            "horizontal_stretch",
            "offset_x",
            "offset_y",
            "media_player",
            "swap",
            "procmem",
            "proc_vram",
            "fps_color",
            "gpu_load_color",
            "cpu_load_color",
            "toggle_hud",
            "fps_color_change",
            "gpu_load_change",
            "cpu_load_change",
            "gpu_color",
            "cpu_color",
        }
        self.preserved_options = [
            item.strip()
            for item in re.split(r"(?<!\\),", config)
            if item.strip()
            and item.strip().split("=", 1)[0] not in represented
        ]

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText("Aceptar")
        buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")

        save_button = QtWidgets.QPushButton(
            "Crear .bak"
        )
        save_button.setToolTip(
            "Copiar el fichero actual en disco a MangoHud.conf.bak"
        )
        save_button.setAutoDefault(False)
        save_button.clicked.connect(self.backup_global_config)

        location_button = QtWidgets.QPushButton("Abrir ubicación")
        location_button.setAutoDefault(False)
        location_button.setToolTip(
            f"Abrir la carpeta de {MANGOHUD_CONFIG_FILE}"
        )
        location_button.clicked.connect(self.open_config_location)

        self.preview_button = QtWidgets.QPushButton("Vista previa")
        self.preview_button.setAutoDefault(False)
        self.preview_button.setToolTip("Abrir un cubo Vulkan con MangoHud y ajustes en vivo")
        self.preview_button.clicked.connect(self.open_preview)
        self.live_status = QtWidgets.QLabel("Los cambios se aplican en vivo. Cancelar restaura el archivo anterior.")
        self.live_status.setWordWrap(True)
        layout.addWidget(self.live_status)

        actions_layout = QtWidgets.QHBoxLayout()
        actions_layout.setContentsMargins(0, 2, 0, 0)
        actions_layout.addWidget(save_button)
        actions_layout.addWidget(location_button)
        actions_layout.addWidget(self.preview_button)
        actions_layout.addStretch(1)
        actions_layout.addWidget(buttons)
        layout.addLayout(actions_layout)
        layout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetMinimumSize)
        self.adjustSize()
        for check in self.metric_checks.values():
            check.toggled.connect(self.schedule_live_update)
        self.position_combo.currentIndexChanged.connect(self.schedule_live_update)
        self.layout_type.currentIndexChanged.connect(self.schedule_live_update)
        self.toggle_key.textEdited.connect(self.schedule_live_update)

    def move_hud(self, delta_x, delta_y):
        """Mueve MangoHud unos píxeles y actualiza la vista previa."""
        self.offset_x += delta_x
        self.offset_y += delta_y
        self.schedule_live_update()

    def schedule_live_update(self, *_args):
        self.live_timer.start()

    def read_preview_output(self):
        self.preview_output = (self.preview_output + bytes(
            self.preview_process.readAllStandardOutput()
        ).decode("utf-8", errors="replace"))[-3000:]

    def preview_failed(self, *_args):
        self.live_status.setText("No se pudo iniciar la vista previa: " + self.preview_process.errorString())

    def preview_finished(self, code, _status):
        self.preview_button.setEnabled(True)
        if code:
            self.live_status.setText("La vista previa se cerró con un error. " + self.preview_output[-600:])

    def open_preview(self):
        if self.preview_process.state() != QtCore.QProcess.ProcessState.NotRunning:
            return
        demo = shutil.which("vkcube") or shutil.which("pascube")
        launcher = shutil.which("mangohud")
        if not demo or not launcher:
            self.live_status.setText("La vista previa necesita MangoHud y vkcube (o pascube).")
            return
        self.live_timer.stop()
        if not self.save_global_config():
            return
        environment = QtCore.QProcessEnvironment.systemEnvironment()
        environment.remove("MANGOHUD_CONFIG")
        environment.insert("MANGOHUD_CONFIGFILE", self.config_path)
        self.preview_process.setProcessEnvironment(environment)
        self.preview_output = ""
        preview_args = [demo]
        # vkcube admite fijar el tamaño inicial de su ventana. La vista
        # previa necesita al menos 720p para que MangoHud horizontal quepa.
        if os.path.basename(demo) == "vkcube":
            preview_args.extend(["--width", "1280", "--height", "720"])
        self.preview_process.start(launcher, preview_args)
        self.live_status.setText("Vista previa: cambia las opciones para ver el resultado en vivo.")

    def stop_preview(self):
        if self.preview_process.state() != QtCore.QProcess.ProcessState.NotRunning:
            self.preview_process.terminate()
            if not self.preview_process.waitForFinished(1000):
                self.preview_process.kill()
                self.preview_process.waitForFinished(1000)

    def write_config_bytes(self, data):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        target = QtCore.QSaveFile(self.config_path)
        if not target.open(QtCore.QIODevice.OpenModeFlag.WriteOnly):
            raise OSError(target.errorString())
        if target.write(data) != len(data):
            target.cancelWriting()
            raise OSError(target.errorString())
        if not target.commit():
            raise OSError(target.errorString())

    def reject(self):
        self.live_timer.stop()
        if self.live_dirty:
            try:
                if self.original_bytes is None:
                    os.unlink(self.config_path)
                else:
                    self.write_config_bytes(self.original_bytes)
            except OSError as error:
                self.live_status.setText("No se pudo restaurar el archivo: " + str(error))
                return
            self.live_dirty = False
        self.stop_preview()
        super().reject()

    def closeEvent(self, event):
        self.reject()
        if self.live_dirty:
            event.ignore()
        else:
            event.accept()

    def open_config_location(self):
        directory = os.path.dirname(MANGOHUD_CONFIG_FILE)
        if not os.path.isdir(directory):
            QtWidgets.QMessageBox.warning(
                self, "Carpeta no encontrada",
                f"La carpeta de configuración todavía no existe:\n{directory}",
            )
            return
        if not QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(directory)):
            QtWidgets.QMessageBox.warning(
                self, "No se pudo abrir la carpeta",
                f"No se pudo iniciar el gestor de archivos para:\n{directory}",
            )

    def update_color_button(self, group):

        color = self.color_values[group][0]
        self.color_buttons[group][0].setStyleSheet(
            f"""
            QPushButton {{
                background-color: #{color};
                border: 2px solid #66C0F4;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                border: 2px solid white;
            }}
            """
        )

    def choose_color(self, group):

        current = QtGui.QColor(
            f"#{self.color_values[group][0]}"
        )
        selected = QtWidgets.QColorDialog.getColor(
            current,
            self,
            "Seleccionar color",
        )

        if not selected.isValid():
            return

        self.color_values[group][0] = selected.name(
            QtGui.QColor.NameFormat.HexRgb
        ).lstrip("#").upper()
        self.update_color_button(group)
        self.schedule_live_update()

    def backup_global_config(self):
        backup_path = f"{MANGOHUD_CONFIG_FILE}.bak"
        try:
            shutil.copy2(MANGOHUD_CONFIG_FILE, backup_path)
        except OSError as error:
            QtWidgets.QMessageBox.critical(
                self, "No se pudo crear la copia", str(error)
            )
            return
        QtWidgets.QMessageBox.information(
            self, "Copia creada",
            f"Copia del fichero actual guardada en:\n{backup_path}\n\n"
            "La copia contiene el fichero que está actualmente en disco.",
        )

    def accept(self):
        self.live_timer.stop()
        if self.save_global_config():
            self.live_dirty = False
            self.stop_preview()
            super().accept()

    def save_global_config(self):
        if self.snapshot_error:
            self.live_status.setText("No se pudo leer el archivo original: " + self.snapshot_error)
            return False
        if not self.toggle_key.hasAcceptableInput():
            self.live_status.setText("Introduce una tecla válida, por ejemplo F1 o Shift_R+F12.")
            return False
        config = self.config_string()
        list_values = {
            "gpu_load_value", "gpu_load_color", "cpu_load_value",
            "cpu_load_color", "fps_color", "fps_value",
        }

        try:
            lines = ["# Configuración guardada por SteamCommandGen"]
            for item in re.split(r"(?<!\\),", config):
                item = item.strip().replace(r"\,", ",")
                if not item:
                    continue
                if "=" in item:
                    key, value = item.split("=", 1)
                    if key in list_values:
                        value = value.replace("+", ",")
                    item = f"{key}={value}"
                lines.append(item)
            data = ("\n".join(lines) + "\n").encode("utf-8")
            if data != self.last_written:
                self.write_config_bytes(data)
                self.last_written = data
                self.live_dirty = True
        except OSError as error:
            self.live_status.setText("No se pudieron aplicar los cambios: " + str(error))
            return False
        self.live_status.setText("Cambios aplicados en vivo. Aceptar los conserva; Cancelar los revierte.")
        return True

    def config_string(self):

        values = [
            f"{key}={int(check.isChecked())}"
            for key, check in self.metric_checks.items()
        ]

        values.extend([
            f"position={self.position_combo.currentData()}",
        ])

        values.append(f"horizontal={int(self.layout_type.currentData() == 'horizontal')}")
        # Evita que el fondo se extienda hasta los bordes de la pantalla.
        values.append("horizontal_stretch=0")
        values.append(f"offset_x={self.offset_x}")
        values.append(f"offset_y={self.offset_y}")
        values.append(f"toggle_hud={self.toggle_key.text().strip()}")

        for key, colors in self.color_values.items():
            values.append(f"{key}={colors[0]}+{colors[0]}+{colors[0]}")

        # Las paletas por niveles no se usan sin sus interruptores.
        # Los tres niveles comparten el color elegido en cada selector.
        values.extend([
            "fps_color_change=1",
            "gpu_load_change=1",
            "cpu_load_change=1",
            f"gpu_color={self.color_values['gpu_load_color'][0]}",
            f"cpu_color={self.color_values['cpu_load_color'][0]}",
        ])

        values.extend(self.preserved_options)

        return ",".join(values)


# ============================================================
# GUI PRINCIPAL
# ============================================================

class GameScanWorker(QtCore.QObject):
    """Ejecuta el escaneo de Steam fuera del hilo de la interfaz."""

    finished = QtCore.pyqtSignal(object)
    failed = QtCore.pyqtSignal(str)

    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.finished.emit(scan_games())
        except Exception as error:
            self.failed.emit(str(error))

class ElidedPathLabel(QtWidgets.QLabel):
    """Show a long game path without changing the window's size hint."""

    def __init__(self):
        super().__init__("")
        self.full_path = ""

    def set_path(self, path):
        self.full_path = path
        self.setToolTip(path)
        self._update_display()

    def clear(self):
        self.full_path = ""
        super().clear()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_display()

    def _update_display(self):
        display = self.fontMetrics().elidedText(
            self.full_path, QtCore.Qt.TextElideMode.ElideMiddle,
            max(0, self.width() - 2),
        )
        if display != self.text():
            super().setText(display)


class GamescopeManager(
    QtWidgets.QMainWindow
):

    def __init__(self):

        super().__init__()

        # ====================================================
        # ESTILO GENERAL
        # ====================================================

        self.setStyleSheet("""
            QMainWindow {
                background-color: #171D25;
            }

            QWidget {
                background-color: #171D25;
                color: #D6D7D8;
            }

            QLabel {
                color: #D6D7D8;
            }

            QGroupBox {
                background-color: #1B2838;
                border: 1px solid #2A475E;
                border-radius: 8px;
                margin-top: 12px;
                padding: 10px;
            }

            QGroupBox::title {
                color: #66C0F4;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }

            QComboBox {
                background-color: #2A475E;
                color: white;
                border: 1px solid #3A6A8A;
                border-radius: 5px;
                padding: 5px;
            }

            QComboBox:hover {
                border: 1px solid #66C0F4;
            }

            QLineEdit,
            QTextEdit,
            QPlainTextEdit {
                background-color: #101820;
                color: #D6D7D8;
                border: 1px solid #2A475E;
                border-radius: 5px;
                padding: 5px;
            }

            QListWidget {
                background-color: #101820;
                color: #D6D7D8;
                border: 1px solid #2A475E;
                border-radius: 5px;
            }

            QListWidget::item {
                padding: 7px;
            }

            QListWidget::item:selected {
                background-color: #1A9FFF;
                color: white;
            }

            QCheckBox {
                color: #D6D7D8;
                spacing: 7px;
                padding: 2px 0;
                background: transparent;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #547087;
                border-radius: 3px;
                background: #101820;
            }

            QCheckBox::indicator:checked {
                background: #1A9FFF;
                border-color: #66C0F4;
            }

            QSlider::groove:horizontal {
                background: #2A475E;
                height: 6px;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #66C0F4;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
        """)

        # ====================================================
        # CONFIGURACIÓN
        # ====================================================

        self.setWindowIcon(
            QtGui.QIcon.fromTheme(
                "SteamCommandGen"
            )
        )

        # Start inside the usable desktop area, including 1280x720 desktops.
        screen = QtWidgets.QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else QtCore.QRect(0, 0, 1280, 720)
        self.setMaximumSize(max(1, available.width() - 40),
                            max(1, available.height() - 40))
        self.resize(min(1200, available.width() - 40),
                    min(700, available.height() - 40))

        self.games = []
        self.current_game = None
        self.scan_thread = None
        self.scan_worker = None

        self.network_manager = (
            QNetworkAccessManager(self)
        )

        # ====================================================
        # LISTA DE JUEGOS
        # ====================================================

        self.game_list = (
            QtWidgets.QListWidget()
        )

        self.game_list.setIconSize(
            QtCore.QSize(
                120,
                45
            )
        )
        self.game_list.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.game_list.setTextElideMode(QtCore.Qt.TextElideMode.ElideRight)

        # ====================================================
        # IMAGEN
        # ====================================================

        self.img_label = (
            QtWidgets.QLabel()
        )

        self.img_label.setFixedHeight(
            200
        )
        self._game_pixmap = None

        self.img_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignCenter
        )

        # ====================================================
        # PANEL DE DETALLES
        # ====================================================

        self.details_widget = (
            QtWidgets.QWidget()
        )

        self.details_layout = (
            QtWidgets.QFormLayout(
                self.details_widget
            )
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

        self.base_res_combo = (
            QtWidgets.QComboBox()
        )

        self.out_res_combo = (
            QtWidgets.QComboBox()
        )

        # Dejamos la selección inicial vacía.
        self.base_res_combo.addItem(
            "Seleccionar resolución..."
        )
        self.base_res_combo.setCurrentIndex(0)

        self.out_res_combo.addItem(
            "Seleccionar resolución..."
        )
        self.out_res_combo.setCurrentIndex(0)

        for label, resolution in resolutions.items():

            self.base_res_combo.addItem(
                label,
                resolution
            )

            self.out_res_combo.addItem(
                label,
                resolution
            )

        # ====================================================
        # SLIDER FSR
        # ====================================================

        self.sharpness_slider = (
            QtWidgets.QSlider(
                QtCore.Qt.Orientation.Horizontal
            )
        )

        self.sharpness_slider.setMinimumHeight(
            30
        )

        self.sharpness_slider.setMinimumWidth(
            200
        )

        self.sharpness_slider.setRange(
            0,
            5
        )

        self.sharpness_slider.setValue(
            0
        )

        self.sharpness_slider.setTickInterval(
            1
        )

        self.sharpness_slider.setTickPosition(
            QtWidgets.QSlider.TickPosition.TicksBelow
        )

        self.sharpness_slider.setEnabled(
            False
        )

        self.sharpness_label = (
            QtWidgets.QLabel("0")
        )

        self.sharpness_slider.valueChanged.connect(
            lambda value:
            self.sharpness_label.setText(
                str(value)
            )
        )

        self.sharpness_box = (
            QtWidgets.QWidget()
        )

        sharpness_layout = (
            QtWidgets.QHBoxLayout(
                self.sharpness_box
            )
        )

        sharpness_layout.setContentsMargins(
            0, 0, 0, 0
        )

        sharpness_layout.setSpacing(
            8
        )

        sharpness_layout.addWidget(
            self.sharpness_slider,
            1
        )

        sharpness_layout.addWidget(
            self.sharpness_label
        )

        # ====================================================
        # SLIDER NIS
        # ====================================================

        self.nis_slider = (
            QtWidgets.QSlider(
                QtCore.Qt.Orientation.Horizontal
            )
        )

        self.nis_slider.setMinimumHeight(
            30
        )

        self.nis_slider.setMinimumWidth(
            200
        )

        self.nis_slider.setRange(
            0,
            5
        )

        self.nis_slider.setValue(
            0
        )

        self.nis_slider.setTickInterval(
            1
        )

        self.nis_slider.setTickPosition(
            QtWidgets.QSlider.TickPosition.TicksBelow
        )

        self.nis_slider.setEnabled(
            False
        )

        self.nis_label = (
            QtWidgets.QLabel("0")
        )

        self.nis_slider.valueChanged.connect(
            lambda value:
            self.nis_label.setText(
                str(value)
            )
        )

        self.nis_box = (
            QtWidgets.QWidget()
        )

        nis_layout = (
            QtWidgets.QHBoxLayout(
                self.nis_box
            )
        )

        nis_layout.setContentsMargins(
            0, 0, 0, 0
        )

        nis_layout.setSpacing(
            8
        )

        nis_layout.addWidget(
            self.nis_slider,
            1
        )

        nis_layout.addWidget(
            self.nis_label
        )

        # ====================================================
        # WINEDLLOVERRIDES
        # ====================================================

        self.txt_winedll = (
            QtWidgets.QLineEdit()
        )

        self.txt_winedll.setPlaceholderText(
            "WINEDLLOVERRIDES= (opcional)"
        )

        # ====================================================
        # BOTONES DE ESCALADO
        # ====================================================

        self.scaling_mode = None

        self.btn_fsr = (
            QtWidgets.QPushButton()
        )

        self.btn_nis = (
            QtWidgets.QPushButton()
        )

        self.btn_nearest = (
            QtWidgets.QPushButton()
        )

        # ====================================================
        # BOTÓN MANGOHUD
        # ====================================================

        self.mangohud_config = load_mangohud_config_file()

        self.btn_mangohud = (
            QtWidgets.QPushButton()
        )

        scaling_button_style = """
            QPushButton {
                border: none;
                padding: 0px;
                margin: 0px;
                background: transparent;
            }

            QPushButton:checked {
                border: 3px solid white;
                border-radius: 12px;
            }
        """

        for button in (
            self.btn_fsr,
            self.btn_nis,
            self.btn_nearest
        ):

            button.setCheckable(
                True
            )

            button.setFlat(
                True
            )

            button.setCursor(
                QtGui.QCursor(
                    QtCore.Qt.CursorShape.PointingHandCursor
                )
            )

            button.setStyleSheet(
                scaling_button_style
            )

        # ====================================================
        # IMÁGENES DE ESCALADO
        # ====================================================

        self.btn_fsr.setIcon(
            QtGui.QIcon(
                QtGui.QPixmap(
                    os.path.join(
                        SCALING_DIR,
                        "FSR.png"
                    )
                )
            )
        )

        self.btn_nis.setIcon(
            QtGui.QIcon(
                QtGui.QPixmap(
                    os.path.join(
                        SCALING_DIR,
                        "NIS.png"
                    )
                )
            )
        )

        self.btn_nearest.setIcon(
            QtGui.QIcon(
                QtGui.QPixmap(
                    os.path.join(
                        SCALING_DIR,
                        "NEAREST.png"
                    )
                )
            )
        )

        self.btn_mangohud.setIcon(
            QtGui.QIcon(
                QtGui.QPixmap(
                    os.path.join(
                        BUTTONS_DIR,
                        "MANGOHUD.png"
                    )
                )
            )
        )

        # ====================================================
        # TAMAÑOS ESCALADO
        # ====================================================

        button_size = QtCore.QSize(
            210,
            145
        )

        icon_size = QtCore.QSize(
            200,
            135
        )

        for button in (
            self.btn_fsr,
            self.btn_nis,
            self.btn_nearest
        ):

            button.setFixedSize(
                button_size
            )

            button.setIconSize(
                icon_size
            )

        # ====================================================
        # MANGOHUD
        # ====================================================

        self.btn_mangohud.setFixedSize(
            QtCore.QSize(
                110,
                110
            )
        )

        self.btn_mangohud.setIconSize(
            QtCore.QSize(
                92,
                92
            )
        )

        self.btn_mangohud.setCheckable(
            True
        )

        self.btn_mangohud.setFlat(
            True
        )

        self.btn_mangohud.setCursor(
            QtGui.QCursor(
                QtCore.Qt.CursorShape.PointingHandCursor
            )
        )

        self.btn_mangohud.setStyleSheet("""
            QPushButton {
                border: 2px solid #2A475E;
                border-radius: 12px;
                padding: 5px;
                margin: 0px;
                background-color: #101820;
            }

            QPushButton:hover {
                border: 2px solid #66C0F4;
                background-color: #1B2838;
            }

            QPushButton:checked {
                border: 3px solid #66C0F4;
                border-radius: 12px;
                background-color: #1B2838;
            }
        """)

        # ====================================================
        # CHECKBOXES
        # ====================================================

        self.chk_hdr = (
            QtWidgets.QCheckBox("HDR")
        )

        self.chk_vrr = (
            QtWidgets.QCheckBox(
                "VRR (Adaptive Sync)"
            )
        )

        self.chk_immediate = (
            QtWidgets.QCheckBox(
                "Modo Baja Latencia"
            )
        )

        # ====================================================
        # CONEXIONES DE COMPATIBILIDAD
        # ====================================================

        self.chk_vrr.stateChanged.connect(
            self.vrr_changed
        )

        self.chk_immediate.stateChanged.connect(
            self.immediate_changed
        )

        # ====================================================
        # CONEXIONES ESCALADO
        # ====================================================

        self.btn_fsr.clicked.connect(
            self.fsr_button_clicked
        )

        self.btn_nis.clicked.connect(
            self.nis_button_clicked
        )

        self.btn_nearest.clicked.connect(
            self.nearest_button_clicked
        )

        # ====================================================
        # RUTA / EJECUTABLES / COMANDO
        # ====================================================

        self.lbl_game_dir = (
            ElidedPathLabel()
        )
        # A game path can be arbitrarily long; it must not set the minimum
        # width of the entire window after a game is selected.
        self.lbl_game_dir.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )

        self.exec_list = (
            QtWidgets.QListWidget()
        )

        self.cmd_text = (
            QtWidgets.QPlainTextEdit()
        )

        self.cmd_text.setReadOnly(
            True
        )

        # ====================================================
        # BOTONES PRINCIPALES
        # ====================================================

        self.btn_scan = (
            QtWidgets.QPushButton(
                "Buscar juegos"
            )
        )

        self.btn_preview = (
            QtWidgets.QPushButton(
                "Generar comando"
            )
        )

        self.btn_copy = (
            QtWidgets.QPushButton(
                "Copiar comando"
            )
        )

        self.btn_apply = (
            QtWidgets.QPushButton(
                "Aplicar a Steam"
            )
        )

        self.btn_clear = (
            QtWidgets.QPushButton(
                "Limpiar Propiedades"
            )
        )

        self.btn_kill_steam = (
            QtWidgets.QPushButton(
                "Cerrar Steam"
            )
        )

        main_button_style = """
            QPushButton {
                background-color: #2a475e;
                color: white;
                padding: 6px;
                border-radius: 10px;
                font-size: 18px;
                font-family: 'DejaVu Sans';
            }

            QPushButton:hover {
                background-color: #3AA0FF;
            }
        """

        for button in (
            self.btn_scan,
            self.btn_preview,
            self.btn_copy,
            self.btn_apply,
            self.btn_clear,
            self.btn_kill_steam
        ):

            button.setStyleSheet(
                main_button_style
            )

        # ====================================================
        # LAYOUT PRINCIPAL
        # ====================================================

        main_widget = (
            QtWidgets.QWidget()
        )

        main_layout = (
            QtWidgets.QHBoxLayout(
                main_widget
            )
        )
        self.main_layout = main_layout

        # ====================================================
        # PANEL IZQUIERDO
        # ====================================================

        left = (
            QtWidgets.QVBoxLayout()
        )

        left.addWidget(
            QtWidgets.QLabel(
                "Juegos detectados"
            )
        )

        left.addWidget(
            self.game_list
        )

        left.addWidget(
            self.btn_scan
        )

        # ====================================================
        # PANEL DERECHO
        # ====================================================

        right = (
            QtWidgets.QVBoxLayout()
        )
        self.right_layout = right

        right.addWidget(
            QtWidgets.QLabel(
                "Imagen del juego"
            )
        )

        right.addWidget(
            self.img_label
        )

        right.addWidget(
            QtWidgets.QLabel(
                "Configuración"
            )
        )

        right.addWidget(
            self.details_widget
        )

        right.addWidget(
            QtWidgets.QLabel(
                "Ruta del juego"
            )
        )

        right.addWidget(
            self.lbl_game_dir
        )

        right.addWidget(
            QtWidgets.QLabel(
                "Ejecutables"
            )
        )

        right.addWidget(
            self.exec_list
        )

        right.addWidget(
            QtWidgets.QLabel(
                "Comando"
            )
        )

        right.addWidget(
            self.cmd_text
        )

        # ====================================================
        # BOTONES INFERIORES
        # ====================================================

        buttons_layout = QtWidgets.QGridLayout()
        self.buttons_layout = buttons_layout
        self.action_buttons = (
            self.btn_preview, self.btn_copy, self.btn_apply,
            self.btn_clear, self.btn_kill_steam,
        )

        for column, button in enumerate(self.action_buttons):
            buttons_layout.addWidget(button, 0, column)

        right.addLayout(
            buttons_layout
        )

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

        # ====================================================
        # TÍTULO ESCALADO
        # ====================================================

        scaling_title = (
            QtWidgets.QLabel(
                "TECNOLOGÍAS DE REESCALADO"
            )
        )

        scaling_title.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignCenter
        )

        scaling_title.setStyleSheet("""
            QLabel {
                font-family: 'DejaVu Sans';
                font-size: 25px;
                font-weight: bold;
                letter-spacing: 1px;
                padding: 6px 0px;
            }
        """)

        self.details_layout.addRow(
            scaling_title
        )

        # ====================================================
        # BOTONES ESCALADO
        # ====================================================

        scaling_buttons_widget = (
            QtWidgets.QWidget()
        )

        scaling_buttons_layout = (
            QtWidgets.QHBoxLayout(
                scaling_buttons_widget
            )
        )
        self.scaling_buttons_layout = scaling_buttons_layout

        scaling_buttons_layout.setContentsMargins(
            0, 0, 0, 0
        )

        scaling_buttons_layout.addWidget(
            self.btn_fsr
        )

        scaling_buttons_layout.addWidget(
            self.btn_nis
        )

        scaling_buttons_layout.addWidget(
            self.btn_nearest
        )

        self.details_layout.addRow(
            scaling_buttons_widget
        )

        # ====================================================
        # NITIDEZ FSR
        # ====================================================

        self.fsr_sharpness_label = (
            QtWidgets.QLabel(
                "Nitidez FSR (0–5):"
            )
        )

        # ====================================================
        # NITIDEZ NIS
        # ====================================================

        self.nis_sharpness_label = (
            QtWidgets.QLabel(
                "Nitidez NIS (0–5):"
            )
        )

        # Both scalers use the same form row. Stacked widgets retain the
        # larger page's size hint, so switching FSR/NIS cannot add a row or
        # make a window manager enlarge the top-level window.
        self.sharpness_labels = QtWidgets.QStackedWidget()
        self.sharpness_labels.addWidget(self.fsr_sharpness_label)
        self.sharpness_labels.addWidget(self.nis_sharpness_label)
        self.sharpness_controls = QtWidgets.QStackedWidget()
        self.sharpness_controls.addWidget(self.sharpness_box)
        self.sharpness_controls.addWidget(self.nis_box)
        self.sharpness_labels.addWidget(QtWidgets.QLabel())
        self.sharpness_controls.addWidget(QtWidgets.QWidget())
        self.details_layout.addRow(
            self.sharpness_labels,
            self.sharpness_controls
        )

        # ====================================================
        # RESERVAR LA FILA DE NITIDEZ DESDE EL INICIO
        # ====================================================

        self.sharpness_labels.setCurrentIndex(2)
        self.sharpness_controls.setCurrentIndex(2)

        # ====================================================
        # WINEDLLOVERRIDES
        # ====================================================

        self.details_layout.addRow(
            "WINEDLLOVERRIDES:",
            self.txt_winedll
        )

        # ====================================================
        # OPCIONES DE PANTALLA
        # ====================================================

        display_options_widget = (
            QtWidgets.QWidget()
        )

        display_options_layout = (
            QtWidgets.QHBoxLayout(
                display_options_widget
            )
        )

        display_options_layout.setContentsMargins(
            0,
            8,
            0,
            8
        )

        display_options_layout.setSpacing(
            0
        )

        # ====================================================
        # COLUMNA IZQUIERDA
        # HDR / VRR / BAJA LATENCIA
        # ====================================================

        display_checks_widget = (
            QtWidgets.QWidget()
        )

        display_checks_widget.setMinimumWidth(0)

        display_checks = (
            QtWidgets.QVBoxLayout(
                display_checks_widget
            )
        )

        display_checks.setContentsMargins(
            0,
            0,
            0,
            0
        )

        display_checks.setSpacing(
            6
        )

        display_checks.addWidget(
            self.chk_hdr
        )

        display_checks.addWidget(
            self.chk_vrr
        )

        display_checks.addWidget(
            self.chk_immediate
        )

        display_options_layout.addWidget(
            display_checks_widget
        )

        # ====================================================
        # COLUMNA CENTRAL
        # MANGOHUD
        # ====================================================

        mangohud_widget = (
            QtWidgets.QWidget()
        )

        mangohud_widget.setMinimumWidth(0)

        mangohud_column = (
            QtWidgets.QVBoxLayout(
                mangohud_widget
            )
        )

        mangohud_column.setContentsMargins(
            0,
            0,
            0,
            0
        )

        mangohud_column.setSpacing(
            3
        )

        mangohud_label = (
            QtWidgets.QLabel(
                "MangoHud"
            )
        )

        mangohud_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignCenter
        )

        mangohud_label.setStyleSheet("""
            QLabel {
                color: #D6D7D8;
                font-family: 'DejaVu Sans';
                font-size: 13px;
                font-weight: bold;
            }
        """)

        mangohud_column.addWidget(
            self.btn_mangohud,
            alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

        mangohud_column.addWidget(
            mangohud_label
        )

        display_options_layout.addWidget(
            mangohud_widget
        )

        # ====================================================
        # COLUMNA DERECHA
        # CONFIGURACIÓN DE MANGOHUD
        # ====================================================

        config_widget = (
            QtWidgets.QWidget()
        )

        config_widget.setMinimumWidth(0)

        config_layout = (
            QtWidgets.QVBoxLayout(
                config_widget
            )
        )

        config_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        config_layout.setSpacing(
            3
        )

        self.btn_mangohud_config = QtWidgets.QPushButton()
        config_icon_paths = (
            os.path.join(
                BUTTONS_DIR,
                "MANGOHUD_CONFIG.svg"
            ),
        )

        config_icon = QtGui.QIcon()
        for config_icon_path in config_icon_paths:
            if os.path.isfile(config_icon_path):
                config_icon = QtGui.QIcon(config_icon_path)
                break

        if config_icon.isNull():
            config_icon = create_mangohud_config_icon()

        self.btn_mangohud_config.setIcon(config_icon)
        self.btn_mangohud_config.setToolTip(
            "Abrir la configuración avanzada de MangoHud"
        )
        self.btn_mangohud_config.setFixedSize(
            QtCore.QSize(110, 110)
        )
        self.btn_mangohud_config.setIconSize(
            QtCore.QSize(92, 92)
        )
        self.btn_mangohud_config.setFlat(True)
        self.btn_mangohud_config.setCursor(
            QtGui.QCursor(
                QtCore.Qt.CursorShape.PointingHandCursor
            )
        )
        self.btn_mangohud_config.setStyleSheet("""
            QPushButton {
                border: 2px solid #2A475E;
                border-radius: 12px;
                padding: 5px;
                margin: 0px;
                background-color: #101820;
            }

            QPushButton:hover {
                border: 2px solid #66C0F4;
                background-color: #1B2838;
            }
        """)

        config_layout.addWidget(
            self.btn_mangohud_config,
            alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

        config_label = (
            QtWidgets.QLabel(
                "Configurar MangoHud"
            )
        )

        config_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignCenter
        )

        config_label.setStyleSheet("""
            QLabel {
                color: #D6D7D8;
                font-family: 'DejaVu Sans';
                font-size: 13px;
                font-weight: bold;
            }
        """)

        config_layout.addWidget(
            config_label
        )

        display_options_layout.addWidget(
            config_widget
        )
        self.display_options_layout = display_options_layout

        # ====================================================
        # AÑADIR A LA INTERFAZ
        # ====================================================

        self.details_layout.addRow(
            display_options_widget
        )

        # Only geometry changes with the available space; controls and their
        # signal connections remain the same on X11, Wayland and SteamOS.
        self._responsive_ready = True
        self._fit_layout()

        # ====================================================
        # CONEXIONES GENERALES
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

        self.btn_mangohud_config.clicked.connect(
            self.open_mangohud_config
        )

        # ====================================================
        # AVISO INICIAL
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

    def showEvent(self, event):
        super().showEvent(event)
        handle = self.windowHandle()
        if handle and not getattr(self, "_screen_connected", False):
            handle.screenChanged.connect(self._screen_changed)
            self._screen_connected = True

    def _screen_changed(self, screen):
        if screen:
            available = screen.availableGeometry()
            self.setMaximumSize(max(1, available.width() - 40),
                                max(1, available.height() - 40))
            self._fit_layout()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, "_responsive_ready", False):
            self._fit_layout()

    def _fit_layout(self):
        if getattr(self, "_fitting_layout", False):
            return
        self._fitting_layout = True
        try:
            self._fit_layout_to_height()
        finally:
            self._fitting_layout = False

    def _fit_layout_to_height(self):
        # Font metrics and desktop panels change the minimum height. Measure
        # the complete layout after each adjustment instead of estimating it
        # from the screen resolution alone.
        usable_height = min(self.height(), self.maximumHeight())
        width = self.width()
        # Keep the original proportions whenever the window has room.
        factor = max(0.35, min(1.0, (usable_height - 480) / 520))
        if width < 1100:
            factor = min(factor, 0.35)
        for _ in range(16):
            self._set_layout_scale(factor, width)
            self.main_layout.activate()
            self.centralWidget().updateGeometry()
            self.layout().invalidate()
            excess = self.main_layout.minimumSize().height() - usable_height
            if excess <= 0 or factor <= 0.20:
                break
            factor = max(0.20, factor - max(0.04, excess / 450))

        minimum = self.main_layout.minimumSize()
        self.setMinimumSize(min(minimum.width(), self.maximumWidth()),
                            min(minimum.height(), self.maximumHeight()))

        # If a minimum-size hint grew the window before the new layout took
        # effect, bring it back inside the screen's usable area.
        if self.height() > self.maximumHeight():
            self.resize(self.width(), self.maximumHeight())

    def _set_layout_scale(self, factor, width):
        self.img_label.setFixedHeight(round(200 * factor))
        self._fit_game_image()
        for button in (self.btn_fsr, self.btn_nis, self.btn_nearest):
            button_width = min(210, max(105, (width - 320) // 3))
            button.setFixedSize(button_width, round(145 * factor))
            button.setIconSize(QtCore.QSize(button_width - 10,
                                            round(135 * factor)))
        for button in (self.btn_mangohud, self.btn_mangohud_config):
            side = round(110 * factor)
            button.setFixedSize(side, side)
            button.setIconSize(QtCore.QSize(side - 18, side - 18))

        self.exec_list.setMinimumHeight(30)
        self.cmd_text.setMinimumHeight(36)
        self.main_layout.setSpacing(round(6 * factor))
        self.right_layout.setSpacing(round(6 * factor))
        self.details_layout.setVerticalSpacing(round(6 * factor))
        self.scaling_buttons_layout.setSpacing(round(6 * factor))
        self.display_options_layout.setContentsMargins(0, round(8 * factor),
                                                       0, round(8 * factor))

        columns = 5 if width >= 1100 else 3
        if getattr(self, "_action_columns", None) != columns:
            self._action_columns = columns
            for index, button in enumerate(self.action_buttons):
                self.buttons_layout.addWidget(button, index // columns,
                                              index % columns)

    def _fit_game_image(self):
        if self._game_pixmap is not None:
            self.img_label.setPixmap(self._game_pixmap.scaled(
                min(400, max(1, self.img_label.width())),
                self.img_label.height(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            ))

    # ============================================================
    # CARGAR IMAGEN DEL JUEGO
    # ============================================================

    def load_image(self, appid):

        url = (
            "https://steamcdn-a.akamaihd.net/"
            f"steam/apps/{appid}/header.jpg"
        )

        request = QNetworkRequest(
            QtCore.QUrl(url)
        )

        reply = self.network_manager.get(
            request
        )

        def done():

            if (
                reply.error()
                == QNetworkReply.NetworkError.NoError
            ):

                pixmap = QtGui.QPixmap()

                if pixmap.loadFromData(
                    reply.readAll()
                ):

                    self._game_pixmap = pixmap
                    self._fit_game_image()

            reply.deleteLater()

        reply.finished.connect(
            done
        )

    # ============================================================
    # CARGAR ICONO
    # ============================================================

    def load_icon(
        self,
        appid,
        item
    ):

        url = (
            "https://steamcdn-a.akamaihd.net/"
            f"steam/apps/{appid}/capsule_231x87.jpg"
        )

        request = QNetworkRequest(
            QtCore.QUrl(url)
        )

        reply = self.network_manager.get(
            request
        )

        def done():

            if (
                reply.error()
                == QNetworkReply.NetworkError.NoError
            ):

                pixmap = QtGui.QPixmap()

                if pixmap.loadFromData(
                    reply.readAll()
                ):

                    if item.listWidget() is not None:

                        item.setIcon(
                            QtGui.QIcon(
                                pixmap
                            )
                        )

            reply.deleteLater()

        reply.finished.connect(
            done
        )

    # ============================================================
    # COMPATIBILIDAD VRR / BAJA LATENCIA
    # ============================================================

    def vrr_changed(self, _state):

        if self.chk_vrr.isChecked():

            self.chk_immediate.blockSignals(
                True
            )

            self.chk_immediate.setChecked(
                False
            )

            self.chk_immediate.blockSignals(
                False
            )

    def immediate_changed(self, _state):

        if self.chk_immediate.isChecked():

            self.chk_vrr.blockSignals(
                True
            )

            self.chk_vrr.setChecked(
                False
            )

            self.chk_vrr.blockSignals(
                False
            )

    # ============================================================
    # ACTUALIZAR VISIBILIDAD DEL ESCALADO
    # ============================================================

    def update_scaling_ui(self):

        is_fsr = (
            self.scaling_mode == "fsr"
        )

        is_nis = (
            self.scaling_mode == "nis"
        )

        index = 0 if is_fsr else 1 if is_nis else 2
        self.sharpness_labels.setCurrentIndex(index)
        self.sharpness_controls.setCurrentIndex(index)

        self.sharpness_slider.setEnabled(
            is_fsr
        )

        self.nis_slider.setEnabled(
            is_nis
        )

        if getattr(self, "_responsive_ready", False):
            self._fit_layout()

    # ============================================================
    # RESET ESCALADO
    # ============================================================

    def open_mangohud_config(self):

        dialog = MangoHudConfigDialog(
            load_mangohud_config_file(),
            self,
        )

        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.mangohud_config = dialog.config_string()

            if not self.mangohud_config:
                self.mangohud_config = load_mangohud_config_file()

    def reset_scaling_options(self):

        self.scaling_mode = None

        self.btn_fsr.blockSignals(
            True
        )

        self.btn_nis.blockSignals(
            True
        )

        self.btn_nearest.blockSignals(
            True
        )

        self.btn_fsr.setChecked(
            False
        )

        self.btn_nis.setChecked(
            False
        )

        self.btn_nearest.setChecked(
            False
        )

        self.btn_fsr.blockSignals(
            False
        )

        self.btn_nis.blockSignals(
            False
        )

        self.sharpness_slider.setValue(
            0
        )

        self.nis_slider.setValue(
            0
        )

        self.chk_hdr.setChecked(
            False
        )

        self.chk_vrr.setChecked(
            False
        )

        self.chk_immediate.setChecked(
            False
        )

        self.btn_mangohud.setChecked(
            False
        )

        self.mangohud_config = load_mangohud_config_file()

        self.txt_winedll.clear()

        self.update_scaling_ui()

    # ============================================================
    # BOTÓN FSR
    # ============================================================

    def fsr_button_clicked(self):

        if self.btn_fsr.isChecked():

            self.scaling_mode = "fsr"

            self.btn_nis.setChecked(
                False
            )

            self.btn_nearest.setChecked(
                False
            )

        else:

            self.scaling_mode = None

        self.update_scaling_ui()

    # ============================================================
    # BOTÓN NIS
    # ============================================================

    def nis_button_clicked(self):

        if self.btn_nis.isChecked():

            self.scaling_mode = "nis"

            self.btn_fsr.setChecked(
                False
            )

            self.btn_nearest.setChecked(
                False
            )

        else:

            self.scaling_mode = None

        self.update_scaling_ui()

    # ============================================================
    # BOTÓN NEAREST
    # ============================================================

    def nearest_button_clicked(self):

        if self.btn_nearest.isChecked():

            self.scaling_mode = "nearest"

            self.btn_fsr.setChecked(
                False
            )

            self.btn_nis.setChecked(
                False
            )

        else:

            self.scaling_mode = None

        self.update_scaling_ui()

    # ============================================================
    # PARSEAR GAMESCOPE
    # ============================================================

    def parse_gamescope_command(
        self,
        cmd
    ):

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

            "mangohud": False,
            "mangohud_config": load_mangohud_config_file(),
        }

        # ====================================================
        # WINEDLLOVERRIDES
        # ====================================================

        match = re.search(
            r'WINEDLLOVERRIDES=(?:"([^"]*)"|\'([^\']*)\'|(\S+))',
            cmd
        )

        if match:

            result["winedll"] = next(
                value
                for value in match.groups()
                if value is not None
            )

        # ====================================================
        # RESOLUCIÓN BASE
        # ====================================================

        match = re.search(
            r'(?:^|\s)-w\s+(\d+)',
            cmd
        )

        if match:
            result["res_w"] = int(
                match.group(1)
            )

        match = re.search(
            r'(?:^|\s)-h\s+(\d+)',
            cmd
        )

        if match:
            result["res_h"] = int(
                match.group(1)
            )

        # ====================================================
        # RESOLUCIÓN SALIDA
        # ====================================================

        match = re.search(
            r'(?:^|\s)-W\s+(\d+)',
            cmd
        )

        if match:
            result["out_w"] = int(
                match.group(1)
            )

        match = re.search(
            r'(?:^|\s)-H\s+(\d+)',
            cmd
        )

        if match:
            result["out_h"] = int(
                match.group(1)
            )

        # ====================================================
        # ESCALADO
        # ====================================================

        if re.search(
            r'(?:^|\s)-F\s+fsr(?:\s|$)',
            cmd
        ):

            result["fsr_enabled"] = True

        elif re.search(
            r'(?:^|\s)-F\s+nis(?:\s|$)',
            cmd
        ):

            result["nis_enabled"] = True

        elif re.search(
            r'(?:^|\s)-F\s+nearest(?:\s|$)',
            cmd
        ):

            result["nearest_enabled"] = True

        # ====================================================
        # SHARPNESS
        #
        # Tanto FSR como NIS utilizan ahora:
        #
        # --sharpness N
        # ====================================================

        match = re.search(
            r'--sharpness\s+([0-9]+(?:\.[0-9]+)?)',
            cmd
        )

        if match:

            sharpness = float(
                match.group(1)
            )

            if sharpness.is_integer():
                sharpness = int(
                    sharpness
                )

            if result["fsr_enabled"]:

                result["sharpness"] = sharpness

            elif result["nis_enabled"]:

                result["nis_sharpness"] = sharpness

        # ====================================================
        # FLAGS
        # ====================================================

        result["hdr"] = (
            "--hdr-enabled" in cmd
        )

        result["vrr"] = (
            "--adaptive-sync" in cmd
        )

        result["immediate"] = (
            "--immediate-flips" in cmd
        )

        result["mangohud"] = (
            "--mangoapp" in cmd
        )

        return result

    # ============================================================
    # APLICAR OPCIONES PARSEADAS
    # ============================================================

    def apply_parsed_options(
        self,
        opts
    ):

        # ====================================================
        # RESOLUCIÓN BASE
        # ====================================================

        if (
            opts["res_w"] is not None
            and opts["res_h"] is not None
        ):

            for index in range(
                self.base_res_combo.count()
            ):

                data = (
                    self.base_res_combo.itemData(
                        index
                    )
                )

                if not data:
                    continue

                width, height = data

                if (
                    width == opts["res_w"]
                    and height == opts["res_h"]
                ):

                    self.base_res_combo.setCurrentIndex(
                        index
                    )

                    break

        # ====================================================
        # RESOLUCIÓN SALIDA
        # ====================================================

        if (
            opts["out_w"] is not None
            and opts["out_h"] is not None
        ):

            for index in range(
                self.out_res_combo.count()
            ):

                data = (
                    self.out_res_combo.itemData(
                        index
                    )
                )

                if not data:
                    continue

                width, height = data

                if (
                    width == opts["out_w"]
                    and height == opts["out_h"]
                ):

                    self.out_res_combo.setCurrentIndex(
                        index
                    )

                    break

        # ====================================================
        # HDR / VRR / LATENCIA
        # ====================================================

        self.chk_hdr.setChecked(
            opts["hdr"]
        )

        self.chk_vrr.setChecked(
            opts["vrr"]
        )

        self.chk_immediate.setChecked(
            opts["immediate"]
        )

        # ====================================================
        # MANGOHUD
        # ====================================================

        self.btn_mangohud.setChecked(
            opts.get(
                "mangohud",
                False
            )
        )

        self.mangohud_config = opts.get(
            "mangohud_config",
            load_mangohud_config_file(),
        )

        # ====================================================
        # WINEDLLOVERRIDES
        # ====================================================

        self.txt_winedll.setText(
            opts["winedll"]
        )

        # ====================================================
        # RESET ESCALADO
        # ====================================================

        self.btn_fsr.blockSignals(
            True
        )

        self.btn_nis.blockSignals(
            True
        )

        self.btn_nearest.blockSignals(
            True
        )

        self.btn_fsr.setChecked(
            opts["fsr_enabled"]
        )

        self.btn_nis.setChecked(
            opts["nis_enabled"]
        )

        self.btn_nearest.setChecked(
            opts["nearest_enabled"]
        )

        self.btn_fsr.blockSignals(
            False
        )

        self.btn_nis.blockSignals(
            False
        )

        self.btn_nearest.blockSignals(
            False
        )

        # ====================================================
        # DETERMINAR MODO
        # ====================================================

        if opts["fsr_enabled"]:

            self.scaling_mode = "fsr"

        elif opts["nis_enabled"]:

            self.scaling_mode = "nis"

        elif opts["nearest_enabled"]:

            self.scaling_mode = "nearest"

        else:

            self.scaling_mode = None

        # ====================================================
        # FSR SHARPNESS
        # ====================================================

        if opts["sharpness"] is not None:

            slider_value = round(
                (20 - float(opts["sharpness"])) / 4
            )

            slider_value = max(
                0,
                min(
                    5,
                    slider_value
                )
            )

            self.sharpness_slider.setValue(
                slider_value
            )

        # ====================================================
        # NIS SHARPNESS
        # ====================================================

        if opts["nis_sharpness"] is not None:

            slider_value = round(
                (20 - float(opts["nis_sharpness"])) / 4
            )

            slider_value = max(
                0,
                min(
                    5,
                    slider_value
                )
            )

            self.nis_slider.setValue(
                slider_value
            )

        # ====================================================
        # ACTUALIZAR INTERFAZ
        # ====================================================

        self.update_scaling_ui()

    # ============================================================
    # ESCANEAR JUEGOS
    # ============================================================

    def scan_clicked(self):

        if self.scan_thread is not None and self.scan_thread.isRunning():
            return

        self.btn_scan.setEnabled(False)
        self.btn_scan.setText("Buscando…")

        self.scan_thread = QtCore.QThread(self)
        self.scan_worker = GameScanWorker()
        self.scan_worker.moveToThread(self.scan_thread)
        self.scan_thread.started.connect(self.scan_worker.run)
        self.scan_worker.finished.connect(self.scan_finished)
        self.scan_worker.failed.connect(self.scan_failed)
        self.scan_worker.finished.connect(self.scan_thread.quit)
        self.scan_worker.failed.connect(self.scan_thread.quit)
        self.scan_thread.finished.connect(self.scan_worker.deleteLater)
        self.scan_thread.finished.connect(self.scan_thread.deleteLater)
        self.scan_thread.finished.connect(self.scan_thread_finished)
        self.scan_thread.start()

    @QtCore.pyqtSlot(object)
    def scan_finished(self, games):

        self.games = games

        self.games.sort(
            key=lambda game: (
                game.get("name")
                or ""
            ).lower()
        )

        self.game_list.clear()

        for game in self.games:

            item = (
                QtWidgets.QListWidgetItem(
                    game["name"]
                )
            )

            item.setData(
                QtCore.Qt.ItemDataRole.UserRole,
                game
            )

            self.game_list.addItem(
                item
            )

            self.load_icon(
                game["appid"],
                item
            )

        # A long game title must not increase the minimum width of the window.
        self.game_list.setMinimumWidth(0)
        self.game_list.setMaximumWidth(16777215)

        self.game_list.updateGeometry()

    @QtCore.pyqtSlot(str)
    def scan_failed(self, error):
        QtWidgets.QMessageBox.warning(
            self,
            "Error al buscar juegos",
            f"No se pudieron leer las bibliotecas de Steam:\n{error}",
        )

    @QtCore.pyqtSlot()
    def scan_thread_finished(self):
        self.btn_scan.setEnabled(True)
        self.btn_scan.setText("Buscar juegos")
        self.scan_thread = None
        self.scan_worker = None

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

            self.lbl_game_dir.clear()

            self.exec_list.clear()

            self._game_pixmap = None
            self.img_label.clear()

            self.cmd_text.clear()

            self.base_res_combo.setCurrentIndex(
                0
            )

            self.out_res_combo.setCurrentIndex(
                0
            )

            self.reset_scaling_options()

            return

        game = current.data(
            QtCore.Qt.ItemDataRole.UserRole
        )

        self.current_game = game

        self.lbl_game_dir.set_path(
            game["game_dir"]
        )

        self.exec_list.clear()

        for executable in game["executables"]:

            self.exec_list.addItem(
                executable
            )

        self._game_pixmap = None
        self.img_label.clear()

        self.load_image(
            game["appid"]
        )

        # ====================================================
        # RESET ANTES DE CARGAR CONFIGURACIÓN
        # ====================================================

        self.base_res_combo.setCurrentIndex(
            0
        )

        self.out_res_combo.setCurrentIndex(
            0
        )

        self.reset_scaling_options()

        # ====================================================
        # DETECTAR LAUNCH OPTIONS
        # ====================================================

        active_cmd = (
            get_active_launch_options(
                game["appid"]
            )
        )

        if not active_cmd.strip():

            self.cmd_text.clear()

            return

        self.cmd_text.setPlainText(
            active_cmd
        )

        parsed = (
            self.parse_gamescope_command(
                active_cmd
            )
        )

        self.apply_parsed_options(
            parsed
        )

    # ============================================================
    # RECOGER OPCIONES
    # ============================================================

    def collect_options(self):

        base_data = (
            self.base_res_combo.currentData()
        )

        out_data = (
            self.out_res_combo.currentData()
        )

        if not base_data:

            raise ValueError(
                "Selecciona una resolución base."
            )

        if not out_data:

            raise ValueError(
                "Selecciona una resolución de salida."
            )

        base_w, base_h = base_data
        out_w, out_h = out_data

        # ====================================================
        # FSR
        #
        # Slider:
        # 0 -> 20
        # 1 -> 16
        # 2 -> 12
        # 3 -> 8
        # 4 -> 4
        # 5 -> 0
        # ====================================================

        fsr_sharpness = (
            20
            - (
                self.sharpness_slider.value()
                * 4
            )
        )

        # ====================================================
        # NIS
        #
        # Mismo rango de 0-20 utilizado por
        # --sharpness.
        # ====================================================

        nis_sharpness = (
            20
            - (
                self.nis_slider.value()
                * 4
            )
        )

        return {
            "res_w": base_w,
            "res_h": base_h,

            "out_w": out_w,
            "out_h": out_h,

            "sharpness": (
                fsr_sharpness
                if self.btn_fsr.isChecked()
                else None
            ),

            "nis_sharpness": (
                nis_sharpness
                if self.btn_nis.isChecked()
                else None
            ),

            "hdr": (
                self.chk_hdr.isChecked()
            ),

            "vrr": (
                self.chk_vrr.isChecked()
            ),

            "immediate": (
                self.chk_immediate.isChecked()
            ),

            "winedll": (
                self.txt_winedll.text().strip()
            ),

            "fsr_enabled": (
                self.btn_fsr.isChecked()
            ),

            "nis_enabled": (
                self.btn_nis.isChecked()
            ),

            "nearest_enabled": (
                self.btn_nearest.isChecked()
            ),

            "mangohud": (
                self.btn_mangohud.isChecked()
            ),

            "mangohud_config": self.mangohud_config,
        }

    # ============================================================
    # GENERAR COMANDO
    # ============================================================

    def generate_command(self):

        try:

            opts = (
                self.collect_options()
            )

        except ValueError as error:

            QtWidgets.QMessageBox.warning(
                self,
                "Configuración incompleta",
                str(error)
            )

            return

        command = (
            build_gamescope_command(
                opts
            )
        )

        self.cmd_text.setPlainText(
            command
        )

    # ============================================================
    # COPIAR COMANDO
    # ============================================================

    def copy_command(self):

        command = (
            self.cmd_text
            .toPlainText()
            .strip()
        )

        if not command:

            QtWidgets.QMessageBox.warning(
                self,
                "Sin comando",
                "Genera el comando primero."
            )

            return

        QtWidgets.QApplication.clipboard().setText(
            command
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

        try:

            opts = (
                self.collect_options()
            )

        except ValueError as error:

            QtWidgets.QMessageBox.warning(
                self,
                "Configuración incompleta",
                str(error)
            )

            return

        command = (
            build_gamescope_command(
                opts
            )
        )

        appid = (
            self.current_game["appid"]
        )

        try:

            write_launch_options(
                appid,
                command
            )

        except Exception as error:

            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                "No se pudo escribir "
                f"LaunchOptions:\n{error}"
            )

            return

        self.cmd_text.setPlainText(
            command
        )

        QtWidgets.QMessageBox.information(
            self,
            "Aplicado",
            "LaunchOptions aplicadas "
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

        appid = (
            self.current_game["appid"]
        )

        name = (
            self.current_game["name"]
        )

        try:

            clear_launch_options(
                appid
            )

        except Exception as error:

            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                "No se pudo limpiar "
                f"LaunchOptions:\n{error}"
            )

            return

        self.cmd_text.clear()

        self.base_res_combo.setCurrentIndex(
            0
        )

        self.out_res_combo.setCurrentIndex(
            0
        )

        self.reset_scaling_options()

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

            subprocess.run(
                ["pkill", "-x", "steam"],
                check=False
            )

        except Exception as error:

            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"No se pudo cerrar Steam:\n{error}"
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

    QtGui.QGuiApplication.setDesktopFileName(
        "SteamCommandGen"
    )

    app = (
        QtWidgets.QApplication(
            sys.argv
        )
    )

    app.setApplicationName(
        "SteamCommandGen"
    )

    app.setApplicationDisplayName(
        "Steam Command Gen v3.2.8"
    )

    win = (
        GamescopeManager()
    )

    win.show()

    sys.exit(
        app.exec()
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
