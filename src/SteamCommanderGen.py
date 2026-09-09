#!/usr/bin/env python3
import os
import sys
import vdf
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest


# ============================================================
#  DETECCIÓN DE STEAM
# ============================================================

def detect_steam_paths():
    candidates = [
        os.path.expanduser("~/.steam/steam"),
        os.path.expanduser("~/.local/share/Steam"),
    ]

    for base in candidates:
        if os.path.isdir(base):
            userdata = os.path.join(base, "userdata")
            if os.path.isdir(userdata):
                users = [u for u in os.listdir(userdata) if u.isdigit()]
                steamid = users[0] if users else "0"

                return {
                    "root": base,
                    "steamapps": os.path.join(base, "steamapps"),
                    "libraryfolders": os.path.join(base, "steamapps", "libraryfolders.vdf"),
                    "localconfig": os.path.join(base, "userdata", steamid, "config", "localconfig.vdf"),
                }

    return None


STEAM = detect_steam_paths()
if STEAM is None:
    print("No se encontró Steam.")
    sys.exit(1)


# ============================================================
#  ESCANEO DE BIBLIOTECAS Y JUEGOS
# ============================================================

def get_libraries():
    libs = []
    lf_path = STEAM["libraryfolders"]

    if not os.path.isfile(lf_path):
        return [STEAM["steamapps"]]

    data = vdf.load(open(lf_path, encoding="utf-8", errors="ignore"))
    lf = data.get("libraryfolders", {})

    for k, v in lf.items():
        if isinstance(v, dict) and "path" in v:
            libs.append(os.path.join(v["path"], "steamapps"))

    if STEAM["steamapps"] not in libs:
        libs.append(STEAM["steamapps"])

    return libs


def find_acf_files(path):
    acf_list = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if f.endswith(".acf"):
                acf_list.append(os.path.join(root, f))
    return acf_list


def parse_acf(path):
    data = vdf.load(open(path, encoding="utf-8", errors="ignore"))
    app = data.get("AppState", {})
    return {
        "appid": app.get("appid"),
        "name": app.get("name"),
        "install_dir": app.get("installdir"),
        "acf_path": path,
    }


def find_executables(game_dir):
    if not os.path.isdir(game_dir):
        return []

    exes = []
    for f in os.listdir(game_dir):
        full = os.path.join(game_dir, f)
        if os.path.isfile(full) and f.lower().endswith((".exe", ".sh")):
            exes.append(full)

    if not exes:
        return []

    exes.sort(key=lambda x: os.path.getsize(x), reverse=True)
    return [exes[0]]


def scan_games():
    games = []
    for lib in get_libraries():
        for acf in find_acf_files(lib):
            info = parse_acf(acf)
            if not info["install_dir"]:
                continue

            game_dir = os.path.join(lib, "common", info["install_dir"])
            info["game_dir"] = game_dir
            info["executables"] = find_executables(game_dir)

            if not any(g["appid"] == info["appid"] for g in games):
                games.append(info)

    return games


# ============================================================
#  GENERADOR DE COMANDO GAMESCOPE (SIN env, SIN LD_PRELOAD)
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

    cmd.append("-F fsr")
    cmd.append(f"--fsr-sharpness {opts['sharpness']}")
    cmd.append("-f")
    cmd.append("-- %command%")

    final = " ".join(cmd)
    
    if opts["winedll"]:
        return f'WINEDLLOVERRIDES="{opts["winedll"]}" {final}'
    
    return final

# ============================================================
#  ESCRITURA DE LAUNCH OPTIONS
# ============================================================

def write_launch_options(appid, cmd):
    bases = [
        os.path.expanduser("~/.steam/steam/userdata"),
        os.path.expanduser("~/.local/share/Steam/userdata"),
    ]

    cfg_path = None

    for base in bases:
        if os.path.isdir(base):
            for user in os.listdir(base):
                if user.isdigit():
                    path = os.path.join(base, user, "config", "localconfig.vdf")
                    if os.path.isfile(path):
                        cfg_path = path
                        break
        if cfg_path:
            break

    if not cfg_path:
        raise FileNotFoundError("No se encontró localconfig.vdf")

    data = vdf.load(open(cfg_path, encoding="utf-8", errors="ignore"))

    ulcs = data.setdefault("UserLocalConfigStore", {})
    software = ulcs.setdefault("Software", {})
    valve = software.setdefault("Valve", {})
    steam = valve.setdefault("Steam", {})
    apps = steam.setdefault("apps", {})

    apps.setdefault(str(appid), {})["LaunchOptions"] = cmd

    with open(cfg_path, "w", encoding="utf-8", errors="ignore") as f:
        vdf.dump(data, f, pretty=False)
        
# ============================================================
#  Borrado DE LAUNCH OPTIONS
# ============================================================

def clear_launch_options(appid):
    bases = [
        os.path.expanduser("~/.steam/steam/userdata"),
        os.path.expanduser("~/.local/share/Steam/userdata"),
    ]

    cfg_path = None

    for base in bases:
        if os.path.isdir(base):
            for user in os.listdir(base):
                if user.isdigit():
                    path = os.path.join(base, user, "config", "localconfig.vdf")
                    if os.path.isfile(path):
                        cfg_path = path
                        break
        if cfg_path:
            break

    if not cfg_path:
        raise FileNotFoundError("No se encontró localconfig.vdf")

    data = vdf.load(open(cfg_path, encoding="utf-8", errors="ignore"))

    ulcs = data.setdefault("UserLocalConfigStore", {})
    software = ulcs.setdefault("Software", {})
    valve = software.setdefault("Valve", {})
    steam = valve.setdefault("Steam", {})
    apps = steam.setdefault("apps", {})

    # ✔ Dejar LaunchOptions vacío
    apps.setdefault(str(appid), {})["LaunchOptions"] = ""

    with open(cfg_path, "w", encoding="utf-8", errors="ignore") as f:
        vdf.dump(data, f, pretty=False)
        
def get_active_launch_options(appid):
    bases = [
        os.path.expanduser("~/.steam/steam/userdata"),
        os.path.expanduser("~/.local/share/Steam/userdata"),
    ]

    cfg_path = None

    for base in bases:
        if os.path.isdir(base):
            for user in os.listdir(base):
                if user.isdigit():
                    path = os.path.join(base, user, "config", "localconfig.vdf")
                    if os.path.isfile(path):
                        cfg_path = path
                        break
        if cfg_path:
            break

    if not cfg_path:
        return ""

    data = vdf.load(open(cfg_path, encoding="utf-8", errors="ignore"))

    ulcs = data.get("UserLocalConfigStore", {})
    software = ulcs.get("Software", {})
    valve = software.get("Valve", {})
    steam = valve.get("Steam", {})
    apps = steam.get("apps", {})

    return apps.get(str(appid), {}).get("LaunchOptions", "")


# ============================================================
#  GUI PRINCIPAL
# ============================================================

class GamescopeManager(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        app_icon = QtGui.QIcon.fromTheme("SteamCommandGen")
        self.setWindowIcon(app_icon)
        self.setWindowTitle("Steam Command Gen")
        self.resize(1200, 700)

        self.games = []
        self.current_game = None

        # Lista de juegos
        self.game_list = QtWidgets.QListWidget()
        self.game_list.setIconSize(QtCore.QSize(120, 45))

        # Imagen del juego
        self.img_label = QtWidgets.QLabel()
        self.img_label.setFixedHeight(200)
        self.img_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Panel de opciones
        self.details_widget = QtWidgets.QWidget()
        self.details_layout = QtWidgets.QFormLayout(self.details_widget)

        # Resoluciones
        self.base_res_combo = QtWidgets.QComboBox()
        for label, res in {
            "480p (640x480)": (640, 480),
            "720p (1280x720)": (1280, 720),
            "900p (1600x900)": (1600, 900),
            "1080p (1920x1080)": (1920, 1080),
            "1440p (2560x1440)": (2560, 1440),
        }.items():
            self.base_res_combo.addItem(label, res)

        self.out_res_combo = QtWidgets.QComboBox()
        for label, res in {
            "1080p (1920x1080)": (1920, 1080),
            "1440p (2560x1440)": (2560, 1440),
            "4K (3840x2160)": (3840, 2160),
        }.items():
            self.out_res_combo.addItem(label, res)

        # Nitidez FSR (0–5 → 20–0)
        self.sharpness_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.sharpness_slider.setRange(0, 5)
        self.sharpness_slider.setValue(5)
        self.sharpness_slider.setTickInterval(1)
        self.sharpness_slider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)

        self.sharpness_label = QtWidgets.QLabel("5")
        self.sharpness_slider.valueChanged.connect(lambda v: self.sharpness_label.setText(str(v)))

        sharpness_box = QtWidgets.QHBoxLayout()
        sharpness_box.addWidget(self.sharpness_slider)
        sharpness_box.addWidget(self.sharpness_label)
        
        # WINEDLLOVERRIDES
        self.txt_winedll = QtWidgets.QLineEdit()
        self.txt_winedll.setPlaceholderText("WINEDLLOVERRIDES= (opcional)")
        self.details_layout.addRow("WINEDLLOVERRIDES:", self.txt_winedll)
        
        # Checkboxes
        self.chk_hdr = QtWidgets.QCheckBox("HDR")
        self.chk_vrr = QtWidgets.QCheckBox("VRR (Adaptive Sync)")
        self.chk_immediate = QtWidgets.QCheckBox("Modo Baja Latencia")
        self.chk_immediate.setChecked(True)

        # Ruta del juego
        self.lbl_game_dir = QtWidgets.QLabel("")

        # Ejecutables
        self.exec_list = QtWidgets.QListWidget()

        # Comando generado
        self.cmd_text = QtWidgets.QPlainTextEdit()
        self.cmd_text.setReadOnly(True)

        # Botones
        self.btn_scan = QtWidgets.QPushButton("Buscar juegos")
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
        self.btn_preview = QtWidgets.QPushButton("Generar comando")
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
        self.btn_copy = QtWidgets.QPushButton("Copiar comando")
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
        self.btn_apply = QtWidgets.QPushButton("Aplicar a Steam")
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
        self.btn_clear = QtWidgets.QPushButton("Limpiar Propiedades")
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
        self.btn_kill_steam = QtWidgets.QPushButton("Cerrar Steam")
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
       

        # Layout principal
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QHBoxLayout(main_widget)

        left = QtWidgets.QVBoxLayout()
        left.addWidget(QtWidgets.QLabel("Juegos detectados"))
        left.addWidget(self.game_list)
        left.addWidget(self.btn_scan)

        right = QtWidgets.QVBoxLayout()
        right.addWidget(QtWidgets.QLabel("Imagen del juego"))
        right.addWidget(self.img_label)
        right.addWidget(QtWidgets.QLabel("Configuración"))
        right.addWidget(self.details_widget)
        right.addWidget(QtWidgets.QLabel("Ruta del juego"))
        right.addWidget(self.lbl_game_dir)
        right.addWidget(QtWidgets.QLabel("Ejecutables"))
        right.addWidget(self.exec_list)
        right.addWidget(QtWidgets.QLabel("Comando"))
        right.addWidget(self.cmd_text)

        btns = QtWidgets.QHBoxLayout()
        btns.addWidget(self.btn_preview)
        btns.addWidget(self.btn_copy)
        btns.addWidget(self.btn_apply)
        btns.addWidget(self.btn_clear)
        btns.addWidget(self.btn_kill_steam)

        right.addLayout(btns)

        main_layout.addLayout(left, 2)
        main_layout.addLayout(right, 3)

        self.setCentralWidget(main_widget)

        # Añadir opciones al panel
        self.details_layout.addRow("Resolución base:", self.base_res_combo)
        self.details_layout.addRow("Resolución salida:", self.out_res_combo)
        self.details_layout.addRow("Nitidez FSR (0–5):", sharpness_box)
        self.details_layout.addRow(self.chk_hdr)
        self.details_layout.addRow(self.chk_vrr)
        self.details_layout.addRow(self.chk_immediate)

        # Conexiones
        self.btn_scan.clicked.connect(self.scan_clicked)
        self.game_list.currentItemChanged.connect(self.game_selected)
        self.btn_preview.clicked.connect(self.generate_command)
        self.btn_copy.clicked.connect(self.copy_command)
        self.btn_apply.clicked.connect(self.apply_command)
        self.btn_clear.clicked.connect(self.clear_command)
        self.btn_kill_steam.clicked.connect(self.kill_steam)
        
        QtWidgets.QMessageBox.information(
            self,
            "Aviso importante",
            "SteamCommandGen requiere que Steam esté cerrado para aplicar o borrar LaunchOptions.\n"
            "Si Steam está abierto, los cambios no se guardarán.\n\n"
            "Cierre Steam antes de continuar."
        )

    # ============================================================
    #  CARGA DE IMÁGENES
    # ============================================================

    def load_image(self, appid):
        url = f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/header.jpg"
        req = QNetworkRequest(QtCore.QUrl(url))
        manager = QNetworkAccessManager(self)

        def done(reply):
            if reply.error() == reply.NetworkError.NoError:
                pix = QtGui.QPixmap()
                pix.loadFromData(reply.readAll())
                self.img_label.setPixmap(pix.scaledToWidth(400))
            reply.deleteLater()

        manager.finished.connect(done)
        manager.get(req)

    def load_icon(self, appid, item):
        url = f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/capsule_231x87.jpg"
        req = QNetworkRequest(QtCore.QUrl(url))
        manager = QNetworkAccessManager(self)

        def done(reply):
            if reply.error() == reply.NetworkError.NoError:
                pix = QtGui.QPixmap()
                pix.loadFromData(reply.readAll())

        # ✔ Comprobar que el item sigue en la lista
                if item.listWidget() is not None:
                    item.setIcon(QtGui.QIcon(pix))

            reply.deleteLater()


        manager.finished.connect(done)
        manager.get(req)

    # ============================================================
    #  LÓGICA
    # ============================================================
        
    def parse_gamescope_command(self, cmd):
        import re

        result = {
            "res_w": None,
            "res_h": None,
            "out_w": None,
            "out_h": None,
            "sharpness": None,
            "hdr": False,
            "vrr": False,
            "immediate": False,
            "winedll": "",
        }

        m = re.search(r'WINEDLLOVERRIDES="([^"]+)"', cmd)
        if m:
            result["winedll"] = m.group(1)

        m = re.search(r'-w (\d+)', cmd)
        if m:
            result["res_w"] = int(m.group(1))

        m = re.search(r'-h (\d+)', cmd)
        if m:
            result["res_h"] = int(m.group(1))

        m = re.search(r'-W (\d+)', cmd)
        if m:
            result["out_w"] = int(m.group(1))

        m = re.search(r'-H (\d+)', cmd)
        if m:
            result["out_h"] = int(m.group(1))

        m = re.search(r'--fsr-sharpness (\d+)', cmd)
        if m:
            result["sharpness"] = int(m.group(1))

        result["hdr"] = "--hdr-enabled" in cmd
        result["vrr"] = "--adaptive-sync" in cmd
        result["immediate"] = "--immediate-flips" in cmd

        return result
    
    def apply_parsed_options(self, opts):
        # Resolución base
        for i in range(self.base_res_combo.count()):
            w, h = self.base_res_combo.itemData(i)
            if w == opts["res_w"] and h == opts["res_h"]:
                self.base_res_combo.setCurrentIndex(i)
                break

        # Resolución salida
        for i in range(self.out_res_combo.count()):
            w, h = self.out_res_combo.itemData(i)
            if w == opts["out_w"] and h == opts["out_h"]:
                self.out_res_combo.setCurrentIndex(i)
                break

        # Nitidez
        if opts["sharpness"] is not None:
            slider_val = (20 - opts["sharpness"]) // 4
            self.sharpness_slider.setValue(slider_val)

        # Flags
        self.chk_hdr.setChecked(opts["hdr"])
        self.chk_vrr.setChecked(opts["vrr"])
        self.chk_immediate.setChecked(opts["immediate"])

        # WINEDLLOVERRIDES
        self.txt_winedll.setText(opts["winedll"])

    
    def scan_clicked(self):
        self.games = scan_games()
        self.game_list.clear()

        for g in self.games:
            item = QtWidgets.QListWidgetItem(f"{g['name']} (appid {g['appid']})")
            item.setData(QtCore.Qt.ItemDataRole.UserRole, g)
            self.game_list.addItem(item)
            self.load_icon(g["appid"], item)

    def game_selected(self, current, previous):
        if current is None:
            self.current_game = None
            self.lbl_game_dir.setText("")
            self.exec_list.clear()
            self.img_label.clear()
            return

        game = current.data(QtCore.Qt.ItemDataRole.UserRole)
        self.current_game = game

        self.lbl_game_dir.setText(game["game_dir"])
        self.exec_list.clear()

        for exe in game["executables"]:
            self.exec_list.addItem(exe)

        self.load_image(game["appid"])
                # === Detectar comando activo ===
        active_cmd = get_active_launch_options(game["appid"])
        if active_cmd.strip():
            self.cmd_text.setPlainText(active_cmd)

            parsed = self.parse_gamescope_command(active_cmd)
            self.apply_parsed_options(parsed)
        else:
            self.cmd_text.setPlainText("")


    def collect_options(self):
        base_w, base_h = self.base_res_combo.currentData()
        out_w, out_h = self.out_res_combo.currentData()

        # Conversión nitidez: slider 0–5 → valor real 20–0
        slider_val = self.sharpness_slider.value()
        sharpness_real = 20 - (slider_val * 4)

        return {
            "res_w": base_w,
            "res_h": base_h,
            "out_w": out_w,
            "out_h": out_h,
            "sharpness": sharpness_real,
            "hdr": self.chk_hdr.isChecked(),
            "vrr": self.chk_vrr.isChecked(),
            "immediate": self.chk_immediate.isChecked(),
            "winedll": self.txt_winedll.text().strip(),
        }

    def generate_command(self):
        opts = self.collect_options()
        cmd = build_gamescope_command(opts)
        self.cmd_text.setPlainText(cmd)

    def copy_command(self):
        cmd = self.cmd_text.toPlainText().strip()
        if not cmd:
            QtWidgets.QMessageBox.warning(self, "Sin comando", "Genera el comando primero.")
            return
        QtWidgets.QApplication.clipboard().setText(cmd)
        QtWidgets.QMessageBox.information(self, "Copiado", "Comando copiado al portapapeles.")

    def apply_command(self):
        if self.current_game is None:
            QtWidgets.QMessageBox.warning(self, "Sin juego", "Selecciona un juego.")
            return

        opts = self.collect_options()
        cmd = build_gamescope_command(opts)
        appid = self.current_game["appid"]

        try:
            write_launch_options(appid, cmd)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo escribir LaunchOptions:\n{e}")
            return

        QtWidgets.QMessageBox.information(self, "Aplicado", f"LaunchOptions aplicadas para appid {appid}.")
    
    def clear_command(self):
        if self.current_game is None:
            QtWidgets.QMessageBox.warning(self, "Sin juego", "Selecciona un juego.")
            return

        appid = self.current_game["appid"]
        name = self.current_game["name"]
        
        try:
            clear_launch_options(appid)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"No se pudo limpiar LaunchOptions:\n{e}")
            return

        self.cmd_text.clear()
        QtWidgets.QMessageBox.information(
            self,
            "Comando eliminado",
            f"Se han borrado las LaunchOptions de:\n\n{name}\n\n(appid {appid})"
        )
        
    def kill_steam(self):
        import subprocess
        subprocess.call(["pkill", "-f", "steam"])

        QtWidgets.QMessageBox.information(
            self,
            "Steam cerrado",
            "Steam ha sido cerrado correctamente."
        )

# ============================================================
#  MAIN
# ============================================================

def main():
    QtGui.QGuiApplication.setDesktopFileName("SteamCommandGen")
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("SteamCommandGen")
    app.setApplicationDisplayName("SteamCommandGen")
    
    win = GamescopeManager()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

