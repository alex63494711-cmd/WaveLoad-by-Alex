import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading, subprocess, os, sys, re, shutil, zipfile
import urllib.request, urllib.parse

VERSION    = "5.0"
APP_NAME   = "WaveLoad"
GITHUB_RAW = "https://raw.githubusercontent.com/alex63494711-cmd/alex-mp3-song-app/refs/heads/main/mp3downloader.py"
GITHUB_EXE = "https://github.com/alex63494711-cmd/alex-mp3-song-app/releases/latest/download/WaveLoad.exe"

IS_EXE   = getattr(sys, 'frozen', False)
BASE_DIR = os.path.dirname(os.path.abspath(sys.executable if IS_EXE else __file__))
TOOLS_DIR   = os.path.join(BASE_DIR, "tools")
YTDLP_PATH  = os.path.join(TOOLS_DIR, "yt-dlp.exe")
FFMPEG_PATH = os.path.join(TOOLS_DIR, "ffmpeg.exe")
YTDLP_URL   = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
FFMPEG_URL  = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

CREATE_NO_WINDOW = 0x08000000

# ── Farben ────────────────────────────────────────────────────────────────────
BG       = "#0a0a14"
CARD     = "#111122"
CARD2    = "#181832"
CARD3    = "#1e1e3a"
BORDER   = "#2a2a50"
ACCENT   = "#8b5cf6"
ACCENT_H = "#a78bfa"
ACCENT_D = "#6d28d9"
GREEN    = "#10b981"
GREEN_L  = "#34d399"
GREEN_BG = "#071a10"
SPOTIFY  = "#1db954"
TIKTOK   = "#5bcdd4"
INSTA    = "#d63070"
TEXT     = "#f0efff"
TEXT2    = "#9090b8"
TEXT3    = "#50507a"
RED      = "#f87171"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def get_icon_path():
    p = os.path.join(BASE_DIR, "icon.ico")
    return p if os.path.exists(p) else None


class App(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color=BG)
        self.title(APP_NAME)
        self.geometry("740x860")
        self.minsize(640, 600)
        self.resizable(True, True)

        self.output_dir  = ctk.StringVar(value=os.path.join(os.path.expanduser("~"), "Music"))
        self.quality_var = ctk.StringVar(value="0")
        self.url_var     = ctk.StringVar()
        self.last_file   = None
        self.open_folder = ctk.BooleanVar(value=True)

        self._settings_open = False

        self._build_ui()
        self.after(100, self._set_icon)
        self.after(400, self._check_tools)
        self.bind("<Control-v>", self._ctrl_v)
        self.bind("<Control-V>", self._ctrl_v)

    def _smooth_scroll(self):
        self._sa = True
        cur = self._cvs.yview()[0]
        diff = self._sy - cur
        if abs(diff) < 0.0003:
            self._cvs.yview_moveto(self._sy); self._sa = False; return
        self._cvs.yview_moveto(cur + diff * 0.16)
        self.after(11, self._smooth_scroll)

    def _set_icon(self):
        ico = get_icon_path()
        if ico:
            try: self.iconbitmap(ico)
            except: pass

    def _ctrl_v(self, e=None):
        try:
            c = self.clipboard_get().strip()
            if "spotify.com" in c:
                self.sp_entry.delete(0, "end"); self.sp_entry.insert(0, c)
                self._log("Spotify erkannt – suche...", GREEN_L)
                self.after(300, self._do_spotify)
            elif "tiktok.com" in c or "instagram.com" in c or "instagr.am" in c:
                self.ti_entry.delete(0, "end"); self.ti_entry.insert(0, c)
                self._log("TikTok/Instagram erkannt – bereit!", ACCENT_H)
            elif c.startswith("http"):
                self.url_var.set(c)
                self._log("Link erkannt – lade...", ACCENT_H)
                self.after(300, self._start_dl)
        except: pass

    # ── UI BUILD ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Scrollable main frame
        # Use Canvas for smooth custom scroll
        import tkinter as tk
        self._cvs = tk.Canvas(self, bg=BG, highlightthickness=0)
        self._cvs.pack(side="left", fill="both", expand=True)
        self._sbc = tk.Canvas(self, bg=BG, width=8, highlightthickness=0)
        self._sbc.pack(side="right", fill="y", padx=(0,2))
        self._sth = self._sbc.create_rectangle(1,2,7,40, fill=ACCENT, outline="")
        self._scroll = tk.Frame(self._cvs, bg=BG)
        self._win = self._cvs.create_window((0,0), window=self._scroll, anchor="nw")
        self._cvs.bind("<Configure>", lambda e: self._cvs.itemconfig(self._win, width=e.width))
        self._scroll.bind("<Configure>", lambda e: self._cvs.configure(scrollregion=self._cvs.bbox("all")))
        def _yscroll(first, last):
            try:
                f,l = float(first), float(last)
                h = self._sbc.winfo_height()
                if h < 4: return
                y0 = max(2, int(f*h)); y1 = min(h-2, int(l*h))
                if y1-y0 < 20: y1 = y0+20
                self._sbc.coords(self._sth,1,y0,7,y1)
                self._sbc.configure(width=0 if (f<=0.0 and l>=1.0) else 9)
            except: pass
        self._cvs.configure(yscrollcommand=_yscroll)
        self._sy = 0.0; self._sa = False
        def _wheel(e):
            total = self._scroll.winfo_reqheight()
            vh = self._cvs.winfo_height()
            if total <= vh: return
            self._sy = max(0.0, min(1.0, self._sy - (e.delta/120)*60/max(total,1)))
            if not self._sa: self._smooth_scroll()
        self._cvs.bind_all("<MouseWheel>", _wheel)

        self._build_header(self._scroll)
        self._build_section_yt(self._scroll)
        self._build_section_search(self._scroll)
        self._build_section_spotify(self._scroll)
        self._build_section_tiktok(self._scroll)
        self._build_download_btn(self._scroll)
        self._build_log(self._scroll)

        # Settings panel (overlay)
        self._settings_win = None
        self._spanel_visible = False
        import tkinter as tk
        self._spanel = tk.Frame(self, bg=CARD2,
                                highlightthickness=1, highlightbackground=ACCENT)


    def _card(self, parent, **kw):
        return ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10,
                            border_width=1, border_color=BORDER,
                            background_corner_colors=None, **kw)

    def _label(self, parent, text, size=10, bold=False, color=TEXT2, **kw):
        weight = "bold" if bold else "normal"
        return ctk.CTkLabel(parent, text=text, text_color=color,
                            font=("Segoe UI", size, weight), **kw)

    def _entry(self, parent, var=None, placeholder="", accent=ACCENT, width=None):
        kw = dict(
            textvariable=var,
            placeholder_text=placeholder,
            fg_color=CARD3,
            border_color=BORDER,
            border_width=1,
            text_color=TEXT,
            placeholder_text_color=TEXT3,
            font=("Segoe UI", 10),
            corner_radius=8,
            height=40,
        )
        if width: kw["width"] = width
        e = ctk.CTkEntry(parent, **kw)
        return e

    def _btn(self, parent, text, cmd, color=ACCENT, hover=ACCENT_H,
             text_color=TEXT, width=None, height=38, font_size=10):
        def _animated_cmd(b=None, c=color, h=hover, fn=cmd):
            if b:
                b.configure(fg_color=h)
                b.after(80, lambda: b.configure(fg_color=c))
            fn()
        kw = dict(
            text=text,
            fg_color=color, hover_color=hover,
            text_color=text_color,
            font=("Segoe UI", font_size, "bold"),
            corner_radius=8,
            height=height,
        )
        if width: kw["width"] = width
        b = ctk.CTkButton(parent, **kw)
        b.configure(command=lambda b=b: _animated_cmd(b))
        return b

    def _sec_header(self, parent, title, subtitle, accent=ACCENT):
        import tkinter as tk
        hdr = tk.Frame(parent, bg=CARD2)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=accent, width=4).pack(side="left", fill="y")
        tk.Label(hdr, text=title, fg=TEXT, bg=CARD2,
                 font=("Segoe UI", 11, "bold")).pack(side="left", pady=8, padx=(10,4))
        tk.Label(hdr, text=subtitle, fg=TEXT3, bg=CARD2,
                 font=("Segoe UI", 9)).pack(side="left")
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self, p):
        hdr = ctk.CTkFrame(p, fg_color=CARD, corner_radius=16,
                           border_width=1, border_color=BORDER)
        hdr.pack(fill="x", padx=20, pady=(20,10))

        left = ctk.CTkFrame(hdr, fg_color="transparent")
        left.pack(side="left", padx=20, pady=16)

        # Icon box
        icon_box = ctk.CTkFrame(left, fg_color=ACCENT_D, width=48, height=48, corner_radius=12)
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text="♪", text_color=TEXT,
                     font=("Segoe UI", 22, "bold")).place(relx=0.5, rely=0.5, anchor="center")

        name_f = ctk.CTkFrame(left, fg_color="transparent")
        name_f.pack(side="left", padx=(14,0))
        ctk.CTkLabel(name_f, text=APP_NAME, text_color=TEXT,
                     font=("Segoe UI Black", 22, "bold")).pack(anchor="w")
        ctk.CTkLabel(name_f, text="MP3 Downloader", text_color=TEXT3,
                     font=("Segoe UI", 9)).pack(anchor="w")

        right = ctk.CTkFrame(hdr, fg_color="transparent")
        right.pack(side="right", padx=20, pady=16)

        self._btn(right, "↑ Update", self._check_update,
                  color=CARD3, hover=CARD2, width=100).pack(side="left", padx=(0,8))
        self._btn(right, "⚙", self._open_settings,
                  color=CARD3, hover=CARD2, width=44).pack(side="left", padx=(0,8))
        ctk.CTkLabel(right, text=f"v{VERSION}", text_color=TEXT3,
                     font=("Segoe UI", 9)).pack(side="left")

    # ── YouTube / SoundCloud ──────────────────────────────────────────────────
    def _build_section_yt(self, p):
        card = self._card(p)
        card.pack(fill="x", padx=20, pady=(0,8))
        self._sec_header(card, "YouTube / SoundCloud",
                         "Link einfügen oder Strg+V", ACCENT)
        import tkinter as _tk
        row = _tk.Frame(card, bg=CARD)
        row.pack(fill="x", padx=16, pady=(8,10))
        self._entry(row, var=self.url_var,
                    placeholder="https://youtube.com/...").pack(side="left", fill="x",
                                                                expand=True, padx=(0,10))
        self._btn(row, "Einfügen",
                  lambda: self._paste_to(self.url_var),
                  color=CARD3, hover=CARD2, width=90).pack(side="left")

    # ── Song suchen ───────────────────────────────────────────────────────────
    def _build_section_search(self, p):
        card = self._card(p)
        card.pack(fill="x", padx=20, pady=(0,8))
        self._sec_header(card, "Song suchen",
                         "Name + Künstler direkt laden", ACCENT_H)
        import tkinter as _tk
        body = _tk.Frame(card, bg=CARD)
        body.pack(fill="x", padx=16, pady=(8,10))

        import tkinter as _tk
        r1 = _tk.Frame(body, bg=CARD)
        r1.pack(fill="x", pady=(0,8))
        ctk.CTkLabel(r1, text="Song", text_color=TEXT3,
                     font=("Segoe UI", 9), width=60).pack(side="left")
        self.search_entry = self._entry(r1, placeholder="Songname...")
        self.search_entry.pack(side="left", fill="x", expand=True)

        r2 = _tk.Frame(body, bg=CARD)
        r2.pack(fill="x")
        ctk.CTkLabel(r2, text="Künstler", text_color=TEXT3,
                     font=("Segoe UI", 9), width=60).pack(side="left")
        self.artist_entry = self._entry(r2, placeholder="Künstler / Interpret...")
        self.artist_entry.pack(side="left", fill="x", expand=True, padx=(0,10))
        self._btn(r2, "Suchen & laden", self._search_btn, width=130).pack(side="left")

    # ── Spotify ───────────────────────────────────────────────────────────────
    def _build_section_spotify(self, p):
        card = self._card(p)
        card.pack(fill="x", padx=20, pady=(0,8))
        self._sec_header(card, "Spotify",
                         "Link einfügen → YouTube-Suche", SPOTIFY)
        import tkinter as _tk
        row = _tk.Frame(card, bg=CARD)
        row.pack(fill="x", padx=16, pady=(8,10))
        self.sp_entry = self._entry(row, placeholder="Spotify-Link hier einfügen...",
                                    accent=SPOTIFY)
        self.sp_entry.pack(side="left", fill="x", expand=True, padx=(0,10))
        self._btn(row, "Einfügen",
                  lambda: self._paste_entry(self.sp_entry),
                  color=CARD3, hover=CARD2, width=90).pack(side="left", padx=(0,8))
        self._btn(row, "Laden", self._do_spotify,
                  color=SPOTIFY, hover="#17a349",
                  text_color="#000000", width=80).pack(side="left")

    # ── TikTok / Instagram ────────────────────────────────────────────────────
    def _build_section_tiktok(self, p):
        card = self._card(p)
        card.pack(fill="x", padx=20, pady=(0,8))
        self._sec_header(card, "TikTok / Instagram",
                         "Sound als MP3 herunterladen", TIKTOK)
        import tkinter as _tk
        row = _tk.Frame(card, bg=CARD)
        row.pack(fill="x", padx=16, pady=(8,10))
        self.ti_entry = self._entry(row, placeholder="TikTok / Instagram Link...",
                                    accent=TIKTOK)
        self.ti_entry.pack(side="left", fill="x", expand=True, padx=(0,10))
        self._btn(row, "Einfügen",
                  lambda: self._paste_entry(self.ti_entry),
                  color=CARD3, hover=CARD2, width=90).pack(side="left", padx=(0,8))
        self._btn(row, "Laden", self._ti_dl,
                  color=TIKTOK, hover="#3fb8bf",
                  text_color="#000000", width=80).pack(side="left")

    # ── Download Button ───────────────────────────────────────────────────────
    def _build_download_btn(self, p):
        def _dl_click():
            self.dl_btn.configure(fg_color=ACCENT_D)
            self.after(100, lambda: self.dl_btn.configure(fg_color=ACCENT))
            self._start_dl()
        self.dl_btn = ctk.CTkButton(
            p, text="  ↓   MP3 herunterladen",
            command=_dl_click,
            fg_color=ACCENT, hover_color=ACCENT_H,
            text_color=TEXT,
            font=("Segoe UI Black", 15),
            corner_radius=12,
            height=56,
        )
        self.dl_btn.pack(fill="x", padx=20, pady=(6,6))

        self.prog = ctk.CTkProgressBar(p, mode="indeterminate",
                                        fg_color=CARD2, progress_color=ACCENT,
                                        corner_radius=4, height=5)
        self.prog.pack(fill="x", padx=20, pady=(0,4))
        self.prog.set(0)

        # OK Banner
        self.ok_frame = ctk.CTkFrame(p, fg_color=GREEN_BG, corner_radius=10,
                                      border_width=1, border_color=GREEN)
        ok_inner = ctk.CTkFrame(self.ok_frame, fg_color="transparent")
        ok_inner.pack(fill="x", padx=20, pady=14)
        ctk.CTkLabel(ok_inner, text="✓", text_color=GREEN_L,
                     font=("Segoe UI Black", 22)).pack(side="left")
        txt_f = ctk.CTkFrame(ok_inner, fg_color="transparent")
        txt_f.pack(side="left", padx=(14,0))
        ctk.CTkLabel(txt_f, text="Download abgeschlossen!",
                     text_color=GREEN_L,
                     font=("Segoe UI Black", 12)).pack(anchor="w")
        self.ok_path = ctk.CTkLabel(txt_f, text="", text_color=GREEN,
                                     font=("Segoe UI", 9))
        self.ok_path.pack(anchor="w")

    # ── Log ───────────────────────────────────────────────────────────────────
    def _build_log(self, p):
        card = self._card(p)
        card.pack(fill="x", padx=20, pady=(4,24))

        lh = ctk.CTkFrame(card, fg_color="transparent")
        lh.pack(fill="x", padx=14, pady=(10,4))
        ctk.CTkLabel(lh, text="● LOG", text_color=TEXT3,
                     font=("Segoe UI", 9, "bold")).pack(side="left")
        self._btn(lh, "leeren", self._clear_log,
                  color=CARD2, hover=CARD3,
                  text_color=TEXT3, height=26, font_size=8, width=60).pack(side="right")

        self.log_box = ctk.CTkTextbox(card, height=130, fg_color=CARD,
                                       text_color=TEXT2,
                                       font=("Consolas", 9),
                                       corner_radius=0,
                                       border_width=0,
                                       activate_scrollbars=True,
                                       wrap="word")
        self.log_box.pack(fill="x", padx=14, pady=(0,12))
        self.log_box.configure(state="disabled")

    # ── Settings Window ───────────────────────────────────────────────────────
    def _open_settings(self):
        if hasattr(self, '_spanel_visible') and self._spanel_visible: return
        self._spanel_visible = True
        # Destroy old panel if exists, rebuild fresh
        if hasattr(self, '_spanel') and self._spanel.winfo_exists():
            for w in self._spanel.winfo_children(): w.destroy()
        self._build_settings_content(self._spanel)
        self._spanel.place(relx=0.5, rely=0.5, anchor="center", width=1, height=1)
        self._spanel.lift()
        self._anim_settings_open(0)

    def _build_settings_content(self, p):
        import tkinter as tk
        # clear
        for w in p.winfo_children(): w.destroy()

        # Header bar
        hdr = tk.Frame(p, bg=CARD, height=50)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="⚙  Einstellungen", fg=TEXT, bg=CARD,
                 font=("Segoe UI", 12, "bold")).place(x=20, rely=0.5, anchor="w")
        cb = tk.Button(hdr, text="✕", command=self._close_settings,
                       bg=CARD, fg=TEXT2, activebackground=RED, activeforeground=TEXT,
                       font=("Segoe UI", 12, "bold"), relief="flat", bd=0, cursor="hand2",
                       width=3)
        cb.place(relx=1.0, x=-12, rely=0.5, anchor="e")
        tk.Frame(p, bg=ACCENT, height=1).pack(fill="x")

        body = tk.Frame(p, bg=CARD2)
        body.pack(fill="both", expand=True, padx=24, pady=18)

        # Ordner
        tk.Label(body, text="Speicherordner", fg=TEXT, bg=CARD2,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        fr = tk.Frame(body, bg=CARD2)
        fr.pack(fill="x", pady=(6,18))
        tk.Label(fr, textvariable=self.output_dir, fg=TEXT2, bg=CARD3,
                 font=("Segoe UI", 9), anchor="w", padx=10, pady=9
                 ).pack(side="left", fill="x", expand=True)
        self._btn(fr, "Auswählen", self._browse, width=110
                  ).pack(side="left", padx=(10,0))

        # Qualität
        tk.Label(body, text="Audioqualität", fg=TEXT, bg=CARD2,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        qr = tk.Frame(body, bg=CARD2)
        qr.pack(fill="x", pady=(6,18))
        self.q_seg = ctk.CTkSegmentedButton(
            qr, values=["320 kbps", "192 kbps", "128 kbps"],
            fg_color=CARD3, selected_color=ACCENT,
            selected_hover_color=ACCENT_H, unselected_color=CARD3,
            unselected_hover_color=CARD2, text_color=TEXT,
            font=("Segoe UI", 10), corner_radius=8,
            command=self._q_changed)
        self.q_seg.pack(fill="x")
        self.q_seg.set("320 kbps")

        # Nach Download
        tk.Label(body, text="Nach Download", fg=TEXT, bg=CARD2,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ctk.CTkCheckBox(body,
                        text="  Dateimanager öffnen mit Datei markiert",
                        variable=self.open_folder,
                        fg_color=ACCENT, hover_color=ACCENT_H,
                        text_color=TEXT2, font=("Segoe UI", 10), corner_radius=4,
                        ).pack(anchor="w", pady=(8,0))

    def _anim_settings_open(self, f):
        W, H = 480, 400
        total = 28
        if f > total:
            self._spanel.place(relx=0.5, rely=0.5, anchor="center", width=W, height=H)
            return
        t = f / total
        c1 = 1.70158; c3 = c1 + 1
        e = 1 + c3*((t-1)**3) + c1*((t-1)**2)
        self._spanel.place(relx=0.5, rely=0.5, anchor="center",
                           width=max(2,int(W*e)), height=max(2,int(H*e)))
        self.after(14, lambda: self._anim_settings_open(f+1))

    def _close_settings(self):
        self._anim_settings_close(0)

    def _anim_settings_close(self, f):
        W, H = 480, 400
        total = 16
        if f > total:
            self._spanel.place_forget()
            self._spanel_visible = False
            return
        t = f / total
        e = max(0.0, 1.0 - t**3)
        self._spanel.place(relx=0.5, rely=0.5, anchor="center",
                           width=max(2,int(W*e)), height=max(2,int(H*e)))
        self.after(14, lambda: self._anim_settings_close(f+1))

    def _q_changed(self, val):
        mapping = {"320 kbps": "0", "192 kbps": "5", "128 kbps": "9"}
        self.quality_var.set(mapping.get(val, "0"))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _paste_to(self, var):
        try: var.set(self.clipboard_get().strip())
        except: pass

    def _paste_entry(self, entry):
        try:
            entry.delete(0, "end")
            entry.insert(0, self.clipboard_get().strip())
        except: pass

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.output_dir.get())
        if d: self.output_dir.set(d)

    def _log(self, msg, color=None):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _show_ok(self, folder):
        self.ok_path.configure(text=folder)
        self.ok_frame.pack(fill="x", padx=20, pady=(4,0),
                           before=self.prog)
        self.after(6000, self._hide_ok)

    def _hide_ok(self):
        try: self.ok_frame.pack_forget()
        except: pass

    def _busy(self, on):
        if on:
            self.dl_btn.configure(state="disabled",
                                   text="  ⏳  Lädt...",
                                   fg_color=CARD3)
            self.prog.pack(fill="x", padx=20, pady=(0,4))
            self.prog.start()
        else:
            self.dl_btn.configure(state="normal",
                                   text="  ↓   MP3 herunterladen",
                                   fg_color=ACCENT)
            self.prog.stop()
            self.prog.set(0)

    def _open_explorer(self, fp):
        if self.open_folder.get() and fp and os.path.exists(fp):
            subprocess.Popen(["explorer", "/select,", os.path.normpath(fp)],
                             creationflags=CREATE_NO_WINDOW)

    # ── Logic ─────────────────────────────────────────────────────────────────
    def _yt_search(self, q):
        req = urllib.request.Request(
            "https://www.youtube.com/results?search_query=" + urllib.parse.quote(q),
            headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="ignore")
        m = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
        return f"https://www.youtube.com/watch?v={m.group(1)}" if m else None

    def _search_btn(self):
        s = self.search_entry.get().strip()
        if not s:
            messagebox.showwarning("Kein Name", "Bitte Songname eingeben!"); return
        a = self.artist_entry.get().strip()
        threading.Thread(target=self._search_thread,
                         args=(f"{a} {s}".strip(),), daemon=True).start()

    def _search_thread(self, q):
        self._busy(True)
        try:
            self._log(f"Suche: {q}")
            url = self._yt_search(q + " official audio")
            if not url:
                self._log("Nichts gefunden."); return
            self._log(f"Gefunden: {url}")
            self.url_var.set(url)
            self.search_entry.delete(0, "end")
            self.artist_entry.delete(0, "end")
            self.after(0, self._start_dl)
        except Exception as e:
            self._log(f"Fehler: {e}")
        finally:
            self._busy(False)

    def _do_spotify(self):
        url = self.sp_entry.get().strip()
        if not url or "spotify.com" not in url:
            messagebox.showwarning("Kein Link", "Bitte Spotify-Link einfügen!"); return
        threading.Thread(target=self._spotify_thread, args=(url,), daemon=True).start()

    def _spotify_thread(self, surl):
        self._busy(True)
        try:
            self._log("Lese Spotify...")
            req = urllib.request.Request(surl, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                html = r.read().decode("utf-8", errors="ignore")
            m = re.search(r"<title>(.*?)</title>", html)
            if not m:
                self._log("Titel nicht lesbar."); return
            name = re.sub(r"\s*[|\-–]\s*Spotify.*$", "", m.group(1)).strip()
            self._log(f"Song: {name}")
            url = self._yt_search(name + " official audio")
            if not url:
                self._log("Kein YouTube-Treffer."); return
            self._log(f"Gefunden: {url}")
            self.url_var.set(url)
            self.sp_entry.delete(0, "end")
            self.after(0, self._start_dl)
        except Exception as e:
            self._log(f"Fehler: {e}")
        finally:
            self._busy(False)

    def _check_tools(self):
        missing = [n for n, p in [("yt-dlp", YTDLP_PATH), ("ffmpeg", FFMPEG_PATH)]
                   if not os.path.exists(p)]
        if missing:
            self._log(f"Installiere: {', '.join(missing)}...")
            threading.Thread(target=self._install_tools, daemon=True).start()
        else:
            self._log("[Bereit]  Strg+V = sofort herunterladen")

    def _install_tools(self):
        self._busy(True)
        os.makedirs(TOOLS_DIR, exist_ok=True)
        try:
            if not os.path.exists(YTDLP_PATH):
                self._log("yt-dlp wird heruntergeladen...")
                urllib.request.urlretrieve(YTDLP_URL, YTDLP_PATH)
                self._log("yt-dlp OK")
            if not os.path.exists(FFMPEG_PATH):
                self._log("ffmpeg wird heruntergeladen (~80 MB)...")
                zp = os.path.join(TOOLS_DIR, "ffmpeg.zip")
                urllib.request.urlretrieve(FFMPEG_URL, zp)
                self._log("Entpacke ffmpeg...")
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
                self._log("ffmpeg OK")
            self._log("Alles bereit!")
        except Exception as e:
            self._log(f"Fehler: {e}")
        finally:
            self._busy(False)

    def _check_update(self):
        self._log("Suche Updates...")
        threading.Thread(target=self._update_thread, daemon=True).start()

    def _update_thread(self):
        self._busy(True)
        try:
            req = urllib.request.Request(GITHUB_RAW, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                content = r.read().decode("utf-8")
            m = re.search(r'^VERSION\s*=\s*"([^"]+)"', content, re.MULTILINE)
            nv = m.group(1) if m else VERSION
            if nv == VERSION:
                self._log(f"Aktuell (v{VERSION})")
                self._busy(False); return
            self._log(f"Neue Version v{nv} gefunden!")
            if IS_EXE:
                self._log("Lade neue EXE...")
                exe = sys.executable; tmp = exe + ".new"
                urllib.request.urlretrieve(GITHUB_EXE, tmp)
                bat = os.path.join(BASE_DIR, "_upd.bat")
                with open(bat, "w") as f:
                    f.write(f'@echo off\ntimeout /t 2 /nobreak >nul\n'
                            f'move /y "{tmp}" "{exe}"\nstart "" "{exe}"\ndel "%~f0"\n')
                subprocess.Popen(["cmd", "/c", bat], creationflags=CREATE_NO_WINDOW)
                self.after(500, self.destroy)
            else:
                py = os.path.join(BASE_DIR, "mp3downloader.py")
                with open(py, "w", encoding="utf-8") as f: f.write(content)
                self._log(f"v{nv} installiert! Starte neu...")
                self.after(800, lambda: (
                    subprocess.Popen([sys.executable, py], creationflags=CREATE_NO_WINDOW),
                    self.destroy()))
        except Exception as e:
            self._log(f"Update-Fehler: {e}")
        finally:
            self._busy(False)

    def _start_dl(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Kein Link", "Bitte Link einfügen!"); return
        if not os.path.exists(YTDLP_PATH):
            messagebox.showerror("Tools fehlen", "Kurz warten – Tools werden installiert.")
            return
        threading.Thread(target=self._dl_thread, args=(url,), daemon=True).start()

    def _dl_thread(self, url):
        self._busy(True); self._hide_ok(); self.last_file = None
        self._log("Download startet...")
        out = os.path.join(self.output_dir.get(), "%(title)s.%(ext)s")
        cmd = [YTDLP_PATH, "-x", "--audio-format", "mp3",
               "--audio-quality", self.quality_var.get(),
               "--ffmpeg-location", TOOLS_DIR,
               "-o", out, "--no-playlist",
               "--print", "after_move:filepath", url]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True,
                                    encoding="utf-8", errors="replace",
                                    creationflags=CREATE_NO_WINDOW)
            for line in proc.stdout:
                line = line.rstrip()
                if not line: continue
                if os.path.sep in line and line.endswith(".mp3"):
                    self.last_file = line.strip()
                else:
                    self._log(line)
            proc.wait()
            if proc.returncode == 0:
                self._log(f"Fertig!  →  {self.output_dir.get()}")
                self.url_var.set("")
                f, l = self.output_dir.get(), self.last_file
                self.after(0,   lambda: self._show_ok(f))
                self.after(500, lambda: self._open_explorer(l))
            else:
                self._log("Fehlgeschlagen. Link prüfen.")
        except Exception as e:
            self._log(f"Fehler: {e}")
        finally:
            self._busy(False)

    def _ti_dl(self):
        url = self.ti_entry.get().strip()
        if not url:
            messagebox.showwarning("Kein Link", "Bitte TikTok- oder Instagram-Link einfügen!")
            return
        if not os.path.exists(YTDLP_PATH):
            messagebox.showerror("Tools fehlen", "Kurz warten – Tools werden installiert.")
            return
        threading.Thread(target=self._ti_thread, args=(url,), daemon=True).start()

    def _ti_thread(self, url):
        self._busy(True); self._hide_ok(); self.last_file = None
        url = url.split("?")[0].strip()
        platform = "TikTok" if "tiktok.com" in url else "Instagram"
        self._log(f"{platform} Sound wird geladen...")
        out = os.path.join(self.output_dir.get(), "%(title).80s.%(ext)s")
        cmd = [YTDLP_PATH,
               "-x", "--audio-format", "mp3",
               "--audio-quality", self.quality_var.get(),
               "--ffmpeg-location", TOOLS_DIR,
               "--no-playlist", "--no-check-certificate",
               "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
               "-o", out,
               "--print", "after_move:filepath",
               url]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True,
                                    encoding="utf-8", errors="replace",
                                    creationflags=CREATE_NO_WINDOW)
            for line in proc.stdout:
                line = line.rstrip()
                if not line: continue
                if os.path.sep in line and line.endswith(".mp3"):
                    self.last_file = line.strip()
                else:
                    self._log(line)
            proc.wait()
            if proc.returncode == 0:
                self._log(f"Fertig!  →  {self.output_dir.get()}")
                self.ti_entry.delete(0, "end")
                f, l = self.output_dir.get(), self.last_file
                self.after(0,   lambda: self._show_ok(f))
                self.after(500, lambda: self._open_explorer(l))
            else:
                self._log("Fehlgeschlagen – versuche mit Browser-Cookies...")
                cmd2 = cmd + ["--cookies-from-browser", "chrome"]
                try:
                    proc2 = subprocess.Popen(cmd2, stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT, text=True,
                                             encoding="utf-8", errors="replace",
                                             creationflags=CREATE_NO_WINDOW)
                    for line in proc2.stdout:
                        line = line.rstrip()
                        if not line: continue
                        if os.path.sep in line and line.endswith(".mp3"):
                            self.last_file = line.strip()
                        else:
                            self._log(line)
                    proc2.wait()
                    if proc2.returncode == 0:
                        self._log(f"Fertig!  →  {self.output_dir.get()}")
                        self.ti_entry.delete(0, "end")
                        f, l = self.output_dir.get(), self.last_file
                        self.after(0,   lambda: self._show_ok(f))
                        self.after(500, lambda: self._open_explorer(l))
                    else:
                        self._log("Fehlgeschlagen. TikTok blockiert evtl. den Download.")
                except Exception as e2:
                    self._log(f"Fehler: {e2}")
        except Exception as e:
            self._log(f"Fehler: {e}")
        finally:
            self._busy(False)


if __name__ == "__main__":
    app = App()
    app.mainloop()
