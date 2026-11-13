"""Windows 창 영역 유틸 (반격 · 방어 장면이 울트론 HUD 와 모니터의 자리를 잴 때 쓴다)."""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt

user32 = ctypes.windll.user32 if hasattr(ctypes, "windll") else None


def window_rect(hwnd: int) -> tuple[int, int, int, int] | None:
    """창이 화면에서 차지하는 영역 (왼, 위, 오, 아래). 최소화돼 있거나 알 수 없으면 None."""
    try:
        if not hwnd or not user32.IsWindow(hwnd) or user32.IsIconic(hwnd):
            return None
        r = wt.RECT()
        # DWMWA_EXTENDED_FRAME_BOUNDS(9): 눈에 보이는 테두리. GetWindowRect 는 보이지 않는 그림자(약 7px)까지 포함한다
        ok = False
        try:
            ok = ctypes.windll.dwmapi.DwmGetWindowAttribute(wt.HWND(hwnd), 9, ctypes.byref(r), ctypes.sizeof(r)) == 0
        except Exception:
            ok = False
        if not ok and not user32.GetWindowRect(wt.HWND(hwnd), ctypes.byref(r)):
            return None
        if r.right - r.left < 8 or r.bottom - r.top < 8:
            return None
        return (r.left, r.top, r.right, r.bottom)
    except Exception:
        return None


class _MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT), ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]


def monitor_rect(hwnd: int = 0) -> tuple[int, int, int, int] | None:
    """hwnd 창이 있는 모니터의 영역 (왼, 위, 오, 아래 — 가상 화면 좌표라 음수일 수 있다).
    hwnd 가 없으면 주 모니터. 알 수 없으면 None (→ 호출한 쪽은 주 모니터 전체를 찍는다)."""
    try:
        fn = user32.MonitorFromWindow
        fn.restype = ctypes.c_void_p            # 64비트 핸들이 잘리지 않게
        fn.argtypes = [wt.HWND, wt.DWORD]
        mon = fn(wt.HWND(hwnd or 0), 2 if hwnd else 1)   # 2 = 가장 가까운 모니터, 1 = 주 모니터
        if not mon:
            return None
        info = _MONITORINFO()
        info.cbSize = ctypes.sizeof(info)
        get = user32.GetMonitorInfoW
        get.argtypes = [ctypes.c_void_p, ctypes.POINTER(_MONITORINFO)]
        get.restype = wt.BOOL
        if not get(mon, ctypes.byref(info)):
            return None
        m = info.rcMonitor
        if m.right - m.left < 100 or m.bottom - m.top < 100:
            return None
        return (m.left, m.top, m.right, m.bottom)
    except Exception:
        return None
