"""Small Windows API surface for polling and a transparent owned popup.

Some Win32 input and click-through ideas are adapted from
Bel1eve-qiu/desktop-pet (MIT); see THIRD_PARTY_NOTICES.md.
"""

import ctypes
import ctypes.wintypes as wt


user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

GWL_EXSTYLE = -20
GWLP_HWNDPARENT = -8
GW_OWNER = 4
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_NOACTIVATE = 0x08000000
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
HWND_TOPMOST = wt.HWND(-1)
MUTEX_NAME = r"Local\BongoCatStatsOverlay"
ERROR_ALREADY_EXISTS = 183

user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.GetWindow.argtypes = (wt.HWND, wt.UINT)
user32.GetWindow.restype = wt.HWND
user32.IsWindow.argtypes = (wt.HWND,)
user32.IsWindow.restype = wt.BOOL
user32.GetWindowLongPtrW.argtypes = (wt.HWND, ctypes.c_int)
user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
user32.SetWindowLongPtrW.argtypes = (wt.HWND, ctypes.c_int, ctypes.c_ssize_t)
user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
user32.SetWindowPos.argtypes = (wt.HWND, wt.HWND, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                wt.UINT)
user32.SetWindowPos.restype = wt.BOOL
kernel32.CreateMutexW.argtypes = (wt.LPVOID, wt.BOOL, wt.LPCWSTR)
kernel32.CreateMutexW.restype = wt.HANDLE
kernel32.CloseHandle.argtypes = (wt.HANDLE,)
kernel32.CloseHandle.restype = wt.BOOL


def set_dpi_aware():
    """Use physical pixel coordinates on mixed-DPI monitor setups."""
    try:
        if ctypes.windll.shcore.SetProcessDpiAwareness(2) == 0:
            return
    except (AttributeError, OSError):
        pass
    user32.SetProcessDPIAware()


def key_down(vk):
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def hwnd_of(window):
    window.update_idletasks()
    return int(window.frame(), 16)


def native_window_exists(hwnd):
    return bool(hwnd and user32.IsWindow(hwnd))


def _set_window_long(hwnd, index, value):
    ctypes.set_last_error(0)
    previous = user32.SetWindowLongPtrW(hwnd, index, value)
    if previous == 0 and ctypes.get_last_error():
        raise ctypes.WinError(ctypes.get_last_error())


def attach_owner(badge_hwnd, cat_hwnd):
    """Windows keeps an owned popup above its owner without z-order polling."""
    owner = user32.GetWindow(badge_hwnd, GW_OWNER)
    if owner and owner != cat_hwnd:
        raise RuntimeError("badge already belongs to another window")
    if not owner:
        _set_window_long(badge_hwnd, GWLP_HWNDPARENT, cat_hwnd)
    if not user32.SetWindowPos(
        badge_hwnd, HWND_TOPMOST, 0, 0, 0, 0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_FRAMECHANGED,
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    if user32.GetWindow(badge_hwnd, GW_OWNER) != cat_hwnd:
        raise RuntimeError("Windows did not attach the badge to BongoCat")


def set_click_through(badge_hwnd):
    style = user32.GetWindowLongPtrW(badge_hwnd, GWL_EXSTYLE)
    _set_window_long(badge_hwnd, GWL_EXSTYLE,
                     style | WS_EX_LAYERED | WS_EX_TRANSPARENT
                     | WS_EX_NOACTIVATE)
    if not user32.SetWindowPos(
        badge_hwnd, None, 0, 0, 0, 0,
        SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER
        | SWP_NOACTIVATE | SWP_FRAMECHANGED,
    ):
        raise ctypes.WinError(ctypes.get_last_error())


def acquire_single_instance():
    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return None
    return handle


def release_single_instance(handle):
    if handle:
        kernel32.CloseHandle(handle)
