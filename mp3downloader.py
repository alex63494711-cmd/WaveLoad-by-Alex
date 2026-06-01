# WaveLoad v10.0
import sys, os, re, threading, subprocess, shutil, zipfile, hashlib, json
import urllib.request, urllib.parse
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit,
    QScrollArea, QStackedWidget, QButtonGroup, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QPoint
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

VERSION    = "10.0"
APP_NAME   = "WaveLoad"
GITHUB_RAW = "https://raw.githubusercontent.com/alex63494711-cmd/alex-mp3-song-app/refs/heads/main/mp3downloader.py"
GITHUB_EXE = "https://github.com/alex63494711-cmd/alex-mp3-song-app/releases/latest/download/WaveLoad.exe"
IS_EXE     = getattr(sys, 'frozen', False)
BASE_DIR   = os.path.dirname(os.path.abspath(sys.executable if IS_EXE else __file__))
TOOLS_DIR  = os.path.join(BASE_DIR, "tools")
YTDLP_PATH = os.path.join(TOOLS_DIR, "yt-dlp.exe")
FFMPEG_PATH= os.path.join(TOOLS_DIR, "ffmpeg.exe")
YTDLP_URL  = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
FFMPEG_URL = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
USERS_FILE = os.path.join(BASE_DIR, "users.json")
ADMIN_CODE = "WL-ADMIN-2024"
CNW        = 0x08000000

# ── Farben ────────────────────────────────────────────────────────────────────
C_BG      = "#0f0f13"   # Hintergrund
C_SURFACE = "#1c1c23"   # Cards / Sections
C_RAISED  = "#242430"   # Inputs, Buttons-Hintergrund
C_BORDER  = "#35354a"   # Rahmen
C_ACCENT  = "#7c6af5"   # Lila Akzent
C_ACCENT2 = "#9d8fff"   # Hover
C_TEXT    = "#f0f0ff"   # Haupttext
C_MUTED   = "#9090b0"   # Sekundärtext
C_DIM     = "#55556a"   # Placeholder / Labels
C_GREEN   = "#22c55e"
C_RED     = "#f87171"
C_SPOTIFY = "#1db954"
C_TIKTOK  = "#2bbdc4"

def _h(s): return hashlib.sha256(s.encode()).hexdigest()
def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE) as f: return json.load(f)
    except: pass
    return {}
def save_users(u):
    with open(USERS_FILE,"w") as f: json.dump(u,f)

STYLE = f"""
* {{ font-family: 'Segoe UI', Arial, sans-serif; color: {C_TEXT}; }}
QMainWindow, QDialog {{ background: {C_BG}; }}
QWidget#bg   {{ background: {C_BG}; }}
QWidget#surf {{ background: {C_SURFACE}; border-radius: 12px; }}

QScrollArea  {{ background: {C_BG}; border: none; }}
QScrollBar:vertical {{ background: {C_BG}; width: 4px; border-radius: 2px; }}
QScrollBar::handle:vertical {{ background: {C_BORDER}; border-radius: 2px; min-height: 20px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QLineEdit {{
    background: {C_RAISED};
    border: 1.5px solid {C_BORDER};
    border-radius: 8px;
    color: {C_TEXT};
    padding: 0 14px;
    font-size: 10pt;
    selection-background-color: {C_ACCENT};
}}
QLineEdit:focus {{ border-color: {C_ACCENT}; background: #26263a; }}
QLineEdit[readOnly="true"] {{ color: {C_MUTED}; }}

QTextEdit {{
    background: {C_SURFACE};
    border: none;
    color: {C_MUTED};
    font-family: Consolas, monospace;
    font-size: 9pt;
    padding: 8px 12px;
}}

QPushButton {{
    background: {C_ACCENT};
    color: {C_TEXT};
    border: none;
    border-radius: 8px;
    font-size: 10pt;
    font-weight: bold;
    padding: 0 18px;
}}
QPushButton:hover   {{ background: {C_ACCENT2}; }}
QPushButton:pressed {{ background: #5a48d4; }}
QPushButton:disabled {{ background: {C_RAISED}; color: {C_DIM}; }}

QPushButton#flat {{
    background: {C_RAISED};
    color: {C_MUTED};
    border: 1.5px solid {C_BORDER};
}}
QPushButton#flat:hover {{ background: #2e2e3e; color: {C_TEXT}; border-color: {C_ACCENT}; }}

QPushButton#spotify {{ background: {C_SPOTIFY}; color: #000; border: none; }}
QPushButton#spotify:hover {{ background: #25d160; }}
QPushButton#tiktok  {{ background: {C_TIKTOK};  color: #000; border: none; }}
QPushButton#tiktok:hover  {{ background: #38d4db; }}

QPushButton#close {{
    background: {C_RAISED};
    color: {C_MUTED};
    border: none;
    border-radius: 6px;
    font-size: 13pt;
    font-weight: bold;
    padding: 0;
}}
QPushButton#close:hover {{ background: {C_RED}; color: #fff; }}

QLabel {{ background: transparent; color: {C_TEXT}; }}
"""

# ── Workers ───────────────────────────────────────────────────────────────────
class Worker(QThread):
    log = pyqtSignal(str); file_out = pyqtSignal(str); done = pyqtSignal(bool)
    def __init__(self, cmd): super().__init__(); self.cmd = cmd
    def run(self):
        try:
            proc = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding="utf-8", errors="replace", creationflags=CNW)
            for line in proc.stdout:
                line = line.rstrip()
                if not line: continue
                if os.path.sep in line and line.endswith((".mp3",".mp4")): self.file_out.emit(line.strip())
                else: self.log.emit(line)
            proc.wait(); self.done.emit(proc.returncode == 0)
        except Exception as e: self.log.emit(f"Fehler: {e}"); self.done.emit(False)

class ToolsWorker(QThread):
    log = pyqtSignal(str); done = pyqtSignal()
    def run(self):
        os.makedirs(TOOLS_DIR, exist_ok=True)
        try:
            if not os.path.exists(YTDLP_PATH):
                self.log.emit("yt-dlp wird installiert...")
                urllib.request.urlretrieve(YTDLP_URL, YTDLP_PATH); self.log.emit("yt-dlp ✓")
            if not os.path.exists(FFMPEG_PATH):
                self.log.emit("ffmpeg wird installiert (~80 MB)...")
                zp = os.path.join(TOOLS_DIR,"ffmpeg.zip")
                urllib.request.urlretrieve(FFMPEG_URL, zp)
                with zipfile.ZipFile(zp) as z:
                    for m in z.namelist():
                        if m.endswith("ffmpeg.exe"):
                            z.extract(m, TOOLS_DIR)
                            shutil.move(os.path.join(TOOLS_DIR,m), FFMPEG_PATH); break
                os.remove(zp)
                for d in os.listdir(TOOLS_DIR):
                    dp = os.path.join(TOOLS_DIR,d)
                    if os.path.isdir(dp): shutil.rmtree(dp, ignore_errors=True)
                self.log.emit("ffmpeg ✓")
            self.log.emit("Bereit — Strg+V zum schnellen Download")
        except Exception as e: self.log.emit(f"Fehler: {e}")
        self.done.emit()

# ── UI Helpers ────────────────────────────────────────────────────────────────
def E(ph="", pw=False, h=44):
    e = QLineEdit(); e.setPlaceholderText(ph); e.setFixedHeight(h)
    if pw: e.setEchoMode(QLineEdit.EchoMode.Password)
    return e

def B(text, oid=None, h=44, w=None):
    b = QPushButton(text); b.setFixedHeight(h)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if oid: b.setObjectName(oid)
    if w:   b.setFixedWidth(w)
    return b

def L(text, size=10, color=C_TEXT, bold=False):
    l = QLabel(text)
    l.setFont(QFont("Segoe UI", size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
    l.setStyleSheet(f"color:{color}; background:transparent;")
    return l

def HSep():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"background:{C_BORDER}; border:none;"); f.setFixedHeight(1)
    return f

class Section(QWidget):
    """Surface card with accent bar left."""
    def __init__(self, title, accent=C_ACCENT):
        super().__init__(); self.setObjectName("surf")
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        # header row
        hdr = QWidget(); hdr.setStyleSheet(f"background:{C_SURFACE}; border-top-left-radius:12px; border-top-right-radius:12px;")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(0,0,16,0); hl.setSpacing(0)
        bar = QWidget(); bar.setFixedWidth(4)
        bar.setStyleSheet(f"background:{accent}; border-top-left-radius:12px;")
        hl.addWidget(bar)
        tl = L(title, 10, C_TEXT, True); tl.setContentsMargins(14,12,0,12)
        hl.addWidget(tl); hl.addStretch()
        root.addWidget(hdr)
        root.addWidget(HSep())
        # body
        self.body = QWidget(); self.body.setStyleSheet(f"background:{C_SURFACE}; border-bottom-left-radius:12px; border-bottom-right-radius:12px;")
        self.bl = QVBoxLayout(self.body); self.bl.setContentsMargins(16,14,16,16); self.bl.setSpacing(10)
        root.addWidget(self.body)
    def add(self, w): self.bl.addWidget(w)
    def row(self, l): self.bl.addLayout(l)

# ── Settings Panel ────────────────────────────────────────────────────────────
class SettingsPanel(QWidget):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            SettingsPanel {{
                background: {C_SURFACE};
                border-radius: 14px;
                border: 1.5px solid {C_BORDER};
            }}
        """)
        self.setFixedWidth(480)
        self._build(); self.hide()
        self._anim = QPropertyAnimation(self, b"pos")

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # ── Header
        hdr = QWidget()
        hdr.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        hdr.setStyleSheet(f"background:{C_RAISED}; border-top-left-radius:14px; border-top-right-radius:14px;")
        hdr.setFixedHeight(56)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(20,0,14,0); hl.setSpacing(0)
        title = QLabel("Einstellungen")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{C_TEXT}; background:transparent;")
        hl.addWidget(title); hl.addStretch()
        close = QPushButton("✕")
        close.setFixedSize(34, 34)
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setObjectName("close")
        close.clicked.connect(self.slide_out)
        hl.addWidget(close)
        root.addWidget(hdr)

        # Accent line under header
        acc = QWidget(); acc.setFixedHeight(2)
        acc.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        acc.setStyleSheet(f"background:{C_ACCENT};")
        root.addWidget(acc)

        # ── Body
        body = QWidget()
        body.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        body.setStyleSheet(f"background:{C_SURFACE}; border-bottom-left-radius:14px; border-bottom-right-radius:14px;")
        bl = QVBoxLayout(body); bl.setContentsMargins(22,20,22,22); bl.setSpacing(18)
        root.addWidget(body)

        # Ordner
        bl.addWidget(QLabel("Speicherordner") if False else self._lbl("Speicherordner"))
        dr = QHBoxLayout(); dr.setSpacing(10)
        self.dir_e = QLineEdit(); self.dir_e.setReadOnly(True); self.dir_e.setFixedHeight(42)
        self.dir_e.setText(self.app._output_dir)
        self.dir_e.setStyleSheet(f"background:{C_RAISED}; border:1.5px solid {C_BORDER}; border-radius:8px; color:{C_MUTED}; padding:0 12px; font-size:10pt;")
        pick = QPushButton("···"); pick.setFixedSize(42,42); pick.setCursor(Qt.CursorShape.PointingHandCursor)
        pick.setObjectName("flat"); pick.clicked.connect(self._browse)
        dr.addWidget(self.dir_e,1); dr.addWidget(pick); bl.addLayout(dr)

        # Qualität
        bl.addWidget(self._lbl("Audioqualität"))
        qr = QHBoxLayout(); qr.setSpacing(8); self._qg = QButtonGroup(self)
        for i,(t,v) in enumerate([("320 kbps","0"),("192 kbps","5"),("128 kbps","9")]):
            b = QPushButton(t); b.setCheckable(True); b.setFixedHeight(42)
            b.setCursor(Qt.CursorShape.PointingHandCursor); b.setProperty("qval",v)
            b.setStyleSheet(f"QPushButton{{background:{C_RAISED};color:{C_MUTED};border-radius:8px;font-size:9pt;font-weight:bold;border:1.5px solid {C_BORDER};}} QPushButton:checked{{background:{C_ACCENT};color:{C_TEXT};border-color:{C_ACCENT};}} QPushButton:hover{{background:#2e2e3e;color:{C_TEXT};}}")
            self._qg.addButton(b,i); qr.addWidget(b)
            if i==0: b.setChecked(True)
        self._qg.idToggled.connect(lambda i,c: c and setattr(self.app,'_quality',self._qg.button(i).property("qval")))
        bl.addLayout(qr)

        # Nach Download
        bl.addWidget(self._lbl("Nach Download"))
        self._ocb = QPushButton("  Dateimanager nach Download öffnen")
        self._ocb.setCheckable(True); self._ocb.setChecked(True); self._ocb.setFixedHeight(42)
        self._ocb.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ocb.setStyleSheet(f"QPushButton{{background:{C_RAISED};color:{C_MUTED};border-radius:8px;font-size:9pt;text-align:left;padding:0 14px;border:1.5px solid {C_BORDER};}} QPushButton:checked{{background:#132218;color:{C_GREEN};border-color:#166534;}}")
        self._ocb.toggled.connect(lambda v: setattr(self.app,'_open_folder',v))
        bl.addWidget(self._ocb)
        self.adjustSize()

    def _lbl(self, text):
        l = QLabel(text); l.setStyleSheet(f"color:{C_DIM}; font-size:9pt; background:transparent;")
        return l

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Ordner wählen", self.app._output_dir)
        if d: self.app._output_dir = d; self.dir_e.setText(d)

    def slide_in(self):
        self.adjustSize()
        pw = self.parent().width(); ph = self.parent().height()
        w = self.width(); h = self.height()
        cx = (pw-w)//2; cy = (ph-h)//2
        self.move(cx, -h); self.show(); self.raise_()
        self._anim.stop()
        self._anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self._anim.setDuration(400)
        self._anim.setStartValue(QPoint(cx, -h))
        self._anim.setEndValue(QPoint(cx, cy))
        self._anim.start()

    def slide_out(self):
        pw = self.parent().width(); ph = self.parent().height()
        w = self.width(); h = self.height()
        cx = (pw-w)//2; cy = (ph-h)//2
        self._anim.stop()
        self._anim.setEasingCurve(QEasingCurve.Type.InBack)
        self._anim.setDuration(260)
        self._anim.setStartValue(QPoint(cx, cy))
        self._anim.setEndValue(QPoint(cx, -h))
        def _hide():
            self.hide()
            try: self._anim.finished.disconnect(_hide)
            except: pass
        self._anim.finished.connect(_hide)
        self._anim.start()

# ── Main Window ───────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME); self.resize(720,820); self.setMinimumSize(600,560)
        self._output_dir  = os.path.join(os.path.expanduser("~"),"Music")
        self._quality     = "0"
        self._open_folder = True
        self._last_file   = None
        ico = os.path.join(BASE_DIR,"icon.ico")
        if os.path.exists(ico): self.setWindowIcon(QIcon(ico))

        root = QWidget(); root.setObjectName("bg"); self.setCentralWidget(root)
        ml = QVBoxLayout(root); ml.setContentsMargins(0,0,0,0)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QWidget(); inner.setStyleSheet(f"background:{C_BG};")
        il = QVBoxLayout(inner); il.setContentsMargins(22,22,22,28); il.setSpacing(10)
        scroll.setWidget(inner); ml.addWidget(scroll)

        self._settings = SettingsPanel(root, self)
        self._build_header(il)
        self._build_yt(il)
        self._build_search(il)
        self._build_spotify(il)
        self._build_tiktok(il)
        self._build_dl(il)
        self._build_log(il)
        il.addStretch()

        QTimer.singleShot(400, self._check_tools)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._settings.isVisible():
            pw = self.centralWidget().width(); ph = self.centralWidget().height()
            w = self._settings.width(); h = self._settings.height()
            self._settings.move((pw-w)//2, (ph-h)//2)

    def keyPressEvent(self, e):
        if e.key()==Qt.Key.Key_V and e.modifiers()==Qt.KeyboardModifier.ControlModifier:
            c = QApplication.clipboard().text().strip()
            if not c: return
            if "spotify.com" in c:
                self._sp.setText(c); QTimer.singleShot(200, self._do_spotify)
            elif "tiktok.com" in c or "instagram.com" in c:
                self._ti.setText(c)
            elif c.startswith("http"):
                self._url.setText(c); QTimer.singleShot(200, self._start_dl)

    def _build_header(self, pl):
        w = QWidget(); w.setObjectName("surf")
        hl = QHBoxLayout(w); hl.setContentsMargins(18,14,18,14)
        hl.addWidget(L(APP_NAME, 17, C_TEXT, True))
        hl.addWidget(L(f"v{VERSION}", 8, C_DIM))
        hl.addStretch()
        u = B("Update","flat",36,90); u.clicked.connect(self._check_update); hl.addWidget(u)
        hl.addSpacing(8)
        s = B("⚙","flat",36,36); s.clicked.connect(self._settings.slide_in); hl.addWidget(s)
        pl.addWidget(w)

    def _build_yt(self, pl):
        sec = Section("YouTube / SoundCloud")
        r = QHBoxLayout(); r.setSpacing(8)
        self._url = E("Link einfügen...")
        p = B("Einfügen","flat",44,95)
        p.clicked.connect(lambda: self._url.setText(QApplication.clipboard().text().strip()))
        r.addWidget(self._url,1); r.addWidget(p); sec.row(r); pl.addWidget(sec)

    def _build_search(self, pl):
        sec = Section("Song suchen", C_ACCENT2)
        r = QHBoxLayout(); r.setSpacing(8)
        self._sq = E("Songname...")
        self._ar = E("Künstler...")
        sb = B("Suchen & laden", h=44, w=145); sb.clicked.connect(self._search_btn)
        r.addWidget(self._sq,1); r.addWidget(self._ar,1); r.addWidget(sb)
        sec.row(r); pl.addWidget(sec)

    def _build_spotify(self, pl):
        sec = Section("Spotify", C_SPOTIFY)
        r = QHBoxLayout(); r.setSpacing(8)
        self._sp = E("Spotify-Link...")
        p = B("Einfügen","flat",44,95)
        p.clicked.connect(lambda: self._sp.setText(QApplication.clipboard().text().strip()))
        lb = B("Laden","spotify",44,80); lb.clicked.connect(self._do_spotify)
        r.addWidget(self._sp,1); r.addWidget(p); r.addWidget(lb); sec.row(r); pl.addWidget(sec)

    def _build_tiktok(self, pl):
        sec = Section("TikTok / Instagram", C_TIKTOK)
        r = QHBoxLayout(); r.setSpacing(8)
        self._ti = E("TikTok / Instagram Link...")
        p = B("Einfügen","flat",44,95)
        p.clicked.connect(lambda: self._ti.setText(QApplication.clipboard().text().strip()))
        lb = B("Laden","tiktok",44,80); lb.clicked.connect(self._do_tiktok)
        r.addWidget(self._ti,1); r.addWidget(p); r.addWidget(lb); sec.row(r); pl.addWidget(sec)

    def _build_dl(self, pl):
        self._dl_btn = QPushButton("↓  MP3 herunterladen")
        self._dl_btn.setFixedHeight(52)
        self._dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dl_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._dl_btn.setStyleSheet(f"QPushButton{{background:{C_ACCENT};color:{C_TEXT};border-radius:10px;}} QPushButton:hover{{background:{C_ACCENT2};}} QPushButton:pressed{{background:#5a48d4;}} QPushButton:disabled{{background:{C_RAISED};color:{C_DIM};}}")
        self._dl_btn.clicked.connect(self._start_dl); pl.addWidget(self._dl_btn)

        pb = QWidget(); pb.setFixedHeight(3); pb.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        pb.setStyleSheet(f"background:{C_RAISED}; border-radius:2px;")
        self._pbi = QWidget(pb); self._pbi.setFixedHeight(3)
        self._pbi.setStyleSheet(f"background:{C_ACCENT}; border-radius:2px;")
        self._pbi.setFixedWidth(0); self._pb_pos=0; self._pb_dir=1; self._pb=pb
        self._pb_t = QTimer(); self._pb_t.timeout.connect(lambda: self._tick())
        pl.addWidget(pb)

        self._ok = QWidget(); self._ok.setObjectName("surf")
        ol = QHBoxLayout(self._ok); ol.setContentsMargins(16,12,16,12)
        ol.addWidget(L("✓  Download abgeschlossen!",10,C_GREEN,True))
        ol.addStretch()
        self._ok_p = L("",9,C_GREEN); ol.addWidget(self._ok_p)
        self._ok.hide(); pl.addWidget(self._ok)

    def _build_log(self, pl):
        w = QWidget(); w.setObjectName("surf")
        wl = QVBoxLayout(w); wl.setContentsMargins(0,0,0,0); wl.setSpacing(0)
        hdr = QWidget(); hdr.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        hdr.setStyleSheet(f"background:{C_RAISED}; border-top-left-radius:12px; border-top-right-radius:12px;")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(16,9,16,9)
        hl.addWidget(L("●",8,C_GREEN)); hl.addWidget(L("  LOG",9,C_DIM,True)); hl.addStretch()
        clr = QPushButton("leeren"); clr.setFixedHeight(26); clr.setCursor(Qt.CursorShape.PointingHandCursor)
        clr.setStyleSheet(f"QPushButton{{background:transparent;color:{C_DIM};font-size:8pt;border:none;}} QPushButton:hover{{color:{C_MUTED};}}")
        clr.clicked.connect(lambda: self._log_box.clear()); hl.addWidget(clr)
        wl.addWidget(hdr); wl.addWidget(HSep())
        self._log_box = QTextEdit(); self._log_box.setReadOnly(True); self._log_box.setFixedHeight(130)
        wl.addWidget(self._log_box); pl.addWidget(w)

    def _tick(self):
        w = self._pb.width(); bw = max(80,w//4)
        self._pb_pos += self._pb_dir*8
        if self._pb_pos+bw>=w: self._pb_dir=-1
        if self._pb_pos<=0: self._pb_dir=1
        self._pbi.setGeometry(self._pb_pos,0,bw,3)

    def _busy(self, on):
        self._dl_btn.setEnabled(not on)
        self._dl_btn.setText("  Lädt..." if on else "↓  MP3 herunterladen")
        if on: self._pb_t.start(14)
        else: self._pb_t.stop(); self._pbi.setFixedWidth(0)

    def _log(self, m): self._log_box.append(m)

    def _show_ok(self, folder):
        self._ok_p.setText(folder); self._ok.show()
        QTimer.singleShot(6000, self._ok.hide)

    def _open_explorer(self, fp):
        if self._open_folder and fp and os.path.exists(fp):
            subprocess.Popen(["explorer","/select,",os.path.normpath(fp)],creationflags=CNW)

    def _check_tools(self):
        missing=[n for n,p in [("yt-dlp",YTDLP_PATH),("ffmpeg",FFMPEG_PATH)] if not os.path.exists(p)]
        if missing:
            self._log(f"Installiere {', '.join(missing)}..."); self._busy(True)
            self._tw=ToolsWorker(); self._tw.log.connect(self._log)
            self._tw.done.connect(lambda: self._busy(False)); self._tw.start()
        else: self._log("Bereit — Strg+V zum schnellen Download")

    def _yt_search(self, q):
        req=urllib.request.Request("https://www.youtube.com/results?search_query="+urllib.parse.quote(q),headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=10) as r: html=r.read().decode("utf-8","ignore")
        m=re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"',html)
        return f"https://www.youtube.com/watch?v={m.group(1)}" if m else None

    def _search_btn(self):
        s=self._sq.text().strip(); a=self._ar.text().strip()
        if not s: return
        self._busy(True)
        def run():
            try:
                url=self._yt_search(f"{a} {s} official audio".strip())
                if url: self._url.setText(url); self._sq.clear(); self._ar.clear(); QTimer.singleShot(0,self._start_dl)
                else: self._log("Nichts gefunden.")
            except Exception as e: self._log(f"Fehler: {e}")
            finally: QTimer.singleShot(0,lambda:self._busy(False))
        threading.Thread(target=run,daemon=True).start()

    def _do_spotify(self):
        url=self._sp.text().strip()
        if not url or "spotify.com" not in url: return
        self._busy(True)
        def run():
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
                with urllib.request.urlopen(req,timeout=10) as r: html=r.read().decode("utf-8","ignore")
                m=re.search(r"<title>(.*?)</title>",html)
                if not m: self._log("Titel nicht lesbar."); return
                name=re.sub(r"\s*[|\-–]\s*Spotify.*$","",m.group(1)).strip()
                yt=self._yt_search(name+" official audio")
                if yt: self._url.setText(yt); self._sp.clear(); QTimer.singleShot(0,self._start_dl)
                else: self._log("Kein YouTube-Treffer.")
            except Exception as e: self._log(f"Fehler: {e}")
            finally: QTimer.singleShot(0,lambda:self._busy(False))
        threading.Thread(target=run,daemon=True).start()

    def _run_worker(self, cmd, clear_fn=None):
        self._busy(True); self._ok.hide(); self._last_file=None
        w=Worker(cmd); w.log.connect(self._log)
        w.file_out.connect(lambda f: setattr(self,'_last_file',f))
        def done(ok):
            self._busy(False)
            if ok:
                if clear_fn: QTimer.singleShot(0,clear_fn)
                self._log(f"Fertig → {self._output_dir}")
                QTimer.singleShot(0,lambda:self._show_ok(self._output_dir))
                QTimer.singleShot(500,lambda:self._open_explorer(self._last_file))
            else: self._log("Fehlgeschlagen.")
        w.done.connect(done); w.start(); self._worker=w

    def _start_dl(self):
        url=self._url.text().strip()
        if not url: return
        if not os.path.exists(YTDLP_PATH): self._log("Tools noch nicht bereit!"); return
        out=os.path.join(self._output_dir,"%(title)s.%(ext)s")
        self._run_worker([YTDLP_PATH,"-x","--audio-format","mp3","--audio-quality",self._quality,
            "--ffmpeg-location",TOOLS_DIR,"-o",out,"--no-playlist","--print","after_move:filepath",url],self._url.clear)

    def _do_tiktok(self):
        url=self._ti.text().strip().split("?")[0]
        if not url: return
        if not os.path.exists(YTDLP_PATH): self._log("Tools noch nicht bereit!"); return
        out=os.path.join(self._output_dir,"%(title).80s.%(ext)s")
        self._run_worker([YTDLP_PATH,"-x","--audio-format","mp3","--audio-quality",self._quality,
            "--ffmpeg-location",TOOLS_DIR,"--no-playlist","--no-check-certificate",
            "--user-agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "-o",out,"--print","after_move:filepath",url],self._ti.clear)

    def _check_update(self):
        self._log("Suche Updates...")
        def run():
            try:
                req=urllib.request.Request(GITHUB_RAW,headers={"User-Agent":"Mozilla/5.0"})
                with urllib.request.urlopen(req,timeout=15) as r: content=r.read().decode("utf-8")
                m=re.search(r'^VERSION\s*=\s*"([^"]+)"',content,re.MULTILINE)
                nv=m.group(1) if m else VERSION
                self._log(f"Aktuell (v{VERSION})" if nv==VERSION else f"Neue Version v{nv} verfügbar!")
            except Exception as e: self._log(f"Update-Fehler: {e}")
        threading.Thread(target=run,daemon=True).start()


# ── Login Window ──────────────────────────────────────────────────────────────
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WaveLoad"); self.setFixedSize(440,560)
        self.logged_in=False
        ico=os.path.join(BASE_DIR,"icon.ico")
        if os.path.exists(ico): self.setWindowIcon(QIcon(ico))
        self._build()

    def _build(self):
        root=QWidget(); root.setObjectName("bg"); self.setCentralWidget(root)
        ml=QVBoxLayout(root); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)

        # Logo
        top=QWidget(); top.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        top.setStyleSheet(f"background:{C_BG};")
        tl=QVBoxLayout(top); tl.setContentsMargins(0,36,0,20)
        tl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        t=QLabel(APP_NAME); t.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        t.setFont(QFont("Segoe UI Black",22,QFont.Weight.Bold))
        t.setStyleSheet(f"color:{C_TEXT}; background:transparent;"); tl.addWidget(t)
        s=QLabel("MP3 Downloader"); s.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        s.setStyleSheet(f"color:{C_DIM}; background:transparent; font-size:9pt;"); tl.addWidget(s)
        ml.addWidget(top)

        # Tab bar
        tb=QWidget(); tb.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        tb.setStyleSheet(f"background:{C_BG}; border-bottom:1px solid {C_BORDER};")
        tbl=QHBoxLayout(tb); tbl.setContentsMargins(32,0,32,0); tbl.setSpacing(0)
        self._tl=QPushButton("Anmelden"); self._tl.setFixedHeight(46)
        self._tr=QPushButton("Registrieren"); self._tr.setFixedHeight(46)
        for b in (self._tl,self._tr):
            b.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
            b.setCursor(Qt.CursorShape.PointingHandCursor); tbl.addWidget(b)
        self._tl.clicked.connect(lambda:self._show(0))
        self._tr.clicked.connect(lambda:self._show(1))
        ml.addWidget(tb)

        # Pages
        self._stack=QStackedWidget(); self._stack.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        self._stack.setStyleSheet(f"background:{C_BG};")
        self._stack.addWidget(self._login_page()); self._stack.addWidget(self._reg_page())
        ml.addWidget(self._stack,1)

        # Admin
        adm=QWidget(); adm.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        adm.setStyleSheet(f"background:{C_BG};")
        al=QVBoxLayout(adm); al.setContentsMargins(32,10,32,24); al.setSpacing(8)
        al.addWidget(HSep())
        ar=QHBoxLayout(); ar.setSpacing(8)
        lbl=QLabel("Admin:"); lbl.setStyleSheet(f"color:{C_DIM}; font-size:9pt; background:transparent;")
        ar.addWidget(lbl)
        self._adm=E("Admin-Code",pw=True,h=38)
        ab=B("→",h=38,w=42); ab.clicked.connect(self._admin)
        ar.addWidget(self._adm,1); ar.addWidget(ab); al.addLayout(ar)
        ml.addWidget(adm)
        self._adm.returnPressed.connect(self._admin)
        self._show(0)

    def _page_widget(self):
        w=QWidget(); w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        w.setStyleSheet(f"background:{C_BG};"); return w

    def _login_page(self):
        w=self._page_widget()
        l=QVBoxLayout(w); l.setContentsMargins(32,26,32,16); l.setSpacing(10)
        for label_text, entry_attr, ph, pw in [
            ("Benutzername","_ue","Dein Benutzername",False),
            ("Passwort","_pe","Dein Passwort",True)
        ]:
            lbl=QLabel(label_text); lbl.setStyleSheet(f"color:{C_DIM}; font-size:9pt; background:transparent;")
            l.addWidget(lbl)
            e=E(ph,pw); setattr(self,entry_attr,e); l.addWidget(e)
        self._err=QLabel(""); self._err.setStyleSheet(f"color:{C_RED}; font-size:9pt; background:transparent;")
        l.addWidget(self._err)
        lb=B("Anmelden",h=48); lb.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        lb.clicked.connect(self._login); l.addWidget(lb); l.addStretch()
        self._pe.returnPressed.connect(self._login)
        return w

    def _reg_page(self):
        w=self._page_widget()
        l=QVBoxLayout(w); l.setContentsMargins(32,26,32,16); l.setSpacing(8)
        for label_text, attr, ph, pw in [
            ("Benutzername","_ru","Gewünschter Benutzername",False),
            ("Passwort","_rp","Mind. 6 Zeichen",True),
            ("Passwort bestätigen","_rp2","Passwort wiederholen",True)
        ]:
            lbl=QLabel(label_text); lbl.setStyleSheet(f"color:{C_DIM}; font-size:9pt; background:transparent;")
            l.addWidget(lbl); e=E(ph,pw); setattr(self,attr,e); l.addWidget(e)
        self._rerr=QLabel(""); self._rerr.setStyleSheet(f"color:{C_RED}; font-size:9pt; background:transparent;")
        l.addWidget(self._rerr)
        rb=B("Konto erstellen →",h=48)
        rb.setStyleSheet(f"QPushButton{{background:#132218;color:{C_GREEN};border-radius:8px;font-size:11pt;font-weight:bold;border:1.5px solid #166534;}} QPushButton:hover{{background:#1a2e20;}}")
        rb.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        rb.clicked.connect(self._do_register); l.addWidget(rb); l.addStretch()
        self._rp2.returnPressed.connect(self._do_register)
        return w

    def _show(self,idx):
        self._stack.setCurrentIndex(idx)
        act  = f"QPushButton{{background:transparent;color:{C_TEXT};border-bottom:2px solid {C_ACCENT};border-radius:0;font-size:11pt;font-weight:bold;padding:10px 20px;}}"
        inact= f"QPushButton{{background:transparent;color:{C_DIM};border-bottom:2px solid transparent;border-radius:0;font-size:11pt;font-weight:bold;padding:10px 20px;}} QPushButton:hover{{color:{C_MUTED};}}"
        self._tl.setStyleSheet(act if idx==0 else inact)
        self._tr.setStyleSheet(act if idx==1 else inact)

    def _login(self):
        u=self._ue.text().strip(); p=self._pe.text()
        if not u or not p: self._err.setText("Bitte alle Felder ausfüllen."); return
        users=load_users()
        if u not in users or users[u]!=_h(p): self._err.setText("Benutzername oder Passwort falsch."); return
        self.logged_in=True; self.close()

    def _do_register(self):
        u=self._ru.text().strip(); p=self._rp.text(); p2=self._rp2.text()
        if not u or not p: self._rerr.setText("Bitte alle Felder ausfüllen."); return
        if len(p)<6: self._rerr.setText("Passwort mind. 6 Zeichen."); return
        if p!=p2: self._rerr.setText("Passwörter stimmen nicht überein."); return
        users=load_users()
        if u in users: self._rerr.setText("Benutzername bereits vergeben."); return
        users[u]=_h(p); save_users(users); self.logged_in=True; self.close()

    def _admin(self):
        if self._adm.text().strip()==ADMIN_CODE: self.logged_in=True; self.close()
        else: self._err.setText("Ungültiger Admin-Code.")


# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__=="__main__":
    app=QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    app.setFont(QFont("Segoe UI",10))
    login=LoginWindow(); login.show(); app.exec()
    if not login.logged_in: sys.exit(0)
    win=MainWindow(); win.show(); sys.exit(app.exec())
