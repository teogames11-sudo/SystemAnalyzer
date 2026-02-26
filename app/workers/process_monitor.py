import psutil
from PyQt6.QtCore import QThread, pyqtSignal


class ProcessMonitor(QThread):
    data_ready = pyqtSignal(list)

    def __init__(self, interval_ms: int = 2000):
        super().__init__()
        self._interval = interval_ms
        self._running = False

    def run(self):
        self._running = True
        while self._running:
            procs = self._collect()
            self.data_ready.emit(procs)
            self.msleep(self._interval)

    def stop(self):
        self._running = False
        self.wait(3000)

    def _collect(self) -> list:
        procs = []
        attrs = ["pid", "name", "cpu_percent", "memory_info",
                 "status", "username", "exe"]
        for proc in psutil.process_iter(attrs, ad_value=None):
            try:
                info = proc.info
                mem = info.get("memory_info")
                procs.append({
                    "pid": info["pid"],
                    "name": info["name"] or "",
                    "cpu": info["cpu_percent"] or 0.0,
                    "ram": mem.rss if mem else 0,
                    "status": info["status"] or "",
                    "user": info["username"] or "",
                    "exe": info["exe"] or "",
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return sorted(procs, key=lambda x: x["cpu"], reverse=True)
