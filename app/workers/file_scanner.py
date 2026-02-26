import os
import string
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtCore import QThread, pyqtSignal

from app.utils.junk_detector import (
    scan_junk_category, find_large_files, JUNK_CATEGORIES, format_size
)


SKIP_DIRS = frozenset({
    "Windows", "System Volume Information", "$Recycle.Bin",
    "Recovery", "ProgramData", "AppData", "Boot",
    "hiberfil.sys", "pagefile.sys", "swapfile.sys",
})


class FileScanner(QThread):
    """Scans all drives for junk files. Emits progress and results."""
    progress = pyqtSignal(int, str)          # (percent, status_text)
    category_done = pyqtSignal(str, list)    # (category_key, file_list)
    large_files_done = pyqtSignal(list)      # list of large file dicts
    scan_complete = pyqtSignal(dict)         # summary dict

    def __init__(self):
        super().__init__()
        self._running = False
        self._drives = self._get_drives()

    def _get_drives(self) -> list[str]:
        drives = []
        for part in psutil.disk_partitions(all=False):
            if "cdrom" not in part.opts and part.fstype:
                drives.append(part.mountpoint)
        return drives

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        total_junk_size = 0
        total_junk_count = 0
        categories = list(JUNK_CATEGORIES.keys())
        n_cats = len(categories)

        # Step 1: Scan junk categories (fast, known paths)
        for i, cat_key in enumerate(categories):
            if not self._running:
                break
            pct = int((i / (n_cats + 1)) * 70)
            label = JUNK_CATEGORIES[cat_key]["label"]
            self.progress.emit(pct, f"Сканирую: {label}...")

            files = list(scan_junk_category(cat_key))
            cat_size = sum(f["size"] for f in files)
            total_junk_size += cat_size
            total_junk_count += len(files)
            self.category_done.emit(cat_key, files)

        # Step 2: Scan for large files (across all drives, in parallel)
        if self._running:
            self.progress.emit(72, "Поиск больших файлов...")
            all_large = []
            with ThreadPoolExecutor(max_workers=len(self._drives) or 1) as exe:
                futures = {exe.submit(self._scan_large_drive, d): d for d in self._drives}
                for fut in as_completed(futures):
                    if not self._running:
                        break
                    result = fut.result()
                    all_large.extend(result)
            all_large.sort(key=lambda x: x["size"], reverse=True)
            self.large_files_done.emit(all_large[:500])  # top 500

        self.progress.emit(100, "Сканирование завершено")
        self.scan_complete.emit({
            "junk_size": total_junk_size,
            "junk_count": total_junk_count,
            "drives": self._drives,
        })

    def _scan_large_drive(self, drive: str) -> list:
        min_bytes = 200 * 1024 * 1024  # 200 MB
        results = []
        self._scan_dir_large(drive, min_bytes, results)
        return results

    def _scan_dir_large(self, path: str, min_bytes: int, results: list, depth: int = 0):
        if not self._running or depth > 15:
            return
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if not self._running:
                        return
                    try:
                        if entry.is_file(follow_symlinks=False):
                            try:
                                size = entry.stat().st_size
                                if size >= min_bytes:
                                    results.append({
                                        "path": entry.path,
                                        "name": entry.name,
                                        "size": size,
                                    })
                            except (PermissionError, OSError):
                                pass
                        elif entry.is_dir(follow_symlinks=False):
                            if entry.name not in SKIP_DIRS and not entry.name.startswith("$"):
                                self._scan_dir_large(entry.path, min_bytes, results, depth + 1)
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError):
            pass


class DiskScanner(QThread):
    """Scans folder sizes on disks."""
    progress = pyqtSignal(int, str)
    results_ready = pyqtSignal(list)   # list of (path, size_bytes)

    def __init__(self, root: str):
        super().__init__()
        self._root = root
        self._running = False

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        self.progress.emit(0, f"Сканирую {self._root}...")
        results = []
        try:
            with os.scandir(self._root) as it:
                entries = list(it)
            total = len(entries)
            for i, entry in enumerate(entries):
                if not self._running:
                    break
                if entry.is_dir(follow_symlinks=False) and entry.name not in SKIP_DIRS:
                    size = self._dir_size(entry.path)
                    results.append((entry.path, size))
                    pct = int((i + 1) / total * 100)
                    self.progress.emit(pct, f"Считаю размер: {entry.name}")
        except (PermissionError, OSError):
            pass
        results.sort(key=lambda x: x[1], reverse=True)
        self.results_ready.emit(results)

    def _dir_size(self, path: str) -> int:
        total = 0
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if not self._running:
                        return total
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total += entry.stat().st_size
                        elif entry.is_dir(follow_symlinks=False):
                            total += self._dir_size(entry.path)
                    except (PermissionError, OSError):
                        pass
        except (PermissionError, OSError):
            pass
        return total
