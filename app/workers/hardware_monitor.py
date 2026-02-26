"""
Hardware info collector.
Uses winreg + platform + psutil only — NO wmi package (it hangs in threads).
"""
import os
import platform
import subprocess
import psutil
from PyQt6.QtCore import QThread, pyqtSignal


# ──────────────────────────────────────────────
# Static loader (runs once in background)
# ──────────────────────────────────────────────

class StaticHardwareLoader(QThread):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result: dict = {}

    def run(self):
        try:
            self.result = get_static_hardware_info()
        except Exception:
            self.result = {}


# ──────────────────────────────────────────────
# Live monitor (updates every N ms)
# ──────────────────────────────────────────────

class HardwareMonitor(QThread):
    data_ready = pyqtSignal(dict)

    def __init__(self, interval_ms: int = 1500):
        super().__init__()
        self._interval = interval_ms
        self._running = False

    def run(self):
        self._running = True
        while self._running:
            try:
                data = _collect_live()
            except Exception:
                data = {}
            self.data_ready.emit(data)
            self.msleep(self._interval)

    def stop(self):
        self._running = False
        # Don't call wait() from main thread — causes deadlock.
        # The thread will finish naturally on next loop iteration.


# ──────────────────────────────────────────────
# Live data (psutil only — fast, no hanging)
# ──────────────────────────────────────────────

def _collect_live() -> dict:
    cpu_pct  = 0.0
    cpu_freq = None
    try:
        cpu_pct  = psutil.cpu_percent(interval=None)
        cpu_freq = psutil.cpu_freq()
    except Exception:
        pass

    ram_data = {"total": 0, "used": 0, "available": 0, "percent": 0.0}
    try:
        ram = psutil.virtual_memory()
        ram_data = {
            "total": ram.total, "used": ram.used,
            "available": ram.available, "percent": ram.percent,
        }
    except Exception:
        pass

    swap_data = {"total": 0, "used": 0, "percent": 0.0}
    try:
        swap = psutil.swap_memory()
        swap_data = {"total": swap.total, "used": swap.used, "percent": swap.percent}
    except Exception:
        pass  # Performance counters may be disabled on some Windows configs

    battery = None
    try:
        b = psutil.sensors_battery()
        if b:
            battery = {"percent": b.percent, "plugged": b.power_plugged}
    except Exception:
        pass

    return {
        "cpu": {
            "percent":        cpu_pct,
            "freq_mhz":       cpu_freq.current if cpu_freq else 0,
            "freq_max_mhz":   cpu_freq.max     if cpu_freq else 0,
            "count_logical":  psutil.cpu_count(logical=True)  or 0,
            "count_physical": psutil.cpu_count(logical=False) or 0,
        },
        "ram":     ram_data,
        "swap":    swap_data,
        "battery": battery,
    }


# ──────────────────────────────────────────────
# Static info (winreg + platform — no WMI)
# ──────────────────────────────────────────────

def get_static_hardware_info() -> dict:
    info: dict = {
        "cpu_name":    _cpu_name(),
        "gpu":         _gpu_list(),
        "board":       _board_name(),
        "bios":        _bios_version(),
        "ram_type":    _ram_type(),
        "disk_models": _disk_models(),
    }
    return info


def _cpu_name() -> str:
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        )
        name = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        winreg.CloseKey(key)
        return name
    except Exception:
        pass
    try:
        return platform.processor() or "Unknown CPU"
    except Exception:
        return "Unknown CPU"


def _gpu_list() -> list:
    gpus = []
    try:
        import winreg
        base = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
        base_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
        i = 0
        while True:
            try:
                sub = winreg.EnumKey(base_key, i)
                if not sub.isdigit():
                    i += 1
                    continue
                sub_key = winreg.OpenKey(base_key, sub)
                try:
                    name = winreg.QueryValueEx(sub_key, "DriverDesc")[0]
                    try:
                        mem = int(winreg.QueryValueEx(sub_key, "HardwareInformation.qwMemorySize")[0])
                    except Exception:
                        try:
                            mem = int(winreg.QueryValueEx(sub_key, "HardwareInformation.MemorySize")[0])
                        except Exception:
                            mem = 0
                    gpus.append({"name": name, "vram": mem})
                except Exception:
                    pass
                winreg.CloseKey(sub_key)
                i += 1
            except OSError:
                break
        winreg.CloseKey(base_key)
    except Exception:
        pass

    if not gpus:
        # Fallback: wmic with timeout (non-blocking)
        try:
            r = subprocess.run(
                ["wmic", "path", "Win32_VideoController", "get", "Name", "/value"],
                capture_output=True, text=True, timeout=4
            )
            for line in r.stdout.splitlines():
                if line.startswith("Name=") and line[5:].strip():
                    gpus.append({"name": line[5:].strip(), "vram": 0})
        except Exception:
            pass

    return gpus


def _board_name() -> str:
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS")
        mfr = winreg.QueryValueEx(key, "BaseBoardManufacturer")[0]
        prd = winreg.QueryValueEx(key, "BaseBoardProduct")[0]
        winreg.CloseKey(key)
        return f"{mfr} {prd}".strip()
    except Exception:
        return ""


def _bios_version() -> str:
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS")
        ver = winreg.QueryValueEx(key, "BIOSVersion")[0]
        winreg.CloseKey(key)
        if isinstance(ver, list):
            ver = " / ".join(ver)
        return str(ver).strip()
    except Exception:
        return ""


def _ram_type() -> str:
    # Try wmic with timeout as a fast subprocess call
    try:
        r = subprocess.run(
            ["wmic", "memorychip", "get", "MemoryType", "/value"],
            capture_output=True, text=True, timeout=4
        )
        types = {20: "DDR", 21: "DDR2", 24: "DDR3", 26: "DDR4", 34: "DDR5"}
        for line in r.stdout.splitlines():
            if line.startswith("MemoryType="):
                try:
                    t = types.get(int(line[11:].strip()), "")
                    if t:
                        return t
                except Exception:
                    pass
    except Exception:
        pass
    return ""


def _disk_models() -> list:
    disks = []
    try:
        r = subprocess.run(
            ["wmic", "diskdrive", "get", "Model,Size", "/value"],
            capture_output=True, text=True, timeout=4
        )
        model, size = "", 0
        for line in r.stdout.splitlines():
            if line.startswith("Model="):
                model = line[6:].strip()
            elif line.startswith("Size="):
                try:
                    size = int(line[5:].strip())
                except Exception:
                    size = 0
                if model:
                    disks.append({"model": model, "size": size, "interface": ""})
                    model, size = "", 0
    except Exception:
        pass

    if not disks:
        # Fallback: just list partitions from psutil
        seen = set()
        for p in psutil.disk_partitions(all=False):
            if p.device not in seen:
                seen.add(p.device)
                try:
                    u = psutil.disk_usage(p.mountpoint)
                    disks.append({"model": p.device, "size": u.total, "interface": p.fstype})
                except Exception:
                    pass
    return disks
