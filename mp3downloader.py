import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading, subprocess, os, sys, re, shutil, zipfile, hashlib, json
import urllib.request, urllib.parse

VERSION    = "6.0"
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
USERS_FILE  = os.path.join(BASE_DIR, "users.json")
ADMIN_CODE  = "WL-ADMIN-2024"   # ← dein geheimer Admin-Bypass

CREATE_NO_WINDOW = 0x08000000

BG      = "#0a0a14"
CARD    = "#111122"
CARD2   = "#181832"
CARD3   = "#1e1e3a"
BORDER  = "#2a2a50"
ACCENT  = "#8b5cf6"
ACCENT_H= "#a78bfa"
ACCENT_D= "#6d28d9"
GREEN   = "#10b981"
GREEN_L = "#34d399"
GREEN_BG= "#071a10"
SPOTIFY = "#1db954"
TIKTOK  = "#5bcdd4"
INSTA   = "#d63070"
TEXT    = "#f0efff"
TEXT2   = "#9090b8"
TEXT3   = "#50507a"
RED     = "#f87171"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def _h(s): return hashlib.sha256(s.encode()).hexdigest()

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE) as f: return json.load(f)
        except: pass
    return {}

def save_users(u):
    with open(USERS_FILE, "w") as f: json.dump(u, f)

def get_icon_path():
    p = os.path.join(BASE_DIR, "icon.ico")
    return p if os.path.exists(p) else None


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN WINDOW
# ══════════════════════════════════════════════════════════════════════════════
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color=BG)
        self.title("WaveLoad")
        self.geometry("440x560")
        self.resizable(False, False)
        self.logged_in = False
        self._page = "login"
        self._build()
        ico = get_icon_path()
        if ico:
            try: self.iconbitmap(ico)
            except: pass

    def _build(self):
        # Logo oben
        top = tk.Frame(self, bg=BG); top.pack(pady=(32,0))
        box = tk.Frame(top, bg=ACCENT_D, width=50, height=50)
        box.pack_propagate(False); box.pack()
        tk.Label(box, text="♪", font=("Segoe UI",22,"bold"),
                 bg=ACCENT_D, fg=TEXT).place(relx=.5,rely=.5,anchor="center")
        tk.Label(self, text="WaveLoad", font=("Segoe UI Black",20,"bold"),
                 bg=BG, fg=TEXT).pack(pady=(10,0))

        # Tab-Leiste
        tabs = tk.Frame(self, bg=CARD2, highlightthickness=1,
                        highlightbackground=BORDER)
        tabs.pack(fill="x", padx=40, pady=(16,0))
        self._tab_login = tk.Label(tabs, text="  Anmelden  ",
                                   font=("Segoe UI",10,"bold"), cursor="hand2",
                                   bg=ACCENT, fg=TEXT, pady=10)
        self._tab_login.pack(side="left", fill="x", expand=True)
        self._tab_reg = tk.Label(tabs, text="  Registrieren  ",
                                 font=("Segoe UI",10,"bold"), cursor="hand2",
                                 bg=CARD2, fg=TEXT3, pady=10)
        self._tab_reg.pack(side="left", fill="x", expand=True)
        self._tab_login.bind("<Button-1>", lambda e: self._show("login"))
        self._tab_reg.bind("<Button-1>",   lambda e: self._show("register"))

        # Card
        self._card_frame = tk.Frame(self, bg=CARD, highlightthickness=1,
                                    highlightbackground=BORDER)
        self._card_frame.pack(fill="x", padx=40, pady=(0,0))

        # Panels
        self._login_panel  = tk.Frame(self._card_frame, bg=CARD)
        self._reg_panel    = tk.Frame(self._card_frame, bg=CARD)

        self._build_login(self._login_panel)
        self._build_reg(self._reg_panel)

        # Admin
        adm = tk.Frame(self, bg=BG); adm.pack(pady=(14,0), padx=40, fill="x")
        tk.Frame(adm, bg=BORDER, height=1).pack(fill="x", pady=(0,10))
        adm_row = tk.Frame(adm, bg=BG); adm_row.pack(fill="x")
        tk.Label(adm_row, text="Admin:", font=("Segoe UI",9),
                 bg=BG, fg=TEXT3).pack(side="left", padx=(0,8))
        self._adm_e = ctk.CTkEntry(adm_row, placeholder_text="Admin-Code",
                                   fg_color=CARD3, border_color=BORDER,
                                   text_color=TEXT, placeholder_text_color=TEXT3,
                                   font=("Segoe UI",9), height=34, corner_radius=8,
                                   show="●")
        self._adm_e.pack(side="left", fill="x", expand=True, padx=(0,8))
        ctk.CTkButton(adm_row, text="→", command=self._admin_login,
                      fg_color=CARD3, hover_color=ACCENT_D,
                      text_color=TEXT2, height=34, width=40,
                      font=("Segoe UI",11,"bold"), corner_radius=8
                      ).pack(side="left")
        self._adm_e.bind("<Return>", lambda e: self._admin_login())

        self._show("login")

    def _build_login(self, p):
        inner = tk.Frame(p, bg=CARD); inner.pack(fill="x", padx=24, pady=20)
        self._err = tk.Label(inner, text="", font=("Segoe UI",9),
                             bg=CARD, fg=RED, anchor="w", wraplength=340)
        tk.Label(inner, text="Benutzername", font=("Segoe UI",9,"bold"),
                 bg=CARD, fg=TEXT2, anchor="w").pack(fill="x")
        self._user_e = ctk.CTkEntry(inner, placeholder_text="Dein Benutzername",
                                    fg_color=CARD3, border_color=BORDER,
                                    text_color=TEXT, placeholder_text_color=TEXT3,
                                    font=("Segoe UI",10), height=40, corner_radius=8)
        self._user_e.pack(fill="x", pady=(4,12))
        tk.Label(inner, text="Passwort", font=("Segoe UI",9,"bold"),
                 bg=CARD, fg=TEXT2, anchor="w").pack(fill="x")
        self._pass_e = ctk.CTkEntry(inner, placeholder_text="Dein Passwort",
                                    fg_color=CARD3, border_color=BORDER,
                                    text_color=TEXT, placeholder_text_color=TEXT3,
                                    font=("Segoe UI",10), height=40, corner_radius=8, show="●")
        self._pass_e.pack(fill="x", pady=(4,8))
        self._err.pack(fill="x", pady=(0,8))
        ctk.CTkButton(inner, text="Anmelden", command=self._login,
                      fg_color=ACCENT, hover_color=ACCENT_H, text_color=TEXT,
                      font=("Segoe UI",11,"bold"), height=44, corner_radius=8
                      ).pack(fill="x")
        self._pass_e.bind("<Return>", lambda e: self._login())

    def _build_reg(self, p):
        inner = tk.Frame(p, bg=CARD); inner.pack(fill="x", padx=24, pady=20)
        self._reg_err = tk.Label(inner, text="", font=("Segoe UI",9),
                                 bg=CARD, fg=RED, anchor="w", wraplength=340)
        tk.Label(inner, text="Benutzername", font=("Segoe UI",9,"bold"),
                 bg=CARD, fg=TEXT2, anchor="w").pack(fill="x")
        self._reg_user = ctk.CTkEntry(inner, placeholder_text="Gewünschter Benutzername",
                                      fg_color=CARD3, border_color=BORDER,
                                      text_color=TEXT, placeholder_text_color=TEXT3,
                                      font=("Segoe UI",10), height=40, corner_radius=8)
        self._reg_user.pack(fill="x", pady=(4,12))
        tk.Label(inner, text="Passwort", font=("Segoe UI",9,"bold"),
                 bg=CARD, fg=TEXT2, anchor="w").pack(fill="x")
        self._reg_pass = ctk.CTkEntry(inner, placeholder_text="Mind. 6 Zeichen",
                                      fg_color=CARD3, border_color=BORDER,
                                      text_color=TEXT, placeholder_text_color=TEXT3,
                                      font=("Segoe UI",10), height=40, corner_radius=8, show="●")
        self._reg_pass.pack(fill="x", pady=(4,12))
        tk.Label(inner, text="Passwort bestätigen", font=("Segoe UI",9,"bold"),
                 bg=CARD, fg=TEXT2, anchor="w").pack(fill="x")
        self._reg_pass2 = ctk.CTkEntry(inner, placeholder_text="Passwort wiederholen",
                                       fg_color=CARD3, border_color=BORDER,
                                       text_color=TEXT, placeholder_text_color=TEXT3,
                                       font=("Segoe UI",10), height=40, corner_radius=8, show="●")
        self._reg_pass2.pack(fill="x", pady=(4,8))
        self._reg_err.pack(fill="x", pady=(0,8))
        ctk.CTkButton(inner, text="Konto erstellen →", command=self._do_register,
                      fg_color=GREEN, hover_color=GREEN_L, text_color="#000",
                      font=("Segoe UI",11,"bold"), height=44, corner_radius=8
                      ).pack(fill="x")
        self._reg_pass2.bind("<Return>", lambda ev: self._do_register())

    def _show(self, page):
        self._page = page
        if page == "login":
            self._reg_panel.pack_forget()
            self._login_panel.pack(fill="x")
            self._tab_login.configure(bg=ACCENT, fg=TEXT)
            self._tab_reg.configure(bg=CARD2, fg=TEXT3)
        else:
            self._login_panel.pack_forget()
            self._reg_panel.pack(fill="x")
            self._tab_login.configure(bg=CARD2, fg=TEXT3)
            self._tab_reg.configure(bg=ACCENT, fg=TEXT)

    def _login(self):
        u = self._user_e.get().strip()
        p = self._pass_e.get()
        if not u or not p:
            self._err.configure(text="Bitte alle Felder ausfüllen."); return
        users = load_users()
        if u not in users or users[u] != _h(p):
            self._err.configure(text="Benutzername oder Passwort falsch."); return
        self.logged_in = True; self.destroy()

    def _do_register(self):
        u = self._reg_user.get().strip()
        p = self._reg_pass.get()
        p2 = self._reg_pass2.get()
        if not u or not p:
            self._reg_err.configure(text="Bitte alle Felder ausfüllen."); return
        if len(p) < 6:
            self._reg_err.configure(text="Passwort mind. 6 Zeichen."); return
        if p != p2:
            self._reg_err.configure(text="Passwörter stimmen nicht überein."); return
        users = load_users()
        if u in users:
            self._reg_err.configure(text="Benutzername bereits vergeben."); return
        users[u] = _h(p); save_users(users)
        self._reg_err.configure(text="")
        # Auto-fill login
        self._user_e.delete(0,"end"); self._user_e.insert(0, u)
        self._pass_e.delete(0,"end"); self._pass_e.insert(0, p)
        self._err.configure(text="✓ Konto erstellt – angemeldet!")
        self.logged_in = True
        self.after(800, self.destroy)

    def _admin_login(self):
        if self._adm_e.get().strip() == ADMIN_CODE:
            self.logged_in = True; self.destroy()
        else:
            self._err.configure(text="Ungültiger Admin-Code.")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════════════════════════════
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
        self._spanel_visible = False
        self._spanel_animating = False
        self._sy = 0.0
        self._sa = False

        self._build_ui()
        self.after(100, self._set_icon)
        self.after(400, self._check_tools)
        self.bind("<Control-v>", self._ctrl_v)
        self.bind("<Control-V>", self._ctrl_v)

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
                self._log("Spotify erkannt – suche...")
                self.after(300, self._do_spotify)
            elif "tiktok.com" in c or "instagram.com" in c or "instagr.am" in c:
                self.ti_entry.delete(0, "end"); self.ti_entry.insert(0, c)
                self._log("TikTok/Instagram erkannt – bereit!")
            elif c.startswith("http"):
                self.url_var.set(c)
                self._log("Link erkannt – lade...")
                self.after(300, self._start_dl)
        except: pass

    # ── Smooth scroll ─────────────────────────────────────────────────────────
    def _smooth_scroll(self):
        self._sa = True
        cur  = self._cvs.yview()[0]
        diff = self._sy - cur
        if abs(diff) < 0.0003:
            self._cvs.yview_moveto(self._sy); self._sa = False; return
        self._cvs.yview_moveto(cur + diff * 0.16)
        self.after(11, self._smooth_scroll)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        wrap = tk.Frame(self, bg=BG); wrap.pack(fill="both", expand=True)

        self._cvs = tk.Canvas(wrap, bg=BG, highlightthickness=0)
        self._cvs.pack(side="left", fill="both", expand=True)

        self._sbc = tk.Canvas(wrap, bg=BG, width=8, highlightthickness=0)
        self._sbc.pack(side="right", fill="y", padx=(0,2))
        self._sth = self._sbc.create_rectangle(1,2,7,40, fill=ACCENT, outline="")

        def _yscroll(first, last):
            try:
                f,l = float(first),float(last)
                h = self._sbc.winfo_height()
                if h < 4: return
                y0 = max(2,int(f*h)); y1 = min(h-2,int(l*h))
                if y1-y0 < 20: y1 = y0+20
                self._sbc.coords(self._sth,1,y0,7,y1)
                self._sbc.configure(width=0 if (f<=0.0 and l>=1.0) else 9)
            except: pass

        self._cvs.configure(yscrollcommand=_yscroll)
        self._scroll = tk.Frame(self._cvs, bg=BG)
        self._win = self._cvs.create_window((0,0), window=self._scroll, anchor="nw")
        self._cvs.bind("<Configure>", lambda e: self._cvs.itemconfig(self._win, width=e.width))
        self._scroll.bind("<Configure>", lambda e: self._cvs.configure(scrollregion=self._cvs.bbox("all")))

        def _wheel(e):
            total = self._scroll.winfo_reqheight()
            vh    = self._cvs.winfo_height()
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

        # Settings overlay – hidden, full size, clipped by parent
        self._spanel = tk.Frame(self, bg=CARD2,
                                highlightthickness=2, highlightbackground=ACCENT)
        # Don't place it yet

    # ── Reusable widgets ──────────────────────────────────────────────────────
    def _card(self, parent):
        return ctk.CTkFrame(parent, fg_color=CARD, corner_radius=10,
                            border_width=1, border_color=BORDER)

    def _btn(self, parent, text, cmd, color=ACCENT, hover=ACCENT_H,
             text_color=TEXT, width=None, height=38, font_size=10):
        def _click(b, c=color, fn=cmd):
            b.configure(fg_color=hover)
            b.after(90, lambda: b.configure(fg_color=c))
            fn()
        kw = dict(fg_color=color, hover_color=hover, text_color=text_color,
                  font=("Segoe UI", font_size, "bold"),
                  corner_radius=8, height=height, text=text)
        if width: kw["width"] = width
        b = ctk.CTkButton(parent, **kw)
        b.configure(command=lambda b=b: _click(b))
        return b

    def _entry(self, parent, var=None, placeholder="", accent=ACCENT):
        return ctk.CTkEntry(parent, textvariable=var,
                            placeholder_text=placeholder,
                            fg_color=CARD3, border_color=BORDER, border_width=1,
                            text_color=TEXT, placeholder_text_color=TEXT3,
                            font=("Segoe UI", 10), corner_radius=8, height=40)

    def _sec_header(self, parent, title, subtitle, accent=ACCENT):
        hdr = tk.Frame(parent, bg=CARD2)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=accent, width=4).pack(side="left", fill="y")
        tk.Label(hdr, text=title, fg=TEXT, bg=CARD2,
                 font=("Segoe UI",11,"bold")).pack(side="left", pady=10, padx=(10,4))
        tk.Label(hdr, text=subtitle, fg=TEXT3, bg=CARD2,
                 font=("Segoe UI",9)).pack(side="left")
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x")

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self, p):
        hdr = ctk.CTkFrame(p, fg_color=CARD, corner_radius=0,
                           border_width=0)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=ACCENT, height=2).pack(side="bottom", fill="x")

        inner = tk.Frame(hdr, bg=CARD); inner.pack(fill="x", padx=20, pady=14)

        lft = tk.Frame(inner, bg=CARD); lft.pack(side="left")
        box = tk.Frame(lft, bg=ACCENT_D, width=44, height=44)
        box.pack_propagate(False); box.pack(side="left")
        tk.Label(box, text="♪", font=("Segoe UI",20,"bold"),
                 bg=ACCENT_D, fg=TEXT).place(relx=.5,rely=.5,anchor="center")
        nf = tk.Frame(lft, bg=CARD); nf.pack(side="left", padx=(12,0))
        tk.Label(nf, text=APP_NAME, font=("Segoe UI Black",20,"bold"),
                 bg=CARD, fg=TEXT).pack(anchor="w")
        tk.Label(nf, text="MP3 Downloader", font=("Segoe UI",8),
                 bg=CARD, fg=TEXT3).pack(anchor="w")

        rgt = tk.Frame(inner, bg=CARD); rgt.pack(side="right")
        self._btn(rgt, "↑ Update", self._check_update,
                  color=CARD3, hover=CARD2, width=100).pack(side="left", padx=(0,8))
        self._btn(rgt, "⚙", self._open_settings,
                  color=CARD3, hover=CARD2, width=44).pack(side="left")
        tk.Label(rgt, text=f"v{VERSION}", font=("Segoe UI",8),
                 bg=CARD, fg=TEXT3).pack(side="left", padx=(8,0))

    # ── Sections ──────────────────────────────────────────────────────────────
    def _build_section_yt(self, p):
        card = self._card(p); card.pack(fill="x", padx=20, pady=(10,8))
        self._sec_header(card, "YouTube / SoundCloud", "Link einfügen oder Strg+V", ACCENT)
        row = tk.Frame(card, bg=CARD); row.pack(fill="x", padx=16, pady=(8,10))
        self._entry(row, var=self.url_var, placeholder="https://youtube.com/..."
                    ).pack(side="left", fill="x", expand=True, padx=(0,10))
        self._btn(row, "Einfügen", lambda: self._paste_to(self.url_var),
                  color=CARD3, hover=CARD2, width=90).pack(side="left")

    def _build_section_search(self, p):
        card = self._card(p); card.pack(fill="x", padx=20, pady=(0,8))
        self._sec_header(card, "Song suchen", "Name + Künstler direkt laden", ACCENT_H)
        body = tk.Frame(card, bg=CARD); body.pack(fill="x", padx=16, pady=(8,10))
        r1 = tk.Frame(body, bg=CARD); r1.pack(fill="x", pady=(0,6))
        tk.Label(r1, text="Song    ", fg=TEXT3, bg=CARD, font=("Segoe UI",9)
                 ).pack(side="left")
        self.search_entry = self._entry(r1, placeholder="Songname...")
        self.search_entry.pack(side="left", fill="x", expand=True)
        r2 = tk.Frame(body, bg=CARD); r2.pack(fill="x")
        tk.Label(r2, text="Künstler", fg=TEXT3, bg=CARD, font=("Segoe UI",9)
                 ).pack(side="left")
        self.artist_entry = self._entry(r2, placeholder="Künstler / Interpret...")
        self.artist_entry.pack(side="left", fill="x", expand=True, padx=(0,10))
        self._btn(r2, "Suchen & laden", self._search_btn, width=130).pack(side="left")

    def _build_section_spotify(self, p):
        card = self._card(p); card.pack(fill="x", padx=20, pady=(0,8))
        self._sec_header(card, "Spotify", "Link einfügen → YouTube-Suche", SPOTIFY)
        row = tk.Frame(card, bg=CARD); row.pack(fill="x", padx=16, pady=(8,10))
        self.sp_entry = self._entry(row, placeholder="Spotify-Link hier einfügen...")
        self.sp_entry.pack(side="left", fill="x", expand=True, padx=(0,10))
        self._btn(row, "Einfügen", lambda: self._paste_entry(self.sp_entry),
                  color=CARD3, hover=CARD2, width=90).pack(side="left", padx=(0,8))
        self._btn(row, "Laden", self._do_spotify,
                  color=SPOTIFY, hover="#17a349", text_color="#000", width=80).pack(side="left")

    def _build_section_tiktok(self, p):
        card = self._card(p); card.pack(fill="x", padx=20, pady=(0,8))
        self._sec_header(card, "TikTok / Instagram", "Sound als MP3 herunterladen", TIKTOK)
        row = tk.Frame(card, bg=CARD); row.pack(fill="x", padx=16, pady=(8,10))
        self.ti_entry = self._entry(row, placeholder="TikTok / Instagram Link...")
        self.ti_entry.pack(side="left", fill="x", expand=True, padx=(0,10))
        self._btn(row, "Einfügen", lambda: self._paste_entry(self.ti_entry),
                  color=CARD3, hover=CARD2, width=90).pack(side="left", padx=(0,8))
        self._btn(row, "Laden", self._ti_dl,
                  color=TIKTOK, hover="#3fb8bf", text_color="#000", width=80).pack(side="left")

    def _build_download_btn(self, p):
        def _dl_click():
            self.dl_btn.configure(fg_color=ACCENT_D)
            self.after(100, lambda: self.dl_btn.configure(fg_color=ACCENT))
            self._start_dl()
        self.dl_btn = ctk.CTkButton(p, text="  ↓   MP3 herunterladen",
                                    command=_dl_click,
                                    fg_color=ACCENT, hover_color=ACCENT_H,
                                    text_color=TEXT, font=("Segoe UI Black",15),
                                    corner_radius=12, height=56)
        self.dl_btn.pack(fill="x", padx=20, pady=(6,4))

        self.prog = ctk.CTkProgressBar(p, mode="indeterminate",
                                        fg_color=CARD2, progress_color=ACCENT,
                                        corner_radius=4, height=5)
        self.prog.pack(fill="x", padx=20, pady=(0,4))
        self.prog.set(0)

        # OK banner
        self.ok_frame = tk.Frame(p, bg=GREEN_BG, highlightthickness=1,
                                  highlightbackground=GREEN)
        ok_inner = tk.Frame(self.ok_frame, bg=GREEN_BG)
        ok_inner.pack(fill="x", padx=20, pady=12)
        tk.Label(ok_inner, text="✓", font=("Segoe UI Black",20),
                 bg=GREEN_BG, fg=GREEN_L).pack(side="left")
        tf = tk.Frame(ok_inner, bg=GREEN_BG); tf.pack(side="left", padx=(12,0))
        tk.Label(tf, text="Download abgeschlossen!", font=("Segoe UI Black",11),
                 bg=GREEN_BG, fg=GREEN_L).pack(anchor="w")
        self.ok_path = tk.Label(tf, text="", font=("Segoe UI",9),
                                bg=GREEN_BG, fg=GREEN)
        self.ok_path.pack(anchor="w")

    def _build_log(self, p):
        card = self._card(p); card.pack(fill="x", padx=20, pady=(0,24))
        lh = tk.Frame(card, bg=CARD); lh.pack(fill="x", padx=14, pady=(8,4))
        tk.Label(lh, text="● LOG", fg=TEXT3, bg=CARD,
                 font=("Segoe UI",9,"bold")).pack(side="left")
        self._btn(lh, "leeren", self._clear_log,
                  color=CARD2, hover=CARD3, text_color=TEXT3,
                  height=26, font_size=8, width=60).pack(side="right")
        self.log_box = ctk.CTkTextbox(card, height=130, fg_color=CARD,
                                       text_color=TEXT2, font=("Consolas",9),
                                       corner_radius=0, border_width=0, wrap="word")
        self.log_box.pack(fill="x", padx=14, pady=(0,10))
        self.log_box.configure(state="disabled")

    # ── Settings Panel ────────────────────────────────────────────────────────
    def _open_settings(self):
        if self._spanel_visible or self._spanel_animating: return
        for w in self._spanel.winfo_children(): w.destroy()
        self._build_settings_content()
        self._spanel_visible = True
        self._spanel_animating = True
        W, H = 480, 330
        # place offscreen above, centered horizontally
        self._spanel.place(relx=0.5, anchor="n", y=-H, width=W, height=H)
        self._spanel.lift()
        self._anim_open(0, W, H)

    def _anim_open(self, f, W, H):
        total = 22
        self.update_idletasks()
        wh = self.winfo_height()
        target_y = (wh - H) // 2
        if f >= total:
            self._spanel.place(relx=0.5, anchor="n", y=target_y, width=W, height=H)
            self._spanel_animating = False
            return
        t = f / total
        c1, c3 = 1.3, 2.3
        e = max(0.0, 1 + c3*(t-1)**3 + c1*(t-1)**2)
        y = int(-H + (target_y + H) * e)
        self._spanel.place(relx=0.5, anchor="n", y=y, width=W, height=H)
        self.after(12, lambda: self._anim_open(f+1, W, H))

    def _close_settings(self):
        if self._spanel_animating: return
        self._spanel_animating = True
        W, H = 480, 330
        self.update_idletasks()
        wh = self.winfo_height()
        start_y = (wh - H) // 2
        self._anim_close(0, W, H, start_y)

    def _anim_close(self, f, W, H, start_y):
        total = 14
        if f >= total:
            self._spanel.place_forget()
            self._spanel_visible = False
            self._spanel_animating = False
            return
        t = f / total
        e = 1.0 - t**2
        y = int(-H + (start_y + H) * e)
        self._spanel.place(relx=0.5, anchor="n", y=y, width=W, height=H)
        self.after(12, lambda: self._anim_close(f+1, W, H, start_y))

    def _q_changed(self, val):
        self.quality_var.set({"320 kbps":"0","192 kbps":"5","128 kbps":"9"}.get(val,"0"))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _paste_to(self, var):
        try: var.set(self.clipboard_get().strip())
        except: pass

    def _paste_entry(self, e):
        try: e.delete(0,"end"); e.insert(0, self.clipboard_get().strip())
        except: pass

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.output_dir.get())
        if d: self.output_dir.set(d)

    def _log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg+"\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0","end")
        self.log_box.configure(state="disabled")

    def _show_ok(self, folder):
        self.ok_path.configure(text=folder)
        self.ok_frame.pack(fill="x", padx=20, pady=(4,0), before=self.prog)
        self.after(6000, self._hide_ok)

    def _hide_ok(self):
        try: self.ok_frame.pack_forget()
        except: pass

    def _busy(self, on):
        if on:
            self.dl_btn.configure(state="disabled", text="  ⏳  Lädt...", fg_color=CARD3)
            self.prog.start()
        else:
            self.dl_btn.configure(state="normal", text="  ↓   MP3 herunterladen", fg_color=ACCENT)
            self.prog.stop(); self.prog.set(0)

    def _open_explorer(self, fp):
        if self.open_folder.get() and fp and os.path.exists(fp):
            subprocess.Popen(["explorer","/select,",os.path.normpath(fp)],
                             creationflags=CREATE_NO_WINDOW)

    # ── Logic ─────────────────────────────────────────────────────────────────
    def _yt_search(self, q):
        req = urllib.request.Request(
            "https://www.youtube.com/results?search_query="+urllib.parse.quote(q),
            headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8","ignore")
        m = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
        return f"https://www.youtube.com/watch?v={m.group(1)}" if m else None

    def _search_btn(self):
        s = self.search_entry.get().strip()
        if not s: messagebox.showwarning("Kein Name","Bitte Songname eingeben!"); return
        a = self.artist_entry.get().strip()
        threading.Thread(target=self._search_thread, args=(f"{a} {s}".strip(),), daemon=True).start()

    def _search_thread(self, q):
        self._busy(True)
        try:
            self._log(f"Suche: {q}")
            url = self._yt_search(q+" official audio")
            if not url: self._log("Nichts gefunden."); return
            self._log(f"Gefunden: {url}")
            self.url_var.set(url)
            self.search_entry.delete(0,"end"); self.artist_entry.delete(0,"end")
            self.after(0, self._start_dl)
        except Exception as e: self._log(f"Fehler: {e}")
        finally: self._busy(False)

    def _do_spotify(self):
        url = self.sp_entry.get().strip()
        if not url or "spotify.com" not in url:
            messagebox.showwarning("Kein Link","Bitte Spotify-Link einfügen!"); return
        threading.Thread(target=self._spotify_thread, args=(url,), daemon=True).start()

    def _spotify_thread(self, surl):
        self._busy(True)
        try:
            self._log("Lese Spotify...")
            req = urllib.request.Request(surl, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                html = r.read().decode("utf-8","ignore")
            m = re.search(r"<title>(.*?)</title>", html)
            if not m: self._log("Titel nicht lesbar."); return
            name = re.sub(r"\s*[|\-–]\s*Spotify.*$","",m.group(1)).strip()
            self._log(f"Song: {name}")
            url = self._yt_search(name+" official audio")
            if not url: self._log("Kein YouTube-Treffer."); return
            self._log(f"Gefunden: {url}")
            self.url_var.set(url); self.sp_entry.delete(0,"end")
            self.after(0, self._start_dl)
        except Exception as e: self._log(f"Fehler: {e}")
        finally: self._busy(False)

    def _check_tools(self):
        missing = [n for n,p in [("yt-dlp",YTDLP_PATH),("ffmpeg",FFMPEG_PATH)] if not os.path.exists(p)]
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
                zp = os.path.join(TOOLS_DIR,"ffmpeg.zip")
                urllib.request.urlretrieve(FFMPEG_URL, zp)
                self._log("Entpacke ffmpeg...")
                with zipfile.ZipFile(zp) as z:
                    for m in z.namelist():
                        if m.endswith("ffmpeg.exe"):
                            z.extract(m,TOOLS_DIR)
                            shutil.move(os.path.join(TOOLS_DIR,m),FFMPEG_PATH); break
                os.remove(zp)
                for d in os.listdir(TOOLS_DIR):
                    dp = os.path.join(TOOLS_DIR,d)
                    if os.path.isdir(dp): shutil.rmtree(dp,ignore_errors=True)
                self._log("ffmpeg OK")
            self._log("Alles bereit!")
        except Exception as e: self._log(f"Fehler: {e}")
        finally: self._busy(False)

    def _check_update(self):
        self._log("Suche Updates...")
        threading.Thread(target=self._update_thread, daemon=True).start()

    def _update_thread(self):
        self._busy(True)
        try:
            req = urllib.request.Request(GITHUB_RAW, headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                content = r.read().decode("utf-8")
            m = re.search(r'^VERSION\s*=\s*"([^"]+)"', content, re.MULTILINE)
            nv = m.group(1) if m else VERSION
            if nv == VERSION: self._log(f"Aktuell (v{VERSION})"); self._busy(False); return
            self._log(f"Neue Version v{nv} gefunden!")
            if IS_EXE:
                exe = sys.executable; tmp = exe+".new"
                urllib.request.urlretrieve(GITHUB_EXE, tmp)
                bat = os.path.join(BASE_DIR,"_upd.bat")
                with open(bat,"w") as f:
                    f.write(f'@echo off\ntimeout /t 2 /nobreak >nul\nmove /y "{tmp}" "{exe}"\nstart "" "{exe}"\ndel "%~f0"\n')
                subprocess.Popen(["cmd","/c",bat], creationflags=CREATE_NO_WINDOW)
                self.after(500, self.destroy)
            else:
                py = os.path.join(BASE_DIR,"mp3downloader.py")
                with open(py,"w",encoding="utf-8") as f: f.write(content)
                self._log(f"v{nv} installiert!")
                self.after(800, lambda: (subprocess.Popen([sys.executable,py],creationflags=CREATE_NO_WINDOW), self.destroy()))
        except Exception as e: self._log(f"Update-Fehler: {e}")
        finally: self._busy(False)

    def _start_dl(self):
        url = self.url_var.get().strip()
        if not url: messagebox.showwarning("Kein Link","Bitte Link einfügen!"); return
        if not os.path.exists(YTDLP_PATH):
            messagebox.showerror("Tools fehlen","Kurz warten – Tools werden installiert."); return
        threading.Thread(target=self._dl_thread, args=(url,), daemon=True).start()

    def _dl_thread(self, url):
        self._busy(True); self._hide_ok(); self.last_file = None
        self._log("Download startet...")
        out = os.path.join(self.output_dir.get(),"%(title)s.%(ext)s")
        cmd = [YTDLP_PATH,"-x","--audio-format","mp3","--audio-quality",self.quality_var.get(),
               "--ffmpeg-location",TOOLS_DIR,"-o",out,"--no-playlist","--print","after_move:filepath",url]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding="utf-8", errors="replace",
                                    creationflags=CREATE_NO_WINDOW)
            for line in proc.stdout:
                line = line.rstrip()
                if not line: continue
                if os.path.sep in line and line.endswith(".mp3"): self.last_file = line.strip()
                else: self._log(line)
            proc.wait()
            if proc.returncode == 0:
                self._log(f"Fertig!  →  {self.output_dir.get()}")
                self.url_var.set("")
                f,l = self.output_dir.get(), self.last_file
                self.after(0, lambda: self._show_ok(f))
                self.after(500, lambda: self._open_explorer(l))
            else: self._log("Fehlgeschlagen. Link prüfen.")
        except Exception as e: self._log(f"Fehler: {e}")
        finally: self._busy(False)

    def _ti_dl(self):
        url = self.ti_entry.get().strip()
        if not url: messagebox.showwarning("Kein Link","Bitte TikTok/Instagram-Link einfügen!"); return
        if not os.path.exists(YTDLP_PATH):
            messagebox.showerror("Tools fehlen","Kurz warten – Tools werden installiert."); return
        threading.Thread(target=self._ti_thread, args=(url,), daemon=True).start()

    def _ti_thread(self, url):
        self._busy(True); self._hide_ok(); self.last_file = None
        url = url.split("?")[0].strip()
        platform = "TikTok" if "tiktok.com" in url else "Instagram"
        self._log(f"{platform} Sound wird geladen...")
        out = os.path.join(self.output_dir.get(),"%(title).80s.%(ext)s")
        cmd = [YTDLP_PATH,"-x","--audio-format","mp3","--audio-quality",self.quality_var.get(),
               "--ffmpeg-location",TOOLS_DIR,"--no-playlist","--no-check-certificate",
               "--user-agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
               "-o",out,"--print","after_move:filepath",url]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, encoding="utf-8", errors="replace",
                                    creationflags=CREATE_NO_WINDOW)
            for line in proc.stdout:
                line = line.rstrip()
                if not line: continue
                if os.path.sep in line and line.endswith(".mp3"): self.last_file = line.strip()
                else: self._log(line)
            proc.wait()
            if proc.returncode == 0:
                self._log(f"Fertig!  →  {self.output_dir.get()}")
                self.ti_entry.delete(0,"end")
                f,l = self.output_dir.get(), self.last_file
                self.after(0, lambda: self._show_ok(f))
                self.after(500, lambda: self._open_explorer(l))
            else:
                self._log("Fehlgeschlagen – versuche mit Chrome-Cookies...")
                cmd2 = cmd + ["--cookies-from-browser","chrome"]
                try:
                    proc2 = subprocess.Popen(cmd2, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                             text=True, encoding="utf-8", errors="replace",
                                             creationflags=CREATE_NO_WINDOW)
                    for line in proc2.stdout:
                        line = line.rstrip()
                        if not line: continue
                        if os.path.sep in line and line.endswith(".mp3"): self.last_file = line.strip()
                        else: self._log(line)
                    proc2.wait()
                    if proc2.returncode == 0:
                        self._log(f"Fertig!  →  {self.output_dir.get()}")
                        self.ti_entry.delete(0,"end")
                        f,l = self.output_dir.get(), self.last_file
                        self.after(0, lambda: self._show_ok(f))
                        self.after(500, lambda: self._open_explorer(l))
                    else: self._log("Fehlgeschlagen. TikTok blockiert evtl. den Download.")
                except Exception as e2: self._log(f"Fehler: {e2}")
        except Exception as e: self._log(f"Fehler: {e}")
        finally: self._busy(False)


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    login = LoginWindow()
    login.mainloop()
    if not login.logged_in:
        sys.exit(0)
    app = App()
    app.mainloop()
