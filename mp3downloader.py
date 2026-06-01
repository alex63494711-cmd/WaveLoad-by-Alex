# ─────────────────────────────────────────────────────────────────────────────
#  WaveLoad v7.0  –  PyQt6 Edition
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, re, threading, subprocess, shutil, zipfile, hashlib, json
import urllib.request, urllib.parse
from PyQt6.QtWidgets import (
    QProgressBar,
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit,
    QSizePolicy, QGraphicsOpacityEffect, QButtonGroup, QScrollArea,
    QFrame, QStackedWidget
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve,
    QRect, QSize, QTimer, QPoint, pyqtProperty
)
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QIcon, QPixmap

VERSION   = "7.0"
APP_NAME  = "WaveLoad"
GITHUB_RAW = "https://raw.githubusercontent.com/alex63494711-cmd/alex-mp3-song-app/refs/heads/main/mp3downloader.py"
GITHUB_EXE = "https://github.com/alex63494711-cmd/alex-mp3-song-app/releases/latest/download/WaveLoad.exe"

IS_EXE   = getattr(sys, 'frozen', False)
BASE_DIR = os.path.dirname(os.path.abspath(sys.executable if IS_EXE else __file__))
TOOLS_DIR   = os.path.join(BASE_DIR, "tools")
YTDLP_PATH  = os.path.join(TOOLS_DIR, "yt-dlp.exe")
FFMPEG_PATH = os.path.join(TOOLS_DIR, "ffmpeg.exe")
YTDLP_URL   = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
FFMPEG_URL  = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
USERS_FILE  = os.path.join(BASE_DIR, "users.json")
ADMIN_CODE  = "WL-ADMIN-2024"
CREATE_NO_WINDOW = 0x08000000

def _h(s): return hashlib.sha256(s.encode()).hexdigest()
def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE) as f: return json.load(f)
    except: pass
    return {}
def save_users(u):
    with open(USERS_FILE, "w") as f: json.dump(u, f)

# ── Stylesheet ────────────────────────────────────────────────────────────────
STYLE = """
* { font-family: 'Segoe UI', sans-serif; }
QMainWindow, QWidget#root { background: #0a0a14; }
QScrollArea { background: #0a0a14; border: none; }
QScrollBar:vertical { background: #0a0a14; width: 6px; border-radius: 3px; }
QScrollBar::handle:vertical { background: #8b5cf6; border-radius: 3px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QWidget#card {
    background: #111122;
    border: 1px solid #2a2a50;
    border-radius: 12px;
}
QWidget#card2 { background: #181832; border-radius: 0px; }

QLineEdit {
    background: #1e1e3a;
    border: 1px solid #2a2a50;
    border-radius: 8px;
    color: #f0efff;
    padding: 8px 14px;
    font-size: 10pt;
}
QLineEdit:focus { border: 1px solid #8b5cf6; }
QLineEdit::placeholder { color: #50507a; }

QTextEdit {
    background: #111122;
    border: none;
    color: #9090b8;
    font-family: Consolas;
    font-size: 9pt;
    padding: 4px 8px;
}

QPushButton {
    background: #8b5cf6;
    color: #f0efff;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
    font-size: 10pt;
    font-weight: bold;
}
QPushButton:hover { background: #a78bfa; }
QPushButton:pressed { background: #6d28d9; }
QPushButton:disabled { background: #1e1e3a; color: #50507a; }

QPushButton#ghost {
    background: #1e1e3a;
    color: #9090b8;
}
QPushButton#ghost:hover { background: #2a2a50; color: #f0efff; }

QPushButton#green {
    background: #10b981;
    color: #000;
}
QPushButton#green:hover { background: #34d399; }

QPushButton#spotify {
    background: #1db954;
    color: #000;
}
QPushButton#spotify:hover { background: #17a349; }

QPushButton#tiktok {
    background: #5bcdd4;
    color: #000;
}
QPushButton#tiktok:hover { background: #3fb8bf; }

QPushButton#danger {
    background: transparent;
    color: #9090b8;
    font-size: 14pt;
    padding: 4px 10px;
}
QPushButton#danger:hover { background: #f87171; color: #fff; border-radius: 6px; }

QLabel { color: #f0efff; background: transparent; }
QLabel#sub { color: #50507a; font-size: 9pt; }
QLabel#muted { color: #9090b8; font-size: 9pt; }
QLabel#green { color: #34d399; }
QLabel#red { color: #f87171; font-size: 9pt; }
QLabel#accent { color: #a78bfa; font-size: 9pt; }

QWidget#tab_active {
    background: #8b5cf6;
    border-radius: 0px;
}
QWidget#tab_inactive {
    background: #181832;
    border-radius: 0px;
}
"""

# ── Worker Thread ─────────────────────────────────────────────────────────────
class Worker(QThread):
    log     = pyqtSignal(str)
    done    = pyqtSignal(bool, str)
    file_out= pyqtSignal(str)

    def __init__(self, cmd):
        super().__init__()
        self.cmd = cmd

    def run(self):
        try:
            proc = subprocess.Popen(
                self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                creationflags=CREATE_NO_WINDOW)
            for line in proc.stdout:
                line = line.rstrip()
                if not line: continue
                if os.path.sep in line and (line.endswith(".mp3") or line.endswith(".mp4")):
                    self.file_out.emit(line.strip())
                else:
                    self.log.emit(line)
            proc.wait()
            self.done.emit(proc.returncode == 0, "")
        except Exception as e:
            self.done.emit(False, str(e))


class ToolsWorker(QThread):
    log  = pyqtSignal(str)
    done = pyqtSignal()

    def run(self):
        os.makedirs(TOOLS_DIR, exist_ok=True)
        try:
            if not os.path.exists(YTDLP_PATH):
                self.log.emit("yt-dlp wird heruntergeladen...")
                urllib.request.urlretrieve(YTDLP_URL, YTDLP_PATH)
                self.log.emit("yt-dlp OK")
            if not os.path.exists(FFMPEG_PATH):
                self.log.emit("ffmpeg wird heruntergeladen (~80 MB)...")
                zp = os.path.join(TOOLS_DIR, "ffmpeg.zip")
                urllib.request.urlretrieve(FFMPEG_URL, zp)
                self.log.emit("Entpacke ffmpeg...")
                with zipfile.ZipFile(zp) as z:
                    for m in z.namelist():
                        if m.endswith("ffmpeg.exe"):
                            z.extract(m, TOOLS_DIR)
                            shutil.move(os.path.join(TOOLS_DIR, m), FFMPEG_PATH)
                            break
                os.remove(zp)
                for d in os.listdir(TOOLS_DIR):
                    dp = os.path.join(TOOLS_DIR, d)
                    if os.path.isdir(dp): shutil.rmtree(dp, ignore_errors=True)
                self.log.emit("ffmpeg OK")
            self.log.emit("[Bereit]  Strg+V = sofort herunterladen")
        except Exception as e:
            self.log.emit(f"Fehler: {e}")
        self.done.emit()


# ── Reusable Widgets ──────────────────────────────────────────────────────────
def card(parent=None):
    w = QWidget(parent); w.setObjectName("card"); return w

def label(text, size=10, bold=False, color=None, parent=None):
    l = QLabel(text, parent)
    l.setFont(QFont("Segoe UI", size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
    if color: l.setStyleSheet(f"color: {color};")
    return l

def entry(placeholder="", password=False):
    e = QLineEdit()
    e.setPlaceholderText(placeholder)
    if password: e.setEchoMode(QLineEdit.EchoMode.Password)
    e.setFixedHeight(42)
    return e

def btn(text, obj_name=None, height=40):
    b = QPushButton(text)
    b.setFixedHeight(height)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if obj_name: b.setObjectName(obj_name)
    return b

def hline(color="#2a2a50"):
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"color: {color}; background: {color};")
    f.setFixedHeight(1); return f


class SectionCard(QWidget):
    def __init__(self, title, subtitle, accent="#8b5cf6", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # Header
        hdr = QWidget(); hdr.setObjectName("card2")
        hdr.setStyleSheet(f"background:#181832; border-radius:0; border-top-left-radius:12px; border-top-right-radius:12px;")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(0,0,16,0)
        # accent bar
        bar = QWidget(); bar.setFixedWidth(4)
        bar.setStyleSheet(f"background:{accent}; border-top-left-radius:12px;")
        hl.addWidget(bar)
        tl = QLabel(title); tl.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        tl.setStyleSheet("color:#f0efff; padding: 10px 8px;")
        hl.addWidget(tl)
        sl = QLabel(subtitle); sl.setObjectName("sub")
        sl.setStyleSheet("color:#50507a; font-size:9pt;")
        hl.addWidget(sl)
        hl.addStretch()
        root.addWidget(hdr)
        root.addWidget(hline())

        # Body
        self.body = QWidget()
        self.body.setStyleSheet("background:#111122; border-bottom-left-radius:12px; border-bottom-right-radius:12px;")
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(16,10,16,12)
        self.body_layout.setSpacing(8)
        root.addWidget(self.body)

    def add(self, widget): self.body_layout.addWidget(widget)
    def add_layout(self, layout): self.body_layout.addLayout(layout)


# ── Settings Overlay ──────────────────────────────────────────────────────────
class SettingsPanel(QWidget):
    def __init__(self, parent, output_dir_getter, output_dir_setter, quality_setter, open_folder_getter, open_folder_setter):
        super().__init__(parent)
        self.get_dir    = output_dir_getter
        self.set_dir    = output_dir_setter
        self.set_quality= quality_setter
        self.get_open   = open_folder_getter
        self.set_open   = open_folder_setter
        self.setFixedSize(500, 340)
        self.setStyleSheet("""
            QWidget { background: #181832; border-radius: 12px; }
            QWidget#hdr { background: #111122; border-top-left-radius:12px; border-top-right-radius:12px; border-bottom-left-radius:0; border-bottom-right-radius:0; }
        """)
        self._build()
        self.hide()
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self._anim.setDuration(320)

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # Header
        hdr = QWidget(); hdr.setObjectName("hdr"); hdr.setFixedHeight(50)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(20,0,12,0)
        hl.addWidget(label("⚙  Einstellungen", 12, True))
        hl.addStretch()
        close = btn("✕", "danger", 34); close.setFixedWidth(34)
        close.clicked.connect(self.slide_out)
        hl.addWidget(close)
        root.addWidget(hdr)

        # Accent line
        acc = QWidget(); acc.setFixedHeight(2)
        acc.setStyleSheet("background:#8b5cf6; border-radius:0;")
        root.addWidget(acc)

        body = QWidget(); body.setStyleSheet("background:#181832; border-bottom-left-radius:12px; border-bottom-right-radius:12px;")
        bl = QVBoxLayout(body); bl.setContentsMargins(24,18,24,18); bl.setSpacing(14)
        root.addWidget(body)

        # Ordner
        bl.addWidget(label("Speicherordner", 10, True))
        dr = QHBoxLayout(); dr.setSpacing(10)
        self.dir_label = QLabel()
        self.dir_label.setStyleSheet("background:#1e1e3a; color:#9090b8; padding:8px 12px; border-radius:8px; font-size:9pt;")
        self.dir_label.setText(self.get_dir())
        dr.addWidget(self.dir_label, 1)
        b = btn("Auswählen"); b.setFixedWidth(110)
        b.clicked.connect(self._browse)
        dr.addWidget(b)
        bl.addLayout(dr)

        # Qualität
        bl.addWidget(label("Audioqualität", 10, True))
        qr = QHBoxLayout(); qr.setSpacing(8)
        self._q_btns = QButtonGroup(self)
        for i,(lbl,val) in enumerate([("320 kbps","0"),("192 kbps","5"),("128 kbps","9")]):
            b2 = QPushButton(lbl)
            b2.setCheckable(True); b2.setFixedHeight(36)
            b2.setCursor(Qt.CursorShape.PointingHandCursor)
            b2.setProperty("qval", val)
            b2.setStyleSheet("""
                QPushButton { background:#1e1e3a; color:#9090b8; border-radius:8px; font-size:9pt; font-weight:bold; }
                QPushButton:checked { background:#8b5cf6; color:#f0efff; }
                QPushButton:hover { background:#2a2a50; }
            """)
            self._q_btns.addButton(b2, i)
            qr.addWidget(b2)
            if i == 0: b2.setChecked(True)
        self._q_btns.idToggled.connect(self._q_changed)
        bl.addLayout(qr)

        # Nach Download
        bl.addWidget(label("Nach Download", 10, True))
        self._open_cb = QPushButton("✓  Dateimanager öffnen mit Datei markiert")
        self._open_cb.setCheckable(True); self._open_cb.setChecked(self.get_open())
        self._open_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_cb.setStyleSheet("""
            QPushButton { background:#1e1e3a; color:#9090b8; border-radius:8px; font-size:9pt; text-align:left; padding:8px 14px; }
            QPushButton:checked { background:#1e2a1e; color:#34d399; border:1px solid #10b981; }
        """)
        self._open_cb.toggled.connect(self.set_open)
        bl.addWidget(self._open_cb)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Ordner wählen", self.get_dir())
        if d: self.set_dir(d); self.dir_label.setText(d)

    def _q_changed(self, idx, checked):
        if checked:
            val = self._q_btns.button(idx).property("qval")
            self.set_quality(val)

    def slide_in(self):
        self.show(); self.raise_()
        pw, ph = self.parent().width(), self.parent().height()
        w, h   = self.width(), self.height()
        cx = (pw - w) // 2; cy = (ph - h) // 2
        self._anim.stop()
        self._anim.setStartValue(QPoint(cx, -h))
        self._anim.setEndValue(QPoint(cx, cy))
        self._anim.start()

    def slide_out(self):
        pw, ph = self.parent().width(), self.parent().height()
        w, h   = self.width(), self.height()
        cx = (pw - w) // 2; cy = (ph - h) // 2
        self._anim.stop()
        self._anim.setEasingCurve(QEasingCurve.Type.InBack)
        self._anim.setDuration(220)
        self._anim.setStartValue(QPoint(cx, cy))
        self._anim.setEndValue(QPoint(cx, -h))
        self._anim.finished.connect(self._on_close_done)
        self._anim.start()

    def _on_close_done(self):
        self.hide()
        self._anim.finished.disconnect(self._on_close_done)
        self._anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self._anim.setDuration(320)


# ── Main Window ───────────────────────────────────────────────────────────────

class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hide()
        self.setStyleSheet("background:rgba(0,0,0,180);")
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label = QLabel("Features werden heruntergeladen...")
        self.label.setStyleSheet("color:white;font-size:24px;font-weight:700;")
        self.bar = QProgressBar()
        self.bar.setRange(0,0)
        self.bar.setFixedWidth(350)
        lay.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.bar, alignment=Qt.AlignmentFlag.AlignCenter)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._overlay.setGeometry(self.centralWidget().rect())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(740, 860)
        self.setMinimumSize(640, 600)
        self._output_dir  = os.path.join(os.path.expanduser("~"), "Music")
        self._quality     = "0"
        self._open_folder = True
        self._last_file   = None
        self._worker      = None

        ico = os.path.join(BASE_DIR, "icon.ico")
        if os.path.exists(ico): self.setWindowIcon(QIcon(ico))

        root = QWidget(); root.setObjectName("root"); self.setCentralWidget(root)
        self._overlay = LoadingOverlay(root)
        ml = QVBoxLayout(root); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)

        # Scroll area
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setObjectName("scroll")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QWidget(); inner.setStyleSheet("background:#0a0a14;")
        il = QVBoxLayout(inner); il.setContentsMargins(20,20,20,24); il.setSpacing(10)
        scroll.setWidget(inner)
        ml.addWidget(scroll)

        # Settings panel overlay – must be created before header (button refs it)
        self._settings = SettingsPanel(
            root,
            lambda: self._output_dir,
            self._set_dir,
            self._set_quality,
            lambda: self._open_folder,
            self._set_open_folder,
        )

        self._build_header(il)
        self._build_yt(il)
        self._build_search(il)
        self._build_spotify(il)
        self._build_tiktok(il)
        self._build_dl_btn(il)
        self._build_log(il)
        il.addStretch()

        self._overlay.setGeometry(root.rect())
        QTimer.singleShot(400, self._check_tools)

    def _set_dir(self, d): self._output_dir = d
    def _set_quality(self, q): self._quality = q
    def _set_open_folder(self, v): self._open_folder = v

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._overlay.setGeometry(self.centralWidget().rect())
        # Keep settings panel centered when window resizes
        if self._settings.isVisible():
            pw, ph = self.centralWidget().width(), self.centralWidget().height()
            w, h = self._settings.width(), self._settings.height()
            self._settings.move((pw-w)//2, (ph-h)//2)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_V,) and e.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self._paste_detect()

    def _paste_detect(self):
        c = QApplication.clipboard().text().strip()
        if not c: return
        if "spotify.com" in c:
            self._sp_entry.setText(c); self._log("Spotify erkannt – suche..."); QTimer.singleShot(300, self._do_spotify)
        elif "tiktok.com" in c or "instagram.com" in c:
            self._ti_entry.setText(c); self._log("TikTok/Instagram erkannt!")
        elif c.startswith("http"):
            self._url_entry.setText(c); self._log("Link erkannt – lade..."); QTimer.singleShot(300, self._start_dl)

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self, parent_layout):
        hdr = QWidget(); hdr.setObjectName("card")
        hdr.setStyleSheet("background:#111122; border-radius:12px; border-bottom:2px solid #8b5cf6;")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(20,14,20,14)

        # Icon box
        icon_box = QWidget(); icon_box.setFixedSize(46,46)
        icon_box.setStyleSheet("background:#6d28d9; border-radius:10px;")
        ibl = QVBoxLayout(icon_box); ibl.setContentsMargins(0,0,0,0)
        ic = QLabel("♪"); ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setFont(QFont("Segoe UI",20,QFont.Weight.Bold)); ic.setStyleSheet("color:#f0efff;")
        ibl.addWidget(ic)
        hl.addWidget(icon_box)

        # Name
        nw = QWidget(); nl = QVBoxLayout(nw); nl.setContentsMargins(12,0,0,0); nl.setSpacing(1)
        t = QLabel(APP_NAME); t.setFont(QFont("Segoe UI Black",20,QFont.Weight.Bold)); t.setStyleSheet("color:#f0efff;")
        s = QLabel("MP3 Downloader"); s.setObjectName("sub")
        nl.addWidget(t); nl.addWidget(s)
        hl.addWidget(nw); hl.addStretch()

        upd = btn("↑ Update", "ghost", 36); upd.setFixedWidth(100)
        upd.clicked.connect(self._check_update)
        hl.addWidget(upd)
        sett = btn("⚙", "ghost", 36); sett.setFixedWidth(44)
        sett.clicked.connect(self._settings.slide_in)
        hl.addWidget(sett)
        v = QLabel(f"v{VERSION}"); v.setObjectName("sub"); v.setContentsMargins(8,0,0,0)
        hl.addWidget(v)
        parent_layout.addWidget(hdr)

    # ── Sections ──────────────────────────────────────────────────────────────
    def _build_yt(self, pl):
        sec = SectionCard("YouTube / SoundCloud", "Link einfügen oder Strg+V", "#8b5cf6")
        row = QHBoxLayout(); row.setSpacing(10)
        self._url_entry = entry("https://youtube.com/...")
        paste = btn("Einfügen", "ghost", 42); paste.setFixedWidth(90)
        paste.clicked.connect(lambda: self._url_entry.setText(QApplication.clipboard().text().strip()))
        row.addWidget(self._url_entry, 1); row.addWidget(paste)
        sec.add_layout(row); pl.addWidget(sec)

    def _build_search(self, pl):
        sec = SectionCard("Song suchen", "Name + Künstler direkt laden", "#a78bfa")
        r1 = QHBoxLayout(); r1.setSpacing(10)
        lbl = QLabel("Song"); lbl.setFixedWidth(60); lbl.setObjectName("muted")
        self._search_entry = entry("Songname...")
        r1.addWidget(lbl); r1.addWidget(self._search_entry, 1)
        r2 = QHBoxLayout(); r2.setSpacing(10)
        lbl2 = QLabel("Künstler"); lbl2.setFixedWidth(60); lbl2.setObjectName("muted")
        self._artist_entry = entry("Künstler / Interpret...")
        sb = btn("Suchen & laden", height=42); sb.setFixedWidth(140)
        sb.clicked.connect(self._search_btn)
        r2.addWidget(lbl2); r2.addWidget(self._artist_entry, 1); r2.addWidget(sb)
        sec.add_layout(r1); sec.add_layout(r2); pl.addWidget(sec)

    def _build_spotify(self, pl):
        sec = SectionCard("Spotify", "Link einfügen → YouTube-Suche", "#1db954")
        row = QHBoxLayout(); row.setSpacing(10)
        self._sp_entry = entry("Spotify-Link hier einfügen...")
        pe = btn("Einfügen", "ghost", 42); pe.setFixedWidth(90)
        pe.clicked.connect(lambda: self._sp_entry.setText(QApplication.clipboard().text().strip()))
        lb = btn("Laden", "spotify", 42); lb.setFixedWidth(80)
        lb.clicked.connect(self._do_spotify)
        row.addWidget(self._sp_entry, 1); row.addWidget(pe); row.addWidget(lb)
        sec.add_layout(row); pl.addWidget(sec)

    def _build_tiktok(self, pl):
        sec = SectionCard("TikTok / Instagram", "Sound als MP3 herunterladen", "#5bcdd4")
        row = QHBoxLayout(); row.setSpacing(10)
        self._ti_entry = entry("TikTok / Instagram Link...")
        pe = btn("Einfügen", "ghost", 42); pe.setFixedWidth(90)
        pe.clicked.connect(lambda: self._ti_entry.setText(QApplication.clipboard().text().strip()))
        lb = btn("Laden", "tiktok", 42); lb.setFixedWidth(80)
        lb.clicked.connect(self._do_tiktok)
        row.addWidget(self._ti_entry, 1); row.addWidget(pe); row.addWidget(lb)
        sec.add_layout(row); pl.addWidget(sec)

    def _build_dl_btn(self, pl):
        self._dl_btn = QPushButton("  ↓   MP3 herunterladen")
        self._dl_btn.setFixedHeight(58)
        self._dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dl_btn.setFont(QFont("Segoe UI Black", 14))
        self._dl_btn.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #8b5cf6, stop:1 #6d28d9); color:#f0efff; border-radius:12px; }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #a78bfa, stop:1 #8b5cf6); }
            QPushButton:pressed { background: #6d28d9; }
            QPushButton:disabled { background: #1e1e3a; color:#50507a; }
        """)
        self._dl_btn.clicked.connect(self._start_dl)
        pl.addWidget(self._dl_btn)

        # Progress bar (custom)
        self._prog = QWidget()
        self._prog.setFixedHeight(4)
        self._prog.setStyleSheet("background:#1e1e3a; border-radius:2px;")
        self._prog_inner = QWidget(self._prog)
        self._prog_inner.setStyleSheet("background:#8b5cf6; border-radius:2px;")
        self._prog_inner.setFixedHeight(4)
        self._prog_inner.setFixedWidth(0)
        self._prog_anim_dir = 1; self._prog_pos = 0
        self._prog_timer = QTimer(); self._prog_timer.timeout.connect(self._tick_prog)
        pl.addWidget(self._prog)

        # OK banner
        self._ok_banner = QWidget()
        self._ok_banner.setStyleSheet("background:#071a10; border:1px solid #10b981; border-radius:10px;")
        ol = QHBoxLayout(self._ok_banner); ol.setContentsMargins(20,12,20,12)
        ck = QLabel("✓"); ck.setFont(QFont("Segoe UI Black",20)); ck.setStyleSheet("color:#34d399;")
        ol.addWidget(ck)
        tf = QWidget(); tf.setStyleSheet("background:transparent;")
        tfl = QVBoxLayout(tf); tfl.setContentsMargins(12,0,0,0); tfl.setSpacing(2)
        tfl.addWidget(label("Download abgeschlossen!", 11, True, "#34d399"))
        self._ok_path = QLabel(""); self._ok_path.setObjectName("green")
        self._ok_path.setStyleSheet("color:#10b981; font-size:9pt;")
        tfl.addWidget(self._ok_path)
        ol.addWidget(tf, 1)
        self._ok_banner.hide()
        pl.addWidget(self._ok_banner)

    def _build_log(self, pl):
        card_w = QWidget(); card_w.setObjectName("card")
        cl = QVBoxLayout(card_w); cl.setContentsMargins(0,0,0,0); cl.setSpacing(0)
        hdr = QWidget(); hdr.setStyleSheet("background:#111122; border-top-left-radius:12px; border-top-right-radius:12px;")
        hl2 = QHBoxLayout(hdr); hl2.setContentsMargins(16,8,16,8)
        dot = QLabel("●"); dot.setStyleSheet("color:#10b981; font-size:8pt;")
        ll = QLabel("LOG"); ll.setObjectName("sub")
        hl2.addWidget(dot); hl2.addWidget(ll); hl2.addStretch()
        clr = btn("leeren", "ghost", 26); clr.setFixedWidth(60)
        clr.setStyleSheet("QPushButton{background:transparent;color:#50507a;font-size:8pt;} QPushButton:hover{color:#f0efff;}")
        clr.clicked.connect(lambda: self._log_box.clear())
        hl2.addWidget(clr)
        cl.addWidget(hdr); cl.addWidget(hline())
        self._log_box = QTextEdit(); self._log_box.setReadOnly(True); self._log_box.setFixedHeight(140)
        cl.addWidget(self._log_box)
        pl.addWidget(card_w)

    # ── Progress animation ─────────────────────────────────────────────────────
    def _tick_prog(self):
        w = self._prog.width()
        bw = max(80, w // 3)
        self._prog_pos += self._prog_anim_dir * 6
        if self._prog_pos + bw >= w: self._prog_anim_dir = -1
        if self._prog_pos <= 0: self._prog_anim_dir = 1
        self._prog_inner.setGeometry(self._prog_pos, 0, bw, 4)

    def _start_prog(self): self._prog_timer.start(16)
    def _stop_prog(self):
        self._prog_timer.stop()
        self._prog_inner.setFixedWidth(0)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _log(self, msg): self._log_box.append(msg)

    def _busy(self, on):
        self._dl_btn.setEnabled(not on)
        self._dl_btn.setText("  ⏳  Lädt..." if on else "  ↓   MP3 herunterladen")
        if on: self._start_prog()
        else: self._stop_prog()

    def _show_ok(self, folder):
        self._ok_path.setText(folder)
        self._ok_banner.show()
        QTimer.singleShot(6000, self._ok_banner.hide)

    def _open_explorer(self, fp):
        if self._open_folder and fp and os.path.exists(fp):
            subprocess.Popen(["explorer","/select,",os.path.normpath(fp)],
                             creationflags=CREATE_NO_WINDOW)

    # ── Tools ─────────────────────────────────────────────────────────────────
    def _check_tools(self):
        missing = [n for n,p in [("yt-dlp",YTDLP_PATH),("ffmpeg",FFMPEG_PATH)] if not os.path.exists(p)]
        if missing:
            self._log(f"Installiere: {', '.join(missing)}...")
            self._tw = ToolsWorker()
            self._tw.log.connect(self._log)
            self._tw.done.connect(lambda: self._busy(False))
            self._busy(True); self._tw.start()
        else:
            self._log("[Bereit]  Strg+V = sofort herunterladen")

    # ── Search ────────────────────────────────────────────────────────────────
    def _yt_search(self, q):
        req = urllib.request.Request(
            "https://www.youtube.com/results?search_query="+urllib.parse.quote(q),
            headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8","ignore")
        m = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
        return f"https://www.youtube.com/watch?v={m.group(1)}" if m else None

    def _search_btn(self):
        s = self._search_entry.text().strip()
        if not s: return
        a = self._artist_entry.text().strip()
        self._busy(True)
        def run():
            try:
                url = self._yt_search(f"{a} {s} official audio".strip())
                if url:
                    self._url_entry.setText(url)
                    self._search_entry.clear(); self._artist_entry.clear()
                    QTimer.singleShot(0, self._start_dl)
                else: self._log("Nichts gefunden.")
            except Exception as e: self._log(f"Fehler: {e}")
            finally: QTimer.singleShot(0, lambda: self._busy(False))
        threading.Thread(target=run, daemon=True).start()

    def _do_spotify(self):
        url = self._sp_entry.text().strip()
        if not url or "spotify.com" not in url: return
        self._busy(True)
        def run():
            try:
                req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    html = r.read().decode("utf-8","ignore")
                m = re.search(r"<title>(.*?)</title>", html)
                if not m: self._log("Titel nicht lesbar."); return
                name = re.sub(r"\s*[|\-–]\s*Spotify.*$","",m.group(1)).strip()
                yt = self._yt_search(name+" official audio")
                if yt:
                    self._url_entry.setText(yt); self._sp_entry.clear()
                    QTimer.singleShot(0, self._start_dl)
                else: self._log("Kein YouTube-Treffer.")
            except Exception as e: self._log(f"Fehler: {e}")
            finally: QTimer.singleShot(0, lambda: self._busy(False))
        threading.Thread(target=run, daemon=True).start()

    # ── Download ──────────────────────────────────────────────────────────────
    def _start_dl(self):
        url = self._url_entry.text().strip()
        if not url: return
        if not os.path.exists(YTDLP_PATH): self._log("Tools noch nicht bereit!"); return
        out = os.path.join(self._output_dir, "%(title)s.%(ext)s")
        cmd = [YTDLP_PATH,"-x","--audio-format","mp3","--audio-quality",self._quality,
               "--ffmpeg-location",TOOLS_DIR,"-o",out,"--no-playlist","--print","after_move:filepath",url]
        self._run_worker(cmd, lambda ok, fp: self._dl_done(ok, fp, clear_fn=lambda: self._url_entry.clear()))

    def _do_tiktok(self):
        url = self._ti_entry.text().strip().split("?")[0]
        if not url: return
        if not os.path.exists(YTDLP_PATH): self._log("Tools noch nicht bereit!"); return
        out = os.path.join(self._output_dir, "%(title).80s.%(ext)s")
        cmd = [YTDLP_PATH,"-x","--audio-format","mp3","--audio-quality",self._quality,
               "--ffmpeg-location",TOOLS_DIR,"--no-playlist","--no-check-certificate",
               "--user-agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
               "-o",out,"--print","after_move:filepath",url]
        self._run_worker(cmd, lambda ok, fp: self._dl_done(ok, fp, clear_fn=lambda: self._ti_entry.clear()))

    def _run_worker(self, cmd, on_done):
        self._busy(True); self._ok_banner.hide(); self._last_file = None
        self._worker = Worker(cmd)
        self._worker.log.connect(self._log)
        self._worker.file_out.connect(lambda f: setattr(self, '_last_file', f))
        def _done(ok, err):
            self._busy(False)
            if ok:
                on_done(ok, self._last_file)
            else:
                self._log("Fehlgeschlagen.")
        self._worker.done.connect(_done)
        self._worker.start()

    def _dl_done(self, ok, fp, clear_fn=None):
        if ok:
            self._log(f"Fertig!  →  {self._output_dir}")
            if clear_fn: clear_fn()
            self._show_ok(self._output_dir)
            QTimer.singleShot(500, lambda: self._open_explorer(fp))
        else:
            self._log("Fehlgeschlagen.")

    def _check_update(self):
        self._log("Suche Updates...")
        def run():
            try:
                req = urllib.request.Request(GITHUB_RAW, headers={"User-Agent":"Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as r: content = r.read().decode("utf-8")
                m = re.search(r'^VERSION\s*=\s*"([^"]+)"', content, re.MULTILINE)
                nv = m.group(1) if m else VERSION
                if nv == VERSION: self._log(f"Aktuell (v{VERSION})"); return
                self._log(f"Neue Version v{nv}!")
            except Exception as e: self._log(f"Update-Fehler: {e}")
        threading.Thread(target=run, daemon=True).start()


# ── Login Window ──────────────────────────────────────────────────────────────
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WaveLoad")
        self.setFixedSize(460, 580)
        self.logged_in = False
        ico = os.path.join(BASE_DIR, "icon.ico")
        if os.path.exists(ico): self.setWindowIcon(QIcon(ico))
        self._build()

    def _build(self):
        root = QWidget(); root.setObjectName("root"); self.setCentralWidget(root)
        self._overlay = LoadingOverlay(root)
        ml = QVBoxLayout(root); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)

        # Logo top
        top = QWidget(); top.setStyleSheet("background:#0a0a14;")
        tl = QVBoxLayout(top); tl.setContentsMargins(0,30,0,10); tl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        box = QWidget(); box.setFixedSize(52,52); box.setStyleSheet("background:#6d28d9; border-radius:12px;")
        bl2 = QVBoxLayout(box); bl2.setContentsMargins(0,0,0,0)
        ic = QLabel("♪"); ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setFont(QFont("Segoe UI",22,QFont.Weight.Bold)); ic.setStyleSheet("color:#f0efff;")
        bl2.addWidget(ic)
        bw = QWidget(); bw.setStyleSheet("background:transparent;")
        bwl = QHBoxLayout(bw); bwl.addWidget(box)
        tl.addWidget(bw)
        t = QLabel("WaveLoad"); t.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        t.setFont(QFont("Segoe UI Black",20,QFont.Weight.Bold)); t.setStyleSheet("color:#f0efff; background:transparent;")
        tl.addWidget(t)
        ml.addWidget(top)

        # Tab bar
        tab_bar = QWidget(); tab_bar.setStyleSheet("background:#181832;")
        tb = QHBoxLayout(tab_bar); tb.setContentsMargins(40,0,40,0); tb.setSpacing(0)
        self._tab_login = QPushButton("  Anmelden  "); self._tab_login.setFixedHeight(42)
        self._tab_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self._tab_reg   = QPushButton("  Registrieren  "); self._tab_reg.setFixedHeight(42)
        self._tab_reg.setCursor(Qt.CursorShape.PointingHandCursor)
        for b in (self._tab_login, self._tab_reg):
            b.setFont(QFont("Segoe UI",10,QFont.Weight.Bold))
            tb.addWidget(b)
        self._tab_login.clicked.connect(lambda: self._show_page(0))
        self._tab_reg.clicked.connect(lambda: self._show_page(1))
        ml.addWidget(tab_bar)

        # Pages
        self._pages = QStackedWidget()
        self._pages.setStyleSheet("background:#111122;")
        self._pages.addWidget(self._build_login_page())
        self._pages.addWidget(self._build_reg_page())
        ml.addWidget(self._pages, 1)

        # Admin
        adm = QWidget(); adm.setStyleSheet("background:#0a0a14;")
        al = QVBoxLayout(adm); al.setContentsMargins(40,12,40,20); al.setSpacing(8)
        al.addWidget(hline())
        ar = QHBoxLayout(); ar.setSpacing(8)
        al2 = QLabel("Admin:"); al2.setObjectName("sub"); al2.setFixedWidth(50)
        self._adm_entry = entry("Admin-Code", password=True)
        ab = btn("→", height=36); ab.setFixedWidth(40)
        ab.clicked.connect(self._admin_login)
        ar.addWidget(al2); ar.addWidget(self._adm_entry, 1); ar.addWidget(ab)
        al.addLayout(ar)
        ml.addWidget(adm)

        self._show_page(0)

    def _build_login_page(self):
        w = QWidget(); w.setStyleSheet("background:#111122;")
        l = QVBoxLayout(w); l.setContentsMargins(40,24,40,24); l.setSpacing(10)
        l.addWidget(label("Benutzername", 9, True, "#9090b8"))
        self._user_e = entry("Dein Benutzername")
        l.addWidget(self._user_e)
        l.addWidget(label("Passwort", 9, True, "#9090b8"))
        self._pass_e = entry("Dein Passwort", password=True)
        l.addWidget(self._pass_e)
        self._err = QLabel(""); self._err.setObjectName("red")
        self._err.setStyleSheet("color:#f87171; font-size:9pt;")
        l.addWidget(self._err)
        lb = btn("Anmelden", height=44)
        lb.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        lb.clicked.connect(self._login)
        l.addWidget(lb)
        l.addStretch()
        self._pass_e.returnPressed.connect(self._login)
        return w

    def _build_reg_page(self):
        w = QWidget(); w.setStyleSheet("background:#111122;")
        l = QVBoxLayout(w); l.setContentsMargins(40,24,40,24); l.setSpacing(8)
        l.addWidget(label("Benutzername", 9, True, "#9090b8"))
        self._reg_user = entry("Gewünschter Benutzername")
        l.addWidget(self._reg_user)
        l.addWidget(label("Passwort", 9, True, "#9090b8"))
        self._reg_pass = entry("Mind. 6 Zeichen", password=True)
        l.addWidget(self._reg_pass)
        l.addWidget(label("Passwort bestätigen", 9, True, "#9090b8"))
        self._reg_pass2 = entry("Passwort wiederholen", password=True)
        l.addWidget(self._reg_pass2)
        self._reg_err = QLabel(""); self._reg_err.setStyleSheet("color:#f87171; font-size:9pt;")
        l.addWidget(self._reg_err)
        rb = btn("Konto erstellen →", "green", 44)
        rb.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        rb.clicked.connect(self._do_register)
        l.addWidget(rb)
        l.addStretch()
        self._reg_pass2.returnPressed.connect(self._do_register)
        return w

    def _show_page(self, idx):
        self._pages.setCurrentIndex(idx)
        active = "QPushButton{background:#8b5cf6;color:#f0efff;border-radius:0;font-size:10pt;font-weight:bold;border-bottom:2px solid #a78bfa;}"
        inactive = "QPushButton{background:#181832;color:#50507a;border-radius:0;font-size:10pt;font-weight:bold;} QPushButton:hover{color:#9090b8;}"
        self._tab_login.setStyleSheet(active if idx==0 else inactive)
        self._tab_reg.setStyleSheet(active if idx==1 else inactive)

    def _login(self):
        u = self._user_e.text().strip(); p = self._pass_e.text()
        if not u or not p: self._err.setText("Bitte alle Felder ausfüllen."); return
        users = load_users()
        if u not in users or users[u] != _h(p):
            self._err.setText("Benutzername oder Passwort falsch."); return
        self.logged_in = True; self.close()

    def _do_register(self):
        u = self._reg_user.text().strip(); p = self._reg_pass.text(); p2 = self._reg_pass2.text()
        if not u or not p: self._reg_err.setText("Bitte alle Felder ausfüllen."); return
        if len(p) < 6: self._reg_err.setText("Passwort mind. 6 Zeichen."); return
        if p != p2: self._reg_err.setText("Passwörter stimmen nicht überein."); return
        users = load_users()
        if u in users: self._reg_err.setText("Benutzername bereits vergeben."); return
        users[u] = _h(p); save_users(users)
        self.logged_in = True; self.close()

    def _admin_login(self):
        if self._adm_entry.text().strip() == ADMIN_CODE:
            self.logged_in = True; self.close()
        else:
            self._err.setText("Ungültiger Admin-Code.")
# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    app.setFont(QFont("Segoe UI", 10))

    login = LoginWindow()
    login.show()
    app.exec()

    if not login.logged_in:
        sys.exit(0)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())
