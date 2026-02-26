"""
Per-file type descriptions, icons (emoji) and categories.
Also reads Windows version info from EXE/DLL.
"""
from pathlib import Path

# (description, emoji, category_key)
EXT_INFO: dict[str, tuple[str, str, str]] = {
    # ── Executables ──────────────────────────
    ".exe":      ("Исполняемый файл",              "⚙",  "executable"),
    ".dll":      ("Динамическая библиотека (DLL)",  "📦", "library"),
    ".sys":      ("Системный драйвер",              "🔧", "driver"),
    ".ocx":      ("ActiveX компонент",              "📦", "library"),
    ".com":      ("Программа командной строки",     "⚙",  "executable"),
    ".scr":      ("Экранная заставка",              "⚙",  "executable"),
    ".ax":       ("DirectShow фильтр",              "📦", "library"),
    ".drv":      ("Драйвер устройства",             "🔧", "driver"),
    # ── Config ───────────────────────────────
    ".ini":      ("Файл настроек INI",              "⚙",  "config"),
    ".cfg":      ("Файл конфигурации",              "⚙",  "config"),
    ".conf":     ("Файл конфигурации",              "⚙",  "config"),
    ".config":   ("Файл конфигурации .config",      "⚙",  "config"),
    ".json":     ("JSON данные / настройки",        "📄", "config"),
    ".xml":      ("XML документ",                   "📄", "config"),
    ".yaml":     ("YAML конфигурация",              "📄", "config"),
    ".toml":     ("TOML конфигурация",              "📄", "config"),
    ".reg":      ("Записи реестра Windows",         "🔧", "config"),
    ".manifest": ("Манифест приложения",            "📄", "config"),
    ".plist":    ("Property List (настройки)",      "📄", "config"),
    # ── Cache / Temp ─────────────────────────
    ".tmp":      ("Временный файл",                 "🗑",  "cache"),
    ".temp":     ("Временный файл",                 "🗑",  "cache"),
    ".dmp":      ("Дамп памяти (crash dump)",       "🗑",  "cache"),
    ".bak":      ("Резервная копия",                "🗑",  "cache"),
    ".old":      ("Устаревший файл",                "🗑",  "cache"),
    # ── Logs ────────────────────────────────
    ".log":      ("Журнал событий",                 "📋", "log"),
    ".trace":    ("Файл трассировки",               "📋", "log"),
    ".etl":      ("Журнал ETW (Windows)",           "📋", "log"),
    # ── Data / Databases ────────────────────
    ".db":       ("База данных",                    "💾", "data"),
    ".sqlite":   ("SQLite база данных",             "💾", "data"),
    ".sqlite3":  ("SQLite база данных",             "💾", "data"),
    ".mdb":      ("База данных Access",             "💾", "data"),
    ".dat":      ("Файл данных приложения",         "💾", "data"),
    ".bin":      ("Бинарный файл данных",           "💾", "data"),
    ".cache":    ("Кэш-файл",                       "💾", "cache"),
    # ── Resources ────────────────────────────
    ".ico":      ("Иконка Windows",                 "🖼",  "resource"),
    ".png":      ("Изображение PNG",                "🖼",  "resource"),
    ".jpg":      ("Изображение JPEG",               "🖼",  "resource"),
    ".jpeg":     ("Изображение JPEG",               "🖼",  "resource"),
    ".bmp":      ("Растровое изображение",          "🖼",  "resource"),
    ".svg":      ("Векторное изображение SVG",      "🖼",  "resource"),
    ".gif":      ("Анимированное изображение GIF",  "🖼",  "resource"),
    ".webp":     ("Изображение WebP",               "🖼",  "resource"),
    ".ttf":      ("Шрифт TrueType",                 "🔤", "resource"),
    ".otf":      ("Шрифт OpenType",                 "🔤", "resource"),
    ".woff":     ("Веб-шрифт WOFF",                 "🔤", "resource"),
    ".woff2":    ("Веб-шрифт WOFF2",                "🔤", "resource"),
    ".eot":      ("Встроенный шрифт EOT",           "🔤", "resource"),
    ".pak":      ("Пакет ресурсов браузера/Chromium","📦", "resource"),
    ".rsrc":     ("Ресурсы приложения",             "📦", "resource"),
    ".mui":      ("Ресурсы интерфейса MUI",         "🔤", "resource"),
    # ── Shortcuts ────────────────────────────
    ".lnk":      ("Ярлык Windows",                  "🔗", "shortcut"),
    ".url":      ("Интернет-ссылка",                "🔗", "shortcut"),
    # ── Archives ────────────────────────────
    ".zip":      ("ZIP архив",                      "📦", "archive"),
    ".7z":       ("7-Zip архив",                    "📦", "archive"),
    ".rar":      ("RAR архив",                      "📦", "archive"),
    ".cab":      ("Cabinet архив Windows",          "📦", "archive"),
    ".msi":      ("Пакет установки Windows (MSI)", "📦", "archive"),
    # ── Scripts ─────────────────────────────
    ".bat":      ("Пакетный файл (batch)",          "⚙",  "script"),
    ".cmd":      ("Командный файл Windows",         "⚙",  "script"),
    ".ps1":      ("PowerShell скрипт",              "⚙",  "script"),
    ".vbs":      ("VBScript скрипт",                "⚙",  "script"),
    ".js":       ("JavaScript файл",                "📄", "script"),
    ".py":       ("Python скрипт",                  "📄", "script"),
    # ── Debug ────────────────────────────────
    ".pdb":      ("Символы отладки (PDB)",          "🔧", "debug"),
    ".map":      ("Source map файл",                "🔧", "debug"),
}

CATEGORY_NAMES: dict[str, str] = {
    "executable": "Исполняемые файлы (.exe)",
    "library":    "Библиотеки и компоненты (.dll)",
    "driver":     "Драйверы",
    "config":     "Настройки и конфигурация",
    "cache":      "Кэш и временные файлы",
    "log":        "Журналы событий",
    "data":       "Данные и базы данных",
    "resource":   "Ресурсы (иконки, шрифты, изображения)",
    "shortcut":   "Ярлыки",
    "archive":    "Архивы и пакеты установки",
    "script":     "Скрипты и командные файлы",
    "debug":      "Файлы отладки",
    "other":      "Прочие файлы",
}

CATEGORY_COLORS: dict[str, str] = {
    "executable": "#e94560",
    "library":    "#9b59b6",
    "driver":     "#e74c3c",
    "config":     "#3498db",
    "cache":      "#f39c12",
    "log":        "#7f8c8d",
    "data":       "#2ecc71",
    "resource":   "#1abc9c",
    "shortcut":   "#f1c40f",
    "archive":    "#e67e22",
    "script":     "#3498db",
    "debug":      "#7f8c8d",
    "other":      "#606080",
}

CATEGORY_ORDER = [
    "executable", "library", "driver", "config",
    "data", "cache", "log", "resource",
    "shortcut", "archive", "script", "debug", "other",
]


def get_file_info(path: str) -> tuple[str, str, str]:
    """
    Returns (description, emoji, category_key) for a file path.
    For EXE/DLL also reads Windows version info.
    """
    ext = Path(path).suffix.lower()
    base_desc, emoji, cat = EXT_INFO.get(ext, ("Файл данных приложения", "📄", "other"))

    if ext in (".exe", ".dll", ".sys", ".ocx", ".ax", ".drv"):
        ver = _version_description(path)
        if ver:
            base_desc = ver

    return base_desc, emoji, cat


def _version_description(path: str) -> str:
    """Read FileDescription or ProductName from Windows version info."""
    try:
        import win32api
        for lang in (r"\StringFileInfo\040904B0\\",
                     r"\StringFileInfo\040904E4\\",
                     r"\StringFileInfo\000004B0\\"):
            for field in ("FileDescription", "ProductName"):
                try:
                    val = win32api.GetFileVersionInfo(path, lang + field)
                    if val and val.strip():
                        return val.strip()
                except Exception:
                    pass
    except Exception:
        pass
    return ""


def get_file_version(path: str) -> str:
    """Returns version string like '120.0.6099.130' or ''."""
    try:
        import win32api
        info = win32api.GetFileVersionInfo(path, "\\")
        ms = info["FileVersionMS"]
        ls = info["FileVersionLS"]
        return f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
    except Exception:
        return ""
