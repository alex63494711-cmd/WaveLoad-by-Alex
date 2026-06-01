# WaveLoad v10.1
import sys, os, re, threading, subprocess, shutil, zipfile, hashlib, json
import urllib.request, urllib.parse
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit,
    QScrollArea, QStackedWidget, QButtonGroup, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QPoint, QVariantAnimation
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor, QPainter

VERSION    = "10.1"
APP_NAME   = "WaveLoad"
GITHUB_RAW = "https://raw.githubusercontent.com/alex63494711-cmd/WaveLoad-by-Alex/refs/heads/WaveLoad-Updates/mp3downloader.py"
GITHUB_EXE = "https://github.com/alex63494711-cmd/WaveLoad-by-Alex/releases/latest/download/WaveLoad.exe"
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

# ── Modernes Farb-Set ──────────────────────────────────────────────────────────
C_BG      = "#08080c"   # Tiefschwarz/Blau
C_SURFACE = "#111118"   # Sanftes Dunkelgrau für Cards
C_RAISED  = "#181824"   # Inputs & Standard-Buttons
C_BORDER  = "#222235"   # Dezente Trennlinien
C_ACCENT  = "#6366f1"   # Premium Indigo / Hauptfarbe
C_ACCENT2 = "#4f46e5"   # Dunkleres Indigo für Klicks
C_TEXT    = "#f8fafc"   # Reinweiß für Text
C_MUTED   = "#94a3b8"   # Slate-Grau für Sekundärtexte
C_DIM     = "#475569"   # Placeholder
C_GREEN   = "#10b981"   # Smaragd-Grün
C_RED     = "#ef4444"   # Alarmsignal-Rot
C_SPOTIFY = "#1ed760"   # Echtes Spotify-Grün
C_TIKTOK  = "#00f2fe"   # Neon-Cyan für TikTok

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
* {{ font-family: 'Segoe UI', system-ui, sans-serif; color: {C_TEXT}; }}
QMainWindow, QDialog {{ background: {C_BG}; }}
QWidget#bg   {{ background: {C_BG}; }}
QWidget#surf {{ background: {C_SURFACE}; border: 1px solid {C_BORDER}; border-radius: 14px; }}

QScrollArea  {{ background: {C_BG}; border: none; }}
QScrollBar:vertical {{ background: {C_BG}; width: 6px; border-radius: 3px; }}
QScrollBar::handle:vertical {{ background: {C_BORDER}; border-radius: 3px; min-height: 25px; }}
QScrollBar::handle:vertical:hover {{ background: {C_ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QLineEdit {{
    background: {C_RAISED};
    border: 1px solid {C_BORDER};
    border-radius: 10px;
    color: {C_TEXT};
    padding: 0 16px;
    font-size: 10pt;
}}
QLineEdit:focus {{ border: 1.5px solid {C_ACCENT}; background: #1c1c2b; }}
QLineEdit[readOnly="true"] {{ color: {C_MUTED}; background: #0e0e16; }}

QTextEdit {{
    background: #0c0c14;
    border: 1px solid {C_BORDER};
    border-bottom-left-radius: 14px;
    border-bottom-right-radius: 14px;
    color: {C_MUTED};
    font-family: 'Consolas', monospace;
    font-size: 9pt;
    padding: 12px;
}}

QLabel {{ background: transparent; color: {C_TEXT}; }}
"""

# ── Animierter High-End Button ────────────────────────────────────────────────
class AnimatedButton(QPushButton):
    def __init__(self, text, bg_color, hover_color, text_color="#ffffff", parent=None, is_flat=False):
        super().__init__(text, parent)
        self.c_base = QColor(bg_color)
        self.c_hover = QColor(hover_color)
        self.c_text = text_color
        self.is_flat = is_flat
        self.curr_bg = self.c_base
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Color-Fade Animation
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(220)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.valueChanged.connect(self._animate_style)
        
        self._apply_style(self.c_base)

    def _animate_style(self, color):
        self.curr_bg = color
        self._apply_style(color)

    def _apply_style(self, color):
        border_css = f"border: 1px solid {C_BORDER};" if self.is_flat else "border: none;"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color.name()};
                color: {self.c_text};
                {border_css}
                border-radius: 10px;
                font-size: 10pt;
                font-weight: bold;
                padding: 0 18px;
            }}
        """)

    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.curr_bg)
        self.anim.setEndValue(self.c_hover)
        self.anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.curr_bg)
        self.anim.setEndValue(self.c_base)
        self.anim.start()
        super().leaveEvent(event)

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

def L(text, size=10, color=C_TEXT, bold=False):
    l = QLabel(text)
    l.setFont(QFont("Segoe UI", size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
    return l

def HSep():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"background:{C_BORDER}; border:none;"); f.setFixedHeight(1)
    return f

class Section(QWidget):
    def __init__(self, title, accent=C_ACCENT):
        super().__init__(); self.setObjectName("surf")
        
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(12); sh.setXOffset(0); sh.setYOffset(4)
        sh.setColor(QColor(0,0,0,60)); self.setGraphicsEffect(sh)

        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        hdr = QWidget(); hdr.setStyleSheet(f"background:{C_SURFACE}; border-top-left-radius:14px; border-top-right-radius:14px;")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(0,0,16,0); hl.setSpacing(0)
        
        bar = QWidget(); bar.setFixedWidth(4); bar.setFixedHeight(20)
        bar.setStyleSheet(f"background:{accent}; border-top-right-radius:4px; border-bottom-right-radius:4px;")
        hl.addWidget(bar)
        
        tl = L(title, 10, C_TEXT, True); tl.setContentsMargins(14,14,0,14)
        hl.addWidget(tl); hl.addStretch()
        root.addWidget(hdr); root.addWidget(HSep())
        
        self.body = QWidget(); self.body.setStyleSheet(f"background:{C_SURFACE}; border-bottom-left-radius:14px; border-bottom-right-radius:14px;")
        self.bl = QVBoxLayout(self.body); self.bl.setContentsMargins(18,16,18,18); self.bl.setSpacing(12)
        root.addWidget(self.body)
        
    def add(self, w): self.bl.addWidget(w)
    def row(self, l): self.bl.addLayout(l)

# ── Settings Panel ────────────────────────────────────────────────────────────
class SettingsPanel(QWidget):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"SettingsPanel {{ background: {C_SURFACE}; border-radius: 16px; border: 1px solid {C_BORDER}; }}")
        self.setFixedWidth(460)
        sh = QGraphicsDropShadowEffect(); sh.setBlurRadius(25); sh.setColor(QColor(0,0,0,150)); self.setGraphicsEffect(sh)
        self._build(); self.hide()
        self._anim = QPropertyAnimation(self, b"pos")

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        hdr = QWidget(); hdr.setStyleSheet(f"background:{C_RAISED}; border-top-left-radius:16px; border-top-right-radius:16px;")
        hdr.setFixedHeight(56)
        hl = QHBoxLayout(hdr); hl.setContentsMargins(20,0,14,0); hl.setSpacing(0)
        title = QLabel("Einstellungen")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        hl.addWidget(title); hl.addStretch()
        
        close = AnimatedButton("✕", C_RAISED, C_RED, C_MUTED, is_flat=True)
        close.setFixedSize(34, 34); close.clicked.connect(self.slide_out)
        hl.addWidget(close); root.addWidget(hdr); root.addWidget(HSep())

        body = QWidget(); bl = QVBoxLayout(body); bl.setContentsMargins(24,20,24,24); bl.setSpacing(18)
        root.addWidget(body)

        bl.addWidget(self._lbl("Speicherordner"))
        dr = QHBoxLayout(); dr.setSpacing(10)
        self.dir_e = QLineEdit(); self.dir_e.setReadOnly(True); self.dir_e.setFixedHeight(42)
        self.dir_e.setText(self.app._output_dir)
        pick = AnimatedButton("···", C_RAISED, "#2d2d3d", C_TEXT, is_flat=True); pick.setFixedSize(42,42)
        pick.clicked.connect(self._browse)
        dr.addWidget(self.dir_e,1); dr.addWidget(pick); bl.addLayout(dr)

        bl.addWidget(self._lbl("Audioqualität"))
        qr = QHBoxLayout(); qr.setSpacing(8); self._qg = QButtonGroup(self)
        for i,(t,v) in enumerate([("320 kbps","0"),("192 kbps","5"),("128 kbps","9")]):
            b = QPushButton(t); b.setCheckable(True); b.setFixedHeight(42)
            b.setCursor(Qt.CursorShape.PointingHandCursor); b.setProperty("qval",v)
            b.setStyleSheet(f"QPushButton{{background:{C_RAISED};color:{C_MUTED};border-radius:10px;font-size:9pt;font-weight:bold;border:1px solid {C_BORDER};}} QPushButton:checked{{background:{C_ACCENT};color:{C_TEXT};border-color:{C_ACCENT};}} QPushButton:hover{{background:#222232;}}")
            self._qg.addButton(b,i); qr.addWidget(b)
            if i==0: b.setChecked(True)
        self._qg.idToggled.connect(lambda i,c: c and setattr(self.app,'_quality',self._qg.button(i).property("qval")))
        bl.addLayout(qr)

        bl.addWidget(self._lbl("Nach Download"))
        self._ocb = QPushButton("  Dateimanager nach Abschluss öffnen")
        self._ocb.setCheckable(True); self._ocb.setChecked(True); self._ocb.setFixedHeight(42)
        self._ocb.setCursor(Qt.CursorShape.PointingHandCursor)
        self._ocb.setStyleSheet(f"QPushButton{{background:{C_RAISED};color:{C_MUTED};border-radius:10px;font-size:9pt;text-align:left;padding:0 14px;border:1px solid {C_BORDER};}} QPushButton:checked{{background:#062017;color:{C_GREEN};border-color:#0f5138;}}")
        self._ocb.toggled.connect(lambda v: setattr(self.app,'_open_folder',v))
        bl.addWidget(self._ocb)
        self.adjustSize()

    def _lbl(self, text):
        l = QLabel(text); l.setStyleSheet(f"color:{C_MUTED}; font-size:9pt; font-weight:bold;")
        return l

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Ordner wählen", self.app._output_dir)
        if d: self.app._output_dir = d; self.dir_e.setText(d)

    def slide_in(self):
        self.adjustSize()
        pw = self.parent().width(); ph = self.parent().height()
        cx = (pw-self.width())//2; cy = (ph-self.height())//2
        self.move(cx, -self.height()); self.show(); self.raise_()
        self._anim.stop(); self._anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self._anim.setDuration(400); self._anim.setStartValue(QPoint(cx, -self.height())); self._anim.setEndValue(QPoint(cx, cy)); self._anim.start()

    def slide_out(self):
        pw = self.parent().width(); cx = (pw-self.width())//2; cy = self.pos().y()
        self._anim.stop(); self._anim.setEasingCurve(QEasingCurve.Type.InBack); self._anim.setDuration(250)
        self._anim.setStartValue(QPoint(cx, cy)); self._anim.setEndValue(QPoint(cx, -self.height()))
        self._anim.finished.connect(self.hide); self._anim.start()

# ── Main Window ───────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    update_checked = pyqtSignal(str)
    update_downloaded = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME); self.resize(740,840); self.setMinimumSize(620,580)
        self._output_dir  = os.path.join(os.path.expanduser("~"),"Music")
        self._quality     = "0"
        self._open_folder = True
        self._last_file   = None
        ico = os.path.join(BASE_DIR,"icon.ico")
        if os.path.exists(ico): self.setWindowIcon(QIcon(ico))

        root = QWidget(); root.setObjectName("bg"); self.setCentralWidget(root)
        ml = QVBoxLayout(root); ml.setContentsMargins(0,0,0,0)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        inner = QWidget(); inner.setStyleSheet(f"background:{C_BG};")
        il = QVBoxLayout(inner); il.setContentsMargins(24,24,24,28); il.setSpacing(16)
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
            self._settings.move((self.centralWidget().width()-self._settings.width())//2, (self.centralWidget().height()-self._settings.height())//2)

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
        hl = QHBoxLayout(w); hl.setContentsMargins(20,14,20,14)
        hl.addWidget(L(APP_NAME, 18, C_TEXT, True))
        hl.addWidget(L(f"v{VERSION}", 8, C_DIM))
        hl.addStretch()
        
        self._ui_update_btn = AnimatedButton("Update", C_RAISED, "#2a2a3a", C_MUTED, is_flat=True)
        self._ui_update_btn.setFixedHeight(36)
        self._ui_update_btn.clicked.connect(self._check_update)
        hl.addWidget(self._ui_update_btn)
        hl.addSpacing(8)
        
        s = AnimatedButton("⚙", C_RAISED, "#2a2a3a", C_TEXT, is_flat=True)
        s.setFixedSize(36,36); s.clicked.connect(self._settings.slide_in); hl.addWidget(s)
        pl.addWidget(w)

    def _build_yt(self, pl):
        sec = Section("YouTube / SoundCloud")
        r = QHBoxLayout(); r.setSpacing(10)
        self._url = E("Link hier einfügen...")
        p = AnimatedButton("Einfügen", C_RAISED, "#252535", C_MUTED, is_flat=True)
        p.clicked.connect(lambda: self._url.setText(QApplication.clipboard().text().strip()))
        r.addWidget(self._url,1); r.addWidget(p); sec.row(r); pl.addWidget(sec)

    def _build_search(self, pl):
        sec = Section("Song manuell suchen", "#a855f7")
        r = QHBoxLayout(); r.setSpacing(10)
        self._sq = E("Songname...")
        self._ar = E("Künstler...")
        sb = AnimatedButton("Suchen & laden", C_ACCENT, C_ACCENT2)
        sb.clicked.connect(self._search_btn)
        r.addWidget(self._sq,1); r.addWidget(self._ar,1); r.addWidget(sb)
        sec.row(r); pl.addWidget(sec)

    def _build_spotify(self, pl):
        sec = Section("Spotify Synchronizer", C_SPOTIFY)
        r = QHBoxLayout(); r.setSpacing(10)
        self._sp = E("Spotify Track Link...")
        p = AnimatedButton("Einfügen", C_RAISED, "#252535", C_MUTED, is_flat=True)
        p.clicked.connect(lambda: self._sp.setText(QApplication.clipboard().text().strip()))
        lb = AnimatedButton("Laden", C_SPOTIFY, "#169c46", "#000000")
        lb.clicked.connect(self._do_spotify)
        r.addWidget(self._sp,1); r.addWidget(p); r.addWidget(lb); sec.row(r); pl.addWidget(sec)

    def _build_tiktok((self, pl):
        sec = Section("TikTok / Instagram Audio Extractor", C_TIKTOK)
        r = QHBoxLayout(); r.setSpacing(10)
        self._ti = E("Video Link...")
        p = AnimatedButton("Einfügen", C_RAISED, "#252535", C_MUTED, is_flat=True)
        p.clicked.connect(lambda: self._ti.setText(QApplication.clipboard().text().strip()))
        lb = AnimatedButton("Laden", C_TIKTOK, "#00b4bd", "#000000")
        lb.clicked.connect(self._do_tiktok)
        r.addWidget(self._ti,1); r.addWidget(p); r.addWidget(lb); sec.row(r); pl.addWidget(sec)

    def _build_dl(self, pl):
        self._dl_btn = AnimatedButton("↓   MP3 herunterladen", C_ACCENT, C_ACCENT2)
        self._dl_btn.setFixedHeight(54)
        self._dl_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._dl_btn.clicked.connect(self._start_dl); pl.addWidget(self._dl_btn)

        pb = QWidget(); pb.setFixedHeight(4); pb.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        pb.setStyleSheet(f"background:{C_RAISED}; border-radius:2px;")
        self._pbi = QWidget(pb); self._pbi.setFixedHeight(4)
        self._pbi.setStyleSheet(f"background:{C_ACCENT}; border-radius:2px;")
        self._pbi.setFixedWidth(0); self._pb_pos=0; self._pb_dir=1; self._pb=pb
        self._pb_t = QTimer(); self._pb_t.timeout.connect(lambda: self._tick())
        pl.addWidget(pb)

        self._ok = QWidget(); self._ok.setObjectName("surf")
        ol = QHBoxLayout(self._ok); ol.setContentsMargins(18,14,18,14)
        ol.addWidget(L("✓  Download erfolgreich abgeschlossen!",10,C_GREEN,True))
        ol.addStretch()
        self._ok_p = L("",9,C_MUTED); ol.addWidget(self._ok_p)
        self._ok.hide(); pl.addWidget(self._ok)

    def _build_log(self, pl):
        w = QWidget(); w.setObjectName("surf")
        wl = QVBoxLayout(w); wl.setContentsMargins(0,0,0,0); wl.setSpacing(0)
        hdr = QWidget(); hdr.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        hdr.setStyleSheet(f"background:{C_RAISED}; border-top-left-radius:14px; border-top-right-radius:14px;")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(18,10,18,10)
        hl.addWidget(L("●",8,C_GREEN)); hl.addWidget(L("  SYSTEM LOG",9,C_DIM,True)); hl.addStretch()
        clr = QPushButton("leeren"); clr.setCursor(Qt.CursorShape.PointingHandCursor)
        clr.setStyleSheet(f"QPushButton{{background:transparent;color:{C_DIM};font-size:8.5pt;border:none;}} QPushButton:hover{{color:{C_MUTED};}}")
        clr.clicked.connect(lambda: self._log_box.clear()); hl.addWidget(clr)
        wl.addWidget(hdr); wl.addWidget(HSep())
        self._log_box = QTextEdit(); self._log_box.setReadOnly(True); self._log_box.setFixedHeight(140)
        wl.addWidget(self._log_box); pl.addWidget(w)

    def _tick(self):
        w = self._pb.width(); bw = max(90,w//4)
        self._pb_pos += self._pb_dir*7
        if self._pb_pos+bw>=w: self._pb_dir=-1
        if self._pb_pos<=0: self._pb_dir=1
        self._pbi.setGeometry(self._pb_pos,0,bw,4)

    def _busy(self, on):
        self._dl_btn.setEnabled(not on)
        self._dl_btn.setText("  Wird verarbeitet..." if on else "↓   MP3 herunterladen")
        if on: self._pb_t.start(12)
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
            self._log(f"Komponenten fehlen: {', '.join(missing)}..."); self._busy(True)
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
        self._log("Suche Updates auf GitHub...")
        
        def on_check_finished(nv):
            if nv != VERSION:
                self._log(f"Update verfügbar: Version v{nv} steht bereit!")
                self._ui_update_btn.setText(f"v{nv} installieren")
                self._ui_update_btn.c_base = QColor(C_GREEN)
                self._ui_update_btn.c_hover = QColor("#059669")
                self._ui_update_btn.c_text = "#000000"
                self._ui_update_btn._apply_style(QColor(C_GREEN))
                try: self._ui_update_btn.clicked.disconnect()
                except: pass
                self._ui_update_btn.clicked.connect(lambda: self._download_and_install_update(nv))
            else:
                self._log(f"WaveLoad ist auf dem neuesten Stand (v{VERSION}).")

        def run_check():
            try:
                req = urllib.request.Request(GITHUB_RAW, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as r: 
                    content = r.read().decode("utf-8")
                m = re.search(r'^VERSION\s*=\s*"([^"]+)"', content, re.MULTILINE)
                nv = m.group(1) if m else VERSION
                self.update_checked.emit(nv)
            except Exception as e: 
                self.update_checked.emit(VERSION)
                self._log(f"Update-Check fehlgeschlagen: {e}")

        try: self.update_checked.disconnect()
        except: pass
        self.update_checked.connect(on_check_finished)
        threading.Thread(target=run_check, daemon=True).start()

    def _download_and_install_update(self, new_version):
        self._log(f"Lade Update v{new_version} herunter...")
        self._ui_update_btn.setEnabled(False)
        self._ui_update_btn.setText("Wird geladen...")

        def on_download_finished(exe_path):
            if exe_path and os.path.exists(exe_path):
                self._log("Update erfolgreich heruntergeladen. Starte Installation...")
                subprocess.Popen([exe_path], creationflags=CNW)
                QApplication.quit()
            else:
                self._log("Fehler beim Herunterladen der Updatedatei.")
                self._ui_update_btn.setEnabled(True)
                self._ui_update_btn.setText("Erneut versuchen")

        def run_download():
            try:
                target_path = os.path.join(BASE_DIR, "WaveLoad_Update.exe")
                req = urllib.request.Request(GITHUB_EXE, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req) as response, open(target_path, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                self.update_downloaded.emit(target_path)
            except Exception as e:
                self._log(f"Download-Fehler: {e}")
                self.update_downloaded.emit("")

        try: self.update_downloaded.disconnect()
        except: pass
        self.update_downloaded.connect(on_download_finished)
        threading.Thread(target=run_download, daemon=True).start()


# ── Login Window ──────────────────────────────────────────────────────────────
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WaveLoad"); self.setFixedSize(440,580)
        self.logged_in=False
        ico=os.path.join(BASE_DIR,"icon.ico")
        if os.path.exists(ico): self.setWindowIcon(QIcon(ico))
        self._build()

    def _build(self):
        root=QWidget(); root.setObjectName("bg"); self.setCentralWidget(root)
        ml=QVBoxLayout(root); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)

        top=QWidget(); top.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        top.setStyleSheet(f"background:{C_BG};")
        tl=QVBoxLayout(top); tl.setContentsMargins(0,40,0,24)
        tl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        t=QLabel(APP_NAME); t.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        t.setFont(QFont("Segoe UI",24,QFont.Weight.Bold))
        t.setStyleSheet(f"color:{C_TEXT}; background:transparent; letter-spacing: 1px;"); tl.addWidget(t)
        s=QLabel("PREMIUM AUDIO DOWNLOADER"); s.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        s.setStyleSheet(f"color:{C_DIM}; background:transparent; font-size:8pt; font-weight: bold; letter-spacing: 2px;"); tl.addWidget(s)
        ml.addWidget(top)

        tb=QWidget(); tb.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        tb.setStyleSheet(f"background:{C_BG}; border-bottom:1px solid {C_BORDER};")
        tbl=QHBoxLayout(tb); tbl.setContentsMargins(40,0,40,0); tbl.setSpacing(0)
        self._tl=QPushButton("Anmelden"); self._tl.setFixedHeight(46)
        self._tr=QPushButton("Registrieren"); self._tr.setFixedHeight(46)
        for b in (self._tl,self._tr):
            b.setFont(QFont("Segoe UI",10,QFont.Weight.Bold))
            b.setCursor(Qt.CursorShape.PointingHandCursor); tbl.addWidget(b)
        self._tl.clicked.connect(lambda:self._show(0))
        self._tr.clicked.connect(lambda:self._show(1))
        ml.addWidget(tb)

        self._stack=QStackedWidget(); self._stack.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        self._stack.setStyleSheet(f"background:{C_BG};")
        self._stack.addWidget(self._login_page()); self._stack.addWidget(self._reg_page())
        ml.addWidget(self._stack,1)

        adm=QWidget(); adm.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        adm.setStyleSheet(f"background:{C_BG};")
        al=QVBoxLayout(adm); al.setContentsMargins(40,10,40,26); al.setSpacing(10)
        al.addWidget(HSep())
        ar=QHBoxLayout(); ar.setSpacing(10)
        lbl=QLabel("Bypass:"); lbl.setStyleSheet(f"color:{C_DIM}; font-size:9pt; font-weight:bold; background:transparent;")
        ar.addWidget(lbl)
        self._adm=E("Admin-Code",pw=True,h=38)
        ab=AnimatedButton("→", C_RAISED, "#2d2d3d", C_TEXT, is_flat=True); ab.setFixedSize(42,38)
        ab.clicked.connect(self._admin)
        ar.addWidget(self._adm,1); ar.addWidget(ab); al.addLayout(ar)
        ml.addWidget(adm)
        self._adm.returnPressed.connect(self._admin)
        self._show(0)

    def _page_widget(self):
        w=QWidget(); w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,True)
        w.setStyleSheet(f"background:{C_BG};"); return w

    def _login_page(self):
        w=self._page_widget()
        l=QVBoxLayout(w); l.setContentsMargins(40,26,40,16); l.setSpacing(12)
        for label_text, entry_attr, ph, pw in [
            ("BENUTZERNAME","_ue","Dein Benutzername",False),
            ("PASSWORT","_pe","Dein Passwort",True)
        ]:
            lbl=QLabel(label_text); lbl.setStyleSheet(f"color:{C_MUTED}; font-size:8pt; font-weight:bold; background:transparent;")
            l.addWidget(lbl)
            e=E(ph,pw); setattr(self,entry_attr,e); l.addWidget(e)
        self._err=QLabel(""); self._err.setStyleSheet(f"color:{C_RED}; font-size:9pt; background:transparent;")
        l.addWidget(self._err)
        
        lb=AnimatedButton("Anmelden", C_ACCENT, C_ACCENT2)
        lb.setFixedHeight(48); lb.clicked.connect(self._login); l.addWidget(lb); l.addStretch()
        self._pe.returnPressed.connect(self._login)
        return w

    def _reg_page(self):
        w=self._page_widget()
        l=QVBoxLayout(w); l.setContentsMargins(40,26,40,16); l.setSpacing(10)
        for label_text, attr, ph, pw in [
            ("BENUTZERNAME","_ru","Gewünschter Benutzername",False),
            ("PASSWORT","_rp","Mindestens 6 Zeichen",True),
            ("PASSWORT BESTÄTIGEN","_rp2","Passwort wiederholen",True)
        ]:
            lbl=QLabel(label_text); lbl.setStyleSheet(f"color:{C_MUTED}; font-size:8pt; font-weight:bold; background:transparent;")
            l.addWidget(lbl); e=E(ph,pw); setattr(self,attr,e); l.addWidget(e)
        self._rerr=QLabel(""); self._rerr.setStyleSheet(f"color:{C_RED}; font-size:9pt; background:transparent;")
        l.addWidget(self._rerr)
        
        rb=AnimatedButton("Konto erstellen", "#062017", "#0f5138", C_GREEN, is_flat=True)
        rb.setFixedHeight(48); rb.clicked.connect(self._do_register); l.addWidget(rb); l.addStretch()
        self._rp2.returnPressed.connect(self._do_register)
        return w

    def _show(self,idx):
        self._stack.setCurrentIndex(idx)
        act  = f"QPushButton{{background:transparent;color:{C_TEXT};border-bottom:3px solid {C_ACCENT};border-radius:0;font-size:10pt;font-weight:bold;padding:10px 20px;}}"
        inact= f"QPushButton{{background:transparent;color:{C_DIM};border-bottom:3px solid transparent;border-radius:0;font-size:10pt;font-weight:bold;padding:10px 20px;}} QPushButton:hover{{color:{C_MUTED};}}"
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