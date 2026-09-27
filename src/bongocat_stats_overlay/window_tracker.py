"""Locate ayangweb/BongoCat by both title and executable name."""

import ctypes
import ctypes.wintypes as wt
from dataclasses import dataclass
from pathlib import PureWindowsPath


user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)

WINDOW_TITLE = "BongoCat"
EXECUTABLE_NAME = "bongo-cat.exe"
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
DWMWA_CLOAKED = 14

WINDOW_CALLBACK = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
user32.EnumWindows.argtypes = (WINDOW_CALLBACK, wt.LPARAM)
user32.EnumWindows.restype = wt.BOOL
user32.GetWindowThreadProcessId.argtypes = (wt.HWND, ctypes.POINTER(wt.DWORD))
user32.GetWindowThreadProcessId.restype = wt.DWORD
user32.GetWindowTextLengthW.argtypes = (wt.HWND,)
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = (wt.HWND, wt.LPWSTR, ctypes.c_int)
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetWindowRect.argtypes = (wt.HWND, ctypes.POINTER(wt.RECT))
user32.GetWindowRect.restype = wt.BOOL
user32.IsWindowVisible.argtypes = (wt.HWND,)
user32.IsWindowVisible.restype = wt.BOOL
user32.IsIconic.argtypes = (wt.HWND,)
user32.IsIconic.restype = wt.BOOL
kernel32.OpenProcess.argtypes = (wt.DWORD, wt.BOOL, wt.DWORD)
kernel32.OpenProcess.restype = wt.HANDLE
kernel32.QueryFullProcessImageNameW.argtypes = (
    wt.HANDLE, wt.DWORD, wt.LPWSTR, ctypes.POINTER(wt.DWORD))
kernel32.QueryFullProcessImageNameW.restype = wt.BOOL
kernel32.CloseHandle.argtypes = (wt.HANDLE,)
kernel32.CloseHandle.restype = wt.BOOL
dwmapi.DwmGetWindowAttribute.argtypes = (
    wt.HWND, wt.DWORD, wt.LPVOID, wt.DWORD)
dwmapi.DwmGetWindowAttribute.restype = ctypes.c_long


@dataclass(frozen=True)
class CatWindow:
    hwnd: int
    left: int
    top: int
    right: int
    bottom: int
    visible: bool

    @property
    def area(self):
        return max(0, self.right - self.left) * max(0, self.bottom - self.top)


def _executable_name(pid):
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False,
                                  pid)
    if not handle:
        return ""
    try:
        path = ctypes.create_unicode_buffer(32768)
        size = wt.DWORD(len(path))
        if kernel32.QueryFullProcessImageNameW(handle, 0, path,
                                                ctypes.byref(size)):
            return PureWindowsPath(path.value).name.casefold()
        return ""
    finally:
        kernel32.CloseHandle(handle)


def _cloaked(hwnd):
    value = wt.DWORD()
    result = dwmapi.DwmGetWindowAttribute(
        hwnd, DWMWA_CLOAKED, ctypes.byref(value), ctypes.sizeof(value))
    return result == 0 and value.value != 0


def find_bongocat():
    """Return the real cat window, excluding Steam's similarly named one."""
    candidates = []

    def visit(hwnd, _):
        length = user32.GetWindowTextLengthW(hwnd)
        if length != len(WINDOW_TITLE):
            return True
        title = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title, length + 1)
        if title.value != WINDOW_TITLE:
            return True
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if _executable_name(pid.value) != EXECUTABLE_NAME:
            return True
        rect = wt.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return True
        visible = (bool(user32.IsWindowVisible(hwnd))
                   and not bool(user32.IsIconic(hwnd))
                   and not _cloaked(hwnd))
        candidates.append(CatWindow(int(hwnd), rect.left, rect.top,
                                    rect.right, rect.bottom, visible))
        return True

    callback = WINDOW_CALLBACK(visit)
    user32.EnumWindows(callback, 0)
    return max(candidates, key=lambda item: (item.visible, item.area),
               default=None)
