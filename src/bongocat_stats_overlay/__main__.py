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
        messagebox.showinfo("按键统计已在运行", "请查看系统托盘中的 KPS 图标。")
        root.destroy()
        return 0

    try:
        try:
            from .overlay import StatsApp
            StatsApp().run()
        except Exception as error:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("BongoCat Stats Overlay 启动失败", str(error))
            root.destroy()
            return 1
    finally:
        release_single_instance(mutex)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
