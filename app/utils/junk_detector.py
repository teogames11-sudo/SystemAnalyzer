"""
Junk file categories and detection logic.
"""
import os
import hashlib
from pathlib import Path
from typing import Generator


JUNK_CATEGORIES = {
    "temp_system": {
        "label": "Системные временные файлы",
        "color": "#e74c3c",
        "paths": [
            os.environ.get("TEMP", ""),
            os.environ.get("TMP", ""),
            r"C:\Windows\Temp",
            r"C:\Windows\Prefetch",
        ],
        "extensions": {".tmp", ".temp", ".~"},
        "recursive": True,
    },
    "browser_cache": {
        "label": "Кэш браузеров",
        "color": "#e67e22",
        "paths": [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\User Data\Default\Cache"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\User Data\Default\Code Cache"),
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Microsoft\Edge\User Data\Default\Cache"),
            os.path.join(os.environ.get("APPDATA", ""), r"Mozilla\Firefox\Profiles"),
        ],
        "extensions": set(),
        "recursive": True,
    },
    "windows_update": {
        "label": "Старые обновления Windows",
        "color": "#9b59b6",
        "paths": [
            r"C:\Windows\SoftwareDistribution\Download",
            r"C:\Windows\SoftwareDistribution\DataStore",
        ],
        "extensions": set(),
        "recursive": True,
    },
    "thumbnails": {
        "label": "Кэш миниатюр",
        "color": "#1abc9c",
        "paths": [
            os.path.join(os.environ.get("LOCALAPPDATA", ""),
                         r"Microsoft\Windows\Explorer"),
        ],
        "extensions": {".db"},
        "recursive": False,
    },
    "log_files": {
        "label": "Файлы логов",
        "color": "#34495e",
        "paths": [
            r"C:\Windows\Logs",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"),
        ],
        "extensions": {".log", ".dmp"},
        "recursive": True,
    },
    "recycle_bin": {
        "label": "Корзина",
        "color": "#95a5a6",
        "paths": [],  # handled separately
        "extensions": set(),
        "recursive": False,
    },
    "office_temp": {
        "label": "Временные файлы Office",
        "color": "#2980b9",
        "paths": [
            os.environ.get("TEMP", ""),
        ],
        "extensions": {".tmp"},
        "name_patterns": ["~$", "~WRL"],
        "recursive": False,
    },
}


def scan_junk_category(category_key: str) -> Generator[dict, None, None]:
    """Yields file info dicts for a junk category."""
    cat = JUNK_CATEGORIES.get(category_key, {})
    if not cat:
        return

    for base_path in cat.get("paths", []):
        if not base_path or not os.path.exists(base_path):
            continue
        yield from _scan_dir(
            base_path,
            cat.get("extensions", set()),
            cat.get("recursive", True),
            cat.get("name_patterns", []),
        )


def _scan_dir(path: str, extensions: set, recursive: bool, name_patterns: list) -> Generator[dict, None, None]:
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_file(follow_symlinks=False):
                        ext = Path(entry.name).suffix.lower()
                        if not extensions or ext in extensions:
                            if not name_patterns or any(entry.name.startswith(p) for p in name_patterns):
                                try:
                                    size = entry.stat().st_size
                                    yield {
                                        "path": entry.path,
                                        "name": entry.name,
                                        "size": size,
                                    }
                                except (PermissionError, OSError):
                                    pass
                        elif not extensions:
                            try:
                                size = entry.stat().st_size
                                yield {
                                    "path": entry.path,
                                    "name": entry.name,
                                    "size": size,
                                }
                            except (PermissionError, OSError):
                                pass
                    elif entry.is_dir(follow_symlinks=False) and recursive:
                        yield from _scan_dir(entry.path, extensions, recursive, name_patterns)
                except (PermissionError, OSError):
                    pass
    except (PermissionError, OSError):
        pass


def find_large_files(drives: list[str], min_size_mb: int = 500) -> Generator[dict, None, None]:
    """Find files larger than min_size_mb MB."""
    min_bytes = min_size_mb * 1024 * 1024
    for drive in drives:
        yield from _scan_large(drive, min_bytes)


def _scan_large(path: str, min_bytes: int) -> Generator[dict, None, None]:
    SKIP_DIRS = {
        "Windows", "System Volume Information", "$Recycle.Bin",
        "Recovery", "ProgramData\\Microsoft\\Windows\\WER",
    }
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_file(follow_symlinks=False):
                        try:
                            size = entry.stat().st_size
                            if size >= min_bytes:
                                yield {"path": entry.path, "name": entry.name, "size": size}
                        except (PermissionError, OSError):
                            pass
                    elif entry.is_dir(follow_symlinks=False):
                        if entry.name not in SKIP_DIRS:
                            yield from _scan_large(entry.path, min_bytes)
                except (PermissionError, OSError):
                    pass
    except (PermissionError, OSError):
        pass


def find_duplicates(file_list: list[dict]) -> list[list[dict]]:
    """Group duplicate files by size then MD5 hash."""
    from collections import defaultdict
    by_size = defaultdict(list)
    for f in file_list:
        by_size[f["size"]].append(f)

    duplicates = []
    for size, files in by_size.items():
        if len(files) < 2 or size == 0:
            continue
        by_hash = defaultdict(list)
        for f in files:
            h = _md5(f["path"])
            if h:
                by_hash[h].append(f)
        for group in by_hash.values():
            if len(group) >= 2:
                duplicates.append(group)
    return duplicates


def _md5(path: str) -> str | None:
    try:
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except (PermissionError, OSError):
        return None


def format_size(size_bytes: int) -> str:
    if size_bytes >= 1024 ** 3:
        return f"{size_bytes / 1024**3:.1f} ГБ"
    elif size_bytes >= 1024 ** 2:
        return f"{size_bytes / 1024**2:.1f} МБ"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} КБ"
    return f"{size_bytes} Б"
