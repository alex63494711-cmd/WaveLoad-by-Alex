# WaveLoad v8.0 – PyQt6, UI nach Referenzbild
import sys, os, re, threading, subprocess, shutil, zipfile, hashlib, json
import urllib.request, urllib.parse
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit,
    QScrollArea, QFrame, QStackedWidget, QSizePolicy, QButtonGroup
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve,
    QTimer, QPoint, QRect
)
from PyQt6.QtGui import QFont, QIcon, QColor

VERSION    = "8.0"
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

def _h(s): return hashlib.sha256(s.encode()).hexdigest()
def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE) as f: return json.load(f)
    except: pass
    return {}
def save_users(u):
    with open(USERS_FILE,"w") as f: json.dump(u,f)

# ─── Stylesheet ───────────────────────────────────────────────────────────────
STYLE = """
* { font-family: 'Segoe UI', Arial, sans-serif; }
QMainWindow, QDialog { background: #0d0d1a; }
QWidget#bg    { background: #0d0d1a; }
QWidget#card  { background: #12122a; border: 1px solid #252545; border-radius: 14px; }
QWidget#hdr   { background: #16163a; border-top-left-radius:14px; border-top-right-radius:14px; border-bottom-left-radius:0; border-bottom-right-radius:0; }
QWidget#body  { background: #12122a; border-bottom-left-radius:14px; border-bottom-right-radius:14px; }
QWidget#logcard { background: #12122a; border: 1px solid #252545; border-radius: 14px; }
QWidget#loghdr  { background: #16163a; border-top-left-radius:14px; border-top-right-radius:14px; }

QScrollArea   { background: #0d0d1a; border: none; }
QScrollBar:vertical { background: #0d0d1a; width: 6px; }
QScrollBar::handle:vertical { background: #8b5cf6; border-radius: 3px; min-height: 24px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QLineEdit {
    background: #1a1a38;
    border: 1px solid #2e2e58;
    border-radius: 10px;
    color: #e8e8ff;
    padding: 0 14px;
    font-size: 10pt;
    selection-background-color: #8b5cf6;
}
QLineEdit:focus { border: 1.5px solid #8b5cf6; background: #1e1e42; }

QTextEdit {
    background: #12122a;
    border: none;
    color: #5cdf96;
    font-family: Consolas, monospace;
    font-size: 9pt;
    padding: 4px 10px;
}

QPushButton {
    background: #8b5cf6;
    color: #fff;
    border: none;
    border-radius: 10px;
    padding: 0 20px;
    font-size: 10pt;
    font-weight: bold;
}
QPushButton:hover   { background: #9d70f8; }
QPushButton:pressed { background: #6d28d9; }
QPushButton:disabled { background: #252545; color: #404060; }

QPushButton#ghost {
    background: #1a1a38;
    color: #8080b0;
    border: 1px solid #2e2e58;
}
QPushButton#ghost:hover { background: #252550; color: #e8e8ff; }

QPushButton#spotify { background: #1db954; color: #000; }
QPushButton#spotify:hover { background: #25d160; }

QPushButton#tiktok  { background: #5bcdd4; color: #000; }
QPushButton#tiktok:hover  { background: #6ddde4; }

QPushButton#green   { background: #1db954; color: #000; }
QPushButton#green:hover { background: #25d160; }

QPushButton#danger  { background: transparent; color: #8080b0; font-size: 16pt; padding: 0 8px; border-radius: 8px; }
QPushButton#danger:hover { background: #f87171; color: #fff; }

QLabel { color: #e8e8ff; background: transparent; }
"""

# ─── Workers ──────────────────────────────────────────────────────────────────
class Worker(QThread):
    log      = pyqtSignal(str)
    file_out = pyqtSignal(str)
    done     = pyqtSignal(bool)
    def __init__(self, cmd): super().__init__(); self.cmd = cmd
    def run(self):
        try:
            proc = subprocess.Popen(self.cmd, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                errors="replace", creationflags=CNW)
            for line in proc.stdout:
                line = line.rstrip()
                if not line: continue
                if os.path.sep in line and line.endswith((".mp3",".mp4")):
                    self.file_out.emit(line.strip())
                else: self.log.emit(line)
            proc.wait(); self.done.emit(proc.returncode == 0)
        except Exception as e: self.log.emit(f"Fehler: {e}"); self.done.emit(False)

class ToolsWorker(QThread):
    log = pyqtSignal(str); done = pyqtSignal()
    def run(self):
        os.makedirs(TOOLS_DIR, exist_ok=True)
        try:
            if not os.path.exists(YTDLP_PATH):
                self.log.emit("yt-dlp wird heruntergeladen...")
                urllib.request.urlretrieve(YTDLP_URL, YTDLP_PATH)
                self.log.emit("yt-dlp OK")
            if not os.path.exists(FFMPEG_PATH):
                self.log.emit("ffmpeg wird heruntergeladen (~80 MB)...")
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
                self.log.emit("ffmpeg OK")
            self.log.emit("[Bereit]  Strg+V = sofort herunterladen")
        except Exception as e: self.log.emit(f"Fehler: {e}")
        self.done.emit()

# ─── Helpers ──────────────────────────────────────────────────────────────────
def mk_entry(ph="", pw=False, h=46):
    e = QLineEdit(); e.setPlaceholderText(ph); e.setFixedHeight(h)
    if pw: e.setEchoMode(QLineEdit.EchoMode.Password)
    return e

def mk_btn(text, oid=None, h=42, w=None):
    b = QPushButton(text); b.setFixedHeight(h)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if oid: b.setObjectName(oid)
    if w:   b.setFixedWidth(w)
    return b

def mk_sep(color="#252545"):
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet(f"background:{color}; border:none;"); f.setFixedHeight(1)
    return f

def lbl(text, size=10, bold=False, color="#e8e8ff"):
    l = QLabel(text); l.setStyleSheet(f"color:{color};")
    l.setFont(QFont("Segoe UI", size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
    return l

class SectionCard(QWidget):
    """Card mit farbigem Linksbalken, Titel/Subtitle im Header, Body für Inhalte."""
    def __init__(self, title, subtitle, accent="#8b5cf6"):
        super().__init__(); self.setObjectName("card")
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        # Header
        hdr = QWidget(); hdr.setObjectName("hdr")
        hl  = QHBoxLayout(hdr); hl.setContentsMargins(0,0,16,0); hl.setSpacing(0)
        bar = QWidget(); bar.setFixedWidth(5)
        bar.setStyleSheet(f"background:{accent}; border-top-left-radius:14px; border-bottom-left-radius:0;")
        hl.addWidget(bar)
        # Icon placeholder – 48px square with rounded bg
        ico_box = QWidget(); ico_box.setFixedSize(48,48)
        ico_box.setStyleSheet(f"background:{accent}22; border-radius:10px; margin:8px 0 8px 10px;")
        ico_lbl = QLabel(self._icon_for(title)); ico_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico_lbl.setFont(QFont("Segoe UI",18)); ico_lbl.setStyleSheet("color:"+accent+";background:transparent;")
        il2 = QVBoxLayout(ico_box); il2.setContentsMargins(0,0,0,0); il2.addWidget(ico_lbl)
        hl.addWidget(ico_box)
        tl = lbl(title,11,True); tl.setContentsMargins(12,0,0,0)
        hl.addWidget(tl)
        sl = lbl("  "+subtitle,9,False,"#50507a")
        hl.addWidget(sl); hl.addStretch()
        root.addWidget(hdr); root.addWidget(mk_sep())
        # Body
        self.body = QWidget(); self.body.setObjectName("body")
        self.bl   = QVBoxLayout(self.body)
        self.bl.setContentsMargins(16,12,16,14); self.bl.setSpacing(8)
        root.addWidget(self.body)

    def _icon_for(self, title):
        if "YouTube" in title: return "▶"
        if "Song" in title:    return "♪"
        if "Spotify" in title: return "♫"
        if "TikTok" in title:  return "✦"
        return "◈"

    def add(self, w): self.bl.addWidget(w)
    def add_row(self, l): self.bl.addLayout(l)

# ─── Settings Panel ───────────────────────────────────────────────────────────
class SettingsPanel(QWidget):
    def __init__(self, parent, app_ref):
        super().__init__(parent); self.app = app_ref
        self.setFixedWidth(520)
        self.setStyleSheet("""
            QWidget { background:#12122a; border-radius:16px; }
            QWidget#sp_hdr { background:#16163a; border-top-left-radius:16px; border-top-right-radius:16px; }
        """)
        self._build(); self.hide()
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(350)

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        # Header
        hdr = QWidget(); hdr.setObjectName("sp_hdr"); hdr.setFixedHeight(56)
        hl  = QHBoxLayout(hdr); hl.setContentsMargins(24,0,16,0)
        ico = lbl("⚙",16,False,"#8b5cf6"); hl.addWidget(ico)
        hl.addWidget(lbl("  Einstellungen",13,True)); hl.addStretch()
        x = mk_btn("✕","danger",36,36); x.clicked.connect(self.slide_out); hl.addWidget(x)
        root.addWidget(hdr); root.addWidget(mk_sep("#2a2a55"))
        # Body
        body = QWidget()
        bl = QVBoxLayout(body); bl.setContentsMargins(28,22,28,24); bl.setSpacing(18)
        root.addWidget(body)

        # Ordner
        r0 = QWidget(); r0.setStyleSheet("background:#16163a; border-radius:12px; padding:2px;")
        r0l = QHBoxLayout(r0); r0l.setContentsMargins(14,6,10,6); r0l.setSpacing(10)
        ico2 = lbl("📁",18); ico2.setFixedWidth(36); r0l.addWidget(ico2)
        vl = QVBoxLayout(); vl.setSpacing(2)
        vl.addWidget(lbl("Speicherordner",10,True))
        self.dir_lbl = lbl(self.app._output_dir, 9, False, "#8080b0")
        self.dir_lbl.setWordWrap(True); vl.addWidget(self.dir_lbl)
        r0l.addLayout(vl,1)
        ab = mk_btn("Auswählen",h=36,w=110); ab.clicked.connect(self._browse)
        r0l.addWidget(ab)
        bl.addWidget(r0)

        # Qualität
        r1 = QWidget(); r1.setStyleSheet("background:#16163a; border-radius:12px; padding:2px;")
        r1l = QVBoxLayout(r1); r1l.setContentsMargins(14,12,14,12); r1l.setSpacing(10)
        rh = QHBoxLayout(); rh.setSpacing(0)
        rh.addWidget(lbl("🎚",18,"","")); rh.addWidget(lbl("  Audioqualität",10,True)); rh.addStretch()
        r1l.addLayout(rh)
        qr = QHBoxLayout(); qr.setSpacing(8); self._qg = QButtonGroup(self)
        for i,(t,v) in enumerate([("320 kbps\nBeste","0"),("192 kbps\nGut","5"),("128 kbps\nNormal","9")]):
            b = QPushButton(t); b.setCheckable(True); b.setFixedHeight(56)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setProperty("qval",v)
            b.setStyleSheet("""
                QPushButton{background:#1a1a38;color:#8080b0;border-radius:10px;font-size:9pt;font-weight:bold;border:1px solid #2e2e58;}
                QPushButton:checked{background:#8b5cf6;color:#fff;border:1.5px solid #a78bfa;}
                QPushButton:hover{background:#252550;}
            """)
            self._qg.addButton(b,i); qr.addWidget(b)
            if i==0: b.setChecked(True)
        self._qg.idToggled.connect(self._q_changed)
        r1l.addLayout(qr); bl.addWidget(r1)

        # Nach Download
        r2 = QWidget(); r2.setStyleSheet("background:#16163a; border-radius:12px; padding:2px;")
        r2l = QHBoxLayout(r2); r2l.setContentsMargins(14,10,14,10); r2l.setSpacing(10)
        r2l.addWidget(lbl("📥",18))
        vl2 = QVBoxLayout(); vl2.setSpacing(2)
        vl2.addWidget(lbl("Nach Download",10,True))
        self._open_cb = QPushButton("✓  Dateimanager öffnen mit Datei markiert")
        self._open_cb.setCheckable(True); self._open_cb.setChecked(True)
        self._open_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_cb.setStyleSheet("""
            QPushButton{background:#1a1a38;color:#8080b0;border-radius:8px;font-size:9pt;text-align:left;padding:8px 14px;border:1px solid #2e2e58;}
            QPushButton:checked{background:#0d2218;color:#34d399;border:1.5px solid #10b981;}
        """)
        self._open_cb.toggled.connect(lambda v: setattr(self.app,'_open_folder',v))
        vl2.addWidget(self._open_cb); r2l.addLayout(vl2,1); bl.addWidget(r2)

        # Auto-size
        self.adjustSize()

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self,"Ordner wählen",self.app._output_dir)
        if d: self.app._output_dir = d; self.dir_lbl.setText(d)

    def _q_changed(self, idx, checked):
        if checked: self.app._quality = self._qg.button(idx).property("qval")

    def slide_in(self):
        self.adjustSize()
        pw = self.parent().width(); ph = self.parent().height()
        w  = self.width();          h  = self.height()
        cx = (pw-w)//2; cy = (ph-h)//2
        self.move(cx, -h); self.show(); self.raise_()
        self._anim.stop()
        self._anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self._anim.setDuration(380)
        self._anim.setStartValue(QPoint(cx,-h))
        self._anim.setEndValue(QPoint(cx,cy))
        self._anim.start()

    def slide_out(self):
        pw = self.parent().width(); ph = self.parent().height()
        w  = self.width();          h  = self.height()
        cx = (pw-w)//2; cy = (ph-h)//2
        self._anim.stop()
        self._anim.setEasingCurve(QEasingCurve.Type.InBack)
        self._anim.setDuration(260)
        self._anim.setStartValue(QPoint(cx,cy))
        self._anim.setEndValue(QPoint(cx,-h))
        self._anim.finished.connect(self._on_close)
        self._anim.start()

    def _on_close(self):
        self.hide()
        try: self._anim.finished.disconnect(self._on_close)
        except: pass

# ─── Main Window ──────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME); self.resize(760,880); self.setMinimumSize(640,600)
        self._output_dir  = os.path.join(os.path.expanduser("~"),"Music")
        self._quality     = "0"
        self._open_folder = True
        self._last_file   = None
        self._worker      = None
        ico = os.path.join(BASE_DIR,"icon.ico")
        if os.path.exists(ico): self.setWindowIcon(QIcon(ico))

        root = QWidget(); root.setObjectName("bg"); self.setCentralWidget(root)
        ml = QVBoxLayout(root); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QWidget(); inner.setStyleSheet("background:#0d0d1a;")
        il = QVBoxLayout(inner); il.setContentsMargins(20,20,20,24); il.setSpacing(10)
        scroll.setWidget(inner); ml.addWidget(scroll)

        # Settings overlay (created before header!)
        self._settings = SettingsPanel(root, self)

        self._build_header(il)
        self._build_yt(il)
        self._build_search(il)
        self._build_spotify(il)
        self._build_tiktok(il)
        self._build_dl_btn(il)
        self._build_log(il)
        il.addStretch()

        QTimer.singleShot(400, self._check_tools)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._settings.isVisible():
            pw = self.centralWidget().width(); ph = self.centralWidget().height()
            w  = self._settings.width();       h  = self._settings.height()
            self._settings.move((pw-w)//2, (ph-h)//2)

    def keyPressEvent(self, e):
        if e.key()==Qt.Key.Key_V and e.modifiers()==Qt.KeyboardModifier.ControlModifier:
            self._paste_detect()

    def _paste_detect(self):
        c = QApplication.clipboard().text().strip()
        if not c: return
        if "spotify.com" in c:
            self._sp_entry.setText(c); self._log("Spotify erkannt – suche...")
            QTimer.singleShot(200, self._do_spotify)
        elif "tiktok.com" in c or "instagram.com" in c:
            self._ti_entry.setText(c); self._log("TikTok/Instagram erkannt!")
        elif c.startswith("http"):
            self._url_entry.setText(c); self._log("Link erkannt – lade...")
            QTimer.singleShot(200, self._start_dl)

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self, pl):
        hdr = QWidget(); hdr.setObjectName("card")
        hdr.setStyleSheet("background:#12122a; border-radius:14px; border-bottom:2px solid #8b5cf6; border-left:1px solid #252545; border-right:1px solid #252545; border-top:1px solid #252545;")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(20,14,20,14); hl.setSpacing(0)

        ico_box = QWidget(); ico_box.setFixedSize(48,48)
        ico_box.setStyleSheet("background:#6d28d9; border-radius:12px;")
        ibl = QVBoxLayout(ico_box); ibl.setContentsMargins(0,0,0,0)
        ic = QLabel("♪"); ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setFont(QFont("Segoe UI",22,QFont.Weight.Bold)); ic.setStyleSheet("color:#f0efff;")
        ibl.addWidget(ic); hl.addWidget(ico_box)

        nw = QWidget(); nw.setStyleSheet("background:transparent;")
        nl = QVBoxLayout(nw); nl.setContentsMargins(14,0,0,0); nl.setSpacing(1)
        t  = lbl(APP_NAME,20,True); nl.addWidget(t)
        nl.addWidget(lbl("MP3 Downloader",8,False,"#50507a"))
        hl.addWidget(nw); hl.addStretch()

        upd = mk_btn("☁  Update","ghost",38,110)
        upd.clicked.connect(self._check_update); hl.addWidget(upd)
        hl.addSpacing(8)
        sett = mk_btn("⚙","ghost",38,44)
        sett.clicked.connect(self._settings.slide_in); hl.addWidget(sett)
        hl.addSpacing(10)
        hl.addWidget(lbl(f"v{VERSION}",8,False,"#50507a"))
        pl.addWidget(hdr)

    # ── Sections ──────────────────────────────────────────────────────────────
    def _build_yt(self, pl):
        sec = SectionCard("YouTube / SoundCloud","Link einfügen oder Strg+V","#8b5cf6")
        row = QHBoxLayout(); row.setSpacing(10)
        self._url_entry = mk_entry("Link hier einfügen...")
        pe = mk_btn("Einfügen","ghost",46,100)
        pe.clicked.connect(lambda: self._url_entry.setText(QApplication.clipboard().text().strip()))
        row.addWidget(self._url_entry,1); row.addWidget(pe)
        sec.add_row(row); pl.addWidget(sec)

    def _build_search(self, pl):
        sec = SectionCard("Song suchen","Name + Künstler direkt laden","#a78bfa")
        row = QHBoxLayout(); row.setSpacing(10)
        self._search_entry = mk_entry("Songname...")
        self._artist_entry = mk_entry("Künstler / Interpret...")
        sb = mk_btn("Suchen & laden",h=46,w=150); sb.clicked.connect(self._search_btn)
        row.addWidget(self._search_entry,1); row.addWidget(self._artist_entry,1); row.addWidget(sb)
        sec.add_row(row); pl.addWidget(sec)

    def _build_spotify(self, pl):
        sec = SectionCard("Spotify","Link einfügen, Song wird auf YouTube gesucht","#1db954")
        row = QHBoxLayout(); row.setSpacing(10)
        self._sp_entry = mk_entry("Spotify-Link hier einfügen...")
        pe = mk_btn("Einfügen","ghost",46,100)
        pe.clicked.connect(lambda: self._sp_entry.setText(QApplication.clipboard().text().strip()))
        lb = mk_btn("Laden","spotify",46,80); lb.clicked.connect(self._do_spotify)
        row.addWidget(self._sp_entry,1); row.addWidget(pe); row.addWidget(lb)
        sec.add_row(row); pl.addWidget(sec)

    def _build_tiktok(self, pl):
        sec = SectionCard("TikTok / Instagram","Sound oder Video herunterladen","#5bcdd4")
        row = QHBoxLayout(); row.setSpacing(10)
        self._ti_entry = mk_entry("Link hier einfügen...")
        pe = mk_btn("Einfügen","ghost",46,100)
        pe.clicked.connect(lambda: self._ti_entry.setText(QApplication.clipboard().text().strip()))
        lb = mk_btn("Laden (MP3)","tiktok",46,110); lb.clicked.connect(self._do_tiktok)
        row.addWidget(self._ti_entry,1); row.addWidget(pe); row.addWidget(lb)
        sec.add_row(row); pl.addWidget(sec)

    def _build_dl_btn(self, pl):
        self._dl_btn = QPushButton("↓   MP3 herunterladen")
        self._dl_btn.setFixedHeight(60)
        self._dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dl_btn.setFont(QFont("Segoe UI Black",14,QFont.Weight.Bold))
        self._dl_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #8b5cf6,stop:1 #5b21b6);
                color:#fff; border-radius:14px; letter-spacing:1px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #a78bfa,stop:1 #7c3aed);
            }
            QPushButton:pressed { background:#6d28d9; }
            QPushButton:disabled { background:#252545; color:#404060; }
        """)
        self._dl_btn.clicked.connect(self._start_dl)
        pl.addWidget(self._dl_btn)

        # Progress bar
        pb = QWidget(); pb.setFixedHeight(6)
        pb.setStyleSheet("background:#1a1a38; border-radius:3px;")
        self._pb_inner = QWidget(pb)
        self._pb_inner.setStyleSheet("background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #8b5cf6,stop:1 #5bcdd4); border-radius:3px;")
        self._pb_inner.setFixedHeight(6); self._pb_inner.setFixedWidth(0)
        self._pb_pos = 0; self._pb_dir = 1
        self._pb_timer = QTimer(); self._pb_timer.timeout.connect(self._tick_pb)
        pl.addWidget(pb)
        self._pb_widget = pb

        # OK Banner
        self._ok = QWidget()
        self._ok.setStyleSheet("background:#071a10; border:1.5px solid #10b981; border-radius:12px;")
        ol = QHBoxLayout(self._ok); ol.setContentsMargins(20,12,20,12); ol.setSpacing(0)
        ck = lbl("✓",22,True,"#34d399"); ol.addWidget(ck)
        tf = QWidget(); tf.setStyleSheet("background:transparent;")
        tfl = QVBoxLayout(tf); tfl.setContentsMargins(14,0,0,0); tfl.setSpacing(2)
        tfl.addWidget(lbl("Download abgeschlossen!",11,True,"#34d399"))
        self._ok_path = lbl("",9,False,"#10b981"); tfl.addWidget(self._ok_path)
        ol.addWidget(tf,1); self._ok.hide(); pl.addWidget(self._ok)

    def _build_log(self, pl):
        lc = QWidget(); lc.setObjectName("logcard")
        ll = QVBoxLayout(lc); ll.setContentsMargins(0,0,0,0); ll.setSpacing(0)
        lhdr = QWidget(); lhdr.setObjectName("loghdr")
        lhl = QHBoxLayout(lhdr); lhl.setContentsMargins(16,8,16,8); lhl.setSpacing(6)
        dot = lbl("●",9,False,"#10b981"); lhl.addWidget(dot)
        lhl.addWidget(lbl("LOG",9,True,"#50507a")); lhl.addStretch()
        clr = mk_btn("Log leeren","ghost",28,90)
        clr.setStyleSheet("QPushButton{background:transparent;color:#50507a;font-size:8pt;border:none;} QPushButton:hover{color:#e8e8ff;}")
        clr.clicked.connect(lambda: self._log_box.clear()); lhl.addWidget(clr)
        ll.addWidget(lhdr); ll.addWidget(mk_sep())
        self._log_box = QTextEdit(); self._log_box.setReadOnly(True); self._log_box.setFixedHeight(140)
        ll.addWidget(self._log_box); pl.addWidget(lc)

    # ── Progress ──────────────────────────────────────────────────────────────
    def _tick_pb(self):
        w = self._pb_widget.width(); bw = max(100, w//3)
        self._pb_pos += self._pb_dir * 7
        if self._pb_pos + bw >= w: self._pb_dir = -1
        if self._pb_pos <= 0: self._pb_dir = 1
        self._pb_inner.setGeometry(self._pb_pos, 0, bw, 6)

    def _start_prog(self): self._pb_timer.start(14)
    def _stop_prog(self): self._pb_timer.stop(); self._pb_inner.setFixedWidth(0)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _log(self, m): self._log_box.append(m)
    def _busy(self, on):
        self._dl_btn.setEnabled(not on)
        self._dl_btn.setText("  ⏳  Lädt..." if on else "↓   MP3 herunterladen")
        if on: self._start_prog()
        else:  self._stop_prog()
    def _show_ok(self, folder):
        self._ok_path.setText(folder); self._ok.show()
        QTimer.singleShot(6000, self._ok.hide)
    def _open_explorer(self, fp):
        if self._open_folder and fp and os.path.exists(fp):
            subprocess.Popen(["explorer","/select,",os.path.normpath(fp)], creationflags=CNW)

    # ── Tools ─────────────────────────────────────────────────────────────────
    def _check_tools(self):
        missing = [n for n,p in [("yt-dlp",YTDLP_PATH),("ffmpeg",FFMPEG_PATH)] if not os.path.exists(p)]
        if missing:
            self._log(f"Installiere: {', '.join(missing)}..."); self._busy(True)
            self._tw = ToolsWorker()
            self._tw.log.connect(self._log)
            self._tw.done.connect(lambda: self._busy(False))
            self._tw.start()
        else: self._log("[Bereit]  Strg+V = sofort herunterladen")

    # ── Search/Spotify ────────────────────────────────────────────────────────
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
    def _run_worker(self, cmd, clear_fn=None):
        self._busy(True); self._ok.hide(); self._last_file = None
        self._worker = Worker(cmd)
        self._worker.log.connect(self._log)
        self._worker.file_out.connect(lambda f: setattr(self,'_last_file',f))
        def _done(ok):
            self._busy(False)
            if ok:
                if clear_fn: QTimer.singleShot(0, clear_fn)
                self._log(f"Fertig!  →  {self._output_dir}")
                QTimer.singleShot(0, lambda: self._show_ok(self._output_dir))
                QTimer.singleShot(500, lambda: self._open_explorer(self._last_file))
            else: self._log("Fehlgeschlagen.")
        self._worker.done.connect(_done); self._worker.start()

    def _start_dl(self):
        url = self._url_entry.text().strip()
        if not url: return
        if not os.path.exists(YTDLP_PATH): self._log("Tools noch nicht bereit!"); return
        out = os.path.join(self._output_dir,"%(title)s.%(ext)s")
        cmd = [YTDLP_PATH,"-x","--audio-format","mp3","--audio-quality",self._quality,
               "--ffmpeg-location",TOOLS_DIR,"-o",out,"--no-playlist","--print","after_move:filepath",url]
        self._run_worker(cmd, self._url_entry.clear)

    def _do_tiktok(self):
        url = self._ti_entry.text().strip().split("?")[0]
        if not url: return
        if not os.path.exists(YTDLP_PATH): self._log("Tools noch nicht bereit!"); return
        out = os.path.join(self._output_dir,"%(title).80s.%(ext)s")
        cmd = [YTDLP_PATH,"-x","--audio-format","mp3","--audio-quality",self._quality,
               "--ffmpeg-location",TOOLS_DIR,"--no-playlist","--no-check-certificate",
               "--user-agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
               "-o",out,"--print","after_move:filepath",url]
        self._run_worker(cmd, self._ti_entry.clear)

    def _check_update(self):
        self._log("Suche Updates...")
        def run():
            try:
                req = urllib.request.Request(GITHUB_RAW, headers={"User-Agent":"Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as r: content = r.read().decode("utf-8")
                m = re.search(r'^VERSION\s*=\s*"([^"]+)"', content, re.MULTILINE)
                nv = m.group(1) if m else VERSION
                if nv == VERSION: self._log(f"Aktuell (v{VERSION})"); return
                self._log(f"Neue Version v{nv} verfügbar!")
            except Exception as e: self._log(f"Update-Fehler: {e}")
        threading.Thread(target=run, daemon=True).start()


# ─── Login Window ─────────────────────────────────────────────────────────────
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WaveLoad"); self.setFixedSize(480,600)
        self.logged_in = False
        ico = os.path.join(BASE_DIR,"icon.ico")
        if os.path.exists(ico): self.setWindowIcon(QIcon(ico))
        self._build()

    def _build(self):
        root = QWidget(); root.setObjectName("bg"); self.setCentralWidget(root)
        ml = QVBoxLayout(root); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)

        # Top logo
        top = QWidget(); top.setStyleSheet("background:#0d0d1a;")
        tl = QVBoxLayout(top); tl.setContentsMargins(0,32,0,12)
        tl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        bw = QWidget(); bw.setFixedSize(56,56)
        bw.setStyleSheet("background:#6d28d9; border-radius:14px;")
        bwl = QVBoxLayout(bw); bwl.setContentsMargins(0,0,0,0)
        ic = QLabel("♪"); ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setFont(QFont("Segoe UI",24,QFont.Weight.Bold)); ic.setStyleSheet("color:#f0efff;")
        bwl.addWidget(ic)
        wrap = QWidget(); wrap.setStyleSheet("background:transparent;")
        wl = QHBoxLayout(wrap); wl.addWidget(bw)
        tl.addWidget(wrap)
        t = QLabel("WaveLoad"); t.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        t.setFont(QFont("Segoe UI Black",22,QFont.Weight.Bold))
        t.setStyleSheet("color:#e8e8ff; background:transparent;"); tl.addWidget(t)
        ml.addWidget(top)

        # Tab bar
        tb = QWidget(); tb.setStyleSheet("background:#16163a; border-bottom:2px solid #252545;")
        tbl = QHBoxLayout(tb); tbl.setContentsMargins(40,0,40,0); tbl.setSpacing(0)
        self._tl = QPushButton("Anmelden"); self._tl.setFixedHeight(46)
        self._tr = QPushButton("Registrieren"); self._tr.setFixedHeight(46)
        for b in (self._tl, self._tr):
            b.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
            b.setCursor(Qt.CursorShape.PointingHandCursor); tbl.addWidget(b)
        self._tl.clicked.connect(lambda: self._show(0))
        self._tr.clicked.connect(lambda: self._show(1))
        ml.addWidget(tb)

        # Pages
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background:#12122a;")
        self._stack.addWidget(self._login_page())
        self._stack.addWidget(self._reg_page())
        ml.addWidget(self._stack,1)

        # Admin
        adm = QWidget(); adm.setStyleSheet("background:#0d0d1a;")
        al = QVBoxLayout(adm); al.setContentsMargins(40,10,40,24); al.setSpacing(8)
        al.addWidget(mk_sep("#252545"))
        ar = QHBoxLayout(); ar.setSpacing(8)
        ar.addWidget(lbl("Admin:",9,False,"#50507a"))
        self._adm = mk_entry("Admin-Code",pw=True,h=38)
        ab = mk_btn("→",h=38,w=42); ab.clicked.connect(self._admin)
        ar.addWidget(self._adm,1); ar.addWidget(ab); al.addLayout(ar)
        ml.addWidget(adm)
        self._adm.returnPressed.connect(self._admin)
        self._show(0)

    def _login_page(self):
        w = QWidget(); w.setStyleSheet("background:#12122a;")
        l = QVBoxLayout(w); l.setContentsMargins(40,28,40,20); l.setSpacing(10)
        l.addWidget(lbl("Benutzername",9,True,"#8080b0"))
        self._ue = mk_entry("Dein Benutzername"); l.addWidget(self._ue)
        l.addWidget(lbl("Passwort",9,True,"#8080b0"))
        self._pe = mk_entry("Dein Passwort",pw=True); l.addWidget(self._pe)
        self._err = lbl("",9,False,"#f87171"); l.addWidget(self._err)
        lb = mk_btn("Anmelden",h=48)
        lb.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        lb.clicked.connect(self._login); l.addWidget(lb); l.addStretch()
        self._pe.returnPressed.connect(self._login)
        return w

    def _reg_page(self):
        w = QWidget(); w.setStyleSheet("background:#12122a;")
        l = QVBoxLayout(w); l.setContentsMargins(40,28,40,20); l.setSpacing(8)
        l.addWidget(lbl("Benutzername",9,True,"#8080b0"))
        self._ru = mk_entry("Gewünschter Benutzername"); l.addWidget(self._ru)
        l.addWidget(lbl("Passwort",9,True,"#8080b0"))
        self._rp = mk_entry("Mind. 6 Zeichen",pw=True); l.addWidget(self._rp)
        l.addWidget(lbl("Passwort bestätigen",9,True,"#8080b0"))
        self._rp2 = mk_entry("Passwort wiederholen",pw=True); l.addWidget(self._rp2)
        self._rerr = lbl("",9,False,"#f87171"); l.addWidget(self._rerr)
        rb = mk_btn("Konto erstellen →","green",48)
        rb.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        rb.clicked.connect(self._do_register); l.addWidget(rb); l.addStretch()
        self._rp2.returnPressed.connect(self._do_register)
        return w

    def _show(self, idx):
        self._stack.setCurrentIndex(idx)
        act = "QPushButton{background:#8b5cf6;color:#fff;border-radius:0;border-bottom:3px solid #a78bfa;font-size:11pt;font-weight:bold;}"
        ina = "QPushButton{background:#16163a;color:#50507a;border-radius:0;font-size:11pt;font-weight:bold;} QPushButton:hover{color:#9090b8;}"
        self._tl.setStyleSheet(act if idx==0 else ina)
        self._tr.setStyleSheet(act if idx==1 else ina)

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


# ─── Entry ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    app.setFont(QFont("Segoe UI",10))

    login = LoginWindow(); login.show(); app.exec()
    if not login.logged_in: sys.exit(0)

    win = MainWindow(); win.show(); sys.exit(app.exec())
