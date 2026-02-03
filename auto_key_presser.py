import tkinter as tk
from tkinter import messagebox
import threading
import time

import pydirectinput
import keyboard


class AutoKeyPresser:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Key Presser")
        self.root.geometry("400x390")
        self.root.resizable(False, False)

        self.running = False
        self.count = 0

        self.selected_key = None
        self.selected_hotkey = None

        self.waiting_for_key = False
        self.waiting_for_hotkey = False

        self.hotkey_handle = None  # handle pour remove proprement

        # ---------------- UI ----------------
        tk.Label(root, text="Touche à presser :", font=("Arial", 10)).pack(pady=6)

        self.key_button = tk.Button(
            root, text="Choisir la touche à presser",
            command=self.wait_for_key, width=28
        )
        self.key_button.pack()

        self.key_label = tk.Label(root, text="Aucune touche sélectionnée", fg="gray")
        self.key_label.pack(pady=4)

        tk.Label(root, text="Intervalle (secondes) :", font=("Arial", 10)).pack(pady=6)
        self.interval_entry = tk.Entry(root, width=24)
        self.interval_entry.pack()

        # ---------- HOTKEY ----------
        tk.Label(root, text="Touche Start / Stop :", font=("Arial", 10)).pack(pady=8)

        self.hotkey_button = tk.Button(
            root, text="Choisir la touche Start/Stop",
            command=self.wait_for_hotkey, width=28
        )
        self.hotkey_button.pack()

        self.hotkey_label = tk.Label(root, text="Aucune hotkey définie", fg="gray")
        self.hotkey_label.pack(pady=4)

        # ---------- INDICATEUR ON/OFF ----------
        self.status_label = tk.Label(root, text="État : OFF", fg="white", bg="red", font=("Arial", 12), width=18)
        self.status_label.pack(pady=10)

        self.counter_label = tk.Label(root, text="Compteur : 0", font=("Arial", 12))
        self.counter_label.pack(pady=10)

        self.start_button = tk.Button(
            root, text="▶ Start", command=self.start,
            bg="green", fg="white", width=12
        )
        self.start_button.pack(pady=4)

        self.stop_button = tk.Button(
            root, text="■ Stop", command=self.stop,
            bg="red", fg="white", width=12
        )
        self.stop_button.pack()

        # Bind clavier Tkinter (sélection locale)
        self.root.bind("<KeyPress>", self.capture_key)

        # Nettoyage à la fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # -----------------------------
    # UI helpers
    # -----------------------------
    def update_status(self):
        if self.running:
            self.status_label.config(text="État : ON", bg="green", fg="white")
        else:
            self.status_label.config(text="État : OFF", bg="red", fg="white")

    # -----------------------------
    # Sélection touches
    # -----------------------------
    def wait_for_key(self):
        self.waiting_for_key = True
        self.waiting_for_hotkey = False
        self.key_label.config(text="Appuie sur une touche...", fg="orange")

    def wait_for_hotkey(self):
        self.waiting_for_hotkey = True
        self.waiting_for_key = False
        self.hotkey_label.config(text="Appuie sur la touche Start/Stop...", fg="orange")

    def capture_key(self, event):
        if self.waiting_for_key:
            self.selected_key = event.keysym.lower()
            self.waiting_for_key = False
            self.key_label.config(text=f"Touche à presser : {self.selected_key}", fg="green")
            return

        if self.waiting_for_hotkey:
            self.selected_hotkey = event.keysym.lower()
            self.waiting_for_hotkey = False

            # Retire l'ancienne hotkey si elle existait
            if self.hotkey_handle is not None:
                try:
                    keyboard.remove_hotkey(self.hotkey_handle)
                except Exception:
                    pass
                self.hotkey_handle = None

            # Enregistre la nouvelle hotkey
            self.hotkey_handle = keyboard.add_hotkey(
                self.selected_hotkey,
                lambda: self.root.after(0, self.toggle)
            )

            self.hotkey_label.config(text=f"Hotkey : {self.selected_hotkey.upper()}", fg="green")

    # -----------------------------
    # Toggle Start / Stop
    # -----------------------------
    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    # -----------------------------
    # Auto key presser
    # -----------------------------
    def start(self):
        if self.running:
            return

        if not self.selected_key:
            messagebox.showerror("Erreur", "Aucune touche à presser sélectionnée.")
            return

        if not self.selected_hotkey:
            messagebox.showerror("Erreur", "Aucune hotkey Start/Stop définie.")
            return

        try:
            interval = float(self.interval_entry.get().strip())
            if interval <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erreur", "Intervalle invalide.")
            return

        self.running = True
        self.count = 0
        self.update_counter()
        self.update_status()

        t = threading.Thread(target=self.run, args=(self.selected_key, interval), daemon=True)
        t.start()

    def stop(self):
        self.running = False
        self.update_status()

    def run(self, key, interval):
        time.sleep(0.8)  # temps pour focus le jeu
        while self.running:
            pydirectinput.press(key)
            self.count += 1
            self.root.after(0, self.update_counter)
            time.sleep(interval)

    def update_counter(self):
        self.counter_label.config(text=f"Compteur : {self.count}")

    def on_close(self):
        self.running = False
        if self.hotkey_handle is not None:
            try:
                keyboard.remove_hotkey(self.hotkey_handle)
            except Exception:
                pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoKeyPresser(root)
    root.mainloop()
