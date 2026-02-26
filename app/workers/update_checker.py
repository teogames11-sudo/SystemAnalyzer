"""
Проверка обновлений через GitHub Releases API.
Запускается в фоновом QThread, не блокирует UI.
Проверяет не чаще одного раза в 24 часа.
"""
import json
import os
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError
from packaging.version import Version

from PyQt6.QtCore import QThread, pyqtSignal

from app.version import VERSION, GITHUB_REPO, APP_NAME

_CACHE_FILE = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    APP_NAME,
    "last_update_check.txt",
)
_CHECK_INTERVAL_HOURS = 24


def _should_check() -> bool:
    """Возвращает True если прошло более 24 часов с последней проверки."""
    try:
        with open(_CACHE_FILE, "r") as f:
            last = datetime.fromisoformat(f.read().strip())
        return datetime.now() - last > timedelta(hours=_CHECK_INTERVAL_HOURS)
    except Exception:
        return True


def _save_check_time() -> None:
    os.makedirs(os.path.dirname(_CACHE_FILE), exist_ok=True)
    with open(_CACHE_FILE, "w") as f:
        f.write(datetime.now().isoformat())


class UpdateChecker(QThread):
    """
    Сигналы:
      update_available(new_version: str, release_url: str)
      check_failed(reason: str)
    """
    update_available = pyqtSignal(str, str)
    check_failed     = pyqtSignal(str)

    def run(self):
        if not _should_check():
            return

        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = Request(url, headers={"User-Agent": f"{APP_NAME}/{VERSION}"})
        try:
            with urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
        except URLError as e:
            self.check_failed.emit(str(e))
            return
        except Exception as e:
            self.check_failed.emit(str(e))
            return

        _save_check_time()

        tag = data.get("tag_name", "").lstrip("v")
        release_url = data.get("html_url", "")
        if not tag:
            return

        try:
            if Version(tag) > Version(VERSION):
                self.update_available.emit(tag, release_url)
        except Exception:
            pass
