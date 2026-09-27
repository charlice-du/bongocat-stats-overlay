"""Run the Windows-only companion overlay with ``python -m``."""

import sys
import tkinter as tk
from tkinter import messagebox


def main():
    if sys.platform != "win32":
        print("BongoCat Stats Overlay currently supports Windows only.",
              file=sys.stderr)
        return 1

    from .windows_api import acquire_single_instance, release_single_instance

    mutex = acquire_single_instance()
    if mutex is None:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Stats Overlay is already running",
                            "Check the KPS icon in the system tray.")
        root.destroy()
        return 0

    try:
        try:
            from .overlay import StatsApp
            StatsApp().run()
        except Exception as error:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Failed to start BongoCat Stats Overlay",
                                 str(error))
            root.destroy()
            return 1
    finally:
        release_single_instance(mutex)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
