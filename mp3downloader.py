# WaveLoad v9.0 – Clean Modern UI
import sys, os, re, threading, subprocess, shutil, zipfile, hashlib, json
import urllib.request, urllib.parse
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit,
    QScrollArea, QStackedWidget, QButtonGroup, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QPoint
from PyQt6.QtGui import QFont, QIcon

VERSION    = "9.0"
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

STYLE = """
* { font-family: 'Segoe UI', Arial, sans-serif; }
QMainWindow { background: #111118; }
QWidget#bg  { background: #111118; }
QScrollArea { background: #111118; border: none; }
QScrollBar:vertical { background: #111118; width: 4px; }
QScrollBar::handle:vertical { background: #333355; border-radius: 2px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QWidget#section {
    background: #1a1a28;
    border-radius: 12px;
}
QWidget#panel {
    background: #1a1a28;
    border-radius: 14px;
}

QLineEdit {
    background: #222235;
    border: 1.5px solid #2e2e4a;
    border-radius: 8px;
    color: #e0e0f0;
    padding: 0 12px;
    font-size: 10pt;
}
QLineEdit:focus { border: 1.5px solid #7c5cf6; }

QTextEdit {
    background: #1a1a28;
    border: none;
    color: #6b6b9a;
    font-family: Consolas, monospace;
    font-size: 9pt;
    padding: 6px 10px;
    border-bottom-left-radius: 12px;
    border-bottom-right-radius: 12px;
}

QPushButton {
    background: #7c5cf6;
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 10pt;
    font-weight: bold;
    padding: 0 18px;
}
QPushButton:hover   { background: #9070ff; }
QPushButton:pressed { background: #5a3fd4; }
QPushButton:disabled { background: #222235; color: #404060; }

QPushButton#secondary {
    background: #222235;
    color: #8080a8;
    border: 1px solid #2e2e4a;
}
QPushButton#secondary:hover { background: #2a2a42; color: #c0c0e0; }

QPushButton#spotify  { background: #1db954; color: #000; }
QPushButton#spotify:hover { background: #22d460; }
QPushButton#tiktok   { background: #2bbdc4; color: #000; }
QPushButton#tiktok:hover  { background: #35cdd4; }
QPushButton#success  { background: #1a4a2a; color: #4ade80; border: 1px solid #166534; }
QPushButton#danger   { background: transparent; color: #666688; border-radius: 6px; padding: 0 8px; font-size: 14pt; }
QPushButton#danger:hover { background: #ef4444; color: #fff; }
QPushButton#tabactive   { background: transparent; color: #e0e0f0; border-bottom: 2px solid #7c5cf6; border-radius: 0; font-size: 11pt; font-weight: bold; padding: 10px 20px; }
QPushButton#tabinactive { background: transparent; color: #50507a; border-bottom: 2px solid transparent; border-radius: 0; font-size: 11pt; font-weight: bold; padding: 10px 20px; }
QPushButton#tabinactive:hover { color: #9090c0; }

QLabel { color: #e0e0f0; background: transparent; }
"""

# ── Workers ───────────────────────────────────────────────────────────────────
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
                self.log.emit("yt-dlp wird installiert...")
                urllib.request.urlretrieve(YTDLP_URL, YTDLP_PATH)
                self.log.emit("yt-dlp ✓")
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

# ── Widgets ───────────────────────────────────────────────────────────────────
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

def L(text, size=10, color="#e0e0f0", bold=False):
    l = QLabel(text)
    l.setFont(QFont("Segoe UI", size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
    l.setStyleSheet(f"color:{color};")
    return l

def sep():
    f = QFrame(); f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("background:#222235; border:none;"); f.setFixedHeight(1)
    return f

class Section(QWidget):
    def __init__(self, title, accent="#7c5cf6"):
        super().__init__(); self.setObjectName("section")
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(20,16,20,16); self._root.setSpacing(12)
        hdr = QHBoxLayout()
        bar = QWidget(); bar.setFixedSize(3, 18)
        bar.setStyleSheet(f"background:{accent}; border-radius:2px;")
        hdr.addWidget(bar)
        hdr.addWidget(L(title, 10, "#e0e0f0", True))
        hdr.addStretch()
        self._root.addLayout(hdr)
    def add(self, w): self._root.addWidget(w)
    def add_row(self, l): self._root.addLayout(l)


# ── Settings Panel ────────────────────────────────────────────────────────────
class SettingsPanel(QWidget):
    def __init__(self, parent, app_ref):
        super().__init__(parent); self.app = app_ref
        self.setObjectName("panel")
        self.setFixedWidth(460)
        self._build(); self.hide()
        self._anim = QPropertyAnimation(self, b"pos")

    def _build(self):
        l = QVBoxLayout(self); l.setContentsMargins(24,20,24,24); l.setSpacing(20)

        # Header
        hdr = QHBoxLayout()
        hdr.addWidget(L("Einstellungen", 13, "#e0e0f0", True))
        hdr.addStretch()
        x = B("✕","danger",32,32); x.clicked.connect(self.slide_out)
        hdr.addWidget(x); l.addLayout(hdr)
        l.addWidget(sep())

        # Ordner
        l.addWidget(L("Speicherordner", 9, "#6b6b9a"))
        dr = QHBoxLayout(); dr.setSpacing(10)
        self.dir_lbl = QLineEdit(); self.dir_lbl.setReadOnly(True)
        self.dir_lbl.setFixedHeight(40); self.dir_lbl.setText(self.app._output_dir)
        ab = B("···", h=40, w=44); ab.clicked.connect(self._browse)
        dr.addWidget(self.dir_lbl, 1); dr.addWidget(ab); l.addLayout(dr)

        # Qualität
        l.addWidget(L("Audioqualität", 9, "#6b6b9a"))
        qr = QHBoxLayout(); qr.setSpacing(8); self._qg = QButtonGroup(self)
        for i,(t,v) in enumerate([("320 kbps","0"),("192 kbps","5"),("128 kbps","9")]):
            b = QPushButton(t); b.setCheckable(True); b.setFixedHeight(40)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setProperty("qval", v)
            b.setStyleSheet("""
                QPushButton { background:#222235; color:#6b6b9a; border-radius:8px;
                              font-size:9pt; font-weight:bold; border:1.5px solid #2e2e4a; }
                QPushButton:checked { background:#7c5cf6; color:#fff; border-color:#7c5cf6; }
                QPushButton:hover   { background:#2a2a42; }
            """)
            self._qg.addButton(b, i); qr.addWidget(b)
            if i == 0: b.setChecked(True)
        self._qg.idToggled.connect(lambda i,c: c and setattr(self.app,'_quality',self._qg.button(i).property("qval")))
        l.addLayout(qr)

        # Nach Download
        l.addWidget(L("Nach Download", 9, "#6b6b9a"))
        self._open_cb = QPushButton("Dateimanager nach Download öffnen")
        self._open_cb.setCheckable(True); self._open_cb.setChecked(True)
        self._open_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_cb.setStyleSheet("""
            QPushButton { background:#222235; color:#6b6b9a; border-radius:8px;
                          font-size:9pt; text-align:left; padding:0 14px;
                          border:1.5px solid #2e2e4a; height:40px; }
            QPushButton:checked { background:#162a1e; color:#4ade80; border-color:#166534; }
        """)
        self._open_cb.toggled.connect(lambda v: setattr(self.app,'_open_folder',v))
        l.addWidget(self._open_cb)
        l.addStretch()
        self.adjustSize()

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self,"Ordner wählen",self.app._output_dir)
        if d: self.app._output_dir = d; self.dir_lbl.setText(d)

    def slide_in(self):
        self.adjustSize()
        pw = self.parent().width(); ph = self.parent().height()
        w = self.width(); h = self.height()
        cx = (pw-w)//2; cy = (ph-h)//2
        self.move(cx, -h); self.show(); self.raise_()
        self._anim.stop()
        self._anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self._anim.setDuration(400)
        self._anim.setStartValue(QPoint(cx,-h))
        self._anim.setEndValue(QPoint(cx,cy))
        self._anim.start()

    def slide_out(self):
        pw = self.parent().width(); ph = self.parent().height()
        w = self.width(); h = self.height()
        cx = (pw-w)//2; cy = (ph-h)//2
        self._anim.stop()
        self._anim.setEasingCurve(QEasingCurve.Type.InBack)
        self._anim.setDuration(280)
        self._anim.setStartValue(QPoint(cx,cy))
        self._anim.setEndValue(QPoint(cx,-h))
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
        self.setWindowTitle(APP_NAME); self.resize(720, 820); self.setMinimumSize(600,560)
        self._output_dir  = os.path.join(os.path.expanduser("~"), "Music")
        self._quality     = "0"
        self._open_folder = True
        self._last_file   = None
        ico = os.path.join(BASE_DIR,"icon.ico")
        if os.path.exists(ico): self.setWindowIcon(QIcon(ico))

        root = QWidget(); root.setObjectName("bg"); self.setCentralWidget(root)
        ml = QVBoxLayout(root); ml.setContentsMargins(0,0,0,0)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QWidget(); inner.setStyleSheet("background:#111118;")
        il = QVBoxLayout(inner); il.setContentsMargins(24,24,24,28); il.setSpacing(10)
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

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self, pl):
        w = QWidget(); w.setObjectName("section")
        hl = QHBoxLayout(w); hl.setContentsMargins(20,14,20,14)
        hl.addWidget(L(APP_NAME, 18, "#e0e0f0", True))
        hl.addWidget(L(f"v{VERSION}", 9, "#444466"))
        hl.addStretch()
        u = B("Update","secondary",36,90); u.clicked.connect(self._check_update)
        s = B("⚙","secondary",36,36); s.clicked.connect(self._settings.slide_in)
        hl.addWidget(u); hl.addSpacing(8); hl.addWidget(s)
        pl.addWidget(w)

    # ── Sections ──────────────────────────────────────────────────────────────
    def _build_yt(self, pl):
        sec = Section("YouTube / SoundCloud")
        row = QHBoxLayout(); row.setSpacing(8)
        self._url = E("Link einfügen...")
        p = B("Einfügen","secondary",44,90)
        p.clicked.connect(lambda: self._url.setText(QApplication.clipboard().text().strip()))
        row.addWidget(self._url,1); row.addWidget(p)
        sec.add_row(row); pl.addWidget(sec)

    def _build_search(self, pl):
        sec = Section("Song suchen")
        row = QHBoxLayout(); row.setSpacing(8)
        self._sq = E("Songname...")
        self._ar = E("Künstler...")
        sb = B("Suchen & laden", h=44, w=140); sb.clicked.connect(self._search_btn)
        row.addWidget(self._sq,1); row.addWidget(self._ar,1); row.addWidget(sb)
        sec.add_row(row); pl.addWidget(sec)

    def _build_spotify(self, pl):
        sec = Section("Spotify", "#1db954")
        row = QHBoxLayout(); row.setSpacing(8)
        self._sp = E("Spotify-Link...")
        p = B("Einfügen","secondary",44,90)
        p.clicked.connect(lambda: self._sp.setText(QApplication.clipboard().text().strip()))
        lb = B("Laden","spotify",44,80); lb.clicked.connect(self._do_spotify)
        row.addWidget(self._sp,1); row.addWidget(p); row.addWidget(lb)
        sec.add_row(row); pl.addWidget(sec)

    def _build_tiktok(self, pl):
        sec = Section("TikTok / Instagram", "#2bbdc4")
        row = QHBoxLayout(); row.setSpacing(8)
        self._ti = E("TikTok / Instagram Link...")
        p = B("Einfügen","secondary",44,90)
        p.clicked.connect(lambda: self._ti.setText(QApplication.clipboard().text().strip()))
        lb = B("Laden","tiktok",44,80); lb.clicked.connect(self._do_tiktok)
        row.addWidget(self._ti,1); row.addWidget(p); row.addWidget(lb)
        sec.add_row(row); pl.addWidget(sec)

    def _build_dl(self, pl):
        self._dl_btn = QPushButton("↓  MP3 herunterladen")
        self._dl_btn.setFixedHeight(54)
        self._dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._dl_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._dl_btn.setStyleSheet("""
            QPushButton { background:#7c5cf6; color:#fff; border-radius:12px; }
            QPushButton:hover { background:#9070ff; }
            QPushButton:pressed { background:#5a3fd4; }
            QPushButton:disabled { background:#222235; color:#404060; }
        """)
        self._dl_btn.clicked.connect(self._start_dl)
        pl.addWidget(self._dl_btn)

        # Progress
        pb = QWidget(); pb.setFixedHeight(3); pb.setStyleSheet("background:#222235; border-radius:2px;")
        self._pbi = QWidget(pb); self._pbi.setFixedHeight(3)
        self._pbi.setStyleSheet("background:#7c5cf6; border-radius:2px;")
        self._pbi.setFixedWidth(0); self._pb_pos=0; self._pb_dir=1
        self._pb_t = QTimer(); self._pb_t.timeout.connect(lambda: self._tick(pb))
        pl.addWidget(pb); self._pb = pb

        # OK
        self._ok = QWidget(); self._ok.setObjectName("section")
        ol = QHBoxLayout(self._ok); ol.setContentsMargins(16,12,16,12)
        ol.addWidget(L("✓  Download abgeschlossen!",10,"#4ade80",True))
        ol.addStretch()
        self._ok_p = L("",9,"#22c55e"); ol.addWidget(self._ok_p)
        self._ok.hide(); pl.addWidget(self._ok)

    def _build_log(self, pl):
        w = QWidget(); w.setObjectName("section")
        wl = QVBoxLayout(w); wl.setContentsMargins(0,0,0,0); wl.setSpacing(0)
        hdr = QWidget(); hl = QHBoxLayout(hdr); hl.setContentsMargins(16,10,16,10)
        hl.addWidget(L("Log",9,"#444466",True)); hl.addStretch()
        clr = B("leeren","secondary",26,60)
        clr.setStyleSheet("QPushButton{background:transparent;color:#444466;font-size:8pt;border:none;} QPushButton:hover{color:#9090c0;}")
        clr.clicked.connect(lambda: self._log_box.clear()); hl.addWidget(clr)
        wl.addWidget(hdr); wl.addWidget(sep())
        self._log_box = QTextEdit(); self._log_box.setReadOnly(True); self._log_box.setFixedHeight(130)
        wl.addWidget(self._log_box); pl.addWidget(w)

    def _tick(self, pb):
        w = pb.width(); bw = max(80, w//4)
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
            "--ffmpeg-location",TOOLS_DIR,"-o",out,"--no-playlist","--print","after_move:filepath",url],
            self._url.clear)

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
        top=QWidget(); top.setStyleSheet("background:#111118;")
        tl=QVBoxLayout(top); tl.setContentsMargins(0,36,0,20); tl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        tl.addWidget(L(APP_NAME,24,"#e0e0f0",True),alignment=Qt.AlignmentFlag.AlignHCenter)
        tl.addWidget(L("MP3 Downloader",9,"#444466"),alignment=Qt.AlignmentFlag.AlignHCenter)
        ml.addWidget(top)

        # Tabs
        tb=QWidget(); tb.setStyleSheet("background:#111118; border-bottom:1px solid #222235;")
        tbl=QHBoxLayout(tb); tbl.setContentsMargins(32,0,32,0); tbl.setSpacing(0)
        self._tl=B("Anmelden","tabactive",46); self._tr=B("Registrieren","tabinactive",46)
        self._tl.clicked.connect(lambda:self._show(0)); self._tr.clicked.connect(lambda:self._show(1))
        tbl.addWidget(self._tl); tbl.addWidget(self._tr); ml.addWidget(tb)

        # Pages
        self._stack=QStackedWidget(); self._stack.setStyleSheet("background:#111118;")
        self._stack.addWidget(self._login_page()); self._stack.addWidget(self._reg_page())
        ml.addWidget(self._stack,1)

        # Admin
        adm=QWidget(); adm.setStyleSheet("background:#111118;")
        al=QVBoxLayout(adm); al.setContentsMargins(32,10,32,24); al.setSpacing(8)
        al.addWidget(sep())
        ar=QHBoxLayout(); ar.setSpacing(8)
        ar.addWidget(L("Admin:",9,"#444466"))
        self._adm=E("Admin-Code",pw=True,h=38)
        ab=B("→",h=38,w=42); ab.clicked.connect(self._admin)
        ar.addWidget(self._adm,1); ar.addWidget(ab); al.addLayout(ar)
        ml.addWidget(adm)
        self._adm.returnPressed.connect(self._admin)
        self._show(0)

    def _login_page(self):
        w=QWidget(); w.setStyleSheet("background:#111118;")
        l=QVBoxLayout(w); l.setContentsMargins(32,24,32,16); l.setSpacing(10)
        l.addWidget(L("Benutzername",9,"#6b6b9a"))
        self._ue=E("Dein Benutzername"); l.addWidget(self._ue)
        l.addWidget(L("Passwort",9,"#6b6b9a"))
        self._pe=E("Dein Passwort",pw=True); l.addWidget(self._pe)
        self._err=L("",9,"#f87171"); l.addWidget(self._err)
        lb=B("Anmelden",h=48); lb.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        lb.clicked.connect(self._login); l.addWidget(lb); l.addStretch()
        self._pe.returnPressed.connect(self._login)
        return w

    def _reg_page(self):
        w=QWidget(); w.setStyleSheet("background:#111118;")
        l=QVBoxLayout(w); l.setContentsMargins(32,24,32,16); l.setSpacing(8)
        l.addWidget(L("Benutzername",9,"#6b6b9a"))
        self._ru=E("Gewünschter Benutzername"); l.addWidget(self._ru)
        l.addWidget(L("Passwort",9,"#6b6b9a"))
        self._rp=E("Mind. 6 Zeichen",pw=True); l.addWidget(self._rp)
        l.addWidget(L("Passwort bestätigen",9,"#6b6b9a"))
        self._rp2=E("Passwort wiederholen",pw=True); l.addWidget(self._rp2)
        self._rerr=L("",9,"#f87171"); l.addWidget(self._rerr)
        rb=B("Konto erstellen →","success",48); rb.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        rb.setStyleSheet("QPushButton{background:#1a4a2a;color:#4ade80;border-radius:8px;font-size:11pt;font-weight:bold;} QPushButton:hover{background:#1e5530;}")
        rb.clicked.connect(self._do_register); l.addWidget(rb); l.addStretch()
        self._rp2.returnPressed.connect(self._do_register)
        return w

    def _show(self,idx):
        self._stack.setCurrentIndex(idx)
        act="QPushButton{background:transparent;color:#e0e0f0;border-bottom:2px solid #7c5cf6;border-radius:0;font-size:11pt;font-weight:bold;padding:10px 20px;}"
        ina="QPushButton{background:transparent;color:#444466;border-bottom:2px solid transparent;border-radius:0;font-size:11pt;font-weight:bold;padding:10px 20px;} QPushButton:hover{color:#8080a8;}"
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


# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__=="__main__":
    app=QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    app.setFont(QFont("Segoe UI",10))
    login=LoginWindow(); login.show(); app.exec()
    if not login.logged_in: sys.exit(0)
    win=MainWindow(); win.show(); sys.exit(app.exec())
