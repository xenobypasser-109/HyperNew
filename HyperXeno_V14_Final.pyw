import ctypes, os, sys, threading, time, requests, io, base64, re, math, random, string, json, hashlib
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk, ImageGrab
import colorsys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
#  DPI AWARENESS
# ─────────────────────────────────────────────
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except: pass

# ─────────────────────────────────────────────
#  SERVER CONFIG  (reads from config.json)
# ─────────────────────────────────────────────
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
DEFAULT_CONFIG = {"server": "https://hyperxeno-kfi0.onrender.com", "version": "14.0"}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f: return json.load(f)
        except: pass
    with open(CONFIG_PATH, "w") as f: json.dump(DEFAULT_CONFIG, f, indent=2)
    return DEFAULT_CONFIG

CFG = load_config()
SERVER = CFG.get("server", DEFAULT_CONFIG["server"]).rstrip("/")

# ─────────────────────────────────────────────
#  SESSION FILE  (persists login between runs)
# ─────────────────────────────────────────────
SESSION_PATH = os.path.join(os.path.expanduser("~"), ".hyperxeno_session.json")

def save_session(data):
    try:
        with open(SESSION_PATH, "w") as f: json.dump(data, f)
    except: pass

def load_session():
    try:
        if os.path.exists(SESSION_PATH):
            with open(SESSION_PATH, "r") as f: return json.load(f)
    except: pass
    return None

def clear_session():
    try:
        if os.path.exists(SESSION_PATH): os.remove(SESSION_PATH)
    except: pass

# ─────────────────────────────────────────────
#  AI MODELS
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
#  AI MODELS
# ─────────────────────────────────────────────
LLAMA_MODEL    = "meta-llama/llama-4-scout-17b-16e-instruct"
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
XENO_MODEL     = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-nano-12b-v2-vl:free")
GEMINI_KEY     = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL     = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# ─────────────────────────────────────────────
#  COLOUR PALETTES
# ─────────────────────────────────────────────
DARK = {
    "bg":"#050505","panel":"#0D0D0D","sidebar":"#111111","border":"#2A2A2A",
    "topbar":"#000000","white":"#FFFFFF","grey":"#888888","dimgrey":"#444444",
    "accent":"#00FFFF","accent2":"#FF3E3E","accent3":"#3EFF8B","accent4":"#FFD73E",
    "accent5":"#B03EFF","user_fg":"#D1D1D1","ai_fg":"#FFFFFF","sys_fg":"#FF00FF",
}
LIGHT = {
    "bg":"#F0F0F0","panel":"#FFFFFF","sidebar":"#E8E8E8","border":"#CCCCCC",
    "topbar":"#DDDDDD","white":"#111111","grey":"#555555","dimgrey":"#999999",
    "accent":"#0066CC","accent2":"#CC0000","accent3":"#008800","accent4":"#886600",
    "accent5":"#6600AA","user_fg":"#222222","ai_fg":"#111111","sys_fg":"#880088",
}
C = dict(DARK)  # start dark

NAV_ITEMS_USER  = ["CHAT","Notepad","Tools","Games","Messager","Subscription","Logs","Settings"]
NAV_ITEMS_ADMIN = ["CHAT","Notepad","Tools","Games","Messager","Subscription","Logs","Settings","ADMIN"]

COMMANDS_LIST = [
    ("SHIFT + 1",  "Purge chat history"),
    ("SHIFT + 2",  "Cycle AI text color"),
    ("SHIFT + 3",  "Stealth-siphon scan"),
    ("SHIFT + 4",  "Show credits"),
    ("SHIFT + 5",  "Exit HyperXeno"),
    ("SHIFT + 7",  "Cycle AI engine"),
    ("INSERT",     "Auto-find highlighted answer"),
    ("TAB",        "Show this command list"),
    ("ESC",        "Exit HyperXeno"),
    ("↖ Top-Left",     "Toggle ELA deep analysis mode"),
    ("↗ Top-Right",    "Toggle Ghost (invisible) mode"),
    ("↙ Bottom-Left",  "Fire batch on queued snaps"),
    ("↘ Bottom-Right", "Silent screenshot snap"),
    ("SNAP button",    "Manual screenshot snap"),
    ("BATCH button",   "Send all snaps to AI"),
    ("PURGE button",   "Clear chat + snap bank"),
]

BOOT_LINES = [
    "Initializing HyperXeno.exe ...",
    "Loading core_modules.dll ...",
    "Mounting neural_interface.sys ...",
    "Handshaking with AI cluster ...",
    "Decrypting engine_payload.bin ...",
    "Validating session_tokens.dat ...",
    "Injecting overlay_renderer.dll ...",
    "Calibrating orbital_rings.cfg ...",
    "Syncing cloud_manifest.json ...",
    "Loading user_profile.enc ...",
    "Compiling reaction_core.pyw ...",
    "Establishing secure tunnel ...",
    "Warming GPU inference pipeline ...",
    "Registering hotkey_daemon.exe ...",
    "HyperXeno V14.0 — READY",
]

# ══════════════════════════════════════════════════════════════════════════════
#  LOADING SCREEN
# ══════════════════════════════════════════════════════════════════════════════
class LoadingScreen:
    def __init__(self, root, on_done):
        self.root = root; self.on_done = on_done
        self.angle = 0; self.step = 0; self.boot_idx = 0
        self.canvas = tk.Canvas(root, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        W, H = 1200, 780; cx, cy = W//2, H//2-50
        for r, col, dash in [(220,"#1A1A1A",(4,8)),(175,"#222222",(2,6)),(130,"#1A1A1A",(3,5)),(85,"#181818",(2,4))]:
            self.canvas.create_oval(cx-r,cy-r,cx+r,cy+r,outline=col,width=1,dash=dash)
        # Scan line effect
        for i in range(0, H, 4):
            self.canvas.create_line(0,i,W,i,fill="#050505",width=1)
        self.title_id = self.canvas.create_text(cx,cy-24,text="HYPER XENO",font=("Consolas",54,"bold"),fill="#000000")
        self.sub_id   = self.canvas.create_text(cx,cy+38,text="V  1  4  .  0",font=("Consolas",14),fill="#000000")
        self.tag_id   = self.canvas.create_text(cx,cy+62,text="DESIGNED BY C-MASTER  //  ENCRYPTED  //  ELITE",font=("Consolas",9),fill="#000000")
        bx1,bx2,by = cx-220,cx+220,cy+100
        self.canvas.create_rectangle(bx1,by,bx2,by+10,outline="#1A1A1A",fill="#0A0A0A")
        self.bar_id = self.canvas.create_rectangle(bx1,by,bx1,by+10,outline="",fill="#00FFFF")
        self.pct_id = self.canvas.create_text(cx,by+24,text="0%",font=("Consolas",9),fill="#444444")
        # Boot text lines (fast scrolling)
        self.boot_ids = []
        for i in range(7):
            tid = self.canvas.create_text(cx,by+44+i*16,text="",font=("Consolas",8),fill="#333333")
            self.boot_ids.append(tid)
        # Orbitals
        self.orbs = [self.canvas.create_oval(0,0,0,0,fill=c,outline="") for c in ["#00FFFF","#FF3E3E","#3EFF8B","#FFD73E","#B03EFF","#FF3EEB"]]
        self.trails = [self.canvas.create_oval(0,0,0,0,fill="#111111",outline="") for _ in range(36)]
        self.cx,self.cy,self.W,self.H = cx,cy,W,H
        self.bx1,self.bx2,self.by = bx1,bx2,by
        self._animate()

    def _animate(self):
        self.step += 1; progress = min(self.step/160, 1.0); self.angle += 2.4
        cx,cy = self.cx,self.cy
        grey = int(progress*255)
        col = f"#{grey:02x}{grey:02x}{grey:02x}"
        self.canvas.itemconfig(self.title_id,fill=col)
        self.canvas.itemconfig(self.sub_id,fill=col)
        self.canvas.itemconfig(self.tag_id,fill=f"#{grey//2:02x}{grey//2:02x}{grey//2:02x}")
        bw = int((self.bx2-self.bx1)*progress)
        self.canvas.coords(self.bar_id,self.bx1,self.by,self.bx1+bw,self.by+10)
        self.canvas.itemconfig(self.pct_id,text=f"{int(progress*100)}%")
        # Update boot lines every 12 frames
        if self.step % 8 == 0 and self.boot_idx < len(BOOT_LINES):
            for i in range(6):
                idx = self.boot_idx - 6 + i
                txt = BOOT_LINES[idx] if 0<=idx<len(BOOT_LINES) else ""
                fade = int(max(0,(220-(6-i)*38)))
                fc = f"#{fade:02x}{fade:02x}{fade:02x}"
                self.canvas.itemconfig(self.boot_ids[i],text=txt,fill=fc)
            if self.boot_idx < len(BOOT_LINES):
                self.canvas.itemconfig(self.boot_ids[6],text=BOOT_LINES[self.boot_idx],fill="#00FFFF")
            self.boot_idx += 1
        configs = [(self.orbs[0],210,1.0,0,9),(self.orbs[1],172,1.4,60,7),(self.orbs[2],134,0.7,120,6),(self.orbs[3],98,2.1,200,5),(self.orbs[4],64,1.8,290,4),(self.orbs[5],38,3.0,0,3)]
        trail_idx = 0
        for dot,rad,spd,offset,sz in configs:
            a = math.radians(self.angle*spd+offset)
            x = cx+rad*math.cos(a); y = cy+rad*math.sin(a)
            self.canvas.coords(dot,x-sz,y-sz,x+sz,y+sz)
            for t in range(6):
                if trail_idx >= len(self.trails): break
                ta = math.radians(self.angle*spd+offset-t*8)
                tx = cx+rad*math.cos(ta); ty = cy+rad*math.sin(ta)
                fade = max(0,110-t*20); tc = f"#{fade:02x}{fade:02x}{fade:02x}"
                ts = max(1,sz-t)
                self.canvas.coords(self.trails[trail_idx],tx-ts,ty-ts,tx+ts,ty+ts)
                self.canvas.itemconfig(self.trails[trail_idx],fill=tc)
                trail_idx += 1
        if progress < 1.0:
            self.root.after(14,self._animate)
        else:
            self.root.after(300,self._finish)

    def _finish(self):
        self.canvas.destroy(); self.on_done()


# ══════════════════════════════════════════════════════════════════════════════
#  AUTH SCREEN  (Login / Register)
# ══════════════════════════════════════════════════════════════════════════════
class AuthScreen:
    def __init__(self, root, on_success):
        self.root = root; self.on_success = on_success
        self.mode = "login"  # or "register"
        self._build()

    def _build(self):
        for w in self.root.winfo_children(): w.destroy()
        self.frame = tk.Frame(self.root, bg=C["bg"])
        self.frame.pack(fill="both", expand=True)

        # Left decorative panel
        left = tk.Frame(self.frame, bg="#000000", width=380)
        left.pack(side="left", fill="y"); left.pack_propagate(False)
        tk.Label(left,text="▣",fg=C["accent"],bg="#000000",font=("Consolas",48,"bold")).pack(pady=(120,10))
        tk.Label(left,text="HYPER XENO",fg=C["white"],bg="#000000",font=("Consolas",22,"bold")).pack()
        tk.Label(left,text="V14.0",fg=C["accent"],bg="#000000",font=("Consolas",13)).pack()
        tk.Frame(left,bg=C["border"],height=1).pack(fill="x",padx=40,pady=20)
        tk.Label(left,text="ELITE BUILD\nDESIGNED BY C-MASTER\n\nENCRYPTED  //  GLOBAL\nMULTI-AI  //  PREMIUM",
                 fg=C["dimgrey"],bg="#000000",font=("Consolas",9),justify="center").pack()

        # Animated status
        self._status_lbl = tk.Label(left,text="● ONLINE",fg=C["accent3"],bg="#000000",font=("Consolas",9,"bold"))
        self._status_lbl.pack(pady=(30,0))
        threading.Thread(target=self._check_server_status,daemon=True).start()

        # Right form panel
        right = tk.Frame(self.frame, bg=C["panel"])
        right.pack(side="right", fill="both", expand=True)
        tk.Frame(right,bg=C["panel"]).pack(expand=True)

        inner = tk.Frame(right, bg=C["panel"])
        inner.pack(expand=True)

        self.form_title = tk.Label(inner,text="WELCOME BACK",fg=C["white"],bg=C["panel"],font=("Consolas",20,"bold"))
        self.form_title.pack(pady=(0,6))
        self.form_sub = tk.Label(inner,text="Sign in to your account",fg=C["grey"],bg=C["panel"],font=("Consolas",10))
        self.form_sub.pack(pady=(0,24))

        # Username
        tk.Label(inner,text="USERNAME",fg=C["dimgrey"],bg=C["panel"],font=("Consolas",8)).pack(anchor="w")
        self.user_entry = tk.Entry(inner,width=32,font=("Consolas",12),bg=C["border"],fg=C["white"],
                                   relief="flat",insertbackground=C["white"],bd=0)
        self.user_entry.pack(ipady=8,pady=(2,12),fill="x")

        # Password
        tk.Label(inner,text="PASSWORD",fg=C["dimgrey"],bg=C["panel"],font=("Consolas",8)).pack(anchor="w")
        self.pass_entry = tk.Entry(inner,width=32,font=("Consolas",12),bg=C["border"],fg=C["white"],
                                   relief="flat",insertbackground=C["white"],show="●",bd=0)
        self.pass_entry.pack(ipady=8,pady=(2,6),fill="x")

        # Error label
        self.err_lbl = tk.Label(inner,text="",fg=C["accent2"],bg=C["panel"],font=("Consolas",9))
        self.err_lbl.pack(pady=(0,10))

        # Submit button
        self.submit_btn = tk.Button(inner,text="SIGN IN",command=self._submit,
                                    bg=C["accent"],fg="#000000",relief="flat",
                                    font=("Consolas",12,"bold"),cursor="hand2",width=26,pady=8)
        self.submit_btn.pack(pady=(0,16))

        # Toggle link
        self.toggle_lbl = tk.Label(inner,text="Don't have an account? Register",
                                   fg=C["accent"],bg=C["panel"],font=("Consolas",9),cursor="hand2")
        self.toggle_lbl.pack()
        self.toggle_lbl.bind("<Button-1>",lambda e: self._toggle_mode())

        tk.Frame(right,bg=C["panel"]).pack(expand=True)

        self.user_entry.bind("<Return>",lambda e: self.pass_entry.focus())
        self.pass_entry.bind("<Return>",lambda e: self._submit())
        self.user_entry.focus()

    def _toggle_mode(self):
        self.mode = "register" if self.mode=="login" else "login"
        self.err_lbl.config(text="")
        if self.mode=="register":
            self.form_title.config(text="CREATE ACCOUNT")
            self.form_sub.config(text="Join HyperXeno — it's free")
            self.submit_btn.config(text="REGISTER")
            self.toggle_lbl.config(text="Already have an account? Sign in")
        else:
            self.form_title.config(text="WELCOME BACK")
            self.form_sub.config(text="Sign in to your account")
            self.submit_btn.config(text="SIGN IN")
            self.toggle_lbl.config(text="Don't have an account? Register")

    def _submit(self):
        u = self.user_entry.get().strip()
        p = self.pass_entry.get().strip()
        if not u or not p:
            self.err_lbl.config(text="Please fill in all fields"); return

        self.submit_btn.config(state="disabled",text="...")
        self.err_lbl.config(text="")
        endpoint = "/signup" if self.mode=="register" else "/login"
        def do_req():
            try:
                res = requests.post(f"{SERVER}{endpoint}",
                    json={"username":u,"password":p}, timeout=12)
                data = res.json()
                if res.status_code in (200,201):
                    if self.mode=="register":
                        self.root.after(0,lambda: self.err_lbl.config(text="Account created! Signing in...",fg=C["accent3"]))
                        time.sleep(0.8)
                        # auto-login
                        res2 = requests.post(f"{SERVER}/login",json={"username":u,"password":p},timeout=12)
                        data = res2.json()
                    token = data.get("token","")
                    role  = data.get("role","user")
                    tier  = data.get("tier","basic")
                    session = {"username":u,"token":token,"role":role,"tier":tier,"groq_key":"","xeno_key":"","gemini_key":""}
                    save_session(session)
                    self.root.after(0,lambda: self.on_success(session))
                else:
                    msg = data.get("error","Login failed")
                    self.root.after(0,lambda m=msg: (self.err_lbl.config(text=m,fg=C["accent2"]),
                                                      self.submit_btn.config(state="normal",
                                                      text="SIGN IN" if self.mode=="login" else "REGISTER")))
            except Exception as e:
                self.root.after(0,lambda: (self.err_lbl.config(text=f"Server unreachable: {e}",fg=C["accent2"]),
                                            self.submit_btn.config(state="normal",
                                            text="SIGN IN" if self.mode=="login" else "REGISTER")))
        threading.Thread(target=do_req,daemon=True).start()

    def _check_server_status(self):
        try:
            r = requests.get(f"{SERVER}/status",timeout=6)
            data = r.json()
            if data.get("maintenance"):
                self.root.after(0,lambda: self._status_lbl.config(text="⚠ MAINTENANCE",fg=C["accent4"]))
            else:
                self.root.after(0,lambda: self._status_lbl.config(text="● ONLINE",fg=C["accent3"]))
        except:
            self.root.after(0,lambda: self._status_lbl.config(text="○ OFFLINE",fg=C["accent2"]))


# ══════════════════════════════════════════════════════════════════════════════
#  GROQ KEY SETUP SCREEN (shown after first register)
# ══════════════════════════════════════════════════════════════════════════════
class GroqSetupScreen:
    def __init__(self, root, session, on_done):
        self.root=root; self.session=session; self.on_done=on_done
        self._build()

    def _build(self):
        for w in self.root.winfo_children(): w.destroy()
        f = tk.Frame(self.root,bg=C["bg"]); f.pack(fill="both",expand=True)
        tk.Frame(f,bg=C["bg"]).pack(expand=True)
        inner = tk.Frame(f,bg=C["panel"],padx=40,pady=30); inner.pack(expand=True)
        tk.Label(inner,text="🔑  SETUP YOUR AI KEY",fg=C["accent"],bg=C["panel"],font=("Consolas",18,"bold")).pack()
        tk.Label(inner,text="You need a FREE Groq API key to use HyperXeno Chat.",fg=C["grey"],bg=C["panel"],font=("Consolas",10)).pack(pady=(6,0))
        tk.Frame(inner,bg=C["border"],height=1).pack(fill="x",pady=14)
        steps = [
            "1. Go to:  https://console.groq.com",
            "2. Sign up for a FREE account",
            "3. Click 'API Keys' in the left sidebar",
            "4. Click 'Create API Key'",
            "5. Copy your key and paste it below ↓",
        ]
        for s in steps:
            tk.Label(inner,text=s,fg=C["white"],bg=C["panel"],font=("Consolas",10),anchor="w").pack(anchor="w",pady=2)
        tk.Frame(inner,bg=C["border"],height=1).pack(fill="x",pady=14)
        tk.Label(inner,text="YOUR GROQ API KEY",fg=C["dimgrey"],bg=C["panel"],font=("Consolas",8)).pack(anchor="w")
        self.key_entry = tk.Entry(inner,width=52,font=("Consolas",11),bg=C["border"],fg=C["accent"],
                                  relief="flat",insertbackground=C["accent"],bd=0)
        self.key_entry.pack(ipady=8,pady=(2,10),fill="x")
        self.err = tk.Label(inner,text="",fg=C["accent2"],bg=C["panel"],font=("Consolas",9)); self.err.pack()
        fr = tk.Frame(inner,bg=C["panel"]); fr.pack(pady=8)
        tk.Button(fr,text="SAVE & CONTINUE",command=self._save,
                  bg=C["accent"],fg="#000",relief="flat",font=("Consolas",11,"bold"),cursor="hand2",padx=16,pady=8).pack(side="left",padx=6)
        tk.Button(fr,text="Skip for now",command=lambda: self.on_done(self.session),
                  bg=C["border"],fg=C["grey"],relief="flat",font=("Consolas",9),cursor="hand2").pack(side="left",padx=6)
        tk.Frame(f,bg=C["bg"]).pack(expand=True)

    def _save(self):
        key = self.key_entry.get().strip()
        if not key.startswith("gsk_"):
            self.err.config(text="That doesn't look like a valid Groq key (should start with gsk_)"); return
        self.session["groq_key"] = key
        save_session(self.session)
        self.on_done(self.session)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════
class HyperXeno:
    def __init__(self, root, session):
        self.root = root; self.session = session
        self.username = session.get("username","user")
        self.role     = session.get("role","user")
        self.tier     = session.get("tier","basic")
        self.token    = session.get("token","")
        self.groq_key = session.get("groq_key","")
        self.xeno_key = session.get("xeno_key","") or OPENROUTER_KEY
        self.gemini_key = session.get("gemini_key","") or GEMINI_KEY

        self.root.title(f"HYPER XENO V14.0 — {self.username}")
        sw = root.winfo_screenwidth(); sh = root.winfo_screenheight()
        W,H=1200,780
        self.root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.root.configure(bg=C["bg"])
        self.root.attributes("-topmost",True)
        self.root.protocol("WM_DELETE_WINDOW",lambda: None)
        self.root.bind("<Escape>",lambda e: os._exit(0))
        try:
            self.hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            self.base_style = 0x00080000|0x00000008|0x00000080
            ctypes.windll.user32.SetWindowLongW(self.hwnd,-20,self.base_style)
        except: self.hwnd=None; self.base_style=0

        # State
        self.is_ghost=False; self.is_ela_enabled=False; self.is_light_mode=False
        self.snap_bank=[]; self.tk_images=[]; self.history=[]; self.siphon_buffer=""
        self.model_mode=0; self.model_names=["GROQ","OPENROUTER","GEMINI"]
        self.color_idx=0; self.ai_colors=[C["white"],C["accent"],C["accent3"],C["accent4"]]
        self.screen_w=sw; self.screen_h=sh; self.active_nav="CHAT"; self.drag_x=self.drag_y=0
        self.current_file_path=None; self.recent_files=[]; self.notepad_font_size=12
        self.word_wrap=tk.BooleanVar(value=True); self.show_line_numbers=tk.BooleanVar(value=False)
        self.notepad_dark_mode=tk.BooleanVar(value=True); self.notepad_read_only=tk.BooleanVar(value=False)
        self.notepad_autosave=tk.BooleanVar(value=False); self.app_always_on_top=tk.BooleanVar(value=True)
        self.sidebar_compact=tk.BooleanVar(value=False); self.logs=[]

        LoadingScreen(self.root, self._build_ui)

    # ──────────────────────────────────────────────────────────────────────────
    #  UI BUILD
    # ──────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Top bar
        self.top_bar=tk.Frame(self.root,bg=C["topbar"],height=44)
        self.top_bar.pack(side="top",fill="x"); self.top_bar.pack_propagate(False)
        self.top_bar.bind("<ButtonPress-1>",self._drag_start)
        self.top_bar.bind("<B1-Motion>",self._drag_move)

        logo=tk.Frame(self.top_bar,bg=C["topbar"]); logo.pack(side="left",padx=16,pady=6)
        tk.Label(logo,text="▣",fg=C["accent"],bg=C["topbar"],font=("Consolas",14,"bold")).pack(side="left",padx=(0,6))
        tk.Label(logo,text="HYPER XENO",fg=C["white"],bg=C["topbar"],font=("Consolas",13,"bold")).pack(side="left")
        tk.Label(logo,text=" // V14.0",fg=C["dimgrey"],bg=C["topbar"],font=("Consolas",10)).pack(side="left")

        # User badge
        role_col={"admin":C["accent2"],"moderator":C["accent4"],"co-admin":C["accent5"],"user":C["grey"]}.get(self.role,C["grey"])
        tk.Label(self.top_bar,text=f"  [{self.role.upper()}] {self.username}",
                 fg=role_col,bg=C["topbar"],font=("Consolas",9,"bold")).pack(side="left",padx=6)

        self.engine_lbl=tk.Label(self.top_bar,text=f"ENGINE: {self.model_names[self.model_mode]}",
                                  fg=C["accent"],bg=C["topbar"],font=("Consolas",9,"bold"))
        self.engine_lbl.pack(side="left",padx=16)

        right=tk.Frame(self.top_bar,bg=C["topbar"]); right.pack(side="right",padx=10)
        for lbl,cmd,col in [("✕",lambda:os._exit(0),C["accent2"]),("⬜",self._toggle_ghost,C["grey"]),("⟳",self._cycle_engine_btn,C["accent3"]),("⏏",self._logout,C["accent4"])]:
            tk.Button(right,text=lbl,command=cmd,bg=C["topbar"],fg=col,relief="flat",
                      font=("Consolas",13,"bold"),bd=0,activebackground="#1A1A1A",
                      activeforeground=col,cursor="hand2").pack(side="right",padx=4)

        # Body
        body=tk.Frame(self.root,bg=C["bg"]); body.pack(fill="both",expand=True)
        self.sidebar=tk.Frame(body,bg=C["sidebar"],width=172); self.sidebar.pack(side="left",fill="y"); self.sidebar.pack_propagate(False)
        self._build_sidebar()
        tk.Frame(body,bg=C["border"],width=1).pack(side="left",fill="y")
        self.main_frame=tk.Frame(body,bg=C["panel"]); self.main_frame.pack(side="left",fill="both",expand=True)

        # Status bar
        self.status_bar=tk.Frame(self.root,bg="#000000",height=22); self.status_bar.pack(side="bottom",fill="x"); self.status_bar.pack_propagate(False)
        self.status_lbl=tk.Label(self.status_bar,
            text="  ↖ELA  ↗GHOST  ↙BATCH  ↘SNAP  │  SHIFT+1 PURGE  │  SHIFT+2 LIGHT MODE  │  SHIFT+4 CREDITS  │  SHIFT+5 EXIT  │  SHIFT+7 ENGINE  │  TAB COMMANDS",
            fg=C["dimgrey"],bg="#000000",font=("Consolas",8),anchor="w")
        self.status_lbl.pack(side="left",fill="x",expand=True)
        self.clock_lbl=tk.Label(self.status_bar,text="",fg=C["dimgrey"],bg="#000000",font=("Consolas",8))
        self.clock_lbl.pack(side="right",padx=10)
        self._tick_clock()

        # Bind TAB globally
        self.root.bind("<Tab>",lambda e: self._show_commands_overlay())

        threading.Thread(target=self._stay_active,daemon=True).start()
        threading.Thread(target=self._corner_engine,daemon=True).start()
        threading.Thread(target=self._passive_clicker_engine,daemon=True).start()
        threading.Thread(target=self._poll_maintenance,daemon=True).start()

        self._nav_switch("CHAT")

    # ──────────────────────────────────────────────────────────────────────────
    #  SIDEBAR
    # ──────────────────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        for w in self.sidebar.winfo_children(): w.destroy()
        tk.Label(self.sidebar,text="◈ C-MASTER",fg=C["accent"],bg=C["sidebar"],font=("Consolas",9,"bold")).pack(pady=(14,2))
        # Tier badge
        tier_col={"basic":C["grey"],"pro":C["accent4"],"business":C["accent2"]}.get(self.tier,C["grey"])
        tk.Label(self.sidebar,text=f"✦ {self.tier.upper()}",fg=tier_col,bg=C["sidebar"],font=("Consolas",7,"bold")).pack()
        tk.Frame(self.sidebar,bg=C["border"],height=1).pack(fill="x",padx=14,pady=6)
        self.nav_buttons={}
        nav_items = NAV_ITEMS_ADMIN if self.role in ("admin","co-admin") else NAV_ITEMS_USER
        for name in nav_items: self._make_nav_btn(name)
        tk.Frame(self.sidebar,bg=C["border"],height=1).pack(fill="x",padx=14,pady=8)
        tk.Label(self.sidebar,text="AI ENGINE",fg=C["dimgrey"],bg=C["sidebar"],font=("Consolas",7)).pack()
        self.sidebar_engine=tk.Label(self.sidebar,text=self.model_names[self.model_mode],fg=C["accent"],bg=C["sidebar"],font=("Consolas",11,"bold"))
        self.sidebar_engine.pack(pady=2)
        tk.Button(self.sidebar,text="CYCLE ▶",command=self._cycle_engine_btn,bg=C["border"],fg=C["white"],relief="flat",font=("Consolas",8),bd=0,activebackground="#333",cursor="hand2").pack(pady=4)
        tk.Frame(self.sidebar,bg=C["border"],height=1).pack(fill="x",padx=14,pady=6)
        self._rb_label=tk.Label(self.sidebar,text="Designed By\nC-Master",bg=C["sidebar"],font=("Consolas",8,"bold"))
        self._rb_label.pack(pady=4)
        threading.Thread(target=self._animate_sidebar_rainbow,daemon=True).start()

    def _make_nav_btn(self,name):
        is_active=(name==self.active_nav)
        bg=C["accent"] if is_active else C["sidebar"]
        fg=C["bg"] if is_active else C["grey"]
        fnt=("Consolas",10,"bold") if is_active else ("Consolas",10)
        col_map={"ADMIN":C["accent2"],"Subscription":C["accent4"]}
        if not is_active and name in col_map: fg=col_map[name]
        btn=tk.Button(self.sidebar,text=f"  {name}",command=lambda n=name:self._nav_switch(n),
                      bg=bg,fg=fg,relief="flat",anchor="w",font=fnt,bd=0,pady=10,padx=14,
                      activebackground=C["accent"],activeforeground=C["bg"],cursor="hand2")
        btn.pack(fill="x"); self.nav_buttons[name]=btn

    def _nav_switch(self,name):
        self.active_nav=name; self.log_event(f"Nav: {name}")
        self._build_sidebar(); self._clear_main()
        {"CHAT":self._show_chat,"Notepad":self.show_notepad,"Tools":self.show_tools,
         "Games":self.show_games,"Messager":self.show_messages,"Logs":self.show_terminal,
         "Settings":self.show_settings,"ADMIN":self.show_admin,"Subscription":self.show_subscription
        }.get(name,self._show_chat)()

    def _clear_main(self):
        for w in self.main_frame.winfo_children(): w.destroy()

    def _page_header(self,text,sub=""):
        hf=tk.Frame(self.main_frame,bg=C["panel"]); hf.pack(fill="x",padx=20,pady=(16,4))
        tk.Label(hf,text=text,fg=C["white"],bg=C["panel"],font=("Consolas",18,"bold")).pack(side="left")
        if sub: tk.Label(hf,text=f"  // {sub}",fg=C["dimgrey"],bg=C["panel"],font=("Consolas",10)).pack(side="left",pady=4)
        tk.Frame(self.main_frame,bg=C["border"],height=1).pack(fill="x",padx=20,pady=2)

    # ──────────────────────────────────────────────────────────────────────────
    #  COMMANDS OVERLAY (TAB)
    # ──────────────────────────────────────────────────────────────────────────
    def _show_commands_overlay(self):
        ov=tk.Toplevel(self.root); ov.title("Commands"); ov.geometry("520x480")
        ov.configure(bg=C["panel"]); ov.attributes("-topmost",True)
        ov.resizable(False,False)
        tk.Label(ov,text="⌨  COMMAND REFERENCE",fg=C["accent"],bg=C["panel"],font=("Consolas",14,"bold")).pack(pady=(16,4))
        tk.Frame(ov,bg=C["border"],height=1).pack(fill="x",padx=20,pady=4)
        scroll_frame=tk.Frame(ov,bg=C["panel"]); scroll_frame.pack(fill="both",expand=True,padx=20,pady=8)
        for key,desc in COMMANDS_LIST:
            row=tk.Frame(scroll_frame,bg=C["panel"]); row.pack(fill="x",pady=3)
            tk.Label(row,text=f"{key:<22}",fg=C["accent4"],bg=C["panel"],font=("Consolas",9,"bold"),width=22,anchor="w").pack(side="left")
            tk.Label(row,text=desc,fg=C["grey"],bg=C["panel"],font=("Consolas",9),anchor="w").pack(side="left")
        tk.Frame(ov,bg=C["border"],height=1).pack(fill="x",padx=20,pady=4)
        tk.Button(ov,text="CLOSE",command=ov.destroy,bg=C["border"],fg=C["white"],relief="flat",font=("Consolas",9)).pack(pady=8)

    # ──────────────────────────────────────────────────────────────────────────
    #  CHAT
    # ──────────────────────────────────────────────────────────────────────────
    def _show_chat(self):
        self._page_header("AETHERAUDIT",f"ENGINE: {self.model_names[self.model_mode]}")
        cf=tk.Frame(self.main_frame,bg=C["panel"]); cf.pack(fill="both",expand=True,padx=20,pady=(4,0))
        self.chat=scrolledtext.ScrolledText(cf,bg="#000000",fg=C["white"],font=("Consolas",10),
            wrap=tk.WORD,borderwidth=0,selectbackground=C["accent"],selectforeground="#000",insertbackground=C["white"])
        self.chat.pack(fill="both",expand=True)
        for tag,col in [("user_msg",C["user_fg"]),("ai_msg",C["ai_fg"]),
                         ("sys",C["sys_fg"]),("credits",C["accent3"]),
                         ("divider",C["border"]),("h1",C["accent2"]),("h2","#3E9CFF"),
                         ("h3",C["accent3"]),("h4",C["accent4"]),("h5","#FF3EEB"),
                         ("h7",C["accent"]),("hins",C["white"])]:
            fnt=("Consolas",9,"italic") if tag=="sys" else ("Consolas",9,"bold") if tag not in ("user_msg","ai_msg","divider") else ("Consolas",10)
            self.chat.tag_config(tag,foreground=col,font=fnt)
        self.chat.tag_config("final",background=C["accent4"],foreground="#000",font=("Consolas",11,"bold"))
        self.chat.config(state="disabled")

        ef=tk.Frame(self.main_frame,bg=C["panel"],pady=8); ef.pack(fill="x",padx=20)
        self.snap_lbl=tk.Label(ef,text="SNAPS:0",fg=C["dimgrey"],bg=C["panel"],font=("Consolas",8))
        self.snap_lbl.pack(side="right",padx=6)
        tk.Button(ef,text="SNAP 📷",command=self._take_snap,bg=C["border"],fg=C["white"],relief="flat",font=("Consolas",8),bd=0,cursor="hand2",activebackground="#333").pack(side="right",padx=4)
        tk.Button(ef,text="BATCH ⚡",command=lambda:threading.Thread(target=self._process_batch,daemon=True).start(),
                  bg=C["border"],fg=C["accent4"],relief="flat",font=("Consolas",8),bd=0,cursor="hand2",activebackground="#333").pack(side="right",padx=4)
        tk.Button(ef,text="PURGE",command=self.purge_chat,bg=C["border"],fg=C["accent2"],relief="flat",font=("Consolas",8),bd=0,cursor="hand2",activebackground="#333").pack(side="right",padx=4)
        self.entry=tk.Entry(ef,bg="#111111",fg=C["white"],font=("Consolas",11),borderwidth=0,insertbackground=C["white"],selectbackground=C["accent"])
        self.entry.pack(side="left",fill="x",expand=True,ipady=6)
        self.entry.bind("<Return>",self._process_input)

        self._rainbow_intro()
        self._chat_log(f"AETHERAUDIT ACTIVE - {self.username} [{self.role}]",tag="sys")
        self._chat_log("[SHIFT+1] PURGE CHAT & SNAPS",tag="h1")
        self._chat_log("[SHIFT+2] CYCLE TEXT COLOR",tag="h2")
        self._chat_log("[SHIFT+3] STEALTH-SIPHON SCAN",tag="h3")
        self._chat_log("[SHIFT+4] VIEW C-MASTER CREDITS",tag="h4")
        self._chat_log("[SHIFT+5] FAST KILL CORE",tag="h5")
        self._chat_log("[SHIFT+7] TOGGLE AI ENGINE",tag="h7")
        self._chat_log("[INSERT] AUTO-FIND & MATCH",tag="hins")
        if not self.groq_key and self.tier=="basic":
            self._chat_log("⚠ No Groq key set! Go to Settings → API Keys to add it.",tag="sys")

    def _rainbow_intro(self):
        self.chat.config(state="normal")
        text="  AetherAudit - Designed By C-Master  "
        for i,ch in enumerate(text):
            tag=f"_rb{i}"; self.chat.insert(tk.END,ch,tag)
        self.chat.insert(tk.END,"\n\n"); self.chat.config(state="disabled")
        def _anim():
            h=0.0
            while True:
                try:
                    for i in range(len(text)):
                        hue=(h+i/len(text))%1.0; r,g,b=colorsys.hsv_to_rgb(hue,1.0,1.0)
                        self.chat.tag_config(f"_rb{i}",foreground="#%02x%02x%02x"%(int(r*255),int(g*255),int(b*255)),font=("Consolas",11,"bold"))
                    h=(h+0.008)%1.0; time.sleep(0.05)
                except: break
        threading.Thread(target=_anim,daemon=True).start()

    def _chat_log(self,msg,tag=None,images=None):
        try:
            self.chat.config(state="normal")
            self.chat.insert(tk.END,"─"*72+"\n","divider")
            if images:
                w=max(self.chat.winfo_width()-30,200)
                for img in images:
                    ratio=w/float(img.size[0]); h=int(img.size[1]*ratio)
                    render=img.resize((w,h),Image.Resampling.LANCZOS)
                    tk_img=ImageTk.PhotoImage(render); self.tk_images.append(tk_img)
                    self.chat.image_create(tk.END,image=tk_img)
                self.chat.insert(tk.END,"\n")
            final_tag=tag
            if not final_tag:
                if str(msg).startswith("CJ:"): final_tag="user_msg"
                elif any(str(msg).startswith(n+":") for n in self.model_names): final_tag="ai_msg"
            self.chat.insert(tk.END,f"{msg}\n\n",final_tag)
            self._apply_highlights(); self.chat.config(state="disabled"); self.chat.yview(tk.END)
        except: pass

    def _apply_highlights(self):
        try:
            self.chat.tag_remove("final","1.0",tk.END); start="1.0"
            while True:
                start=self.chat.search(r"==.*?==",start,stopindex=tk.END,regexp=True)
                if not start: break
                content=self.chat.get(start,f"{start} lineend"); m=re.search(r"==.*?==",content)
                if m:
                    end=f"{start}+{len(m.group(0))}c"; self.chat.tag_add("final",start,end); start=end
                else: break
        except: pass

    def _current_groq_key(self):
        return self.groq_key or os.getenv("GROQ_API_KEY", "")

    def _current_openrouter_key(self):
        return self.xeno_key or os.getenv("OPENROUTER_API_KEY", "")

    def _current_gemini_key(self):
        return self.gemini_key or os.getenv("GEMINI_API_KEY", "")

    def _global_siphon(self):
        def execute_deep_scan():
            self.is_ghost=True
            self.root.after(0,lambda:self.root.attributes("-alpha",0.0))
            try:
                ctypes.windll.user32.SetWindowLongW(self.hwnd,-20,self.base_style|0x00000020)
            except: pass
            self.root.after(0,lambda:self._chat_log("STEALTH-SIPHON: INITIALIZING DUAL SCAN...",tag="sys"))
            time.sleep(0.2)

            captured_payloads=[]
            for side_offset in [self.screen_w//4,(self.screen_w//4)*3]:
                ctypes.windll.user32.SetCursorPos(side_offset,self.screen_h//2)
                time.sleep(0.1)
                for _ in range(4):
                    shot=ImageGrab.grab(all_screens=True)
                    buf=io.BytesIO(); shot.save(buf,format="PNG")
                    captured_payloads.append(base64.b64encode(buf.getvalue()).decode("utf-8"))
                    ctypes.windll.user32.mouse_event(0x0800,0,0,-1200,0)
                    time.sleep(0.15)

            key=self._current_groq_key()
            if not key:
                self.root.after(0,lambda:self._chat_log("SIPHON FAILED: missing Groq key.",tag="sys"))
                return

            final_lines=[]; seen_lines=set(); lock=threading.Lock()
            def ocr_worker(b64_data):
                content=[
                    {"type":"text","text":"OCR MODE: Extract all visible text exactly as it appears. Preserve line breaks. No duplicates."},
                    {"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64_data}","detail":"high"}}
                ]
                try:
                    res=requests.post("https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization":f"Bearer {key}"},
                        json={"model":LLAMA_MODEL,"messages":[{"role":"user","content":content}],"temperature":0.0,"max_tokens":1024},
                        timeout=20)
                    data=res.json()
                    if "choices" in data:
                        for raw in data["choices"][0]["message"]["content"].strip().split("\n"):
                            clean=raw.strip()
                            with lock:
                                if clean and clean.lower() not in seen_lines:
                                    final_lines.append(clean); seen_lines.add(clean.lower())
                except: pass

            threads=[threading.Thread(target=ocr_worker,args=(payload,)) for payload in captured_payloads]
            for t in threads: t.start()
            for t in threads: t.join()

            self.siphon_buffer="\n".join(final_lines)
            if self.siphon_buffer:
                self.root.after(0,lambda:[
                    self.entry.delete(0,tk.END),
                    self.entry.insert(0,"Solve based on: "+self.siphon_buffer),
                    self._process_input()
                ])
                self.root.after(0,lambda:self._chat_log("STEALTH SIPHON SUCCESS (CLEANED).",tag="sys"))
            else:
                self.root.after(0,lambda:self._chat_log("SIPHON FAILED: NO CONTENT CAPTURED.",tag="sys"))
        threading.Thread(target=execute_deep_scan,daemon=True).start()

    def _passive_clicker_engine(self):
        class POINT(ctypes.Structure): _fields_=[("x",ctypes.c_long),("y",ctypes.c_long)]
        while True:
            try:
                if ctypes.windll.user32.GetAsyncKeyState(0x2D)&0x8000:
                    pt=POINT(); ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                    ranges=self.chat.tag_ranges("final") if hasattr(self,"chat") else ()
                    key=self._current_groq_key()
                    if ranges and key:
                        highlighted=self.chat.get(ranges[0],ranges[1]).replace("==","").replace("Final Answer:","").strip().lower()
                        shot=ImageGrab.grab(bbox=(pt.x-300,pt.y-45,pt.x+300,pt.y+45))
                        buf=io.BytesIO(); shot.save(buf,format="PNG")
                        b64=base64.b64encode(buf.getvalue()).decode("utf-8")
                        prompt=f"Target text: '{highlighted}'. Does any part of this specific text appear within this image as an answer choice? Answer ONLY 'YES' or 'NO'."
                        try:
                            res=requests.post("https://api.groq.com/openai/v1/chat/completions",
                                headers={"Authorization":f"Bearer {key}"},
                                json={"model":LLAMA_MODEL,"messages":[{"role":"user","content":[{"type":"text","text":prompt},{"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64}"}}]}],"temperature":0.0},
                                timeout=5)
                            decision=res.json()["choices"][0]["message"]["content"].strip().upper()
                            if "YES" in decision:
                                ctypes.windll.user32.mouse_event(0x0002,0,0,0,0)
                                ctypes.windll.user32.mouse_event(0x0004,0,0,0,0)
                                self.root.after(0,lambda:self._chat_log(f"TARGET MATCHED: {highlighted[:30]}...",tag="sys"))
                                time.sleep(0.2); self.root.after(0,self.purge_chat)
                            else:
                                self.root.after(0,lambda:self._chat_log("NO MATCH IN WIDE SCAN",tag="sys"))
                        except: pass
                    time.sleep(0.5)
            except: pass
            time.sleep(0.01)

    def _process_input(self,event=None):
        text=self.entry.get().strip(); self.entry.delete(0,tk.END)
        if not text: return
        if text.lower()=="exit_core": os._exit(0)
        if text.startswith("Solve based on:"): self.history=[]
        # Check tier / key
        if not self._check_engine_access(): return
        self._chat_log(f"CJ: {text}"); self.history.append({"role":"user","content":text})
        threading.Thread(target=self._call_text_ai,daemon=True).start()

    def _check_engine_access(self):
        if self.model_mode==0:
            if not self._current_groq_key() and self.role not in ("admin","co-admin","moderator"):
                self._chat_log("No Groq key! Add it in Settings -> API Keys",tag="sys"); return False
        elif self.model_mode==1:
            if not self._current_openrouter_key():
                self._chat_log("No OpenRouter key set. Add it in Settings -> API Keys or .env.",tag="sys"); return False
            if self.tier not in ("pro","business") and self.role not in ("admin","co-admin"):
                self._chat_log("OpenRouter engine requires Pro or higher. See Subscription tab.",tag="sys"); return False
        elif self.model_mode==2:
            if not self._current_gemini_key():
                self._chat_log("No Gemini key set. Add it in Settings -> API Keys or .env.",tag="sys"); return False
            if self.tier != "business" and self.role not in ("admin","co-admin"):
                self._chat_log("Gemini engine requires Business plan. See Subscription tab.",tag="sys"); return False
        return True
    def _call_text_ai(self):
        eng=self.model_names[self.model_mode]; ans=""
        try:
            if self.model_mode==0:
                res=requests.post("https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization":f"Bearer {self._current_groq_key()}"},
                    json={"model":LLAMA_MODEL,"messages":self.history,"temperature":0.0},timeout=15)
                ans=res.json()['choices'][0]['message']['content'].strip()
            elif self.model_mode==1:
                key=self._current_openrouter_key()
                res=requests.post("https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
                    json={"model":XENO_MODEL,"messages":self.history,"temperature":0.7},timeout=15)
                ans=res.json()['choices'][0]['message']['content'].strip()
            elif self.model_mode==2:
                key=self._current_gemini_key()
                payload={"contents":[{"role":"user","parts":[{"text":h["content"]}]} for h in self.history]}
                res=requests.post(f"{GEMINI_URL}?key={key}",headers={"Content-Type":"application/json"},json=payload,timeout=15)
                ans=res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            if self.history and "Solve based on:" in self.history[-1]["content"]:
                ans=f"== Final Answer: {ans} =="
            self.history.append({"role":"assistant","content":ans})
            self._chat_log(f"{eng}: {ans}")
        except Exception as e:
            self._chat_log(f"{eng} ERROR: {e}",tag="sys")

    def _take_snap(self):
        try:
            self.root.after(0,lambda:self.root.attributes("-alpha",0.0)); time.sleep(0.15)
            snap=ImageGrab.grab(all_screens=True); self.snap_bank.append(snap)
            self.root.after(0,lambda:self.root.attributes("-alpha",1.0))
            self.root.after(0,lambda:self.snap_lbl.config(text=f"SNAPS:{len(self.snap_bank)}"))
            self._chat_log(f"SNAP #{len(self.snap_bank)} CAPTURED.",tag="sys",images=[snap])
        except Exception as e: self._chat_log(f"SNAP ERROR: {e}",tag="sys")

    def _process_batch(self):
        self.root.after(0,lambda:self.root.attributes("-alpha",0.0))
        time.sleep(0.15)
        final_img=ImageGrab.grab(all_screens=True)

        if self.model_mode!=0:
            self.snap_bank=[final_img]
            instr=("Solve the problem(s) shown in this image. Explain in simple steps a student can understand. "
                   "For each problem: 1. Write formula, 2. Show substitution, 3. Show calculation, "
                   "4. == Final Answer: [RESULT] ==. Keep explanations simple.")
        else:
            self.snap_bank.append(final_img)
            instr="Return the specific answer. FORMAT: == Final Answer: [RESULT] =="
            if self.is_ela_enabled: instr="Deep analysis. Format: == Final Answer: [RESULT] =="

        if not self.is_ghost: self.root.after(0,lambda:self.root.attributes("-alpha",1.0))
        if not self._check_engine_access(): return
        eng=self.model_names[self.model_mode]
        snaps=list(self.snap_bank)
        self.root.after(0,lambda:self._chat_log(f"BATCHING {len(snaps)} IMAGES (ENGINE: {eng})",tag="sys",images=snaps))
        content=[{"type":"text","text":instr}]
        for img in snaps:
            buf=io.BytesIO(); img.save(buf,format="JPEG",quality=90)
            content.append({"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"}})
        self.snap_bank=[]; self.root.after(0,lambda:self.snap_lbl.config(text="SNAPS:0") if hasattr(self,"snap_lbl") else None)
        threading.Thread(target=self._orchestrator,args=(content,),daemon=True).start()
    def _orchestrator(self,content):
        eng=self.model_names[self.model_mode]; ans=""
        try:
            if self.model_mode==0:
                res=requests.post("https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization":f"Bearer {self._current_groq_key()}"},
                    json={"model":LLAMA_MODEL,"messages":[{"role":"user","content":content}],"temperature":0.0},timeout=60)
                ans=res.json()['choices'][0]['message']['content'].strip()
            elif self.model_mode==1:
                key=self._current_openrouter_key()
                res=requests.post("https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
                    json={"model":XENO_MODEL,"messages":[{"role":"user","content":content}],"temperature":0.7},timeout=60)
                ans=res.json()['choices'][0]['message']['content'].strip()
            elif self.model_mode==2:
                key=self._current_gemini_key()
                parts=[{"text":content[0]["text"]}]
                for item in content[1:]:
                    b64=item["image_url"]["url"].split(",")[1]
                    parts.append({"inline_data":{"mime_type":"image/jpeg","data":b64}})
                res=requests.post(f"{GEMINI_URL}?key={key}",headers={"Content-Type":"application/json"},
                    json={"contents":[{"parts":parts}]},timeout=60)
                ans=res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            self.root.after(0,lambda a=ans:self._chat_log(f"{eng}: {a}"))
        except Exception as e:
            self.root.after(0,lambda:self._chat_log(f"{eng} BATCH ERROR: {e}",tag="sys"))

    def purge_chat(self):
        self.history=[]; self.snap_bank=[]
        try:
            self.chat.config(state="normal"); self.chat.delete("1.0",tk.END); self.chat.config(state="disabled")
            self._rainbow_intro(); self._chat_log("CORE PURGED.",tag="sys"); self.snap_lbl.config(text="SNAPS:0")
        except: pass

    def _cycle_engine_btn(self):
        self.model_mode=(self.model_mode+1)%3; name=self.model_names[self.model_mode]
        try: self.engine_lbl.config(text=f"ENGINE: {name}"); self.sidebar_engine.config(text=name)
        except: pass
        try: self._chat_log(f"ENGINE → {name}",tag="sys")
        except: pass

    def _cycle_text_color(self):
        self.color_idx=(self.color_idx+1)%len(self.ai_colors)
        try: self.chat.tag_config("ai_msg",foreground=self.ai_colors[self.color_idx])
        except: pass

    def _toggle_light_mode(self):
        self.is_light_mode=not self.is_light_mode
        palette=LIGHT if self.is_light_mode else DARK
        C.update(palette)
        try: self._chat_log(f"{'LIGHT' if self.is_light_mode else 'DARK'} MODE",tag="sys")
        except: pass
        # Rebuild the whole UI to apply new colours
        for w in self.root.winfo_children(): w.destroy()
        self._build_ui()

    def _toggle_ghost(self):
        self.is_ghost=not self.is_ghost
        self.root.after(0,lambda:self.root.attributes("-alpha",0.0 if self.is_ghost else 1.0))

    def _show_credits(self):
        art="""
╔══════════════════════════════════════════╗
║          C-MASTER  SYSTEMS  V14          ║
╠══════════════════════════════════════════╣
║  > LEAD DEV  :  C-Master                ║
║  > BUILD     :  HyperXeno V14.0         ║
║  > ENGINE    :  GROQ / XENO / GEMINI    ║
║  > STATUS    :  ELITE                   ║
╚══════════════════════════════════════════╝"""
        try: self._chat_log(art,tag="credits")
        except: pass

    def _logout(self):
        clear_session()
        for w in self.root.winfo_children(): w.destroy()
        AuthScreen(self.root, lambda s: self._restart_app(s))

    def _restart_app(self, session):
        for w in self.root.winfo_children(): w.destroy()
        HyperXeno(self.root, session)

    # ──────────────────────────────────────────────────────────────────────────
    #  SUBSCRIPTION TAB
    # ──────────────────────────────────────────────────────────────────────────
    def show_subscription(self):
        self._page_header("SUBSCRIPTION","PLANS")
        container=tk.Frame(self.main_frame,bg=C["panel"]); container.pack(fill="both",expand=True,padx=20,pady=10)

        tk.Label(container,text=f"Current Plan: {self.tier.upper()}",fg=C["accent4"],bg=C["panel"],
                 font=("Consolas",12,"bold")).pack(pady=(0,16))

        cards_row=tk.Frame(container,bg=C["panel"]); cards_row.pack(fill="both",expand=True)

        plans=[
            ("BASIC","Free",C["grey"],["✔ Groq AI (with your own key)","✔ All tools & games","✔ Notepad","✔ Snap & Batch","✘ Xeno AI","✘ Gemini AI"]),
            ("PRO","$4.99/mo",C["accent4"],["✔ Everything in Basic","✔ Xeno AI (OpenRouter)","✔ Enter Xeno API key","✔ Priority support","✘ Gemini AI"]),
            ("BUSINESS","$9.99/mo",C["accent2"],["✔ Everything in Pro","✔ Gemini AI","✔ All 3 AI engines","✔ Business badge","✔ Admin tools access"]),
        ]

        for pname,price,col,features in plans:
            is_current=(pname.lower()==self.tier)
            card=tk.Frame(cards_row,bg=C["sidebar"],bd=2,relief="flat",padx=16,pady=16)
            card.pack(side="left",fill="both",expand=True,padx=8)
            if is_current:
                tk.Frame(card,bg=col,height=3).pack(fill="x",pady=(0,10))

            tk.Label(card,text=pname,fg=col,bg=C["sidebar"],font=("Consolas",16,"bold")).pack()
            tk.Label(card,text=price,fg=C["white"],bg=C["sidebar"],font=("Consolas",12)).pack(pady=4)
            tk.Frame(card,bg=C["border"],height=1).pack(fill="x",pady=8)

            for feat in features:
                fc=C["accent3"] if feat.startswith("✔") else C["dimgrey"]
                tk.Label(card,text=feat,fg=fc,bg=C["sidebar"],font=("Consolas",9),anchor="w").pack(anchor="w",pady=2)

            tk.Frame(card,bg=C["sidebar"]).pack(expand=True)

            if is_current:
                tk.Label(card,text="✦ CURRENT PLAN",fg=col,bg=C["sidebar"],font=("Consolas",9,"bold")).pack(pady=8)
            else:
                btn_txt="DOWNGRADE" if (pname.lower()=="basic") else "UPGRADE"
                tk.Button(card,text=btn_txt,command=lambda p=pname.lower():self._handle_plan(p),
                          bg=col,fg="#000" if col in (C["accent4"],) else C["white"],relief="flat",
                          font=("Consolas",10,"bold"),cursor="hand2",pady=6).pack(fill="x",pady=8)

        # API key section for pro/business
        tk.Frame(container,bg=C["border"],height=1).pack(fill="x",pady=16)
        tk.Label(container,text="API KEY MANAGEMENT",fg=C["accent"],bg=C["panel"],font=("Consolas",11,"bold")).pack(anchor="w")
        kf=tk.Frame(container,bg=C["panel"]); kf.pack(fill="x",pady=8)

        def key_row(parent,label,val,key_name):
            row=tk.Frame(parent,bg=C["panel"]); row.pack(fill="x",pady=4)
            tk.Label(row,text=f"{label:12s}",fg=C["dimgrey"],bg=C["panel"],font=("Consolas",9),width=14).pack(side="left")
            e=tk.Entry(row,width=44,font=("Consolas",9),bg=C["border"],fg=C["accent"],relief="flat",
                       insertbackground=C["accent"],show="●" if val else ""); e.insert(0,val); e.pack(side="left",padx=6,ipady=4)
            def save_key(en=e,kn=key_name):
                setattr(self,kn,en.get().strip()); self.session[kn]=getattr(self,kn); save_session(self.session)
                messagebox.showinfo("Saved",f"{label} saved!")
            tk.Button(row,text="Save",command=save_key,bg=C["accent3"],fg="#000",relief="flat",font=("Consolas",8)).pack(side="left")

        key_row(kf,"Groq Key",self.groq_key,"groq_key")
        if self.tier in ("pro","business") or self.role in ("admin","co-admin"):
            key_row(kf,"Xeno Key",self.xeno_key,"xeno_key")
        if self.tier=="business" or self.role in ("admin","co-admin"):
            key_row(kf,"Gemini Key",self.gemini_key,"gemini_key")

    def _handle_plan(self,plan):
        if plan=="pro":
            msg=("PRO PLAN — $4.99/mo\n\nYou'll need an OpenRouter API key.\n"
                 "Get it free at: https://openrouter.ai\n\n"
                 "Enter your invite/payment code:")
            code=simpledialog.askstring("Pro Upgrade",msg,parent=self.root)
            if code:
                messagebox.showinfo("Upgrade","Contact C-Master with your code to activate Pro!")
        elif plan=="business":
            msg=("BUSINESS PLAN — $9.99/mo\n\nUnlocks all 3 AI engines.\n\nEnter your invite/payment code:")
            code=simpledialog.askstring("Business Upgrade",msg,parent=self.root)
            if code:
                messagebox.showinfo("Upgrade","Contact C-Master with your code to activate Business!")
        elif plan=="basic":
            if messagebox.askyesno("Downgrade","Downgrade to Basic (free)?"):
                self.tier="basic"; self.session["tier"]="basic"; save_session(self.session)
                self._nav_switch("Subscription")

    # ──────────────────────────────────────────────────────────────────────────
    #  ADMIN PANEL
    # ──────────────────────────────────────────────────────────────────────────
    def show_admin(self):
        if self.role not in ("admin","co-admin"):
            self._page_header("ACCESS DENIED"); return
        self._page_header("ADMIN TERMINAL",f"LOGGED IN AS {self.username.upper()}")

        # Tab bar
        tab_bar=tk.Frame(self.main_frame,bg=C["panel"]); tab_bar.pack(fill="x",padx=20,pady=4)
        self.admin_area=tk.Frame(self.main_frame,bg=C["panel"]); self.admin_area.pack(fill="both",expand=True,padx=20,pady=4)

        tabs=[("Users",self._admin_users),("Broadcast",self._admin_broadcast),
              ("Kill Switch",self._admin_killswitch),("Audit Log",self._admin_audit),
              ("Roles",self._admin_roles),("Payment Codes",self._admin_payments)]
        for tname,tcmd in tabs:
            col=C["accent2"] if tname=="Kill Switch" else C["accent"]
            tk.Button(tab_bar,text=tname,command=tcmd,bg=C["border"],fg=col,relief="flat",
                      font=("Consolas",9,"bold"),padx=10,pady=4,cursor="hand2",
                      activebackground=C["accent"],activeforeground="#000").pack(side="left",padx=2)

        self._admin_users()

    def _clear_admin(self):
        for w in self.admin_area.winfo_children(): w.destroy()

    def _auth_headers(self):
        return {"Authorization":f"Bearer {self.token}","Content-Type":"application/json"}

    def _admin_users(self):
        self._clear_admin()
        tk.Label(self.admin_area,text="USER MANAGER",fg=C["accent"],bg=C["panel"],font=("Consolas",12,"bold")).pack(anchor="w",pady=(0,8))
        tk.Button(self.admin_area,text="⟳ Refresh",command=self._admin_users,
                  bg=C["border"],fg=C["white"],relief="flat",font=("Consolas",8),cursor="hand2").pack(anchor="e",pady=(0,4))

        cols_frame=tk.Frame(self.admin_area,bg=C["border"]); cols_frame.pack(fill="x")
        for h,w in [("ID",4),("Username",16),("Role",10),("Tier",10),("Banned",6),("Joined",20),("Actions",20)]:
            tk.Label(cols_frame,text=h,fg=C["dimgrey"],bg=C["border"],font=("Consolas",8,"bold"),width=w,anchor="w").pack(side="left",padx=4)

        scroll_c=tk.Canvas(self.admin_area,bg=C["panel"],highlightthickness=0); scroll_c.pack(fill="both",expand=True)
        sb=tk.Scrollbar(self.admin_area,orient="vertical",command=scroll_c.yview); sb.pack(side="right",fill="y")
        scroll_c.configure(yscrollcommand=sb.set)
        rows_frame=tk.Frame(scroll_c,bg=C["panel"]); scroll_c.create_window((0,0),window=rows_frame,anchor="nw")
        rows_frame.bind("<Configure>",lambda e:scroll_c.configure(scrollregion=scroll_c.bbox("all")))

        def load():
            for w in rows_frame.winfo_children(): w.destroy()
            try:
                res=requests.get(f"{SERVER}/admin/users",headers=self._auth_headers(),timeout=10)
                users=res.json()
                if isinstance(users,list):
                    for u in users:
                        row=tk.Frame(rows_frame,bg=C["panel"]); row.pack(fill="x",pady=1)
                        ban_col=C["accent2"] if u.get("banned") else C["grey"]
                        for val,w in [(str(u.get("id","")),4),(u.get("username",""),16),(u.get("role","user"),10),(u.get("tier","basic"),10),("YES" if u.get("banned") else "NO",6),(str(u.get("joined",""))[:16],20)]:
                            tk.Label(row,text=val,fg=ban_col if val in ("YES","NO") else C["white"],
                                     bg=C["panel"],font=("Consolas",8),width=w,anchor="w").pack(side="left",padx=4)
                        af=tk.Frame(row,bg=C["panel"]); af.pack(side="left")
                        uname=u.get("username","")
                        ban_txt="UNBAN" if u.get("banned") else "BAN"
                        tk.Button(af,text=ban_txt,command=lambda un=uname,b=not u.get("banned"):self._admin_ban(un,b),
                                  bg=C["accent2"] if not u.get("banned") else C["accent3"],fg="#000",relief="flat",
                                  font=("Consolas",7),cursor="hand2",padx=4).pack(side="left",padx=2)
                        tk.Button(af,text="ROLE",command=lambda un=uname:self._admin_set_role_dialog(un),
                                  bg=C["accent4"],fg="#000",relief="flat",font=("Consolas",7),cursor="hand2",padx=4).pack(side="left",padx=2)
                        tk.Button(af,text="TIER",command=lambda un=uname:self._admin_set_tier_dialog(un),
                                  bg=C["accent5"],fg=C["white"],relief="flat",font=("Consolas",7),cursor="hand2",padx=4).pack(side="left",padx=2)
                else:
                    tk.Label(rows_frame,text=str(users),fg=C["accent2"],bg=C["panel"],font=("Consolas",9)).pack()
            except Exception as e:
                tk.Label(rows_frame,text=f"Error: {e}",fg=C["accent2"],bg=C["panel"],font=("Consolas",9)).pack()
        threading.Thread(target=load,daemon=True).start()

    def _admin_ban(self,username,ban):
        def do():
            try:
                res=requests.post(f"{SERVER}/admin/ban",headers=self._auth_headers(),
                    json={"username":username,"banned":ban},timeout=10)
                self.root.after(0,lambda:messagebox.showinfo("Done",f"{'Banned' if ban else 'Unbanned'}: {username}"))
                self.root.after(100,self._admin_users)
            except Exception as e:
                self.root.after(0,lambda:messagebox.showerror("Error",str(e)))
        threading.Thread(target=do,daemon=True).start()

    def _admin_set_role_dialog(self,username):
        role=simpledialog.askstring("Set Role",f"Role for {username}:\n(user / moderator / co-admin / admin)",parent=self.root)
        if role and role in ("user","moderator","co-admin","admin"):
            def do():
                try:
                    requests.post(f"{SERVER}/admin/set_role",headers=self._auth_headers(),
                        json={"username":username,"role":role},timeout=10)
                    self.root.after(0,lambda:self._admin_users())
                except Exception as e:
                    self.root.after(0,lambda:messagebox.showerror("Error",str(e)))
            threading.Thread(target=do,daemon=True).start()

    def _admin_set_tier_dialog(self,username):
        tier=simpledialog.askstring("Set Tier",f"Tier for {username}:\n(basic / pro / business)",parent=self.root)
        if tier and tier in ("basic","pro","business"):
            def do():
                try:
                    requests.post(f"{SERVER}/admin/set_tier",headers=self._auth_headers(),
                        json={"username":username,"tier":tier},timeout=10)
                    self.root.after(0,lambda:self._admin_users())
                except Exception as e:
                    self.root.after(0,lambda:messagebox.showerror("Error",str(e)))
            threading.Thread(target=do,daemon=True).start()

    def _admin_broadcast(self):
        self._clear_admin()
        tk.Label(self.admin_area,text="BROADCAST MESSAGE",fg=C["accent"],bg=C["panel"],font=("Consolas",12,"bold")).pack(anchor="w",pady=(0,8))
        tk.Label(self.admin_area,text="Send a system message to ALL connected users:",fg=C["grey"],bg=C["panel"],font=("Consolas",9)).pack(anchor="w")
        txt=scrolledtext.ScrolledText(self.admin_area,height=6,bg=C["border"],fg=C["white"],font=("Consolas",10),relief="flat"); txt.pack(fill="x",pady=8)
        res_lbl=tk.Label(self.admin_area,text="",fg=C["accent3"],bg=C["panel"],font=("Consolas",9)); res_lbl.pack()
        def send():
            msg=txt.get("1.0","end-1c").strip()
            if not msg: return
            def do():
                try:
                    r=requests.post(f"{SERVER}/admin/broadcast",headers=self._auth_headers(),json={"message":msg},timeout=10)
                    self.root.after(0,lambda:res_lbl.config(text="✔ Broadcast sent!",fg=C["accent3"]))
                except Exception as e:
                    self.root.after(0,lambda:res_lbl.config(text=f"Error: {e}",fg=C["accent2"]))
            threading.Thread(target=do,daemon=True).start()
        tk.Button(self.admin_area,text="SEND BROADCAST",command=send,bg=C["accent4"],fg="#000",
                  relief="flat",font=("Consolas",11,"bold"),cursor="hand2").pack(pady=4)

    def _admin_killswitch(self):
        self._clear_admin()
        tk.Label(self.admin_area,text="⚠ GLOBAL KILL SWITCH",fg=C["accent2"],bg=C["panel"],font=("Consolas",14,"bold")).pack(pady=(10,6))
        tk.Label(self.admin_area,text="Maintenance mode disconnects all users and shows\na maintenance screen on every client.",
                 fg=C["grey"],bg=C["panel"],font=("Consolas",10),justify="left").pack(anchor="w",padx=20)
        tk.Frame(self.admin_area,bg=C["border"],height=1).pack(fill="x",padx=20,pady=12)
        fr=tk.Frame(self.admin_area,bg=C["panel"]); fr.pack()
        status_lbl=tk.Label(fr,text="Checking...",fg=C["accent4"],bg=C["panel"],font=("Consolas",11,"bold")); status_lbl.pack(pady=8)
        msg_entry=tk.Entry(self.admin_area,width=50,font=("Consolas",10),bg=C["border"],fg=C["white"],
                           relief="flat",insertbackground=C["white"])
        msg_entry.insert(0,"Back soon! We're updating HyperXeno.")
        msg_entry.pack(pady=6,ipady=6)
        tk.Label(self.admin_area,text="Custom maintenance message (shown to users)",fg=C["dimgrey"],bg=C["panel"],font=("Consolas",8)).pack()
        def toggle_maintenance(activate):
            def do():
                try:
                    requests.post(f"{SERVER}/admin/maintenance",headers=self._auth_headers(),
                        json={"active":activate,"message":msg_entry.get()},timeout=10)
                    self.root.after(0,lambda:status_lbl.config(
                        text="🔴 MAINTENANCE ON" if activate else "🟢 MAINTENANCE OFF",
                        fg=C["accent2"] if activate else C["accent3"]))
                except Exception as e:
                    self.root.after(0,lambda:status_lbl.config(text=f"Error: {e}",fg=C["accent2"]))
            threading.Thread(target=do,daemon=True).start()
        def check_status():
            try:
                r=requests.get(f"{SERVER}/status",timeout=6)
                d=r.json()
                active=d.get("maintenance",False)
                self.root.after(0,lambda:status_lbl.config(
                    text="🔴 MAINTENANCE ON" if active else "🟢 MAINTENANCE OFF",
                    fg=C["accent2"] if active else C["accent3"]))
            except: pass
        threading.Thread(target=check_status,daemon=True).start()
        bf=tk.Frame(self.admin_area,bg=C["panel"]); bf.pack(pady=14)
        tk.Button(bf,text="🔴  ENABLE MAINTENANCE",command=lambda:toggle_maintenance(True),
                  bg=C["accent2"],fg=C["white"],relief="flat",font=("Consolas",11,"bold"),cursor="hand2",padx=12,pady=8).pack(side="left",padx=8)
        tk.Button(bf,text="🟢  DISABLE MAINTENANCE",command=lambda:toggle_maintenance(False),
                  bg=C["accent3"],fg="#000",relief="flat",font=("Consolas",11,"bold"),cursor="hand2",padx=12,pady=8).pack(side="left",padx=8)
        tk.Frame(self.admin_area,bg=C["border"],height=1).pack(fill="x",padx=20,pady=12)
        tk.Label(self.admin_area,text="Force shutdown HyperXeno server process:",fg=C["grey"],bg=C["panel"],font=("Consolas",9)).pack()
        tk.Button(self.admin_area,text="⚡ FORCE SHUTDOWN SERVER",
                  command=lambda:self._admin_force_shutdown(),
                  bg="#440000",fg=C["accent2"],relief="flat",font=("Consolas",10,"bold"),cursor="hand2",pady=6).pack(pady=6)

    def _admin_force_shutdown(self):
        if messagebox.askyesno("Confirm","Force shutdown the server? All users will be disconnected immediately."):
            def do():
                try: requests.post(f"{SERVER}/admin/shutdown",headers=self._auth_headers(),timeout=5)
                except: pass
            threading.Thread(target=do,daemon=True).start()

    def _admin_audit(self):
        self._clear_admin()
        tk.Label(self.admin_area,text="AUDIT LOG",fg=C["accent"],bg=C["panel"],font=("Consolas",12,"bold")).pack(anchor="w",pady=(0,8))
        term=scrolledtext.ScrolledText(self.admin_area,bg="#000000",fg=C["accent3"],font=("Consolas",9),relief="flat")
        term.pack(fill="both",expand=True)
        def load():
            try:
                res=requests.get(f"{SERVER}/admin/audit",headers=self._auth_headers(),timeout=10)
                logs=res.json()
                self.root.after(0,lambda:term.config(state="normal"))
                if isinstance(logs,list):
                    for entry in logs:
                        line=f"[{entry.get('timestamp','')}] {entry.get('admin','')} → {entry.get('action','')}\n"
                        self.root.after(0,lambda l=line:term.insert(tk.END,l))
                self.root.after(0,lambda:term.config(state="disabled"))
            except Exception as e:
                self.root.after(0,lambda:term.insert(tk.END,f"Error: {e}\n"))
        threading.Thread(target=load,daemon=True).start()
        tk.Button(self.admin_area,text="⟳ Refresh",command=self._admin_audit,
                  bg=C["border"],fg=C["white"],relief="flat",font=("Consolas",8)).pack(pady=4)

    def _admin_roles(self):
        self._clear_admin()
        tk.Label(self.admin_area,text="ROLE MANAGER",fg=C["accent"],bg=C["panel"],font=("Consolas",12,"bold")).pack(anchor="w",pady=(0,8))
        tk.Label(self.admin_area,text="Roles: user  │  moderator  │  co-admin  │  admin",fg=C["grey"],bg=C["panel"],font=("Consolas",9)).pack(anchor="w",pady=4)
        fr=tk.Frame(self.admin_area,bg=C["panel"]); fr.pack(anchor="w",pady=8)
        tk.Label(fr,text="Username:",fg=C["grey"],bg=C["panel"],font=("Consolas",10)).pack(side="left")
        ue=tk.Entry(fr,width=20,bg=C["border"],fg=C["white"],font=("Consolas",10),relief="flat",insertbackground=C["white"]);ue.pack(side="left",padx=6,ipady=4)
        tk.Label(fr,text="Role:",fg=C["grey"],bg=C["panel"],font=("Consolas",10)).pack(side="left")
        rv=tk.StringVar(value="user")
        tk.OptionMenu(fr,rv,"user","moderator","co-admin","admin").pack(side="left",padx=6)
        res_lbl=tk.Label(self.admin_area,text="",fg=C["accent3"],bg=C["panel"],font=("Consolas",9)); res_lbl.pack()
        def apply():
            un=ue.get().strip()
            if not un: return
            def do():
                try:
                    requests.post(f"{SERVER}/admin/set_role",headers=self._auth_headers(),
                        json={"username":un,"role":rv.get()},timeout=10)
                    self.root.after(0,lambda:res_lbl.config(text=f"✔ {un} → {rv.get()}",fg=C["accent3"]))
                except Exception as e:
                    self.root.after(0,lambda:res_lbl.config(text=f"Error: {e}",fg=C["accent2"]))
            threading.Thread(target=do,daemon=True).start()
        tk.Button(self.admin_area,text="APPLY ROLE",command=apply,bg=C["accent"],fg="#000",relief="flat",
                  font=("Consolas",10,"bold"),cursor="hand2").pack(anchor="w",pady=6)

    def _admin_payments(self):
        self._clear_admin()
        tk.Label(self.admin_area,text="PAYMENT / INVITE CODES",fg=C["accent"],bg=C["panel"],font=("Consolas",12,"bold")).pack(anchor="w",pady=(0,8))
        tk.Label(self.admin_area,text="Generate codes to give users Pro or Business access:",fg=C["grey"],bg=C["panel"],font=("Consolas",9)).pack(anchor="w",pady=4)
        fr=tk.Frame(self.admin_area,bg=C["panel"]); fr.pack(anchor="w",pady=8)
        tk.Label(fr,text="Username:",fg=C["grey"],bg=C["panel"],font=("Consolas",10)).pack(side="left")
        ue=tk.Entry(fr,width=18,bg=C["border"],fg=C["white"],font=("Consolas",10),relief="flat",insertbackground=C["white"]); ue.pack(side="left",padx=6,ipady=4)
        tk.Label(fr,text="Tier:",fg=C["grey"],bg=C["panel"],font=("Consolas",10)).pack(side="left")
        tv=tk.StringVar(value="pro")
        tk.OptionMenu(fr,tv,"pro","business").pack(side="left",padx=6)
        out_lbl=tk.Label(self.admin_area,text="",fg=C["accent4"],bg=C["panel"],font=("Consolas",11,"bold")); out_lbl.pack(pady=6)
        res_lbl=tk.Label(self.admin_area,text="",fg=C["accent3"],bg=C["panel"],font=("Consolas",9)); res_lbl.pack()
        def grant():
            un=ue.get().strip()
            if not un: return
            code="XN-"+"".join(random.choices(string.ascii_uppercase+string.digits,k=10))
            out_lbl.config(text=f"Code: {code}")
            def do():
                try:
                    requests.post(f"{SERVER}/admin/set_tier",headers=self._auth_headers(),
                        json={"username":un,"tier":tv.get(),"code":code},timeout=10)
                    self.root.after(0,lambda:res_lbl.config(text=f"✔ {un} upgraded to {tv.get()}",fg=C["accent3"]))
                except Exception as e:
                    self.root.after(0,lambda:res_lbl.config(text=f"Error: {e}",fg=C["accent2"]))
            threading.Thread(target=do,daemon=True).start()
        tk.Button(self.admin_area,text="GRANT TIER + GENERATE CODE",command=grant,
                  bg=C["accent4"],fg="#000",relief="flat",font=("Consolas",10,"bold"),cursor="hand2").pack(anchor="w",pady=6)

    # ──────────────────────────────────────────────────────────────────────────
    #  NOTEPAD  (unchanged from before)
    # ──────────────────────────────────────────────────────────────────────────
    def show_notepad(self):
        self._page_header("NOTEPAD","EDITOR")
        tb=tk.Frame(self.main_frame,bg=C["panel"],pady=4); tb.pack(fill="x",padx=20)
        def tb_btn(text,cmd,col=C["dimgrey"]):
            tk.Button(tb,text=text,command=cmd,bg=C["border"],fg=col,relief="flat",font=("Consolas",8),bd=0,padx=6,pady=3,activebackground="#333",cursor="hand2").pack(side="left",padx=2)
        tb_btn("New",self.notepad_new); tb_btn("Open",self.open_file); tb_btn("Save",self.save_file,C["accent3"])
        tb_btn("Save As",self.save_file_as); tb_btn("|",lambda:None,C["border"])
        tb_btn("Undo",self.notepad_undo); tb_btn("Redo",self.notepad_redo)
        tb_btn("Cut",lambda:self.notepad_event("<<Cut>>")); tb_btn("Copy",lambda:self.notepad_event("<<Copy>>"))
        tb_btn("Paste",lambda:self.notepad_event("<<Paste>>")); tb_btn("|",lambda:None,C["border"])
        tb_btn("Find",self.notepad_find); tb_btn("Replace",self.notepad_replace); tb_btn("Go To",self.notepad_goto)
        tb_btn("A+",self.notepad_font_larger); tb_btn("A-",self.notepad_font_smaller)
        tb_btn("Time/Date",self.notepad_insert_time_date); tb_btn("Recent",self.notepad_open_recent_dialog)
        tg=tk.Frame(self.main_frame,bg=C["panel"]); tg.pack(fill="x",padx=20,pady=2)
        def make_chk(parent,text,var,cmd):
            tk.Checkbutton(parent,text=text,variable=var,command=cmd,bg=C["panel"],fg=C["grey"],selectcolor=C["border"],activebackground=C["panel"],font=("Consolas",8)).pack(side="left",padx=6)
        make_chk(tg,"Word Wrap",self.word_wrap,self.notepad_update_wrap)
        make_chk(tg,"Line #s",self.show_line_numbers,self.notepad_toggle_line_numbers)
        make_chk(tg,"Dark Mode",self.notepad_dark_mode,self.notepad_update_theme)
        make_chk(tg,"Read Only",self.notepad_read_only,self.notepad_update_read_only)
        make_chk(tg,"Auto Save",self.notepad_autosave,self.notepad_toggle_autosave)
        tk.Frame(self.main_frame,bg=C["border"],height=1).pack(fill="x",padx=20,pady=2)
        body=tk.Frame(self.main_frame,bg=C["panel"]); body.pack(fill="both",expand=True,padx=20,pady=4)
        self.line_numbers=tk.Text(body,width=4,padx=4,takefocus=0,border=0,background=C["border"],state="disabled",font=("Consolas",self.notepad_font_size),fg=C["dimgrey"])
        self.line_numbers.pack(side="left",fill="y")
        self.text_area=tk.Text(body,undo=True,font=("Consolas",self.notepad_font_size),relief="flat",borderwidth=0,wrap="word" if self.word_wrap.get() else "none",insertbackground=C["white"])
        self.text_area.pack(side="right",fill="both",expand=True)
        self.text_area.bind("<KeyRelease>",self.notepad_on_change)
        self.text_area.bind("<ButtonRelease-1>",self.notepad_on_change)
        self.text_area.bind("<KeyPress>",self.notepad_on_keypress)
        self.status_note=tk.Label(self.main_frame,text="Ln 1, Col 1 | 0 chars",anchor="w",bg=C["border"],fg=C["grey"],font=("Consolas",8))
        self.status_note.pack(side="bottom",fill="x")
        self.notepad_update_theme(); self.notepad_toggle_line_numbers(); self.notepad_start_autosave_loop()

    def notepad_event(self,seq):
        if hasattr(self,"text_area"): self.text_area.event_generate(seq)
    def notepad_new(self):
        if hasattr(self,"text_area"): self.text_area.delete(1.0,tk.END); self.current_file_path=None; self._update_title()
    def notepad_undo(self):
        try: self.text_area.edit_undo()
        except: pass
    def notepad_redo(self):
        try: self.text_area.edit_redo()
        except: pass
    def notepad_find(self):
        q=simpledialog.askstring("Find","Text to find:",parent=self.root)
        if not q: return
        self.text_area.tag_remove("find_match","1.0",tk.END); s="1.0"
        while True:
            pos=self.text_area.search(q,s,stopindex=tk.END)
            if not pos: break
            end=f"{pos}+{len(q)}c"; self.text_area.tag_add("find_match",pos,end); s=end
        self.text_area.tag_config("find_match",background=C["accent4"],foreground="#000")
    def notepad_replace(self):
        q=simpledialog.askstring("Replace","Find:",parent=self.root)
        if q is None: return
        r=simpledialog.askstring("Replace","Replace with:",parent=self.root)
        if r is None: return
        content=self.text_area.get("1.0",tk.END); self.text_area.delete("1.0",tk.END); self.text_area.insert("1.0",content.replace(q,r))
    def notepad_goto(self):
        ls=simpledialog.askstring("Go To","Line number:",parent=self.root)
        if not ls: return
        try: ln=int(ls); self.text_area.mark_set("insert",f"{ln}.0"); self.text_area.see(f"{ln}.0")
        except: messagebox.showerror("Error","Invalid line number")
    def notepad_update_wrap(self):
        if hasattr(self,"text_area"): self.text_area.config(wrap="word" if self.word_wrap.get() else "none")
    def notepad_toggle_line_numbers(self):
        if not hasattr(self,"line_numbers"): return
        if self.show_line_numbers.get(): self.line_numbers.pack(side="left",fill="y"); self._update_line_numbers()
        else: self.line_numbers.pack_forget()
    def _update_line_numbers(self):
        if not self.show_line_numbers.get(): return
        self.line_numbers.config(state="normal"); self.line_numbers.delete("1.0",tk.END)
        lines=self.text_area.get("1.0",tk.END).count("\n")+1
        self.line_numbers.insert("1.0","\n".join(str(i) for i in range(1,lines+1))); self.line_numbers.config(state="disabled")
    def notepad_font_larger(self):
        self.notepad_font_size+=1
        if hasattr(self,"text_area"): self.text_area.config(font=("Consolas",self.notepad_font_size))
    def notepad_font_smaller(self):
        if self.notepad_font_size>6: self.notepad_font_size-=1
        if hasattr(self,"text_area"): self.text_area.config(font=("Consolas",self.notepad_font_size))
    def notepad_update_theme(self):
        if not hasattr(self,"text_area"): return
        if self.notepad_dark_mode.get(): fg,bg,ln_bg="#FFFFFF","#1A1A1A",C["border"]
        else: fg,bg,ln_bg="#000000","#FFFFFF","#F0F0F0"
        self.text_area.config(fg=fg,bg=bg,insertbackground=fg)
        if hasattr(self,"line_numbers"): self.line_numbers.config(bg=ln_bg,fg=C["dimgrey"])
    def notepad_insert_time_date(self): self.text_area.insert(tk.INSERT,datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    def notepad_update_read_only(self):
        if hasattr(self,"text_area"): self.text_area.config(state="disabled" if self.notepad_read_only.get() else "normal")
    def notepad_on_change(self,e=None): self._update_line_numbers(); self._update_status_note()
    def _update_status_note(self):
        if not hasattr(self,"status_note") or not hasattr(self,"text_area"): return
        pos=self.text_area.index(tk.INSERT); ln,col=pos.split(".")
        self.status_note.config(text=f"Ln {ln}, Col {int(col)+1} | {len(self.text_area.get('1.0','end-1c'))} chars")
    def notepad_on_keypress(self,e):
        if self.notepad_read_only.get(): return "break"
    def notepad_toggle_autosave(self): pass
    def notepad_start_autosave_loop(self):
        def loop():
            if self.notepad_autosave.get() and self.current_file_path:
                try:
                    with open(self.current_file_path,"w",encoding="utf-8") as f: f.write(self.text_area.get("1.0","end-1c"))
                except: pass
            self.root.after(5000,loop)
        self.root.after(5000,loop)
    def notepad_open_recent_dialog(self):
        if not self.recent_files: messagebox.showinfo("Recent","No recent files."); return
        w=tk.Toplevel(self.root); w.title("Recent Files"); w.geometry("400x250"); w.configure(bg=C["panel"]); w.attributes("-topmost",True)
        lb=tk.Listbox(w,bg=C["border"],fg=C["white"],font=("Consolas",10)); lb.pack(fill="both",expand=True,padx=10,pady=10)
        for p in self.recent_files[-10:][::-1]: lb.insert(tk.END,p)
        def open_sel():
            sel=lb.curselection()
            if sel: w.destroy(); self.open_specific_file(lb.get(sel[0]))
        tk.Button(w,text="Open",command=open_sel,bg=C["accent"],fg="#000",relief="flat").pack(pady=5)
    def _update_title(self):
        self.root.title(f"HYPER XENO V14.0 — {self.username}" if not self.current_file_path else f"HYPER XENO — {os.path.basename(self.current_file_path)}")
    def open_specific_file(self,path):
        try:
            with open(path,"r",encoding="utf-8") as f: data=f.read()
            self.text_area.delete(1.0,tk.END); self.text_area.insert(1.0,data)
            self.current_file_path=path
            if path not in self.recent_files: self.recent_files.append(path)
            self._update_title()
        except Exception as e: messagebox.showerror("Error",str(e))
    def open_file(self):
        p=filedialog.askopenfilename()
        if p: self.open_specific_file(p)
    def save_file(self):
        if not self.current_file_path: self.save_file_as(); return
        try:
            with open(self.current_file_path,"w",encoding="utf-8") as f: f.write(self.text_area.get(1.0,tk.END))
        except Exception as e: messagebox.showerror("Error",str(e))
    def save_file_as(self):
        p=filedialog.asksaveasfilename(defaultextension=".txt")
        if p:
            try:
                with open(p,"w",encoding="utf-8") as f: f.write(self.text_area.get(1.0,tk.END))
                self.current_file_path=p
                if p not in self.recent_files: self.recent_files.append(p)
                self._update_title()
            except Exception as e: messagebox.showerror("Error",str(e))

    # ──────────────────────────────────────────────────────────────────────────
    #  TOOLS (unchanged)
    # ──────────────────────────────────────────────────────────────────────────
    def show_tools(self):
        self._page_header("TOOLS","MINI APPS")
        cont=tk.Frame(self.main_frame,bg=C["panel"]); cont.pack(fill="both",expand=True,padx=20,pady=8)
        left=tk.Frame(cont,bg=C["sidebar"],width=180); left.pack(side="left",fill="y"); left.pack_propagate(False)
        tk.Label(left,text="SELECT TOOL",fg=C["dimgrey"],bg=C["sidebar"],font=("Consolas",8)).pack(pady=(14,6))
        self.tool_area=tk.Frame(cont,bg=C["panel"]); self.tool_area.pack(side="right",fill="both",expand=True,padx=12)
        tools=[("Standard Calc",self.tool_standard_calculator),("Scientific Calc",self.tool_scientific_calculator),
               ("Text Counter",self.tool_text_counter),("Password Gen",self.tool_password_generator),
               ("Unit Converter",self.tool_unit_converter),("Random Number",self.tool_random_number),
               ("Stopwatch",self.tool_stopwatch),("Coin Flip",self.tool_coin_flip),
               ("Dice Roller",self.tool_dice_roller),("Note Snippets",self.tool_snippets),
               ("Base64",self.tool_base64_encode),("Hash Gen",self.tool_hash_gen)]
        for name,cmd in tools:
            tk.Button(left,text=name,command=cmd,bg=C["border"],fg=C["white"],relief="flat",font=("Consolas",9),bd=0,pady=8,anchor="w",padx=10,activebackground=C["accent"],activeforeground="#000",cursor="hand2").pack(fill="x",pady=1)
        self.tool_standard_calculator()

    def _clear_tool(self):
        for w in self.tool_area.winfo_children(): w.destroy()
    def _tool_header(self,text):
        tk.Label(self.tool_area,text=text,fg=C["accent"],bg=C["panel"],font=("Consolas",13,"bold")).pack(pady=(10,6))
        tk.Frame(self.tool_area,bg=C["border"],height=1).pack(fill="x",padx=10,pady=4)

    def tool_standard_calculator(self):
        self._clear_tool(); self._tool_header("STANDARD CALCULATOR")
        entry=tk.Entry(self.tool_area,font=("Consolas",18),justify="right",width=22,bg=C["border"],fg=C["white"],insertbackground=C["white"],relief="flat"); entry.pack(pady=8,padx=20)
        fr=tk.Frame(self.tool_area,bg=C["panel"]); fr.pack()
        btns=["7","8","9","/","4","5","6","*","1","2","3","-","0",".","C","+"]
        def on_click(ch):
            if ch=="C": entry.delete(0,tk.END)
            else: entry.insert(tk.END,ch)
        def calc():
            try: r=eval(entry.get()); entry.delete(0,tk.END); entry.insert(0,str(r))
            except: entry.delete(0,tk.END); entry.insert(0,"Error")
        r=c=0
        for b in btns:
            tk.Button(fr,text=b,width=5,height=2,command=lambda ch=b:on_click(ch),bg=C["border"],fg=C["white"],relief="flat",activebackground=C["accent"],activeforeground="#000").grid(row=r,column=c,padx=2,pady=2)
            c+=1
            if c>3: c=0; r+=1
        tk.Button(fr,text="=",width=24,height=2,command=calc,bg=C["accent"],fg="#000",relief="flat",font=("Consolas",11,"bold")).grid(row=r,column=0,columnspan=4,pady=6)

    def tool_scientific_calculator(self):
        self._clear_tool(); self._tool_header("SCIENTIFIC CALCULATOR")
        entry=tk.Entry(self.tool_area,font=("Consolas",16),justify="right",width=26,bg=C["border"],fg=C["white"],insertbackground=C["white"],relief="flat"); entry.pack(pady=8,padx=20)
        fr=tk.Frame(self.tool_area,bg=C["panel"]); fr.pack()
        basic=["7","8","9","/","C","4","5","6","*","(","1","2","3","-",")",  "0",".","+","^","pi"]
        def insert(t): entry.insert(tk.END,t)
        def clear(): entry.delete(0,tk.END)
        def calc():
            expr=entry.get().replace("^","**").replace("pi",str(math.pi))
            try:
                r=eval(expr,{"__builtins__":None},{"sin":math.sin,"cos":math.cos,"tan":math.tan,"log":math.log10,"ln":math.log,"sqrt":math.sqrt,"pi":math.pi,"e":math.e})
                entry.delete(0,tk.END); entry.insert(0,str(r))
            except: entry.delete(0,tk.END); entry.insert(0,"Error")
        r2=c2=0
        for b in basic:
            cmd=clear if b=="C" else (lambda ch=b:insert(ch))
            tk.Button(fr,text=b,width=5,height=2,command=cmd,bg=C["border"],fg=C["white"],relief="flat",activebackground=C["accent"],activeforeground="#000").grid(row=r2,column=c2,padx=2,pady=2)
            c2+=1
            if c2>4: c2=0; r2+=1
        ff=tk.Frame(self.tool_area,bg=C["panel"]); ff.pack(pady=4)
        for lbl,fn in [("sin","sin"),("cos","cos"),("tan","tan"),("log","log"),("ln","ln"),("√","sqrt")]:
            tk.Button(ff,text=lbl,width=7,command=lambda f=fn:insert(f+"("),bg=C["border"],fg=C["accent"],relief="flat").pack(side="left",padx=3)
        tk.Button(self.tool_area,text="=",width=32,height=2,command=calc,bg=C["accent"],fg="#000",font=("Consolas",11,"bold"),relief="flat").pack(pady=8)

    def tool_text_counter(self):
        self._clear_tool(); self._tool_header("TEXT COUNTER")
        txt=scrolledtext.ScrolledText(self.tool_area,width=60,height=12,bg=C["border"],fg=C["white"],font=("Consolas",10),relief="flat"); txt.pack(padx=20,pady=6)
        info=tk.Label(self.tool_area,text="Chars: 0 | Words: 0 | Lines: 0",fg=C["accent"],bg=C["panel"],font=("Consolas",10)); info.pack(pady=4)
        def update(e=None):
            c=txt.get("1.0","end-1c"); info.config(text=f"Chars: {len(c)} | Words: {len(c.split())} | Lines: {c.count(chr(10))+1 if c else 0}")
        txt.bind("<KeyRelease>",update)

    def tool_password_generator(self):
        self._clear_tool(); self._tool_header("PASSWORD GENERATOR")
        fr=tk.Frame(self.tool_area,bg=C["panel"]); fr.pack(pady=10)
        tk.Label(fr,text="Length:",bg=C["panel"],fg=C["grey"],font=("Consolas",10)).grid(row=0,column=0,sticky="w")
        lv=tk.IntVar(value=16); tk.Spinbox(fr,from_=4,to=64,textvariable=lv,width=5,bg=C["border"],fg=C["white"],relief="flat").grid(row=0,column=1,padx=6)
        uu=tk.BooleanVar(value=True); ul=tk.BooleanVar(value=True); ud=tk.BooleanVar(value=True); us=tk.BooleanVar(value=True)
        for row,(text,var) in enumerate([(("Uppercase",uu),("Lowercase",ul)),(("Digits",ud),("Symbols",us))],start=1):
            for col,(t,v) in enumerate(text):
                tk.Checkbutton(fr,text=t,variable=v,bg=C["panel"],fg=C["grey"],selectcolor=C["border"],activebackground=C["panel"]).grid(row=row,column=col,sticky="w")
        out=tk.Entry(self.tool_area,font=("Consolas",13),width=32,justify="center",bg=C["border"],fg=C["accent"],relief="flat"); out.pack(pady=10)
        def gen():
            pool=""
            if uu.get(): pool+=string.ascii_uppercase
            if ul.get(): pool+=string.ascii_lowercase
            if ud.get(): pool+=string.digits
            if us.get(): pool+="!@#$%^&*()-_=+[]{};:,.<>/?"
            if not pool: messagebox.showerror("Error","Pick at least one type."); return
            out.delete(0,tk.END); out.insert(0,"".join(random.choice(pool) for _ in range(lv.get())))
        tk.Button(self.tool_area,text="GENERATE",command=gen,bg=C["accent"],fg="#000",relief="flat",font=("Consolas",11,"bold")).pack(pady=6)

    def tool_unit_converter(self):
        self._clear_tool(); self._tool_header("UNIT CONVERTER")
        cats={"Length":{"m":1,"km":0.001,"cm":100,"mm":1000,"mile":0.000621371,"ft":3.28084,"in":39.3701},"Weight":{"kg":1,"g":1000,"lb":2.20462,"oz":35.274},"Temp":{"C":None,"F":None,"K":None}}
        fr=tk.Frame(self.tool_area,bg=C["panel"]); fr.pack(pady=10)
        cat_v=tk.StringVar(value="Length"); cat_menu=tk.OptionMenu(fr,cat_v,*cats.keys()); cat_menu.config(bg=C["border"],fg=C["white"],relief="flat",highlightthickness=0)
        tk.Label(fr,text="Category:",bg=C["panel"],fg=C["grey"],font=("Consolas",10)).grid(row=0,column=0,sticky="w",pady=4); cat_menu.grid(row=0,column=1,padx=6)
        val_e=tk.Entry(fr,width=14,bg=C["border"],fg=C["white"],relief="flat",insertbackground=C["white"])
        tk.Label(fr,text="Value:",bg=C["panel"],fg=C["grey"],font=("Consolas",10)).grid(row=1,column=0,sticky="w",pady=4); val_e.grid(row=1,column=1,padx=6)
        from_v=tk.StringVar(); to_v=tk.StringVar()
        from_m=tk.OptionMenu(fr,from_v,"m"); from_m.config(bg=C["border"],fg=C["white"],relief="flat",highlightthickness=0)
        to_m=tk.OptionMenu(fr,to_v,"m"); to_m.config(bg=C["border"],fg=C["white"],relief="flat",highlightthickness=0)
        tk.Label(fr,text="From:",bg=C["panel"],fg=C["grey"],font=("Consolas",10)).grid(row=2,column=0,sticky="w"); from_m.grid(row=2,column=1,padx=6)
        tk.Label(fr,text="To:",bg=C["panel"],fg=C["grey"],font=("Consolas",10)).grid(row=3,column=0,sticky="w"); to_m.grid(row=3,column=1,padx=6)
        result_lbl=tk.Label(self.tool_area,text="Result: —",fg=C["accent"],bg=C["panel"],font=("Consolas",12)); result_lbl.pack(pady=8)
        def update_menus(*a):
            units=list(cats[cat_v.get()].keys())
            for menu,sv in [(from_m,from_v),(to_m,to_v)]:
                menu["menu"].delete(0,"end")
                for u in units: menu["menu"].add_command(label=u,command=tk._setit(sv,u))
            from_v.set(units[0]); to_v.set(units[1])
        cat_v.trace("w",update_menus); update_menus()
        def convert():
            try:
                v=float(val_e.get()); cat=cat_v.get(); f=from_v.get(); t=to_v.get()
                if cat=="Temp":
                    r={"C-F":v*9/5+32,"C-K":v+273.15,"F-C":(v-32)*5/9,"F-K":(v-32)*5/9+273.15,"K-C":v-273.15,"K-F":(v-273.15)*9/5+32}.get(f+"-"+t,v)
                else: r=v/cats[cat][f]*cats[cat][t]
                result_lbl.config(text=f"Result: {r:.6g} {t}")
            except: result_lbl.config(text="Invalid")
        tk.Button(self.tool_area,text="CONVERT",command=convert,bg=C["accent"],fg="#000",relief="flat",font=("Consolas",11,"bold")).pack(pady=4)

    def tool_random_number(self):
        self._clear_tool(); self._tool_header("RANDOM NUMBER")
        fr=tk.Frame(self.tool_area,bg=C["panel"]); fr.pack(pady=10)
        mn=tk.IntVar(value=1); mx=tk.IntVar(value=100)
        tk.Label(fr,text="Min:",bg=C["panel"],fg=C["grey"],font=("Consolas",10)).grid(row=0,column=0,sticky="w")
        tk.Label(fr,text="Max:",bg=C["panel"],fg=C["grey"],font=("Consolas",10)).grid(row=1,column=0,sticky="w")
        tk.Entry(fr,textvariable=mn,width=10,bg=C["border"],fg=C["white"],relief="flat").grid(row=0,column=1,padx=6)
        tk.Entry(fr,textvariable=mx,width=10,bg=C["border"],fg=C["white"],relief="flat").grid(row=1,column=1,padx=6)
        out=tk.Label(self.tool_area,text="—",fg=C["accent"],bg=C["panel"],font=("Consolas",36,"bold")); out.pack(pady=14)
        def gen():
            a,b=mn.get(),mx.get()
            if a>b: a,b=b,a
            out.config(text=str(random.randint(a,b)))
        tk.Button(self.tool_area,text="GENERATE",command=gen,bg=C["accent"],fg="#000",relief="flat",font=("Consolas",11,"bold")).pack()

    def tool_stopwatch(self):
        self._clear_tool(); self._tool_header("STOPWATCH")
        lbl=tk.Label(self.tool_area,text="00:00.0",fg=C["white"],bg=C["panel"],font=("Consolas",36,"bold")); lbl.pack(pady=16)
        state={"run":False,"t":0}
        def update():
            if state["run"]:
                e=time.time()-state["t"]
                lbl.config(text=f"{int(e//60):02d}:{int(e%60):02d}.{int((e-int(e))*10)}")
            self.tool_area.after(100,update)
        fr=tk.Frame(self.tool_area,bg=C["panel"]); fr.pack()
        def start():
            if not state["run"]: state["t"]=time.time(); state["run"]=True
        def stop(): state["run"]=False
        def reset(): state["run"]=False; lbl.config(text="00:00.0")
        for txt,cmd,col in [("START",start,C["accent3"]),("STOP",stop,C["accent2"]),("RESET",reset,C["dimgrey"])]:
            tk.Button(fr,text=txt,command=cmd,bg=col,fg="#000",relief="flat",font=("Consolas",10,"bold"),width=8).pack(side="left",padx=4)
        update()

    def tool_coin_flip(self):
        self._clear_tool(); self._tool_header("COIN FLIP")
        lbl=tk.Label(self.tool_area,text="?",fg=C["accent4"],bg=C["panel"],font=("Consolas",52,"bold")); lbl.pack(pady=20)
        def flip():
            r=random.choice(["HEADS","TAILS"]); lbl.config(text=r,fg=C["accent3"] if r=="HEADS" else C["accent2"])
        tk.Button(self.tool_area,text="FLIP",command=flip,bg=C["accent4"],fg="#000",relief="flat",font=("Consolas",13,"bold")).pack()

    def tool_dice_roller(self):
        self._clear_tool(); self._tool_header("DICE ROLLER")
        faces_v=tk.IntVar(value=6); fr=tk.Frame(self.tool_area,bg=C["panel"]); fr.pack(pady=8)
        tk.Label(fr,text="Faces:",bg=C["panel"],fg=C["grey"],font=("Consolas",10)).pack(side="left")
        tk.OptionMenu(fr,faces_v,4,6,8,10,12,20,100).pack(side="left",padx=6)
        lbl=tk.Label(self.tool_area,text="—",fg=C["accent"],bg=C["panel"],font=("Consolas",52,"bold")); lbl.pack(pady=12)
        tk.Button(self.tool_area,text="ROLL",command=lambda:lbl.config(text=str(random.randint(1,faces_v.get()))),bg=C["accent"],fg="#000",relief="flat",font=("Consolas",13,"bold")).pack()

    def tool_snippets(self):
        self._clear_tool(); self._tool_header("NOTE SNIPPETS")
        txt=scrolledtext.ScrolledText(self.tool_area,width=55,height=14,bg=C["border"],fg=C["white"],font=("Consolas",10),relief="flat"); txt.pack(padx=20,pady=6)
        path=os.path.join(os.path.expanduser("~"),"hyperxeno_snippets.txt")
        def load():
            if os.path.exists(path):
                with open(path,"r",encoding="utf-8") as f: txt.delete("1.0",tk.END); txt.insert("1.0",f.read())
        def save():
            try:
                with open(path,"w",encoding="utf-8") as f: f.write(txt.get("1.0","end-1c"))
            except: messagebox.showerror("Error","Could not save")
        fr=tk.Frame(self.tool_area,bg=C["panel"]); fr.pack(pady=4)
        tk.Button(fr,text="Load",command=load,bg=C["border"],fg=C["white"],relief="flat").pack(side="left",padx=4)
        tk.Button(fr,text="Save",command=save,bg=C["accent3"],fg="#000",relief="flat").pack(side="left",padx=4)
        load()

    def tool_base64_encode(self):
        self._clear_tool(); self._tool_header("BASE64 ENCODE/DECODE")
        inp=scrolledtext.ScrolledText(self.tool_area,width=55,height=6,bg=C["border"],fg=C["white"],font=("Consolas",10),relief="flat"); inp.pack(padx=20,pady=6)
        out=scrolledtext.ScrolledText(self.tool_area,width=55,height=6,bg="#0A0A0A",fg=C["accent"],font=("Consolas",10),relief="flat"); out.pack(padx=20,pady=4)
        def encode():
            out.delete("1.0",tk.END)
            try: out.insert("1.0",base64.b64encode(inp.get("1.0","end-1c").encode()).decode())
            except: out.insert("1.0","Error")
        def decode():
            out.delete("1.0",tk.END)
            try: out.insert("1.0",base64.b64decode(inp.get("1.0","end-1c").encode()).decode())
            except: out.insert("1.0","Decode Error")
        fr=tk.Frame(self.tool_area,bg=C["panel"]); fr.pack(pady=4)
        tk.Button(fr,text="ENCODE",command=encode,bg=C["accent"],fg="#000",relief="flat",font=("Consolas",10,"bold")).pack(side="left",padx=6)
        tk.Button(fr,text="DECODE",command=decode,bg=C["accent5"],fg=C["white"],relief="flat",font=("Consolas",10,"bold")).pack(side="left",padx=6)

    def tool_hash_gen(self):
        self._clear_tool(); self._tool_header("HASH GENERATOR")
        inp=tk.Entry(self.tool_area,width=50,bg=C["border"],fg=C["white"],font=("Consolas",11),relief="flat",insertbackground=C["white"]); inp.pack(padx=20,pady=8)
        results_frame=tk.Frame(self.tool_area,bg=C["panel"]); results_frame.pack(fill="x",padx=20)
        labels={}
        for algo in ["md5","sha1","sha256","sha512"]:
            row=tk.Frame(results_frame,bg=C["panel"]); row.pack(fill="x",pady=2)
            tk.Label(row,text=f"{algo.upper():8s}",fg=C["dimgrey"],bg=C["panel"],font=("Consolas",9,"bold"),width=8).pack(side="left")
            lbl=tk.Label(row,text="—",fg=C["accent"],bg=C["panel"],font=("Consolas",9),wraplength=700,anchor="w"); lbl.pack(side="left",fill="x",expand=True)
            labels[algo]=lbl
        def gen():
            data=inp.get().encode()
            for algo,lbl in labels.items(): lbl.config(text=getattr(hashlib,algo)(data).hexdigest())
        tk.Button(self.tool_area,text="HASH IT",command=gen,bg=C["accent"],fg="#000",relief="flat",font=("Consolas",11,"bold")).pack(pady=8)
        inp.bind("<Return>",lambda e:gen())

    # ──────────────────────────────────────────────────────────────────────────
    #  GAMES (all unchanged)
    # ──────────────────────────────────────────────────────────────────────────
    def show_games(self):
        self._page_header("GAMES","MINI ARCADE")
        cont=tk.Frame(self.main_frame,bg=C["panel"]); cont.pack(fill="both",expand=True,padx=20,pady=8)
        left=tk.Frame(cont,bg=C["sidebar"],width=160); left.pack(side="left",fill="y"); left.pack_propagate(False)
        tk.Label(left,text="SELECT GAME",fg=C["dimgrey"],bg=C["sidebar"],font=("Consolas",8)).pack(pady=(14,6))
        self.game_area=tk.Frame(cont,bg=C["panel"]); self.game_area.pack(side="right",fill="both",expand=True,padx=12)
        games=[("Snake",self.game_snake),("Pong",self.game_pong),("Brick Breaker",self.game_brick),("Clicker",self.game_clicker),("Reaction Test",self.game_reaction)]
        for name,cmd in games:
            tk.Button(left,text=name,command=cmd,bg=C["border"],fg=C["white"],relief="flat",font=("Consolas",9),bd=0,pady=9,anchor="w",padx=10,activebackground=C["accent"],activeforeground="#000",cursor="hand2").pack(fill="x",pady=1)
        self.game_snake()

    def _clear_game(self):
        for w in self.game_area.winfo_children(): w.destroy()
    def _game_header(self,text):
        tk.Label(self.game_area,text=text,fg=C["accent"],bg=C["panel"],font=("Consolas",13,"bold")).pack(pady=(8,4))

    def game_snake(self):
        self._clear_game(); self._game_header("SNAKE")
        canvas=tk.Canvas(self.game_area,width=400,height=400,bg="#000000",highlightthickness=1,highlightbackground=C["border"]); canvas.pack(pady=4)
        cell=20; wc=hc=20; snake=[(10,10),(9,10),(8,10)]; direction=[1,0]; food=[random.randint(0,wc-1),random.randint(0,hc-1)]; score=[0]; running=[True]
        score_lbl=tk.Label(self.game_area,text="Score: 0",fg=C["accent"],bg=C["panel"],font=("Consolas",10)); score_lbl.pack()
        def draw():
            canvas.delete("all"); fx,fy=food; canvas.create_rectangle(fx*cell,fy*cell,(fx+1)*cell,(fy+1)*cell,fill=C["accent2"])
            for i,(x,y) in enumerate(snake): canvas.create_rectangle(x*cell,y*cell,(x+1)*cell,(y+1)*cell,fill=C["accent"] if i==0 else C["accent3"])
        def place_food():
            while True:
                fx=random.randint(0,wc-1); fy=random.randint(0,hc-1)
                if (fx,fy) not in snake: food[0],food[1]=fx,fy; break
        def move():
            if not running[0]: return
            hx,hy=snake[0]; dx,dy=direction; nx,ny=hx+dx,hy+dy
            if nx<0 or nx>=wc or ny<0 or ny>=hc or (nx,ny) in snake:
                running[0]=False; canvas.create_text(200,200,text=f"GAME OVER\nScore:{score[0]}",fill=C["white"],font=("Consolas",16,"bold")); return
            snake.insert(0,(nx,ny))
            if nx==food[0] and ny==food[1]: score[0]+=1; score_lbl.config(text=f"Score: {score[0]}"); place_food()
            else: snake.pop()
            draw(); self.game_area.after(110,move)
        def keys(e):
            dx,dy=direction
            if e.keysym=="Up" and dy!=1: direction[0],direction[1]=0,-1
            elif e.keysym=="Down" and dy!=-1: direction[0],direction[1]=0,1
            elif e.keysym=="Left" and dx!=1: direction[0],direction[1]=-1,0
            elif e.keysym=="Right" and dx!=-1: direction[0],direction[1]=1,0
        canvas.focus_set(); canvas.bind("<KeyPress>",keys); draw(); move()

    def game_pong(self):
        self._clear_game(); self._game_header("PONG")
        canvas=tk.Canvas(self.game_area,width=420,height=300,bg="#000",highlightthickness=1,highlightbackground=C["border"]); canvas.pack(pady=4)
        pw,ph,br=10,60,8; px=10; py=150; bx,by=210,150; vx,vy=3,2; score=[0]; running=[True]
        sc=tk.Label(self.game_area,text="Hits: 0",fg=C["accent"],bg=C["panel"],font=("Consolas",10)); sc.pack()
        def draw():
            canvas.delete("all"); canvas.create_line(210,0,210,300,fill="#111",dash=(4,4))
            canvas.create_rectangle(px,py-ph//2,px+pw,py+ph//2,fill=C["white"]); canvas.create_oval(bx-br,by-br,bx+br,by+br,fill=C["accent2"])
        def move():
            nonlocal bx,by,vx,vy,py
            if not running[0]: return
            bx+=vx; by+=vy
            if by-br<=0 or by+br>=300: vy=-vy
            if bx+br>=420: vx=-vx
            if bx-br<=px+pw and py-ph//2<=by<=py+ph//2: vx=abs(vx); score[0]+=1; sc.config(text=f"Hits: {score[0]}")
            if bx-br<0: running[0]=False; canvas.create_text(210,150,text="GAME OVER",fill=C["white"],font=("Consolas",16,"bold")); return
            draw(); self.game_area.after(28,move)
        def keys(e):
            nonlocal py
            if e.keysym=="Up": py=max(ph//2,py-16)
            elif e.keysym=="Down": py=min(300-ph//2,py+16)
        canvas.focus_set(); canvas.bind("<KeyPress>",keys); draw(); move()

    def game_brick(self):
        self._clear_game(); self._game_header("BRICK BREAKER")
        canvas=tk.Canvas(self.game_area,width=420,height=320,bg="#000",highlightthickness=1,highlightbackground=C["border"]); canvas.pack(pady=4)
        pw,ph=70,10; br=6; px=175; py=300; bx,by=210,210; vx,vy=3,-3; bw,bh=42,15
        brick_colors=[C["accent2"],C["accent4"],C["accent3"],C["accent"]]
        bricks=[[c*bw+8,r*(bh+5)+10,brick_colors[r%4]] for r in range(4) for c in range(9)]
        running=[True]; sc_lbl=tk.Label(self.game_area,text="Bricks: 36",fg=C["accent"],bg=C["panel"],font=("Consolas",10)); sc_lbl.pack()
        def draw():
            canvas.delete("all")
            for x,y,col in bricks: canvas.create_rectangle(x,y,x+bw-4,y+bh,fill=col,outline=C["bg"])
            canvas.create_rectangle(px,py,px+pw,py+ph,fill=C["white"]); canvas.create_oval(bx-br,by-br,bx+br,by+br,fill=C["accent4"])
        def move():
            nonlocal bx,by,vx,vy,px
            if not running[0]: return
            bx+=vx; by+=vy
            if by-br<=0: vy=-vy
            if bx-br<=0 or bx+br>=420: vx=-vx
            if py<=by+br<=py+ph and px<=bx<=px+pw: vy=-abs(vy)
            for b in bricks[:]:
                x,y,_=b
                if x<=bx<=x+bw-4 and y<=by<=y+bh: bricks.remove(b); vy=-vy; sc_lbl.config(text=f"Bricks: {len(bricks)}"); break
            if by-br>320: running[0]=False; canvas.create_text(210,160,text="GAME OVER",fill=C["white"],font=("Consolas",16,"bold")); return
            if not bricks: running[0]=False; canvas.create_text(210,160,text="YOU WIN!",fill=C["accent3"],font=("Consolas",18,"bold")); return
            draw(); self.game_area.after(28,move)
        def keys(e):
            nonlocal px
            if e.keysym=="Left": px=max(0,px-16)
            elif e.keysym=="Right": px=min(420-pw,px+16)
        canvas.focus_set(); canvas.bind("<KeyPress>",keys); draw(); move()

    def game_clicker(self):
        self._clear_game(); self._game_header("CLICKER")
        score=[0]; cps_data={"t":time.time(),"count":0}
        score_lbl=tk.Label(self.game_area,text="0",fg=C["accent"],bg=C["panel"],font=("Consolas",52,"bold")); score_lbl.pack(pady=10)
        cps_lbl=tk.Label(self.game_area,text="CPS: 0.0",fg=C["dimgrey"],bg=C["panel"],font=("Consolas",10)); cps_lbl.pack()
        def click():
            score[0]+=1; cps_data["count"]+=1; score_lbl.config(text=str(score[0]))
            now=time.time(); elapsed=now-cps_data["t"]
            if elapsed>=1.0: cps_lbl.config(text=f"CPS: {cps_data['count']/elapsed:.1f}"); cps_data["t"]=now; cps_data["count"]=0
        tk.Button(self.game_area,text="CLICK ME",font=("Consolas",16,"bold"),command=click,bg=C["accent"],fg="#000",relief="flat",width=14,height=3,activebackground=C["accent3"]).pack(pady=14)
        def reset(): score[0]=0; score_lbl.config(text="0"); cps_lbl.config(text="CPS: 0.0")
        tk.Button(self.game_area,text="Reset",command=reset,bg=C["border"],fg=C["grey"],relief="flat",font=("Consolas",9)).pack()

    def game_reaction(self):
        self._clear_game(); self._game_header("REACTION TEST")
        tk.Label(self.game_area,text="Press START, then click when screen turns GREEN",fg=C["grey"],bg=C["panel"],font=("Consolas",9)).pack(pady=4)
        box=tk.Canvas(self.game_area,width=360,height=180,bg=C["border"],highlightthickness=0); box.pack(pady=8)
        box_txt=box.create_text(180,90,text="READY",fill=C["white"],font=("Consolas",22,"bold"))
        result=tk.Label(self.game_area,text="",fg=C["accent4"],bg=C["panel"],font=("Consolas",12)); result.pack()
        state={"waiting":False,"start":None}
        btn=tk.Button(self.game_area,text="START",font=("Consolas",11,"bold"),width=12); btn.pack(pady=6)
        def start():
            result.config(text=""); box.config(bg="#550000"); box.itemconfig(box_txt,text="WAIT...")
            btn.config(state="disabled"); state["waiting"]=True; state["start"]=None
            def go_green():
                if not state["waiting"]: return
                box.config(bg="#003300"); box.itemconfig(box_txt,text="CLICK!"); state["start"]=time.time()
            box.after(random.randint(1200,4000),go_green)
        def click_box(e=None):
            if not state["waiting"]: return
            if state["start"] is None:
                box.config(bg="#550000"); box.itemconfig(box_txt,text="TOO EARLY!"); result.config(text="Too early!",fg=C["accent2"])
            else:
                elapsed=time.time()-state["start"]; box.config(bg=C["border"]); box.itemconfig(box_txt,"")
                result.config(text=f"⚡ {elapsed*1000:.0f} ms",fg=C["accent3"] if elapsed<0.25 else C["accent4"])
            state["waiting"]=False; btn.config(state="normal",text="START")
        btn.config(command=start); box.bind("<Button-1>",click_box)

    # ──────────────────────────────────────────────────────────────────────────
    #  MESSAGER
    # ──────────────────────────────────────────────────────────────────────────
    def show_messages(self):
        self._page_header("MESSAGER","COMMS")
        tk.Label(self.main_frame,text="⚙  COMING SOON",fg=C["accent2"],bg=C["panel"],font=("Consolas",22,"bold")).pack(expand=True)

    # ──────────────────────────────────────────────────────────────────────────
    #  LOGS
    # ──────────────────────────────────────────────────────────────────────────
    def show_terminal(self):
        self._page_header("LOGS","ACTIVITY")
        term=scrolledtext.ScrolledText(self.main_frame,bg="#000000",fg=C["accent3"],font=("Consolas",10),relief="flat"); term.pack(fill="both",expand=True,padx=20,pady=8)
        for line in self.logs: term.insert(tk.END,line+"\n")
        term.config(state="disabled")
        fr=tk.Frame(self.main_frame,bg=C["panel"]); fr.pack(pady=6)
        tk.Button(fr,text="Refresh",command=self.show_terminal,bg=C["border"],fg=C["white"],relief="flat",font=("Consolas",9)).pack(side="left",padx=6)
        tk.Button(fr,text="Clear",command=lambda:(self.logs.clear(),self.show_terminal()),bg=C["accent2"],fg=C["white"],relief="flat",font=("Consolas",9)).pack(side="left",padx=6)
        def export():
            p=filedialog.asksaveasfilename(defaultextension=".log")
            if p:
                with open(p,"w",encoding="utf-8") as f: f.write("\n".join(self.logs))
        tk.Button(fr,text="Export",command=export,bg=C["accent3"],fg="#000",relief="flat",font=("Consolas",9)).pack(side="left",padx=6)

    # ──────────────────────────────────────────────────────────────────────────
    #  SETTINGS
    # ──────────────────────────────────────────────────────────────────────────
    def show_settings(self):
        self._page_header("SETTINGS","CONTROL PANEL")
        canvas=tk.Canvas(self.main_frame,bg=C["panel"],highlightthickness=0)
        scroll=tk.Scrollbar(self.main_frame,orient="vertical",command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set); scroll.pack(side="right",fill="y"); canvas.pack(fill="both",expand=True,padx=20)
        frame=tk.Frame(canvas,bg=C["panel"]); canvas.create_window((0,0),window=frame,anchor="nw")
        frame.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
        def section(text):
            tk.Label(frame,text=f"── {text} ──",fg=C["accent"],bg=C["panel"],font=("Consolas",10,"bold")).pack(anchor="w",pady=(14,2),padx=10)
            tk.Frame(frame,bg=C["border"],height=1).pack(fill="x",padx=10,pady=2)
        def row_chk(parent,text,var,cmd=None):
            tk.Checkbutton(parent,text=text,variable=var,command=cmd,bg=C["panel"],fg=C["grey"],selectcolor=C["border"],activebackground=C["panel"],font=("Consolas",9)).pack(anchor="w",padx=20,pady=2)

        section("WINDOW")
        row_chk(frame,"Always on top",self.app_always_on_top,lambda:self.root.attributes("-topmost",self.app_always_on_top.get()))

        section("ACCOUNT")
        af=tk.Frame(frame,bg=C["panel"]); af.pack(anchor="w",padx=20,pady=4)
        tk.Label(af,text=f"Logged in as: {self.username}  [{self.role}]  Plan: {self.tier}",fg=C["grey"],bg=C["panel"],font=("Consolas",9)).pack(side="left")
        tk.Button(frame,text="Logout",command=self._logout,bg=C["accent2"],fg=C["white"],relief="flat",font=("Consolas",9)).pack(anchor="w",padx=20,pady=4)

        section("API KEYS")
        def key_row_s(label,val,key_name):
            row=tk.Frame(frame,bg=C["panel"]); row.pack(anchor="w",padx=20,pady=4,fill="x")
            tk.Label(row,text=f"{label}:",fg=C["dimgrey"],bg=C["panel"],font=("Consolas",9),width=12).pack(side="left")
            e=tk.Entry(row,width=40,font=("Consolas",9),bg=C["border"],fg=C["accent"],relief="flat",insertbackground=C["accent"],show="●" if val else ""); e.insert(0,val); e.pack(side="left",padx=6,ipady=4)
            def save(en=e,kn=key_name):
                setattr(self,kn,en.get().strip()); self.session[kn]=getattr(self,kn); save_session(self.session)
                messagebox.showinfo("Saved","Key saved!")
            tk.Button(row,text="Save",command=save,bg=C["accent3"],fg="#000",relief="flat",font=("Consolas",8)).pack(side="left")
        key_row_s("Groq Key",self.groq_key,"groq_key")
        if self.tier in ("pro","business") or self.role in ("admin","co-admin"):
            key_row_s("Xeno Key",self.xeno_key,"xeno_key")
        if self.tier=="business" or self.role in ("admin","co-admin"):
            key_row_s("Gemini Key",self.gemini_key,"gemini_key")

        section("NOTEPAD")
        row_chk(frame,"Word Wrap default",self.word_wrap); row_chk(frame,"Dark Mode default",self.notepad_dark_mode); row_chk(frame,"Auto Save",self.notepad_autosave)
        sf=tk.Frame(frame,bg=C["panel"]); sf.pack(anchor="w",padx=20,pady=4)
        tk.Label(sf,text="Font size:",fg=C["grey"],bg=C["panel"],font=("Consolas",9)).pack(side="left")
        fsv=tk.IntVar(value=self.notepad_font_size); tk.Spinbox(sf,from_=6,to=32,textvariable=fsv,width=4,bg=C["border"],fg=C["white"],relief="flat").pack(side="left",padx=6)
        tk.Button(sf,text="Apply",command=lambda:(setattr(self,"notepad_font_size",fsv.get())),bg=C["border"],fg=C["white"],relief="flat",font=("Consolas",8)).pack(side="left")

        section("AI ENGINE")
        ef=tk.Frame(frame,bg=C["panel"]); ef.pack(anchor="w",padx=20,pady=6)
        tk.Label(ef,text="Current:",fg=C["grey"],bg=C["panel"],font=("Consolas",9)).pack(side="left")
        tk.Label(ef,text=self.model_names[self.model_mode],fg=C["accent"],bg=C["panel"],font=("Consolas",10,"bold")).pack(side="left",padx=8)
        tk.Button(ef,text="CYCLE ▶",command=self._cycle_engine_btn,bg=C["accent"],fg="#000",relief="flat",font=("Consolas",9,"bold")).pack(side="left")

        section("ABOUT")
        tk.Label(frame,text="HyperXeno V14.0  //  Designed By C-Master\nPython / Tkinter  //  Multi-AI  //  ELITE BUILD\nServer: "+SERVER,
                 fg=C["dimgrey"],bg=C["panel"],font=("Consolas",9),justify="left").pack(anchor="w",padx=20,pady=6)

    # ──────────────────────────────────────────────────────────────────────────
    #  UTILITY / THREADS
    # ──────────────────────────────────────────────────────────────────────────
    def log_event(self,text):
        ts=time.strftime("%H:%M:%S"); self.logs.append(f"[{ts}] {text}")

    def _animate_sidebar_rainbow(self):
        h=0.0
        while True:
            try:
                r,g,b=colorsys.hsv_to_rgb(h,0.9,1.0); self._rb_label.config(fg="#%02x%02x%02x"%(int(r*255),int(g*255),int(b*255)))
                h=(h+0.01)%1.0; time.sleep(0.06)
            except: break

    def _tick_clock(self):
        self.clock_lbl.config(text=datetime.now().strftime("%H:%M:%S  %d/%m/%Y  ")); self.root.after(1000,self._tick_clock)

    def _drag_start(self,e): self.drag_x=e.x; self.drag_y=e.y
    def _drag_move(self,e):
        self.root.geometry(f"+{self.root.winfo_x()+(e.x-self.drag_x)}+{self.root.winfo_y()+(e.y-self.drag_y)}")

    def _stay_active(self):
        while True:
            try:
                if self.root.state()=="iconic": self.root.deiconify()
                self.root.lift()
                if not self.is_ghost: self.root.after(0,lambda:self.root.attributes("-topmost",True))
            except: pass
            time.sleep(0.5)

    def _poll_maintenance(self):
        """Check server maintenance flag periodically and show overlay if active."""
        while True:
            try:
                r=requests.get(f"{SERVER}/status",timeout=6)
                d=r.json()
                if d.get("maintenance") and self.role not in ("admin","co-admin"):
                    msg=d.get("message","HyperXeno is under maintenance. Please check back soon.")
                    self.root.after(0,lambda m=msg:self._show_maintenance_screen(m))
            except: pass
            time.sleep(30)

    def _show_maintenance_screen(self,msg):
        for w in self.root.winfo_children(): w.destroy()
        f=tk.Frame(self.root,bg="#000000"); f.pack(fill="both",expand=True)
        tk.Label(f,text="⚠",fg=C["accent2"],bg="#000000",font=("Consolas",52)).pack(pady=(140,10))
        tk.Label(f,text="HYPERXENO — MAINTENANCE",fg=C["white"],bg="#000000",font=("Consolas",18,"bold")).pack()
        tk.Label(f,text=msg,fg=C["grey"],bg="#000000",font=("Consolas",11)).pack(pady=14)
        tk.Label(f,text="We'll be back shortly.",fg=C["dimgrey"],bg="#000000",font=("Consolas",9)).pack()

    def _corner_engine(self):
        class POINT(ctypes.Structure): _fields_=[("x",ctypes.c_long),("y",ctypes.c_long)]
        while True:
            try:
                pt=POINT(); ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                shift=ctypes.windll.user32.GetAsyncKeyState(0x10)&0x8000
                if shift:
                    if ctypes.windll.user32.GetAsyncKeyState(0x31)&0x8000:   self.root.after(0,self.purge_chat); time.sleep(0.5)
                    elif ctypes.windll.user32.GetAsyncKeyState(0x32)&0x8000: self.root.after(0,self._cycle_text_color); time.sleep(0.8)
                    elif ctypes.windll.user32.GetAsyncKeyState(0x33)&0x8000: self._global_siphon(); time.sleep(0.5)
                    elif ctypes.windll.user32.GetAsyncKeyState(0x34)&0x8000: self.root.after(0,self._show_credits); time.sleep(0.5)
                    elif ctypes.windll.user32.GetAsyncKeyState(0x35)&0x8000: os._exit(0)
                    elif ctypes.windll.user32.GetAsyncKeyState(0x37)&0x8000: self.root.after(0,self._cycle_engine_btn); time.sleep(0.5)
                # Corners
                if pt.x<=5 and pt.y<=5:
                    self.is_ela_enabled=not self.is_ela_enabled; s="ON ✓" if self.is_ela_enabled else "OFF"
                    self.root.after(0,lambda s=s:self._chat_log(f"ELA MODE: {s}",tag="sys")); time.sleep(1)
                elif pt.x>=self.screen_w-5 and pt.y<=5:
                    self.is_ghost=not self.is_ghost; alpha=0.0 if self.is_ghost else 1.0
                    self.root.after(0,lambda a=alpha:self.root.attributes("-alpha",a))
                    try:
                        ctypes.windll.user32.SetWindowLongW(self.hwnd,-20,self.base_style|(0x00000020 if self.is_ghost else 0))
                    except: pass
                    time.sleep(1)
                elif pt.x<=5 and pt.y>=self.screen_h-5:
                    threading.Thread(target=self._process_batch,daemon=True).start(); time.sleep(3)
                elif pt.x>=self.screen_w-5 and pt.y>=self.screen_h-5:
                    self.root.after(0,lambda:self.root.attributes("-alpha",0.0)); time.sleep(0.15)
                    snap=ImageGrab.grab(all_screens=True); self.snap_bank.append(snap)
                    self.root.after(0,lambda:self.snap_lbl.config(text=f"SNAPS:{len(self.snap_bank)}") if hasattr(self,"snap_lbl") else None)
                    if not self.is_ghost: self.root.after(0,lambda:self.root.attributes("-alpha",1.0))
                    time.sleep(1)
            except: pass
            time.sleep(0.01)


# ══════════════════════════════════════════════════════════════════════════════
#  BOOT CONTROLLER
# ══════════════════════════════════════════════════════════════════════════════
class BootController:
    def __init__(self, root):
        self.root = root
        self.root.title("HYPER XENO V14.0")
        sw=root.winfo_screenwidth(); sh=root.winfo_screenheight()
        root.geometry(f"1200x780+{(sw-1200)//2}+{(sh-780)//2}")
        root.configure(bg="#000000")
        root.attributes("-topmost",True)
        root.protocol("WM_DELETE_WINDOW",lambda:None)
        root.bind("<Escape>",lambda e:os._exit(0))
        LoadingScreen(root, self._after_load)

    def _after_load(self):
        session=load_session()
        if session and session.get("token"):
            # Validate session against server
            def validate():
                try:
                    r=requests.get(f"{SERVER}/status",timeout=5)
                    if r.status_code==200:
                        self.root.after(0,lambda:HyperXeno(self.root,session))
                    else:
                        self.root.after(0,self._show_auth)
                except:
                    # Offline — use cached session
                    self.root.after(0,lambda:HyperXeno(self.root,session))
            threading.Thread(target=validate,daemon=True).start()
        else:
            self._show_auth()

    def _show_auth(self):
        for w in self.root.winfo_children(): w.destroy()
        AuthScreen(self.root, self._after_auth)

    def _after_auth(self, session):
        is_new = session.get("token") and not load_session()  # fresh registration
        if session.get("groq_key","")=="" and session.get("tier","basic")=="basic" and session.get("role","user")=="user":
            for w in self.root.winfo_children(): w.destroy()
            GroqSetupScreen(self.root, session, lambda s: (save_session(s), HyperXeno(self.root,s).__init__(self.root,s) if False else self._launch(s)))
        else:
            self._launch(session)

    def _launch(self, session):
        for w in self.root.winfo_children(): w.destroy()
        HyperXeno(self.root, session)


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__=="__main__":
    root=tk.Tk()
    BootController(root)
    root.mainloop()
