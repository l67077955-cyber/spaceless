"""What the focused window is doing (Windows only; no-ops elsewhere)."""

import sys

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    _user32 = ctypes.WinDLL("user32")
    _imm32 = ctypes.WinDLL("imm32")
    _kernel32 = ctypes.WinDLL("kernel32")

    _user32.GetForegroundWindow.restype = wintypes.HWND
    _user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _user32.SendMessageTimeoutW.argtypes = [
        wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
        wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t),
    ]
    _user32.SendMessageTimeoutW.restype = ctypes.c_size_t
    _imm32.ImmGetDefaultIMEWnd.argtypes = [wintypes.HWND]
    _imm32.ImmGetDefaultIMEWnd.restype = wintypes.HWND
    _kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _kernel32.OpenProcess.restype = wintypes.HANDLE
    _kernel32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD),
    ]
    _kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    _WM_IME_CONTROL = 0x283
    _IMC_GETCONVERSIONMODE = 0x1
    _IMC_GETOPENSTATUS = 0x5
    _IME_CMODE_NATIVE = 0x1
    _SMTO_ABORTIFHUNG = 0x2
    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    def _ime_control(ime_hwnd, command):
        result = ctypes.c_size_t()
        ok = _user32.SendMessageTimeoutW(
            ime_hwnd, _WM_IME_CONTROL, command, 0, _SMTO_ABORTIFHUNG, 100, ctypes.byref(result)
        )
        return result.value if ok else 0

    def ime_in_native_mode():
        """True when an IME (e.g. Chinese pinyin) is on and in its native-language mode."""
        ime_hwnd = _imm32.ImmGetDefaultIMEWnd(_user32.GetForegroundWindow())
        if not ime_hwnd or not _ime_control(ime_hwnd, _IMC_GETOPENSTATUS):
            return False
        return bool(_ime_control(ime_hwnd, _IMC_GETCONVERSIONMODE) & _IME_CMODE_NATIVE)

    def foreground_app():
        """Lower-case exe name of the focused window, e.g. 'chrome.exe'."""
        pid = wintypes.DWORD()
        _user32.GetWindowThreadProcessId(_user32.GetForegroundWindow(), ctypes.byref(pid))
        handle = _kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not handle:
            return ""
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(len(buf))
            if not _kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                return ""
            return buf.value.rsplit("\\", 1)[-1].lower()
        finally:
            _kernel32.CloseHandle(handle)

else:

    def ime_in_native_mode():
        return False

    def foreground_app():
        return ""
