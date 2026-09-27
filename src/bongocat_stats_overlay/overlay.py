"""Transparent click-through badge and its long-lived hidden controller."""

import queue
import time
import tkinter as tk
from tkinter import messagebox
from threading import Thread

from .config import load_config
from .input_counter import InputCounter, KEYBOARD_VKS, MOUSE_BUTTON_VKS
from .lifecycle import BadgeLifecycle
from .storage import load_total, save_total, user_data_dir
from .window_tracker import find_bongocat
from .windows_api import (attach_owner, hwnd_of, key_down,
                          native_window_exists, set_click_through,
                          set_dpi_aware)


POLL_MS = 25
ATTACH_SECONDS = 0.20
SAVE_SECONDS = 5.0
BADGE_WIDTH, BADGE_HEIGHT = 170, 50
TRANSPARENT = "#ff00ff"


class TkBadge:
    """A disposable popup; Windows may destroy it when the cat exits."""

    def __init__(self, controller, cat_hwnd, config):
        self.window = tk.Toplevel(controller)
        self.window.withdraw()
        self.window.title("BongoCat Keys/KPS")
        self.window.overrideredirect(True)
        self.window.configure(bg=TRANSPARENT)
        self.window.attributes("-transparentcolor", TRANSPARENT)
        self.window.attributes("-topmost", True)
        self.canvas = tk.Canvas(self.window, width=BADGE_WIDTH,
                                height=BADGE_HEIGHT, bg=TRANSPARENT,
                                highlightthickness=0)
        self.canvas.pack()
        self.config = config
        self._geometry = None
        self._display = None
        self._shown = False
        try:
            hwnd = hwnd_of(self.window)
            attach_owner(hwnd, cat_hwnd)
            set_click_through(hwnd)
        except Exception:
            self.window.destroy()
            raise

    def alive(self):
        try:
            return bool(self.window.winfo_exists()
                        and native_window_exists(hwnd_of(self.window)))
        except tk.TclError:
            return False

    def place(self, cat):
        x = cat.left + self.config.offset_x
        y = cat.bottom + self.config.offset_y
        geometry = (x, y)
        if geometry != self._geometry:
            self.window.geometry(f"{BADGE_WIDTH}x{BADGE_HEIGHT}+{x}+{y}")
            self._geometry = geometry
        if not self._shown:
            self.window.deiconify()
            self.window.attributes("-topmost", True)
            # Tk may reset extended styles while showing the popup.
            self.window.after(80, self._restore_click_through)
            self._shown = True

    def _restore_click_through(self):
        if self.alive():
            set_click_through(hwnd_of(self.window))

    def hide(self):
        if self.alive() and self._shown:
            self.window.withdraw()
            self._shown = False

    def draw(self, total, kps):
        display = (total, kps)
        if display == self._display:
            return
        self._display = display
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, BADGE_WIDTH, BADGE_HEIGHT,
                                     fill="#282b36", outline="#575c68",
                                     width=1)
        self.canvas.create_text(11, 14, anchor="w", fill="#f3f4f6",
                                text=f"Keys  {total:,}",
                                font=("Segoe UI", 10, "bold"))
        self.canvas.create_text(11, 36, anchor="w", fill="#ffd166",
                                text=f"KPS   {kps}",
                                font=("Segoe UI", 10, "bold"))

    def close(self):
        try:
            if self.window.winfo_exists():
                self.window.destroy()
        except tk.TclError:
            pass


class StatsApp:
    def __init__(self):
        set_dpi_aware()
        self.data_dir = user_data_dir()
        self.stats_path = self.data_dir / "stats.json"
        loaded = load_total(self.stats_path)
        configured = load_config(self.data_dir / "config.json")
        self.counter = InputCounter(loaded.total)
        self.config = configured.config

        # This root must never be owned by BongoCat. It survives cat restarts.
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.bind("<Destroy>", self._on_root_destroy)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.lifecycle = BadgeLifecycle(
            lambda cat: TkBadge(self.root, cat.hwnd, self.config))
        self.commands = queue.Queue()
        self.tray = None
        self._stopped = False
        self._last_attach = 0.0
        self._last_save = time.monotonic()
        self._reported_attach_error = None
        self._reported_save_error = False
        self._start_tray()

        if loaded.corrupt_backup is not None:
            self.root.after(100, lambda: messagebox.showwarning(
                "Statistics file backed up",
                "The statistics file could not be read. A backup was saved at:\n"
                f"{loaded.corrupt_backup}\n\nCounting starts from 0."))
        if configured.warning is not None:
            self.root.after(200, lambda: messagebox.showwarning(
                "Invalid position settings",
                "config.json was not changed. Using the default position.\n"
                f"Reason: {configured.warning}"))
        self.root.after(0, self._tick)

    def _start_tray(self):
        import pystray
        from PIL import Image, ImageDraw

        icon = Image.new("RGB", (64, 64), "#282b36")
        pen = ImageDraw.Draw(icon)
        pen.text((11, 20), "KPS", fill="white")
        menu = pystray.Menu(pystray.MenuItem(
            "Exit Stats Overlay", lambda *_: self.commands.put("quit")))
        self.tray = pystray.Icon("bongocat-stats-overlay", icon,
                                 "BongoCat Stats Overlay", menu)
        Thread(target=self.tray.run, daemon=True).start()

    def _save(self):
        try:
            save_total(self.counter.total, self.stats_path)
            self._reported_save_error = False
        except OSError as error:
            if not self._reported_save_error:
                messagebox.showerror("Could not save statistics", str(error))
                self._reported_save_error = True

    def _tick(self):
        if self._stopped:
            return
        while not self.commands.empty():
            if self.commands.get_nowait() == "quit":
                self.quit()
                return

        now = time.monotonic()
        keys = {vk for vk in KEYBOARD_VKS if key_down(vk)}
        mouse = {vk for vk in MOUSE_BUTTON_VKS if key_down(vk)}
        self.counter.sample(keys, mouse, now)

        if now - self._last_attach >= ATTACH_SECONDS:
            try:
                self.lifecycle.update(find_bongocat())
                self._reported_attach_error = None
            except (OSError, RuntimeError, tk.TclError) as error:
                self.lifecycle.close()
                details = str(error)
                if details != self._reported_attach_error:
                    self._reported_attach_error = details
                    messagebox.showwarning("Could not attach to BongoCat", details)
            self._last_attach = now
        try:
            self.lifecycle.draw(self.counter.total, self.counter.kps)
        except tk.TclError:
            # The cat can destroy its owned popup between the alive check
            # and a Canvas operation. The next attach tick will recreate it.
            self.lifecycle.close()

        if now - self._last_save >= SAVE_SECONDS:
            self._save()
            self._last_save = now
        self.root.after(POLL_MS, self._tick)

    def _on_root_destroy(self, event):
        if event.widget is self.root and not self._stopped:
            self._save()

    def quit(self):
        if self._stopped:
            return
        self._save()
        self._stopped = True
        self.lifecycle.close()
        if self.tray is not None:
            self.tray.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()
