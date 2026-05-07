"""
LuckyLoop Controlbox 16.0.7 - ENTERPRISE MULTI-DEVICE LICENSE SYSTEM
✨ Updated: Network Time Sync with Seconds Precision + Admin Auto-Elevation
🔧 Fixed: _auto_sync_loop now uses sync_time_force() (NTP direct) instead of windows_sync_now()
🆕 Auto sync will now match time.is — proper 4-timestamp RFC 5905 algorithm via ntplib
🔧 Fixed: ntplib used in get_ntp_time() — multiple servers, best sample filtering
🆕 Auto Update: GitHub থেকে auto update support
🆕 Version display in header
"""

import sys
import os

# ══════════════════════════════════════════════════════
# ADMIN ELEVATION — silent restart without black window
# ══════════════════════════════════════════════════════
if sys.platform == "win32":
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        script = os.path.abspath(sys.argv[0])
        pythonw = sys.executable.replace("python.exe", "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = sys.executable
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", pythonw, f'"{script}"', None, 1
        )
        sys.exit(0)

import tkinter as tk
from tkinter import messagebox
import threading
import time
import subprocess
import webbrowser
import datetime
import json
import hashlib
import uuid
import random
import atexit
import ssl
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# ══════════════════════════════════════════════════════
# AUTO UPDATER — GitHub থেকে auto update
# ══════════════════════════════════════════════════════
CURRENT_VERSION    = "16.0.7"
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/alifmondolalif66-byte/luckyloop-tracker/main/version.txt"
GITHUB_SCRIPT_URL  = "https://raw.githubusercontent.com/alifmondolalif66-byte/luckyloop-tracker/main/controlbox.py"

class AutoUpdater:
    @staticmethod
    def check_and_update():
        try:
            ctx = ssl.create_default_context()

            req = urllib.request.Request(
                GITHUB_VERSION_URL,
                headers={"User-Agent": "LuckyLoop-Controlbox/AutoUpdate"}
            )
            with urllib.request.urlopen(req, timeout=8, context=ctx) as r:
                latest_version = r.read().decode().strip()

            if latest_version == CURRENT_VERSION:
                print(f"[UPDATE] Already up to date: {CURRENT_VERSION}")
                return

            print(f"[UPDATE] New version found: {latest_version}, updating...")

            req2 = urllib.request.Request(
                GITHUB_SCRIPT_URL,
                headers={"User-Agent": "LuckyLoop-Controlbox/AutoUpdate"}
            )
            with urllib.request.urlopen(req2, timeout=30, context=ctx) as r:
                new_code = r.read()

            script_path = os.path.abspath(sys.argv[0])
            backup_path = script_path + ".bak"

            with open(script_path, "rb") as f:
                old_code = f.read()
            with open(backup_path, "wb") as f:
                f.write(old_code)

            with open(script_path, "wb") as f:
                f.write(new_code)

            pythonw = sys.executable.replace("python.exe", "pythonw.exe")
            if not os.path.exists(pythonw):
                pythonw = sys.executable

            subprocess.Popen([pythonw, script_path])
            sys.exit(0)

        except Exception as e:
            print(f"[UPDATE] Skipped: {e}")

# Auto update check — License dialog এর আগেই চলবে
AutoUpdater.check_and_update()

VALID_LICENSES = {
    "Luckyloop-position-update328362": {
        "max_devices": 1,
        "description": "Single Device License"
    },
    "Luckyloop-multi-device-pro": {
        "max_devices": 5,
        "description": "Multi-Device Pro (5 Devices)"
    },
    "Luckyloop-Position-Update-328362AbcWvBasVBassdDWVBsssfeWZ328362ASD265485ZXAXXXX": {
        "max_devices": 999,
        "description": "Licenses Key Active"
    }
}

class DeviceManager:
    @staticmethod
    def get_device_id():
        try:
            if sys.platform == "win32":
                mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                               for elements in range(0, 2*6, 2)][::-1])
                return hashlib.sha256(mac.encode()).hexdigest()[:16]
            else:
                import socket
                hostname = socket.gethostname()
                return hashlib.sha256(hostname.encode()).hexdigest()[:16]
        except:
            return str(uuid.uuid4())[:16]

    @staticmethod
    def get_device_name():
        try:
            if sys.platform == "win32":
                return os.environ.get('COMPUTERNAME', 'Unknown Device')
            else:
                import socket
                return socket.gethostname()
        except:
            return "Unknown Device"

LICENSE_DIR = Path.home() / ".luckyloop" / "license"
LICENSE_DIR.mkdir(parents=True, exist_ok=True)
LICENSE_FILE = LICENSE_DIR / "license_info.json"
DEVICE_ID_FILE = LICENSE_DIR / "device.json"

class LicenseManager:
    def __init__(self):
        self.license_file = LICENSE_FILE
        self.device_id_file = DEVICE_ID_FILE
        self.device_id = self._get_device_id()
        self.device_name = DeviceManager.get_device_name()
        self.is_activated = self._check_activation()
        self.license_key = None
        self.license_type = None
        if self.is_activated:
            self._load_license_info()

    def _get_device_id(self):
        if self.device_id_file.exists():
            try:
                with open(self.device_id_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('device_id')
            except:
                pass
        device_id = DeviceManager.get_device_id()
        try:
            with open(self.device_id_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'device_id': device_id,
                    'device_name': DeviceManager.get_device_name(),
                    'created_at': datetime.datetime.now().isoformat()
                }, f, indent=2)
        except:
            pass
        return device_id

    def _check_activation(self):
        if self.license_file.exists():
            try:
                with open(self.license_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('device_id') == self.device_id:
                        return True
            except:
                pass
        return False

    def _load_license_info(self):
        try:
            with open(self.license_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.license_key = data.get('license_key')
                self.license_type = data.get('license_type')
        except:
            pass

    def activate(self, license_key):
        license_key = license_key.strip()
        if license_key not in VALID_LICENSES:
            return False, "❌ Invalid License Key!"
        try:
            with open(self.license_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'license_key': license_key,
                    'license_type': VALID_LICENSES[license_key]['description'],
                    'device_id': self.device_id,
                    'device_name': self.device_name,
                    'activated_at': datetime.datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            self.license_key = license_key
            self.license_type = VALID_LICENSES[license_key]['description']
            self.is_activated = True
            return True, f"✅ License Activated!\n{VALID_LICENSES[license_key]['description']}"
        except Exception as e:
            return False, f"❌ Error: {str(e)[:50]}"

    def deactivate(self):
        try:
            if self.license_file.exists():
                self.license_file.unlink()
            self.is_activated = False
            self.license_key = None
            self.license_type = None
            return True
        except Exception as e:
            print(f"Warning: Error deactivating: {e}")
            return False

    def get_license_info(self):
        if self.is_activated:
            return f"✅ {self.license_type}", "#22c55e"
        return "❌ Not Activated", "#ef4444"

# ══════════════════════════════════════════════════════
# DEVICE CHECKER — heartbeat and block check with server
# ══════════════════════════════════════════════════════

SERVER_BASE = "https://luckyloop-tracker.onrender.com"

class DeviceChecker:
    def __init__(self, license_manager):
        self.lm = license_manager
        self._stop_event = threading.Event()
        self._check_thread = None

    def send_heartbeat(self):
        try:
            payload = json.dumps({
                "device_id":    self.lm.device_id,
                "device_name":  self.lm.device_name,
                "license_key":  self.lm.license_key  or "",
                "license_type": self.lm.license_type or "",
            }).encode("utf-8")
            ctx = ssl.create_default_context()
            req = urllib.request.Request(
                f"{SERVER_BASE}/api/heartbeat",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "LuckyLoop-Controlbox/16.0.7"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("blocked"):
                    return False, True, data.get("reason", "Your device has been blocked.")
                return True, False, ""
        except Exception as e:
            print(f"[HEARTBEAT] Could not reach server: {e}")
            return True, False, ""

    def check_blocked(self):
        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(
                f"{SERVER_BASE}/api/check/{self.lm.device_id}",
                headers={"User-Agent": "LuckyLoop-Controlbox/16.0.5"}
            )
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("blocked"):
                    return True, data.get("reason", "Your device has been blocked.")
                return False, ""
        except:
            return False, ""

    def start_background_check(self, on_blocked_callback, interval=60):
        def _loop():
            while not self._stop_event.is_set():
                for _ in range(interval * 10):
                    if self._stop_event.is_set():
                        return
                    time.sleep(0.1)
                blocked, reason = self.check_blocked()
                if blocked:
                    on_blocked_callback(reason)
                    return
        self._check_thread = threading.Thread(target=_loop, daemon=True)
        self._check_thread.start()

    def stop(self):
        self._stop_event.set()


def show_license_dialog(is_reset=False):
    license_manager = LicenseManager()
    if license_manager.is_activated and not is_reset:
        return True, license_manager

    dialog = tk.Tk()
    dialog.title("LuckyLoop - License Activation")
    dialog.geometry("520x600")
    dialog.resizable(False, False)
    dialog.configure(bg="#000000")

    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (520 // 2)
    y = (dialog.winfo_screenheight() // 2) - (600 // 2)
    dialog.geometry(f"+{x}+{y}")

    activation_done = [False]
    result_manager = [license_manager]

    def on_verify():
        license_key = entry.get()
        if not license_key.strip():
            status_label.config(text="❌ Please enter a license key!", fg="#ef4444")
            entry.focus()
            return
        if license_key not in VALID_LICENSES:
            status_label.config(text="❌ Invalid License Key!", fg="#ef4444")
            entry.delete(0, tk.END)
            entry.focus()
            return
        success, msg = license_manager.activate(license_key)
        if success:
            status_label.config(text=msg, fg="#22c55e")
            entry.config(state="disabled")
            verify_btn.config(state="disabled")
            activation_done[0] = True
            result_manager[0] = license_manager
            dialog.after(2000, dialog.destroy)
        else:
            status_label.config(text=msg, fg="#ef4444")
            entry.delete(0, tk.END)
            entry.focus()

    logo_frame = tk.Frame(dialog, bg="#000000", pady=20)
    logo_frame.pack(fill="x")
    tk.Label(logo_frame, text="⚡", font=("Arial", 50), fg="#facc15", bg="#000000").pack()
    tk.Label(logo_frame, text="LUCKYLOOP", font=("Arial", 32, "bold"), fg="#ffffff", bg="#000000").pack(pady=(5, 0))
    tk.Label(logo_frame, text="CONTROLBOX", font=("Arial", 14), fg="#00e5ff", bg="#000000").pack(pady=(3, 0))
    tk.Frame(dialog, bg="#facc15", height=3).pack(fill="x", pady=(10, 15))
    tk.Label(dialog, text="License Activation", font=("Segoe UI", 16, "bold"), fg="#ffffff", bg="#000000").pack(pady=(0, 15))

    device_frame = tk.Frame(dialog, bg="#0a0a0a", padx=20, pady=15)
    device_frame.pack(pady=10, padx=25, fill="x")
    tk.Label(device_frame, text="📱 Device Information", font=("Segoe UI", 11, "bold"), fg="#00e5ff", bg="#0a0a0a").pack(anchor="w", pady=(0, 10))
    device_info_text = f"Device ID: {license_manager.device_id}\nDevice Name: {license_manager.device_name}"
    tk.Label(device_frame, text=device_info_text, font=("Segoe UI", 9), fg="#64748b", bg="#0a0a0a", justify="left").pack(anchor="w", pady=3)

    tk.Label(dialog, text="🔑 Activate Your License Key", font=("Segoe UI", 12, "bold"), fg="#facc15", bg="#000000").pack(pady=(15, 12))

    input_frame = tk.Frame(dialog, bg="#0a0a0a", padx=20, pady=15)
    input_frame.pack(pady=10, padx=25, fill="x")
    tk.Label(input_frame, text="Enter License Key:", font=("Segoe UI", 10, "bold"), fg="#e2e8f0", bg="#0a0a0a").pack(anchor="w", pady=(0, 8))
    entry = tk.Entry(input_frame, font=("Segoe UI", 11), fg="#e2e8f0", bg="#111111", insertbackground="#00e5ff", relief="solid", bd=1, width=40)
    entry.pack(fill="x", ipady=10)
    entry.focus()

    btn_frame = tk.Frame(dialog, bg="#000000")
    btn_frame.pack(pady=(15, 10))
    verify_btn = tk.Button(btn_frame, text="✓ Verify License Key", font=("Segoe UI", 11, "bold"), fg="#000", bg="#00d4ff",
                           activebackground="#00b8cc", relief="flat", bd=0, padx=30, pady=12, cursor="hand2", command=on_verify)
    verify_btn.pack()

    status_label = tk.Label(dialog, text="", font=("Segoe UI", 10), fg="#00e5ff", bg="#000000", wraplength=500, justify="center")
    status_label.pack(pady=(10, 15))
    tk.Frame(dialog, bg="#111111", height=2).pack(fill="x", pady=(8, 0))

    footer_frame = tk.Frame(dialog, bg="#000000", pady=12)
    footer_frame.pack(fill="x", side="bottom")
    tk.Label(footer_frame, text="One License Key = One Device", font=("Segoe UI", 9, "bold"), fg="#ffffff", bg="#000000").pack()
    tk.Label(footer_frame, text="Get your license key from developer", font=("Segoe UI", 8), fg="#64748b", bg="#000000").pack(pady=(2, 0))
    tk.Label(footer_frame, text="alifmondolalif65@gmail.com", font=("Segoe UI", 7), fg="#facc15", bg="#000000").pack()

    def on_close():
        if not activation_done[0]:
            sys.exit(0)
        dialog.destroy()

    dialog.protocol("WM_DELETE_WINDOW", on_close)
    entry.bind('<Return>', lambda e: on_verify())
    dialog.mainloop()
    return activation_done[0], result_manager[0]

is_licensed, license_mgr = show_license_dialog()
if not is_licensed:
    sys.exit(0)

def ensure(pkg, import_name=None):
    import_name = import_name or pkg
    try:
        __import__(import_name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

ensure("pyperclip")
ensure("ntplib")
import pyperclip
import ntplib

API_URL       = "https://luckyloop-tracker.onrender.com/api/latest"
REFRESH_SEC   = round(random.uniform(3.0, 10.0), 3)
NUM_TOTAL_PCS = 15
PC_INDEX_HASH = (hash(license_mgr.device_id) % NUM_TOTAL_PCS)
WINDOW_WIDTH  = 580
TARGET_URL    = "https://www.microworkers.com/login.php"

STORAGE_DIR = Path.home() / ".luckyloop" / "data"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
TRACKER_FILE    = STORAGE_DIR / f"tracker_{license_mgr.device_id}.json"
WINDOW_POS_FILE = STORAGE_DIR / f"window_pos_{license_mgr.device_id}.json"

BG     = "#000000"
CARD   = "#0a0a0a"
CARD2  = "#111111"
ACCENT = "#00e5ff"
GREEN  = "#22c55e"
YELLOW = "#facc15"
RED    = "#ef4444"
TEXT   = "#e2e8f0"
MUTED  = "#64748b"
BORDER = "#1a1a1a"
WHITE  = "#ffffff"

def normalize_url(url):
    if not url:
        return ""
    url = url.strip()
    if url.startswith("//"):
        return f"https:{url}"
    if url.startswith("/") and not url.startswith("//"):
        return f"https://ttv.microworkers.com{url}"
    if url and not url.startswith("http://") and not url.startswith("https://"):
        if "microworkers.com" in url:
            return f"https://{url}"
    return url

def get_chromium_path():
    paths = [
        r"C:\Program Files\Chromium\Application\chrome.exe",
        r"C:\Program Files (x86)\Chromium\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Chromium\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Chromium\Application\chrome.exe"),
        r"C:\Program Files\Ungoogled Chromium\Application\chrome.exe",
        r"C:\Program Files (x86)\Ungoogled Chromium\Application\chrome.exe",
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def get_chromium_profiles():
    user_data = os.path.expandvars(r"%LOCALAPPDATA%\Chromium\User Data")
    profiles = []
    if not os.path.isdir(user_data):
        return profiles
    default_prefs = os.path.join(user_data, "Default", "Preferences")
    if os.path.exists(default_prefs):
        try:
            with open(default_prefs, "r", encoding="utf-8") as f:
                prefs = json.load(f)
            name = prefs.get("profile", {}).get("name", "Default")
        except:
            name = "Default"
        profiles.append(("Default", name))
    for item in sorted(os.listdir(user_data)):
        if item.startswith("Profile "):
            prefs_path = os.path.join(user_data, item, "Preferences")
            if os.path.exists(prefs_path):
                try:
                    with open(prefs_path, "r", encoding="utf-8") as f:
                        prefs = json.load(f)
                    name = prefs.get("profile", {}).get("name", item)
                except:
                    name = item
                profiles.append((item, name))
    return profiles

def open_chromium_app_mode(profile_dir, url=TARGET_URL):
    chromium_path = get_chromium_path()
    if not chromium_path:
        webbrowser.open(url)
        return
    user_data = os.path.expandvars(r"%LOCALAPPDATA%\Chromium\User Data")
    try:
        subprocess.Popen([
            chromium_path,
            f"--user-data-dir={user_data}",
            f"--profile-directory={profile_dir}",
            f"--app={url}",
            "--no-first-run",
            "--no-default-browser-check",
        ])
    except Exception as e:
        webbrowser.open(url)

def show_profile_selector_dialog(parent, url=TARGET_URL):
    chromium_path = get_chromium_path()
    if not chromium_path:
        messagebox.showerror("Chromium Not Found", "Chromium browser was not found!")
        return
    profiles = get_chromium_profiles()
    if not profiles:
        open_chromium_app_mode("Default", url)
        return

    dialog = tk.Toplevel(parent)
    dialog.title("Select Chromium Profile")
    dialog.configure(bg="#000000")
    dialog.resizable(False, False)
    dialog.grab_set()

    dialog.update_idletasks()
    w = 420
    h = min(140 + len(profiles) * 65, 520)
    x = parent.winfo_x() + (parent.winfo_width() // 2) - (w // 2)
    y = parent.winfo_y() + (parent.winfo_height() // 2) - (h // 2)
    dialog.geometry(f"{w}x{h}+{x}+{y}")

    tk.Label(dialog, text="🌐 Which Profile do you want to open?",
             font=("Segoe UI", 13, "bold"), fg="#00e5ff", bg="#000000", pady=14).pack(fill="x")
    tk.Label(dialog, text="Selected profile will open Microworkers in app-mode",
             font=("Segoe UI", 9), fg="#64748b", bg="#000000").pack()
    tk.Frame(dialog, bg="#1a1a1a", height=1).pack(fill="x", pady=8)

    canvas = tk.Canvas(dialog, bg="#000000", highlightthickness=0)
    scrollbar = tk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg="#000000")
    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True, padx=10)
    scrollbar.pack(side="right", fill="y")

    COLORS = ["#facc15", "#00e5ff", "#22c55e", "#f97316", "#a855f7", "#ec4899", "#06b6d4", "#84cc16"]

    for idx, (prof_dir, prof_name) in enumerate(profiles):
        color = COLORS[idx % len(COLORS)]
        row = tk.Frame(scroll_frame, bg="#0a0a0a", pady=10, padx=15, cursor="hand2")
        row.pack(fill="x", pady=3, padx=5)
        av = tk.Canvas(row, width=38, height=38, bg="#0a0a0a", highlightthickness=0)
        av.pack(side="left", padx=(0, 12))
        av.create_oval(2, 2, 36, 36, fill=color, outline="")
        av.create_text(19, 19, text=(prof_name[0].upper() if prof_name else "?"),
                       font=("Segoe UI", 15, "bold"), fill="#000000")
        info = tk.Frame(row, bg="#0a0a0a")
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=prof_name, font=("Segoe UI", 11, "bold"), fg="#e2e8f0", bg="#0a0a0a", anchor="w").pack(anchor="w")
        tk.Label(info, text=f"📁 {prof_dir}  •  App Mode", font=("Segoe UI", 8), fg="#64748b", bg="#0a0a0a", anchor="w").pack(anchor="w")
        arrow = tk.Label(row, text="→", font=("Segoe UI", 14, "bold"), fg=color, bg="#0a0a0a")
        arrow.pack(side="right")

        def _open(pd=prof_dir):
            dialog.destroy()
            threading.Thread(target=open_chromium_app_mode, args=(pd, url), daemon=True).start()

        for widget in [row, av, info, arrow]:
            widget.bind("<Button-1>", lambda e, pd=prof_dir: _open(pd))
        for child in info.winfo_children():
            child.bind("<Button-1>", lambda e, pd=prof_dir: _open(pd))

        def _hover_in(e, r=row):
            r.config(bg="#111111")
            for w in r.winfo_children():
                try: w.config(bg="#111111")
                except: pass

        def _hover_out(e, r=row):
            r.config(bg="#0a0a0a")
            for w in r.winfo_children():
                try: w.config(bg="#0a0a0a")
                except: pass

        row.bind("<Enter>", _hover_in)
        row.bind("<Leave>", _hover_out)

    tk.Frame(dialog, bg="#1a1a1a", height=1).pack(fill="x", pady=(8, 0))
    tk.Button(dialog, text="✕ Cancel", font=("Segoe UI", 10), fg="#64748b", bg="#000000",
              activebackground="#0a0a0a", relief="flat", bd=0, pady=8, cursor="hand2",
              command=dialog.destroy).pack(fill="x")

class PersistentTracker:
    def __init__(self, tracker_file):
        self.file = tracker_file
        self.data = {}
        self.lock = threading.Lock()
        self._load()

    def _load(self):
        if self.file.exists():
            try:
                with open(self.file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except:
                self.data = {}

    def _save(self):
        try:
            with open(self.file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except:
            pass

    def update_campaign(self, campaign, position):
        prev_key = f"{campaign}__last_position"
        ts_key   = f"{campaign}__last_changed"
        with self.lock:
            prev_position = self.data.get(prev_key)
            if prev_position != position:
                self.data[prev_key] = position
                self.data[ts_key]   = datetime.datetime.now().isoformat()
                self._save()

    def get_time_ago(self, campaign):
        ts_key = f"{campaign}__last_changed"
        ts_str = self.data.get(ts_key)
        if not ts_str:
            return "just now"
        try:
            timestamp = datetime.datetime.fromisoformat(ts_str)
            delta     = datetime.datetime.now() - timestamp
            seconds   = int(delta.total_seconds())
            return self._format(seconds)
        except:
            return "—"

    def _format(self, s):
        if s < 60:    return "a few second ago"
        if s < 3600:  return f"{s // 60} min ago"
        if s < 86400: return f"{s // 3600} hours ago"
        return f"{s // 86400} day ago"

tracker = PersistentTracker(TRACKER_FILE)

class WindowPositionManager:
    def __init__(self, pos_file):
        self.file = pos_file
        self.data = self._load()

    def _load(self):
        if self.file.exists():
            try:
                with open(self.file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save(self):
        try:
            with open(self.file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
        except:
            pass

    def save_position(self, x, y):
        self.data["x"] = x
        self.data["y"] = y
        self._save()

    def get_position(self):
        return self.data.get("x"), self.data.get("y")

window_manager = WindowPositionManager(WINDOW_POS_FILE)

class ApiScraper(threading.Thread):
    def __init__(self, on_data, on_error, refresh_sec):
        super().__init__(daemon=True)
        self.on_data            = on_data
        self.on_error           = on_error
        self.refresh_sec        = refresh_sec
        self._stop              = threading.Event()
        self.consecutive_errors = 0

    def _fetch(self):
        import urllib.request, ssl
        ctx = ssl.create_default_context()
        req = urllib.request.Request(API_URL, headers={"User-Agent": "LuckyLoop-Controlbox/16.0.5"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            raw  = resp.read().decode("utf-8")
            data = json.loads(raw)
            if isinstance(data, dict) and "jobs" in data:
                return data
            return {"jobs": data, "scraper_ok": True, "scraper_msg": "OK"}

    def run(self):
        while not self._stop.is_set():
            try:
                fetched     = self._fetch()
                rows_raw    = fetched.get("jobs", [])
                scraper_ok  = fetched.get("scraper_ok", True)
                scraper_msg = fetched.get("scraper_msg", "OK")
                rows = []
                for r in rows_raw:
                    campaign  = str(r.get("job_name",  ""))
                    position  = str(r.get("position",  "") or "—")
                    available = str(r.get("available", "") or "—")
                    updated   = str(r.get("updated_at","") or "—")
                    link      = str(r.get("link",      "") or "")
                    tracker.update_campaign(campaign, position)
                    rows.append({"campaign": campaign, "position": position,
                                 "available": available, "updated": updated, "link": link})
                self.consecutive_errors = 0
                self.on_data({
                    "live"       : True,
                    "last_sync"  : datetime.datetime.now().strftime("%I:%M:%S %p"),
                    "rows"       : rows,
                    "scraper_ok" : scraper_ok,
                    "scraper_msg": scraper_msg,
                })
            except Exception as e:
                self.consecutive_errors += 1
                self.on_error(f"❌ {str(e)[:60]}")
                sleep_time = min(30, self.refresh_sec * self.consecutive_errors)
                for _ in range(int(sleep_time * 10)):
                    if self._stop.is_set():
                        return
                    time.sleep(0.1)
                continue
            for _ in range(int(self.refresh_sec * 10)):
                if self._stop.is_set():
                    return
                time.sleep(0.1)

    def stop(self):
        self._stop.set()

# ══════════════════════════════════════════════════════
# NETWORK TIME SYNC — ntplib RFC 5905 + Multi-Server Best Sample
# ══════════════════════════════════════════════════════

class NetworkTimeSync:

    _NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW

    _NTP_SERVERS = [
        "time.google.com",
        "time.nist.gov",
        "time.windows.com",
        "pool.ntp.org",
        "time.cloudflare.com",
    ]

    @staticmethod
    def _run(cmd, timeout=10):
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=NetworkTimeSync._NO_WINDOW
        )

    @staticmethod
    def get_ntp_time():
        c = ntplib.NTPClient()
        samples = []

        for server in NetworkTimeSync._NTP_SERVERS:
            for _ in range(2):
                try:
                    resp = c.request(server, version=3, timeout=4)
                    samples.append({
                        'offset':      resp.offset,
                        'delay':       resp.delay,
                        'dispersion':  resp.root_dispersion,
                        'tx_time':     resp.tx_time,
                    })
                except:
                    continue

        if not samples:
            raise Exception("Could not get time from any NTP server")

        samples.sort(key=lambda x: x['delay'])
        best = samples[:max(1, len(samples) // 2)]
        avg_offset = sum(s['offset'] for s in best) / len(best)
        corrected_ts = time.time() + avg_offset
        return datetime.datetime.utcfromtimestamp(corrected_ts)

    @staticmethod
    def set_windows_time(dt_utc):
        class SYSTEMTIME(ctypes.Structure):
            _fields_ = [
                ("wYear",         ctypes.c_ushort),
                ("wMonth",        ctypes.c_ushort),
                ("wDayOfWeek",    ctypes.c_ushort),
                ("wDay",          ctypes.c_ushort),
                ("wHour",         ctypes.c_ushort),
                ("wMinute",       ctypes.c_ushort),
                ("wSecond",       ctypes.c_ushort),
                ("wMilliseconds", ctypes.c_ushort),
            ]

        st = SYSTEMTIME(
            dt_utc.year, dt_utc.month, dt_utc.weekday(),
            dt_utc.day,  dt_utc.hour, dt_utc.minute,
            dt_utc.second, dt_utc.microsecond // 1000
        )
        result = ctypes.windll.kernel32.SetSystemTime(ctypes.byref(st))
        return result != 0

    @staticmethod
    def sync_time_force():
        if sys.platform != "win32":
            return False, "⚠️ Only works on Windows"

        try:
            ntp_time = NetworkTimeSync.get_ntp_time()
        except Exception as e:
            return False, f"⚠️ NTP error: {str(e)[:50]}"

        try:
            success = NetworkTimeSync.set_windows_time(ntp_time)
            local_now = datetime.datetime.now().strftime("%I:%M:%S %p")

            try:
                NetworkTimeSync._run(["net", "start", "w32time"])
                time.sleep(0.3)
                NetworkTimeSync._run(["w32tm", "/resync", "/force"], timeout=15)
            except:
                pass

            if success:
                return True, f"✅ Time synced! ({local_now})"
            else:
                return True, f"✅ Sync complete ({local_now})"
        except Exception as e:
            return False, f"⚠️ Could not set time: {str(e)[:50]}"

    @staticmethod
    def windows_sync_now():
        if sys.platform != "win32":
            return False, "⚠️ Only works on Windows"
        try:
            subprocess.run(
                ["net", "start", "w32time"],
                capture_output=True, text=True, timeout=10,
                creationflags=0x08000000
            )
            time.sleep(0.3)
            result = subprocess.run(
                ["w32tm", "/resync", "/force"],
                capture_output=True, text=True, timeout=15,
                creationflags=0x08000000
            )
            local_now = datetime.datetime.now().strftime("%I:%M:%S %p")
            if result.returncode == 0:
                return True, f"✅ Windows Sync successful! ({local_now})"
            else:
                err = (result.stderr.strip() or result.stdout.strip())[:60]
                return False, f"⚠️ Sync error: {err}"
        except Exception as e:
            return False, f"❌ Error: {str(e)[:60]}"

    @staticmethod
    def get_system_time():
        return datetime.datetime.now()


class InstantApp(tk.Tk):
    def __init__(self, license_manager):
        super().__init__()
        self.license_manager = license_manager
        self.title("Luckyloop Controlbox v16.0.5")

        screen_h      = self.winfo_screenheight()
        TASKBAR_H     = 60
        MARGIN        = 10
        max_h         = screen_h - TASKBAR_H - MARGIN
        WINDOW_HEIGHT = max(min(800, max_h), 550)

        saved_x, saved_y = window_manager.get_position()
        if saved_x is not None and saved_y is not None:
            saved_x = max(0, min(saved_x, self.winfo_screenwidth() - WINDOW_WIDTH))
            saved_y = max(0, min(saved_y, screen_h - WINDOW_HEIGHT - TASKBAR_H))
            self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{saved_x}+{saved_y}")
        else:
            start_x = self.winfo_screenwidth() - WINDOW_WIDTH - 20
            self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{start_x}+20")

        self.resizable(False, False)
        self.configure(bg=BG)

        self._scraper       = None
        self._executor      = ThreadPoolExecutor(max_workers=2)
        self._last_rows     = []
        self._playing       = True
        self._popup_after   = None
        self._popup_buttons = {}
        self._clock_popup   = None

        self._phpsessid_expired = False

        self._auto_sync_stop = threading.Event()

        self._device_checker = DeviceChecker(self.license_manager)

        ok, blocked, reason = self._device_checker.send_heartbeat()
        if blocked:
            self._show_blocked_and_exit(reason)
            return

        self._device_checker.start_background_check(
            on_blocked_callback=lambda r: self.after(0, self._show_blocked_and_exit, r),
            interval=60
        )

        self._build()
        self.protocol("WM_DELETE_WINDOW", self._quit)
        self.bind("<Configure>", self._on_configure)
        self._launch_scraper()
        self._start_time_refresher()
        atexit.register(self._cleanup)

        self._auto_sync_interval = 30 * 1000  # 30 seconds
        self._auto_sync_loop()

    def _show_blocked_and_exit(self, reason="Your device has been blocked."):
        try:
            for widget in self.winfo_children():
                widget.destroy()
        except:
            pass
        try:
            self.configure(bg="#000000")
            try:
                self.resizable(False, False)
                self.geometry("480x360")
                self.update_idletasks()
                x = (self.winfo_screenwidth() // 2) - 240
                y = (self.winfo_screenheight() // 2) - 180
                self.geometry(f"480x360+{x}+{y}")
            except:
                pass

            frame = tk.Frame(self, bg="#000000")
            frame.place(relx=0.5, rely=0.5, anchor="center")

            tk.Label(frame, text="🚫", font=("Arial", 52), bg="#000000").pack(pady=(0, 8))
            tk.Label(frame, text="ACCESS BLOCKED",
                     font=("Segoe UI", 20, "bold"), fg="#ef4444", bg="#000000").pack()
            tk.Frame(frame, bg="#ef4444", height=2, width=300).pack(pady=10)
            tk.Label(frame, text=reason,
                     font=("Segoe UI", 11), fg="#94a3b8", bg="#000000",
                     wraplength=380, justify="center").pack(pady=(0, 20))
            tk.Label(frame, text="Contact us:",
                     font=("Segoe UI", 9), fg="#64748b", bg="#000000").pack()
            tk.Label(frame, text="alifmondolalif65@gmail.com",
                     font=("Segoe UI", 10, "bold"), fg="#facc15", bg="#000000").pack(pady=(2, 20))
            tk.Button(frame, text="  Close  ", font=("Segoe UI", 10, "bold"),
                      fg="#ffffff", bg="#ef4444", activebackground="#dc2626",
                      relief="flat", padx=20, pady=10,
                      cursor="hand2", command=self.destroy).pack()
        except:
            pass
        try:
            self.after(15_000, self.destroy)
        except:
            pass

    def _on_configure(self, event):
        if event.widget == self:
            window_manager.save_position(self.winfo_x(), self.winfo_y())

    def _build(self):
        self._header()
        self._build_cookie_bar()
        self._table_wrap = tk.Frame(self, bg=BG)
        self._table_wrap.pack(fill="both", expand=True)
        self._table()
        self._footer()

    def _header(self):
        bar = tk.Frame(self, bg=CARD, pady=12)
        bar.pack(fill="x")

        left = tk.Frame(bar, bg=CARD)
        left.pack(side="left", padx=15)

        self._dot = tk.Canvas(left, width=10, height=10, bg=CARD, highlightthickness=0)
        self._dot.pack(side="left", padx=(0, 7))
        self._dot_id = self._dot.create_oval(1, 1, 9, 9, fill=GREEN, outline="")

        tk.Label(left, text="LuckyLoop", font=("Segoe UI", 18, "bold"), fg=WHITE, bg=CARD).pack(side="left")
        tk.Label(left, text=" Position Update", font=("Segoe UI", 14), fg=YELLOW, bg=CARD).pack(side="left")

        # ✅ VERSION LABEL — এখানে version show হবে
        tk.Label(left, text=f"  v{CURRENT_VERSION}", font=("Segoe UI", 8), fg=MUTED, bg=CARD).pack(side="left", pady=(8, 0))

        right = tk.Frame(bar, bg=CARD)
        right.pack(side="right", padx=15)

        license_frame = tk.Frame(right, bg=CARD)
        license_frame.pack()
        license_text, license_color = self.license_manager.get_license_info()
        self._license_lbl = tk.Label(license_frame, text=license_text, font=("Segoe UI", 8), fg=license_color, bg=CARD)
        self._license_lbl.pack(side="left", padx=(0, 5))

        reset_btn = tk.Button(license_frame, text="🔄", font=("Segoe UI", 7, "bold"), fg="#fff", bg="#ff6b6b",
                              activebackground="#ff5252", relief="flat", bd=0, padx=4, pady=0,
                              cursor="hand2", command=self._reset_license)
        reset_btn.pack(side="left")

    def _build_cookie_bar(self):
        self._cookie_bar = tk.Frame(self, bg="#3d0000", pady=8)

        left_part = tk.Frame(self._cookie_bar, bg="#3d0000")
        left_part.pack(side="left", padx=12, fill="x", expand=True)

        tk.Label(left_part, text="⚠️  Server Is Down!",
                 font=("Segoe UI", 10, "bold"), fg="#fca5a5", bg="#3d0000").pack(side="left")

        self._cookie_detail_lbl = tk.Label(left_part, text="  Due to a technical issue. Please wait a moment....",
                                           font=("Segoe UI", 9), fg="#fecaca", bg="#3d0000")
        self._cookie_detail_lbl.pack(side="left")

    def _reset_license(self):
        self._executor.submit(self._do_reset_license)

    def _do_reset_license(self):
        self.after(0, lambda: self._set_status("🔄 Resetting…", YELLOW))
        if self._scraper:
            self._scraper.stop()
            time.sleep(1)
        self.license_manager.deactivate()
        is_licensed, new_license_mgr = show_license_dialog(is_reset=True)
        if is_licensed:
            self.license_manager = new_license_mgr
            license_text, license_color = self.license_manager.get_license_info()
            self.after(0, lambda: self._license_lbl.config(text=license_text, fg=license_color))
            self.after(0, lambda: self._set_status("✅ License Changed", GREEN))
            self._launch_scraper()
        else:
            self.after(0, self._quit)

    def _table(self):
        wrap = self._table_wrap
        tk.Label(wrap, text="Campaign Updates", font=("Segoe UI", 9, "bold"),
                 fg=GREEN, bg=BG, pady=6).pack(anchor="w", padx=12)

        self._COLS = [("Campaign", 5), ("", 1), ("Position", 6), ("Available", 5), ("Update at", 7), ("Links", 6)]

        hbar = tk.Frame(wrap, bg=CARD2, pady=8)
        hbar.pack(fill="x", padx=12)
        for title, w in self._COLS:
            if title == "":
                tk.Frame(hbar, bg=CARD2, width=int(w * 10)).pack(side="left")
            else:
                tk.Label(hbar, text=title, font=("Segoe UI", 11, "bold"), fg=GREEN, bg=CARD2,
                         anchor="center", width=int(w * 1.2)).pack(side="left", expand=True, fill="x", padx=3)

        cf = tk.Frame(wrap, bg=BG)
        cf.pack(fill="both", expand=True, padx=12)

        self._cv = tk.Canvas(cf, bg=BG, highlightthickness=0)
        self._cv.pack(side="left", fill="both", expand=True)

        self._body = tk.Frame(self._cv, bg=BG)
        self._body_win = self._cv.create_window((0, 0), window=self._body, anchor="nw")

        self._body.bind("<Configure>", lambda _: self._cv.configure(scrollregion=self._cv.bbox("all")))
        self._cv.bind("<Configure>", lambda e: self._cv.itemconfig(self._body_win, width=e.width))
        self._cv.bind_all("<MouseWheel>", lambda e: self._cv.yview_scroll(-1 * (e.delta // 120), "units"))
        self._cv.bind_all("<Button-4>",   lambda e: self._cv.yview_scroll(-1, "units"))
        self._cv.bind_all("<Button-5>",   lambda e: self._cv.yview_scroll(1, "units"))

        tk.Label(self._body, text="⏳ Connecting to server…",
                 font=("Segoe UI", 9), fg=MUTED, bg=BG, pady=25).pack()

    def _show_clock_dialog(self):
        if self._clock_popup and self._clock_popup.winfo_exists():
            self._clock_popup.destroy()

        self._clock_popup = tk.Toplevel(self)
        self._clock_popup.title("Network Time Update")
        self._clock_popup.geometry("420x400")
        self._clock_popup.resizable(False, False)
        self._clock_popup.configure(bg=CARD)
        self._clock_popup.grab_set()

        self._clock_popup.update_idletasks()
        x = self.winfo_x() + self.winfo_width() - 440
        y = self.winfo_y() + self.winfo_height() - 430
        self._clock_popup.geometry(f"+{x}+{y}")

        tk.Label(self._clock_popup, text="🕐 Network Time Sync",
                 font=("Segoe UI", 12, "bold"), fg=ACCENT, bg=CARD).pack(pady=10)

        tk.Frame(self._clock_popup, bg=BORDER, height=1).pack(fill="x")

        current_time = NetworkTimeSync.get_system_time().strftime("%I:%M:%S %p")
        self._time_label = tk.Label(self._clock_popup, text=current_time,
                                    font=("Segoe UI", 20, "bold"), fg=GREEN, bg=CARD)
        self._time_label.pack(pady=(10, 2))

        current_date = NetworkTimeSync.get_system_time().strftime("%A, %B %d, %Y")
        self._date_label = tk.Label(self._clock_popup, text=current_date,
                                    font=("Segoe UI", 9), fg=MUTED, bg=CARD)
        self._date_label.pack(pady=2)

        tk.Frame(self._clock_popup, bg=BORDER, height=1).pack(fill="x", pady=6)

        last_sync_frame = tk.Frame(self._clock_popup, bg=CARD2, padx=12, pady=8)
        last_sync_frame.pack(fill="x", padx=15)

        tk.Label(last_sync_frame, text="🔍 Windows Last Sync Status",
                 font=("Segoe UI", 8, "bold"), fg=ACCENT, bg=CARD2).pack(anchor="w")

        self._sync_status_lbl = tk.Label(last_sync_frame,
                                          text="⏳ Checking...",
                                          font=("Segoe UI", 8), fg=MUTED, bg=CARD2,
                                          wraplength=360, justify="left")
        self._sync_status_lbl.pack(anchor="w", pady=(4, 0))

        tk.Frame(self._clock_popup, bg=BORDER, height=1).pack(fill="x", pady=6)

        self._status_label = tk.Label(self._clock_popup,
                                      text="🌐 Update Now",
                                      font=("Segoe UI", 9), fg=MUTED, bg=CARD, wraplength=380)
        self._status_label.pack(pady=4, padx=10)

        btn_frame = tk.Frame(self._clock_popup, bg=CARD)
        btn_frame.pack(pady=12)

        update_now_btn = tk.Button(btn_frame, text="🌐 Update Now (NTP)",
                                   font=("Segoe UI", 10, "bold"),
                                   fg="#000000", bg=ACCENT, activebackground="#00b8cc",
                                   relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
                                   command=self._do_network_sync)
        update_now_btn.pack(side="left", padx=5)

        tk.Button(btn_frame, text="Close", font=("Segoe UI", 10, "bold"),
                  fg=WHITE, bg=RED, activebackground="#dc2626",
                  relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
                  command=self._clock_popup.destroy).pack(side="left", padx=5)

        def _update_time():
            if self._clock_popup and self._clock_popup.winfo_exists():
                try:
                    current_time = NetworkTimeSync.get_system_time().strftime("%I:%M:%S %p")
                    self._time_label.config(text=current_time)
                    self._clock_popup.after(500, _update_time)
                except:
                    pass

        _update_time()

        def _fetch_sync_status():
            try:
                result = subprocess.run(
                    ["w32tm", "/query", "/status"],
                    capture_output=True, text=True, timeout=8,
                    creationflags=0x08000000
                )
                output = result.stdout.strip()
                last_sync = "Not found"
                source = ""
                for line in output.splitlines():
                    if "Last Successful Sync Time" in line or "Last Sync Time" in line:
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            last_sync = parts[1].strip()
                    if "Source" in line:
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            source = parts[1].strip()

                if last_sync and last_sync != "Not found":
                    display = f"✅ Last sync: {last_sync}"
                    if source:
                        display += f"\n🌐 Server: {source}"
                    color = GREEN
                else:
                    display = "⚠️ Sync info not found\n(Check if 'Set time automatically' is ON in Windows Settings)"
                    color = YELLOW

                if self._clock_popup and self._clock_popup.winfo_exists():
                    self.after(0, lambda: self._sync_status_lbl.config(text=display, fg=color))
            except Exception as e:
                if self._clock_popup and self._clock_popup.winfo_exists():
                    self.after(0, lambda: self._sync_status_lbl.config(
                        text=f"⚠️ Could not get status: {str(e)[:40]}", fg=YELLOW))

        threading.Thread(target=_fetch_sync_status, daemon=True).start()

    def _do_network_sync(self):
        self._executor.submit(self._background_network_sync)

    def _background_network_sync(self):
        try:
            self.after(0, lambda: self._status_label.config(
                text="🔄 Fetching time from 5 NTP servers, please wait...", fg=YELLOW))

            success, msg = NetworkTimeSync.sync_time_force()

            self.after(0, lambda: self._update_clock_display())

            if success:
                self.after(0, lambda: self._status_label.config(text=msg, fg=GREEN))
                self.after(0, lambda: self._set_status(msg, GREEN))
            else:
                self.after(0, lambda: self._status_label.config(text=msg, fg=RED))
                self.after(0, lambda: self._set_status(msg, RED))
        except Exception as e:
            msg = f"❌ Error: {str(e)[:70]}"
            self.after(0, lambda: self._status_label.config(text=msg, fg=RED))
            self.after(0, lambda: self._set_status(msg, RED))

    def _do_windows_sync_now(self):
        self._executor.submit(self._background_windows_sync_now)

    def _background_windows_sync_now(self):
        try:
            self.after(0, lambda: self._status_label.config(
                text="🔄 Running Windows Sync Now...", fg=YELLOW))

            success, msg = NetworkTimeSync.windows_sync_now()

            self.after(0, lambda: self._update_clock_display())

            if success:
                self.after(0, lambda: self._status_label.config(text=msg, fg=GREEN))
                self.after(0, lambda: self._set_status(msg, GREEN))
            else:
                self.after(0, lambda: self._status_label.config(text=msg, fg=RED))
                self.after(0, lambda: self._set_status(msg, RED))
        except Exception as e:
            msg = f"❌ Error: {str(e)[:70]}"
            self.after(0, lambda: self._status_label.config(text=msg, fg=RED))
            self.after(0, lambda: self._set_status(msg, RED))

    def _update_clock_display(self):
        if self._clock_popup and self._clock_popup.winfo_exists():
            try:
                current_time = NetworkTimeSync.get_system_time().strftime("%I:%M:%S %p")
                self._time_label.config(text=current_time)
            except:
                pass

            def _refresh_status():
                try:
                    result = subprocess.run(
                        ["w32tm", "/query", "/status"],
                        capture_output=True, text=True, timeout=8,
                        creationflags=0x08000000
                    )
                    last_sync = "Not found"
                    source = ""
                    for line in result.stdout.splitlines():
                        if "Last Successful Sync Time" in line or "Last Sync Time" in line:
                            parts = line.split(":", 1)
                            if len(parts) > 1:
                                last_sync = parts[1].strip()
                        if "Source" in line:
                            parts = line.split(":", 1)
                            if len(parts) > 1:
                                source = parts[1].strip()
                    if last_sync != "Not found":
                        display = f"✅ Last sync: {last_sync}"
                        if source:
                            display += f"\n🌐 Server: {source}"
                        color = GREEN
                    else:
                        display = "⚠️ Sync info not found"
                        color = YELLOW
                    if self._clock_popup and self._clock_popup.winfo_exists():
                        self.after(0, lambda: self._sync_status_lbl.config(text=display, fg=color))
                except:
                    pass
            threading.Thread(target=_refresh_status, daemon=True).start()

    def _footer(self):
        ft = tk.Frame(self, bg=BG, pady=3)
        ft.pack(fill="x", side="bottom")

        self._status = tk.Label(ft, text="⏳ Starting…", font=("Segoe UI", 8), fg=YELLOW, bg=BG)
        self._status.pack(side="right", padx=10)

        left_footer = tk.Frame(ft, bg=BG)
        left_footer.pack(side="left", padx=10)

        self._footer_dot = tk.Canvas(left_footer, width=8, height=8, bg=BG, highlightthickness=0)
        self._footer_dot.pack(side="left", padx=(0, 5))
        self._footer_dot_id = self._footer_dot.create_oval(1, 1, 7, 7, fill=GREEN, outline="")

        tk.Label(left_footer, text="Direct API", font=("Segoe UI", 8), fg=MUTED, bg=BG).pack(side="left")
        tk.Label(ft, text=" | ", font=("Segoe UI", 8), fg=MUTED, bg=BG).pack(side="left")
        tk.Label(ft, text=f"Refresh: {REFRESH_SEC}s", font=("Segoe UI", 8), fg=MUTED, bg=BG).pack(side="left")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", side="bottom")

        toolbar = tk.Frame(self, bg=CARD, pady=0)
        toolbar.pack(fill="x", side="bottom")

        def _tb(text, cmd):
            b = tk.Button(toolbar, text=text, font=("Segoe UI", 18), fg=WHITE,
                          bg=CARD, activebackground=CARD2, activeforeground=ACCENT,
                          relief="flat", bd=0, pady=4, padx=0, cursor="hand2", command=cmd)
            b.pack(side="left", expand=True, fill="x")
            return b

        _tb("↻", self._launch_scraper)
        self._play_btn = _tb("▶", self._open_browser)
        _tb("🔔", lambda: messagebox.showinfo("Notifications", "No new notifications."))
        _tb("🕐", self._show_clock_dialog)
        _tb("✕", self._quit)
        _tb("⋮", self._show_menu)

    def _open_browser(self):
        self._set_status("🌐 Opening profile selector…", ACCENT)
        show_profile_selector_dialog(self, TARGET_URL)

    def _show_menu(self):
        menu = tk.Menu(self, tearoff=0, bg=CARD2, fg=TEXT,
                       activebackground=ACCENT, activeforeground="#000",
                       font=("Segoe UI", 10))
        menu.add_command(label="🔄  Reset License", command=self._reset_license)
        menu.add_separator()
        menu.add_command(label="❌  Exit", command=self._quit)
        try:
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()

    def _show_copied_popup(self, btn_id):
        btn_widget = self._popup_buttons.get(btn_id)
        if not btn_widget:
            return
        if self._popup_after:
            try:
                self.after_cancel(self._popup_after)
            except:
                pass
            self._popup_after = None

        original_bg = btn_widget.master["bg"]
        btn_widget.config(text="✓ Copied!", fg="#000000", bg="#22c55e",
                          font=("Segoe UI", 8, "bold"), activebackground="#16a34a",
                          state="disabled")

        def _reset():
            try:
                if btn_id in self._popup_buttons:
                    btn_widget.config(text="🔗", fg=WHITE, bg=original_bg,
                                      font=("Segoe UI", 13), activebackground=CARD2,
                                      state="normal")
            except:
                pass
            self._popup_after = None

        self._popup_after = self.after(1500, _reset)

    def _make_row(self, r, bg):
        frame = tk.Frame(self._body, bg=bg)
        frame.pack(fill="x")
        tk.Frame(self._body, bg=BORDER, height=2).pack(fill="x")

        campaign    = r.get("campaign",  "")
        position    = r.get("position",  "")
        available   = r.get("available", "")
        updated_str = tracker.get_time_ago(campaign)

        tk.Label(frame, text=campaign, font=("Segoe UI", 11), fg=TEXT, bg=bg,
                 anchor="center", width=6).pack(side="left", expand=True, fill="x", padx=4, pady=8)
        tk.Frame(frame, bg=bg, width=10).pack(side="left")
        tk.Label(frame, text=position, font=("Segoe UI", 11), fg=TEXT, bg=bg,
                 anchor="center", width=8).pack(side="left", expand=True, fill="x", padx=4, pady=8)

        try:
            av_int   = int(available)
            av_color = GREEN if av_int >= 10 else (YELLOW if av_int >= 5 else RED) if av_int > 0 else MUTED
        except:
            av_color = TEXT

        tk.Label(frame, text=available, font=("Segoe UI", 11, "bold"), fg=av_color, bg=bg,
                 anchor="center", width=6).pack(side="left", expand=True, fill="x", padx=4, pady=8)
        tk.Label(frame, text=updated_str, font=("Segoe UI", 11, "bold"), fg=TEXT, bg=bg,
                 anchor="center", width=10).pack(side="left", expand=True, fill="x", padx=4, pady=8)

        link_container = tk.Frame(frame, bg=bg, width=50, height=24)
        link_container.pack(side="left", padx=4, pady=8)
        link_container.pack_propagate(False)

        link = normalize_url(r.get("link", ""))
        if link:
            btn_id = f"{id(frame)}_{campaign}"
            link_btn = tk.Button(link_container, text="🔗", font=("Segoe UI", 13), fg=WHITE, bg=bg,
                                 activebackground=CARD2, relief="flat", bd=0,
                                 padx=2, pady=0, cursor="hand2")
            link_btn.pack(side="left", anchor="center", expand=True, fill="both")
            self._popup_buttons[btn_id] = link_btn

            def _copy_link(btn_id=btn_id, url=link):
                pyperclip.copy(url)
                self._show_copied_popup(btn_id)

            link_btn.config(command=_copy_link)
        else:
            tk.Label(link_container, text="—", font=("Segoe UI", 9), fg=MUTED, bg=bg).pack(anchor="center", expand=True)

    def _render_rows(self, rows):
        for w in self._body.winfo_children():
            w.destroy()
        self._popup_buttons.clear()
        if not rows:
            tk.Label(self._body, text="No data yet. Waiting for server…",
                     font=("Segoe UI", 9), fg=MUTED, bg=BG, pady=22).pack()
            return
        for idx, r in enumerate(rows):
            bg = CARD if idx % 2 == 0 else CARD2
            self._make_row(r, bg)
        self._cv.yview_moveto(0)

    def _start_time_refresher(self):
        if self._last_rows:
            self._render_rows(self._last_rows)
        self.after(30_000, self._start_time_refresher)

    def _auto_sync_loop(self):
        if not self._auto_sync_stop.is_set():
            t = threading.Thread(target=self._background_auto_sync, daemon=True)
            t.start()
        self.after(self._auto_sync_interval, self._auto_sync_loop)

    def _background_auto_sync(self):
        if self._auto_sync_stop.is_set():
            return
        try:
            success, msg = NetworkTimeSync.sync_time_force()
            if success:
                self.after(0, lambda: self._set_status("🕐 " + msg, GREEN))
            else:
                self.after(0, lambda: self._set_status("⚠️ Auto sync: " + msg, YELLOW))
        except Exception as e:
            self.after(0, lambda: self._set_status(f"⚠️ Auto sync error: {str(e)[:40]}", YELLOW))

    def _launch_scraper(self):
        if self._scraper:
            self._scraper.stop()
        self._playing = True
        if hasattr(self, '_play_btn'):
            self._play_btn.config(text="▶")
        self._set_status("⏳ Connecting…", YELLOW)
        self._scraper = ApiScraper(
            on_data=lambda d: self.after(0, self._apply, d),
            on_error=lambda e: self.after(0, self._set_status, e, RED),
            refresh_sec=REFRESH_SEC
        )
        self._scraper.start()

    def _apply(self, data):
        live = data.get("live", False)
        self._dot.itemconfig(self._dot_id, fill=GREEN if live else RED)
        if hasattr(self, '_footer_dot_id'):
            self._footer_dot.itemconfig(self._footer_dot_id, fill=GREEN if live else RED)

        scraper_ok  = data.get("scraper_ok", True)
        scraper_msg = data.get("scraper_msg", "")

        if not scraper_ok:
            if not self._phpsessid_expired:
                self._phpsessid_expired = True
                self._cookie_bar.pack(fill="x")
            self._set_status("⚠️ Server Is Down! Please Wait...", "#fca5a5")
        else:
            if self._phpsessid_expired:
                self._phpsessid_expired = False
                self._cookie_bar.pack_forget()
            self._set_status("✅ Updated", GREEN)

        rows = data.get("rows", [])

        if self._last_rows:
            new_data_map = {row.get("campaign"): row for row in rows}
            for existing_row in self._last_rows:
                campaign = existing_row.get("campaign")
                if campaign in new_data_map:
                    existing_row["position"]  = new_data_map[campaign]["position"]
                    existing_row["available"] = new_data_map[campaign]["available"]
                    existing_row["updated"]   = new_data_map[campaign]["updated"]
                    existing_row["link"]      = new_data_map[campaign]["link"]
            existing_campaigns = {r.get("campaign") for r in self._last_rows}
            for row in rows:
                if row.get("campaign") not in existing_campaigns:
                    self._last_rows.append(row)
        else:
            self._last_rows = rows

        self._render_rows(self._last_rows)

    def _set_status(self, msg, color=TEXT):
        try:
            self._status.config(text=msg, fg=color)
        except:
            pass

    def _cleanup(self):
        try:
            self._auto_sync_stop.set()
        except:
            pass
        try:
            if self._scraper:
                self._scraper.stop()
        except:
            pass
        try:
            self._executor.shutdown(wait=False)
        except:
            pass
        try:
            if hasattr(self, '_device_checker'):
                self._device_checker.stop()
        except:
            pass

    def _quit(self):
        self._cleanup()
        self.destroy()

if __name__ == "__main__":
    app = InstantApp(license_mgr)
    app.mainloop()
