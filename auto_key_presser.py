import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import sys
import platform

import pydirectinput
import keyboard

# Pillow (optionnel)
try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False


def app_root_dir() -> str:
    """
    Renvoie le dossier racine de l'app (compatible PyInstaller).
    - En .py: dossier du fichier
    - En .exe PyInstaller: sys._MEIPASS
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def asset_path(*parts: str) -> str:
    return os.path.join(app_root_dir(), "assets", *parts)


def set_windows_appusermodelid(app_id: str):
    """
    Aide Windows à associer correctement l'icône dans la barre des tâches (surtout en .exe).
    """
    if platform.system().lower() != "windows":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass


class CanvasToggleButton(tk.Canvas):
    """
    Bouton custom Canvas : taille en pixels => contrôle parfait de largeur/hauteur.
    """
    def __init__(
        self, master, width, height, radius=14,
        font=("Segoe UI", 12, "bold"),
        fg="#ffffff",
        bg_off="#20c05c", bg_on="#d11f2f",
        hover_off="#24d66a", hover_on="#e12538",
        command=None, canvas_bg="#12151c"
    ):
        super().__init__(master, width=width, height=height, highlightthickness=0, bd=0, bg=canvas_bg)
        self.w = width
        self.h = height
        self.r = radius
        self.font = font
        self.fg = fg

        self.bg_off = bg_off
        self.bg_on = bg_on
        self.hover_off = hover_off
        self.hover_on = hover_on

        self.command = command
        self.running = False
        self.hover = False

        self.configure(cursor="hand2")

        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)

        self.draw()

    def set_running(self, running: bool):
        self.running = running
        self.draw()

    def _click(self, _e=None):
        if callable(self.command):
            self.command()

    def _enter(self, _e=None):
        self.hover = True
        self.draw()

    def _leave(self, _e=None):
        self.hover = False
        self.draw()

    def _rounded_rect(self, x1, y1, x2, y2, r, color):
        self.create_rectangle(x1 + r, y1, x2 - r, y2, fill=color, outline=color)
        self.create_rectangle(x1, y1 + r, x2, y2 - r, fill=color, outline=color)
        self.create_oval(x1, y1, x1 + 2 * r, y1 + 2 * r, fill=color, outline=color)
        self.create_oval(x2 - 2 * r, y1, x2, y1 + 2 * r, fill=color, outline=color)
        self.create_oval(x1, y2 - 2 * r, x1 + 2 * r, y2, fill=color, outline=color)
        self.create_oval(x2 - 2 * r, y2 - 2 * r, x2, y2, fill=color, outline=color)

    def draw(self):
        self.delete("all")

        if self.running:
            base = self.bg_on
            hover = self.hover_on
            text = "DÉSACTIVER"
        else:
            base = self.bg_off
            hover = self.hover_off
            text = "ACTIVER"

        color = hover if self.hover else base

        pad = 2
        self._rounded_rect(pad, pad, self.w - pad, self.h - pad, self.r, color)
        self.create_text(self.w // 2, self.h // 2, text=text, fill=self.fg, font=self.font)


class AutoKeyPresser:
    def __init__(self, root):
        # ✅ aide taskbar Windows (surtout en .exe)
        set_windows_appusermodelid("AntiAFKRoblox.Tool")

        self.root = root
        self.root.title("Anti-AFK Roblox")
        self.root.geometry("520x480")
        self.root.resizable(False, False)

        # ---------- COLORS ----------
        self.BG = "#0f1115"
        self.CARD = "#12151c"
        self.WHITE = "#ffffff"
        self.MUTED = "#b9bcc4"
        self.RED = "#d11f2f"
        self.GREEN = "#20c05c"
        self.HOVER_RED = "#e12538"
        self.HOVER_GREEN = "#24d66a"

        self.root.configure(bg=self.BG)

        # ✅ Icône fenêtre (haut-gauche) : ICO + fallback PNG
        self._apply_window_icons()

        # ---------- STATE ----------
        self.running = False
        self.count = 0
        self.selected_key = None
        self.selected_hotkey = None
        self.waiting_for_key = False
        self.waiting_for_hotkey = False
        self.hotkey_handle = None

        # ---------- STYLE ----------
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=self.BG)
        style.configure("TLabel", background=self.BG, foreground="#e8e8e8", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), foreground=self.WHITE)
        style.configure("Sub.TLabel", font=("Segoe UI", 9), foreground=self.MUTED)
        style.configure("Card.TFrame", background=self.CARD)

        # ---------- LAYOUT ----------
        container = ttk.Frame(root)
        container.pack(fill="both", expand=True, padx=18, pady=18)

        # ---------- HEADER ----------
        header = ttk.Frame(container)
        header.pack(fill="x")

        self.logo_img = None
        logo_png = asset_path("logo.png")
        if PIL_OK and os.path.exists(logo_png):
            try:
                img = Image.open(logo_png).convert("RGBA").resize((64, 64))
                self.logo_img = ImageTk.PhotoImage(img)
                ttk.Label(header, image=self.logo_img).pack(side="left", padx=(0, 12))
            except Exception:
                ttk.Label(header, text="ANTI-AFK", style="Title.TLabel").pack(side="left", padx=(0, 12))
        else:
            ttk.Label(header, text="ANTI-AFK", style="Title.TLabel").pack(side="left", padx=(0, 12))

        title_box = ttk.Frame(header)
        title_box.pack(side="left", fill="x", expand=True)
        ttk.Label(title_box, text="Anti-AFK Roblox", style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_box, text="Auto key presser • Hotkey Start/Stop", style="Sub.TLabel").pack(anchor="w")

        # ---------- CARD ----------
        card = ttk.Frame(container, style="Card.TFrame")
        card.pack(fill="both", expand=True, pady=(16, 0))

        def section(txt):
            ttk.Label(card, text=txt, background=self.CARD).pack(anchor="w", padx=14, pady=(10, 4))

        # ---------- KEY ----------
        section("Touche à presser")
        ttk.Button(card, text="Choisir la touche", command=self.wait_for_key).pack(anchor="w", padx=14)
        self.key_label = ttk.Label(card, text="Aucune", style="Sub.TLabel", background=self.CARD)
        self.key_label.pack(anchor="w", padx=14)

        # ---------- INTERVAL ----------
        section("Intervalle (secondes)")
        self.interval_entry = ttk.Entry(card)
        self.interval_entry.insert(0, "10")
        self.interval_entry.pack(fill="x", padx=14)

        # ---------- HOTKEY ----------
        section("Hotkey Start / Stop")
        ttk.Button(card, text="Choisir la hotkey", command=self.wait_for_hotkey).pack(anchor="w", padx=14)
        self.hotkey_label = ttk.Label(card, text="Aucune", style="Sub.TLabel", background=self.CARD)
        self.hotkey_label.pack(anchor="w", padx=14)

        # ---------- STATUS ----------
        status_row = ttk.Frame(card, style="Card.TFrame")
        status_row.pack(fill="x", padx=14, pady=(6, 6))
        ttk.Label(status_row, text="État", background=self.CARD).pack(side="left")

        self.status_canvas = tk.Canvas(status_row, width=48, height=26, bg=self.CARD, highlightthickness=0)
        self.status_canvas.pack(side="left", padx=10)
        self.draw_status(False)

        # ---------- COUNTER ----------
        counter_row = ttk.Frame(card, style="Card.TFrame")
        counter_row.pack(fill="x", padx=14, pady=(0, 6))
        ttk.Label(counter_row, text="Compteur", background=self.CARD).pack(side="left")
        self.counter_label = ttk.Label(counter_row, text="0", style="Title.TLabel", background=self.CARD)
        self.counter_label.pack(side="left", padx=10)

        # ✅ Wrapper tk.Frame pour afficher le Canvas bouton sans se faire "écraser"
        btn_wrap = tk.Frame(card, bg=self.CARD)
        btn_wrap.pack(fill="x", padx=14, pady=(14, 10))

        # Bouton large + peu haut (pixels)
        self.toggle_btn = CanvasToggleButton(
            btn_wrap,
            width=380, height=34,          # ajuste ici si tu veux
            radius=14,
            font=("Segoe UI", 12, "bold"),
            fg=self.WHITE,
            bg_off=self.GREEN, bg_on=self.RED,
            hover_off=self.HOVER_GREEN, hover_on=self.HOVER_RED,
            command=self.toggle,
            canvas_bg=self.CARD
        )
        self.toggle_btn.pack(anchor="center")

        # Bind + close
        self.root.bind("<KeyPress>", self.capture_key)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.sync_ui()

    def _apply_window_icons(self):
        """
        1) .ico -> iconbitmap (Windows titlebar)
        2) .png -> iconphoto (fallback / parfois mieux)
        """
        ico = asset_path("app.ico")
        png = asset_path("logo.png")

        # 1) ICO (titlebar, Windows)
        if os.path.exists(ico):
            try:
                self.root.iconbitmap(ico)
            except Exception:
                pass

        # 2) PNG fallback via iconphoto (utile aussi pour certains cas)
        if PIL_OK and os.path.exists(png):
            try:
                img = Image.open(png).convert("RGBA").resize((64, 64))
                photo = ImageTk.PhotoImage(img)
                # garder une référence pour éviter GC
                self._icon_photo_ref = photo
                self.root.iconphoto(True, photo)
            except Exception:
                pass

    # ---------- UI ----------
    def draw_status(self, on: bool):
        self.status_canvas.delete("all")
        color = self.GREEN if on else self.RED
        text = "ON" if on else "OFF"
        self.status_canvas.create_rectangle(4, 4, 44, 22, fill=color, outline=color)
        self.status_canvas.create_text(24, 13, text=text, fill=self.WHITE, font=("Segoe UI", 9, "bold"))

    def sync_ui(self):
        self.toggle_btn.set_running(self.running)
        self.draw_status(self.running)

    # ---------- INPUT ----------
    def wait_for_key(self):
        self.waiting_for_key = True
        self.waiting_for_hotkey = False
        self.key_label.config(text="Appuie sur une touche…")

    def wait_for_hotkey(self):
        self.waiting_for_hotkey = True
        self.waiting_for_key = False
        self.hotkey_label.config(text="Appuie sur la hotkey…")

    def capture_key(self, event):
        if self.waiting_for_key:
            self.selected_key = event.keysym.lower()
            self.waiting_for_key = False
            self.key_label.config(text=self.selected_key.upper())
            return

        if self.waiting_for_hotkey:
            self.selected_hotkey = event.keysym.lower()
            self.waiting_for_hotkey = False

            if self.hotkey_handle:
                try:
                    keyboard.remove_hotkey(self.hotkey_handle)
                except Exception:
                    pass

            self.hotkey_handle = keyboard.add_hotkey(
                self.selected_hotkey,
                lambda: self.root.after(0, self.toggle)
            )
            self.hotkey_label.config(text=self.selected_hotkey.upper())

    # ---------- LOGIC ----------
    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def start(self):
        if self.running:
            return

        if not self.selected_key or not self.selected_hotkey:
            messagebox.showerror("Erreur", "Touche ou hotkey manquante.")
            return

        try:
            interval = float(self.interval_entry.get())
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Intervalle invalide.")
            return

        self.running = True
        self.count = 0
        self.counter_label.config(text="0")
        self.sync_ui()

        threading.Thread(target=self.run, args=(interval,), daemon=True).start()

    def stop(self):
        self.running = False
        self.sync_ui()

    def run(self, interval):
        time.sleep(0.8)
        while self.running:
            pydirectinput.press(self.selected_key)
            self.count += 1
            self.root.after(0, lambda c=self.count: self.counter_label.config(text=str(c)))
            time.sleep(interval)

    def on_close(self):
        self.running = False
        if self.hotkey_handle:
            try:
                keyboard.remove_hotkey(self.hotkey_handle)
            except Exception:
                pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    AutoKeyPresser(root)
    root.mainloop()
