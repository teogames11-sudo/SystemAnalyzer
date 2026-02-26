"""
Database of known Windows processes with descriptions and importance ratings.
importance: 0=system critical, 1=important, 2=normal, 3=unnecessary/bloat
"""

PROCESS_DB = {
    # ===== Windows System Critical =====
    "system": ("Ядро Windows", 0),
    "system idle process": ("Простой процессора", 0),
    "smss.exe": ("Session Manager — управление сеансами Windows", 0),
    "csrss.exe": ("Client/Server Runtime — ядро Win32 подсистемы", 0),
    "wininit.exe": ("Windows Initialization — инициализация Windows", 0),
    "winlogon.exe": ("Windows Logon — управление входом в систему", 0),
    "services.exe": ("Service Control Manager — управление службами", 0),
    "lsass.exe": ("Local Security Authority — аутентификация и политики безопасности", 0),
    "lsm.exe": ("Local Session Manager — управление локальными сеансами", 0),
    "ntoskrnl.exe": ("Ядро операционной системы Windows", 0),

    # ===== Windows Important =====
    "svchost.exe": ("Service Host — контейнер для системных служб Windows", 1),
    "explorer.exe": ("Windows Explorer — оболочка рабочего стола и файловый менеджер", 1),
    "taskhost.exe": ("Task Host — хост для фоновых задач Windows", 1),
    "taskhostw.exe": ("Task Host Worker — запуск задач планировщика", 1),
    "dwm.exe": ("Desktop Window Manager — отрисовка рабочего стола и эффекты Aero", 1),
    "conhost.exe": ("Console Host — хост для консольных приложений", 1),
    "ctfmon.exe": ("CTF Monitor — языковая панель и ввод текста", 1),
    "spoolsv.exe": ("Print Spooler — управление очередью печати", 1),
    "SearchIndexer.exe": ("Windows Search Indexer — индексирование файлов для поиска", 1),
    "wuauclt.exe": ("Windows Update — служба обновления Windows", 1),
    "MsMpEng.exe": ("Windows Defender — антивирусная защита Microsoft", 1),
    "SecurityHealthSystray.exe": ("Windows Security — системный трей безопасности", 1),
    "fontdrvhost.exe": ("Font Driver Host — хост драйвера шрифтов", 1),
    "audiodg.exe": ("Windows Audio Device Graph — аудио подсистема", 1),
    "RuntimeBroker.exe": ("Runtime Broker — управление разрешениями UWP приложений", 1),
    "ShellExperienceHost.exe": ("Shell Experience Host — интерфейс меню Пуск и уведомлений", 1),
    "StartMenuExperienceHost.exe": ("Start Menu — процесс меню Пуск", 1),
    "SearchHost.exe": ("Search Host — поиск Windows", 1),
    "TextInputHost.exe": ("Text Input Host — виртуальная клавиатура", 1),
    "WmiPrvSE.exe": ("WMI Provider Host — поставщик инструментария управления Windows", 1),
    "dllhost.exe": ("COM Surrogate — хост для COM-объектов", 1),
    "sihost.exe": ("Shell Infrastructure Host — инфраструктура оболочки", 1),

    # ===== Browsers =====
    "chrome.exe": ("Google Chrome — браузер", 2),
    "firefox.exe": ("Mozilla Firefox — браузер", 2),
    "msedge.exe": ("Microsoft Edge — браузер", 2),
    "opera.exe": ("Opera — браузер", 2),
    "brave.exe": ("Brave — браузер", 2),
    "iexplore.exe": ("Internet Explorer — устаревший браузер", 3),

    # ===== Office / Productivity =====
    "WINWORD.EXE": ("Microsoft Word — текстовый редактор", 2),
    "EXCEL.EXE": ("Microsoft Excel — таблицы", 2),
    "POWERPNT.EXE": ("Microsoft PowerPoint — презентации", 2),
    "OUTLOOK.EXE": ("Microsoft Outlook — почта и календарь", 2),
    "ONENOTE.EXE": ("Microsoft OneNote — заметки", 2),
    "Teams.exe": ("Microsoft Teams — мессенджер и видеозвонки", 2),
    "Slack.exe": ("Slack — корпоративный мессенджер", 2),
    "Discord.exe": ("Discord — голосовой и текстовый чат", 2),
    "Telegram.exe": ("Telegram — мессенджер", 2),

    # ===== Development =====
    "Code.exe": ("Visual Studio Code — редактор кода", 2),
    "devenv.exe": ("Visual Studio — IDE", 2),
    "pycharm64.exe": ("PyCharm — IDE для Python", 2),
    "idea64.exe": ("IntelliJ IDEA — IDE", 2),
    "git.exe": ("Git — система контроля версий", 2),
    "python.exe": ("Python — интерпретатор Python", 2),
    "node.exe": ("Node.js — среда выполнения JavaScript", 2),

    # ===== Gaming =====
    "Steam.exe": ("Steam — игровая платформа", 2),
    "steamwebhelper.exe": ("Steam Web Helper — веб-движок Steam", 2),
    "EpicGamesLauncher.exe": ("Epic Games Launcher — игровая платформа", 2),
    "origin.exe": ("EA Origin — игровая платформа", 2),
    "GOGGalaxy.exe": ("GOG Galaxy — игровая платформа", 2),

    # ===== Antivirus =====
    "avast.exe": ("Avast Antivirus — антивирусная защита", 1),
    "avgui.exe": ("AVG Antivirus — антивирусная защита", 1),
    "eset.exe": ("ESET NOD32 — антивирусная защита", 1),
    "kaspersky.exe": ("Kaspersky — антивирусная защита", 1),
    "mbam.exe": ("Malwarebytes — защита от вредоносного ПО", 1),

    # ===== Bloatware / Unnecessary =====
    "OneDrive.exe": ("Microsoft OneDrive — облачное хранилище (можно отключить)", 3),
    "Dropbox.exe": ("Dropbox — облачное хранилище", 3),
    "GoogleDriveSync.exe": ("Google Drive Sync — синхронизация Google Диска", 3),
    "SkypeApp.exe": ("Skype — видеозвонки", 3),
    "Cortana.exe": ("Cortana — голосовой ассистент Microsoft (можно отключить)", 3),
    "YourPhone.exe": ("Your Phone — привязка телефона (можно отключить)", 3),
    "WinStore.App.exe": ("Microsoft Store — магазин приложений", 3),
    "GameBarPresenceWriter.exe": ("Xbox Game Bar — игровая панель (можно отключить)", 3),
    "XboxPCApp.exe": ("Xbox App — консоль Xbox (можно отключить)", 3),
    "msedgewebview2.exe": ("Edge WebView2 — веб-движок для приложений", 3),
    "SearchApp.exe": ("Windows Search — поиск (ресурсоёмкий при первом запуске)", 3),
    "HPNotifications.exe": ("HP Notifications — уведомления HP (bloatware)", 3),
    "HPSupportAssistant.exe": ("HP Support Assistant — поддержка HP (можно удалить)", 3),
    "DellUpdate.exe": ("Dell Update — обновления Dell (можно отключить)", 3),
    "LenovoVantageService.exe": ("Lenovo Vantage — сервис Lenovo (можно отключить)", 3),

    # ===== Media =====
    "vlc.exe": ("VLC Media Player — медиаплеер", 2),
    "spotify.exe": ("Spotify — стриминг музыки", 2),
    "iTunes.exe": ("iTunes — медиатека Apple", 2),

    # ===== System Tools =====
    "taskmgr.exe": ("Task Manager — диспетчер задач Windows", 1),
    "regedit.exe": ("Registry Editor — редактор реестра", 1),
    "cmd.exe": ("Command Prompt — командная строка", 2),
    "powershell.exe": ("PowerShell — командная оболочка", 2),
    "mmc.exe": ("Microsoft Management Console — консоль управления", 1),
    "perfmon.exe": ("Performance Monitor — монитор производительности", 1),
    "notepad.exe": ("Notepad — блокнот", 2),
    "mspaint.exe": ("Paint — графический редактор", 2),
    "calc.exe": ("Calculator — калькулятор", 2),
    "7zfm.exe": ("7-Zip — архиватор", 2),
    "7zg.exe": ("7-Zip GUI — архиватор", 2),
}

IMPORTANCE_LABELS = {
    0: ("Системный", "#e74c3c"),
    1: ("Важный", "#2ecc71"),
    2: ("Обычный", "#3498db"),
    3: ("Лишний", "#f39c12"),
}


def get_process_info(name: str) -> tuple[str, int]:
    """Returns (description, importance) for a process name."""
    key = name.lower()
    if key in PROCESS_DB:
        return PROCESS_DB[key]
    # Fuzzy match by prefix
    for db_key, val in PROCESS_DB.items():
        if key.startswith(db_key.split(".")[0].lower()):
            return val
    return ("Неизвестный процесс", 2)
