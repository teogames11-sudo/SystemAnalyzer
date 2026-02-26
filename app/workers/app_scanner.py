"""
Scans installed Windows applications and their files.
Uses winreg only — no WMI, no hanging.
"""
import os
import re
import winreg
from dataclasses import dataclass, field
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

from app.utils.file_description import get_file_info
from app.utils.junk_detector import format_size


# ──────────────────────────────────────────────
# Data classes
# ──────────────────────────────────────────────

@dataclass
class AppInfo:
    name: str
    publisher: str = ""
    version: str = ""
    install_location: str = ""
    uninstall_string: str = ""
    quiet_uninstall: str = ""
    estimated_size_kb: int = 0
    install_date: str = ""

    @property
    def size_str(self) -> str:
        if self.estimated_size_kb:
            return format_size(self.estimated_size_kb * 1024)
        return ""


@dataclass
class FileEntry:
    path: str
    name: str
    size: int
    description: str
    emoji: str
    category: str
    size_str: str = ""

    def __post_init__(self):
        self.size_str = format_size(self.size)


# ──────────────────────────────────────────────
# App list from registry
# ──────────────────────────────────────────────

_UNINSTALL_PATHS = [
    (winreg.HKEY_LOCAL_MACHINE,
     r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_LOCAL_MACHINE,
     r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_CURRENT_USER,
     r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
]


def _reg_str(key, name: str) -> str:
    try:
        return winreg.QueryValueEx(key, name)[0] or ""
    except Exception:
        return ""


def _reg_int(key, name: str) -> int:
    try:
        return int(winreg.QueryValueEx(key, name)[0] or 0)
    except Exception:
        return 0


def get_installed_apps() -> list[AppInfo]:
    seen: set[str] = set()
    apps: list[AppInfo] = []

    for hive, path in _UNINSTALL_PATHS:
        try:
            key = winreg.OpenKey(hive, path)
        except Exception:
            continue
        i = 0
        while True:
            try:
                sub_name = winreg.EnumKey(key, i)
                i += 1
            except OSError:
                break
            try:
                sub = winreg.OpenKey(key, sub_name)
                name = _reg_str(sub, "DisplayName").strip()
                # Skip system components, updates, empty names
                if (not name
                        or name in seen
                        or _reg_int(sub, "SystemComponent") == 1
                        or _reg_str(sub, "ParentKeyName")):
                    winreg.CloseKey(sub)
                    continue
                seen.add(name)
                apps.append(AppInfo(
                    name=name,
                    publisher=_reg_str(sub, "Publisher"),
                    version=_reg_str(sub, "DisplayVersion"),
                    install_location=_reg_str(sub, "InstallLocation").strip().rstrip("\\"),
                    uninstall_string=_reg_str(sub, "UninstallString"),
                    quiet_uninstall=_reg_str(sub, "QuietUninstallString"),
                    estimated_size_kb=_reg_int(sub, "EstimatedSize"),
                    install_date=_reg_str(sub, "InstallDate"),
                ))
                winreg.CloseKey(sub)
            except Exception:
                pass
        winreg.CloseKey(key)

    return sorted(apps, key=lambda a: a.name.lower())


# ──────────────────────────────────────────────
# File scanner for a single app
# ──────────────────────────────────────────────

_SKIP_DIRS = frozenset({
    "Windows", "System32", "SysWOW64", "$Recycle.Bin",
    "System Volume Information",
})

_SEARCH_BASES = [
    os.environ.get("LOCALAPPDATA", ""),
    os.environ.get("APPDATA", ""),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"),
    r"C:\Program Files",
    r"C:\Program Files (x86)",
    r"C:\ProgramData",
]

_SHORTCUT_BASES = [
    os.path.join(os.environ.get("APPDATA", ""),
                 r"Microsoft\Windows\Start Menu\Programs"),
    r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
    os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
    r"C:\Users\Public\Desktop",
]


def _keywords(name: str) -> list[str]:
    """Extract ≥3-char words from app name for folder matching."""
    noise = {"the", "for", "and", "or", "of", "in", "on",
             "app", "com", "inc", "ltd", "llc", "corp"}
    return [w for w in re.findall(r"[a-zA-Zа-яА-Я]{3,}", name.lower())
            if w not in noise]


def _folder_matches(folder: str, kws: list[str]) -> bool:
    fl = folder.lower()
    return any(kw in fl for kw in kws)


def _scan_dir(root: str, results: list[FileEntry], running_ref: list[bool], max_depth=12, _d=0):
    if not running_ref[0] or _d > max_depth:
        return
    try:
        with os.scandir(root) as it:
            for entry in it:
                if not running_ref[0]:
                    return
                try:
                    if entry.is_file(follow_symlinks=False):
                        try:
                            sz = entry.stat().st_size
                        except OSError:
                            sz = 0
                        desc, emoji, cat = get_file_info(entry.path)
                        results.append(FileEntry(
                            path=entry.path,
                            name=entry.name,
                            size=sz,
                            description=desc,
                            emoji=emoji,
                            category=cat,
                        ))
                    elif entry.is_dir(follow_symlinks=False):
                        if entry.name not in _SKIP_DIRS:
                            _scan_dir(entry.path, results, running_ref, max_depth, _d + 1)
                except (PermissionError, OSError):
                    pass
    except (PermissionError, OSError):
        pass


class AppFileScanner(QThread):
    """Scans all files belonging to an app in background."""
    progress   = pyqtSignal(str)          # status message
    files_ready = pyqtSignal(list)        # list[FileEntry]

    def __init__(self, app: AppInfo, parent=None):
        super().__init__(parent)
        self._app = app
        self._running = [True]

    def stop(self):
        self._running[0] = False

    def run(self):
        results: list[FileEntry] = []
        scanned_dirs: set[str] = set()
        app = self._app
        kws = _keywords(app.name)
        if app.publisher:
            kws += _keywords(app.publisher)
        kws = list(dict.fromkeys(kws))  # deduplicate, keep order

        # 1 — Install directory
        if app.install_location and os.path.isdir(app.install_location):
            norm = os.path.normcase(app.install_location)
            if norm not in scanned_dirs:
                scanned_dirs.add(norm)
                self.progress.emit(f"Сканирую: {app.install_location}")
                _scan_dir(app.install_location, results, self._running)

        # 2 — AppData / Program Files folders matching keywords
        for base in _SEARCH_BASES:
            if not base or not os.path.isdir(base):
                continue
            try:
                with os.scandir(base) as it:
                    for entry in it:
                        if not self._running[0]:
                            return
                        if not entry.is_dir(follow_symlinks=False):
                            continue
                        norm = os.path.normcase(entry.path)
                        if norm in scanned_dirs:
                            continue
                        if _folder_matches(entry.name, kws):
                            scanned_dirs.add(norm)
                            self.progress.emit(f"Сканирую: {entry.path}")
                            _scan_dir(entry.path, results, self._running)
            except (PermissionError, OSError):
                pass

        # 3 — Shortcuts
        for base in _SHORTCUT_BASES:
            if not base or not os.path.isdir(base):
                continue
            try:
                with os.scandir(base) as it:
                    for entry in it:
                        if not self._running[0]:
                            return
                        try:
                            name_lower = entry.name.lower()
                            if any(kw in name_lower for kw in kws):
                                if entry.is_file(follow_symlinks=False):
                                    sz = entry.stat().st_size
                                    desc, emoji, cat = get_file_info(entry.path)
                                    results.append(FileEntry(
                                        path=entry.path, name=entry.name,
                                        size=sz, description=desc,
                                        emoji=emoji, category=cat,
                                    ))
                                elif entry.is_dir(follow_symlinks=False):
                                    norm = os.path.normcase(entry.path)
                                    if norm not in scanned_dirs:
                                        scanned_dirs.add(norm)
                                        _scan_dir(entry.path, results, self._running)
                        except (PermissionError, OSError):
                            pass
            except (PermissionError, OSError):
                pass

        # Deduplicate by path
        seen_paths: set[str] = set()
        unique: list[FileEntry] = []
        for f in results:
            norm = os.path.normcase(f.path)
            if norm not in seen_paths:
                seen_paths.add(norm)
                unique.append(f)

        self.files_ready.emit(unique)
