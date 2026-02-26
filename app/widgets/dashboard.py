import psutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QFrame, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from app.utils.junk_detector import format_size
from app.utils.file_utils import get_recycle_bin_size


class StatCard(QWidget):
    def __init__(self, icon: str, title: str, color: str = "#e94560", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumWidth(160)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 20px; color: {color};")
        top.addWidget(icon_lbl)
        top.addStretch()
        layout.addLayout(top)

        self.value_lbl = QLabel("—")
        self.value_lbl.setStyleSheet(
            f"font-size: 20pt; font-weight: bold; color: {color};"
        )
        layout.addWidget(self.value_lbl)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("card_title")
        layout.addWidget(title_lbl)

        self.sub_lbl = QLabel("")
        self.sub_lbl.setObjectName("card_sub")
        layout.addWidget(self.sub_lbl)

    def set_value(self, val: str, sub: str = ""):
        self.value_lbl.setText(val)
        if sub:
            self.sub_lbl.setText(sub)


class DiskMiniBar(QWidget):
    def __init__(self, mountpoint: str, usage, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.setSpacing(5)

        header = QHBoxLayout()
        drive_lbl = QLabel(mountpoint)
        drive_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        drive_lbl.setStyleSheet("color: #c0c0d8;")

        pct = usage.percent
        color = "#e74c3c" if pct >= 90 else "#f39c12" if pct >= 75 else "#2ecc71"
        pct_lbl = QLabel(f"{pct:.1f}%")
        pct_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 10pt;")

        used_lbl = QLabel(f"{format_size(usage.used)} / {format_size(usage.total)}")
        used_lbl.setStyleSheet("color: #404060; font-size: 8pt;")

        header.addWidget(drive_lbl)
        header.addWidget(pct_lbl)
        header.addStretch()
        header.addWidget(used_lbl)
        layout.addLayout(header)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(int(pct))
        bar.setFixedHeight(6)
        bar.setFormat("")
        if pct >= 90:
            bar.setStyleSheet(
                "QProgressBar { background:#1a1a38; border-radius:3px; }"
                "QProgressBar::chunk { background:#e74c3c; border-radius:3px; }"
            )
        elif pct >= 75:
            bar.setStyleSheet(
                "QProgressBar { background:#1a1a38; border-radius:3px; }"
                "QProgressBar::chunk { background:#f39c12; border-radius:3px; }"
            )
        layout.addWidget(bar)


class DashboardWidget(QWidget):
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_live)
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(22)
        scroll.setWidget(page)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        # Title
        title_row = QHBoxLayout()
        title = QLabel("Обзор системы")
        title.setObjectName("page_title")
        title_row.addWidget(title)
        title_row.addStretch()
        import platform, socket
        try:
            host_lbl = QLabel(f"🖥  {socket.gethostname()}  ·  {platform.system()} {platform.release()}")
        except Exception:
            host_lbl = QLabel("")
        host_lbl.setStyleSheet("color: #404060; font-size: 9pt;")
        title_row.addWidget(host_lbl)
        outer.addLayout(title_row)

        # ── Stat cards ───────────────────────────
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.card_cpu   = StatCard("⚡", "НАГРУЗКА CPU",   "#a060ff")
        self.card_ram   = StatCard("🧠", "RAM",            "#3498db")
        self.card_disk  = StatCard("💾", "ДИСК C:",        "#2ecc71")
        self.card_procs = StatCard("⚙",  "ПРОЦЕССОВ",      "#f39c12")
        self.card_rb    = StatCard("🗑",  "КОРЗИНА",        "#e94560")

        for c in [self.card_cpu, self.card_ram, self.card_disk,
                  self.card_procs, self.card_rb]:
            cards_layout.addWidget(c)
        outer.addLayout(cards_layout)

        # ── Disk section ─────────────────────────
        sep_lbl = QLabel("ИСПОЛЬЗОВАНИЕ ДИСКОВ")
        sep_lbl.setStyleSheet(
            "color: #303055; font-size: 8pt; font-weight: bold; letter-spacing: 2px;"
        )
        outer.addWidget(sep_lbl)

        self.disk_container = QWidget()
        self.disk_container.setObjectName("card")
        self.disk_vlayout = QVBoxLayout(self.disk_container)
        self.disk_vlayout.setContentsMargins(18, 14, 18, 14)
        self.disk_vlayout.setSpacing(4)
        outer.addWidget(self.disk_container)

        # ── System info grid ─────────────────────
        sep_lbl2 = QLabel("СИСТЕМНАЯ ИНФОРМАЦИЯ")
        sep_lbl2.setStyleSheet(
            "color: #303055; font-size: 8pt; font-weight: bold; letter-spacing: 2px;"
        )
        outer.addWidget(sep_lbl2)

        info_card = QWidget()
        info_card.setObjectName("card")
        self.info_grid = QGridLayout(info_card)
        self.info_grid.setContentsMargins(18, 14, 18, 14)
        self.info_grid.setSpacing(10)
        self.info_grid.setColumnMinimumWidth(1, 220)
        self.info_grid.setColumnMinimumWidth(3, 220)
        self._info_labels = {}
        info_rows = [
            ("os",       "Операционная система"),
            ("hostname", "Имя компьютера"),
            ("uptime",   "Время работы"),
            ("cpu_count","Ядра CPU"),
            ("ram_total","Всего RAM"),
            ("boot_time","Загружен"),
        ]
        for i, (key, label) in enumerate(info_rows):
            row, col = divmod(i, 2)
            key_lbl = QLabel(label)
            key_lbl.setStyleSheet("color: #404060; font-size: 9pt;")
            val_lbl = QLabel("—")
            val_lbl.setStyleSheet("color: #c0c0d8; font-size: 9pt;")
            self._info_labels[key] = val_lbl
            self.info_grid.addWidget(key_lbl, row, col * 2)
            self.info_grid.addWidget(val_lbl, row, col * 2 + 1)
        outer.addWidget(info_card)
        outer.addStretch()

    def on_shown(self):
        self._refresh_live()
        self._load_static_info()
        if not self._timer.isActive():
            self._timer.start(2000)

    def _refresh_live(self):
        cpu = psutil.cpu_percent(interval=None)
        self.card_cpu.set_value(
            f"{cpu:.0f}%",
            f"{psutil.cpu_count()} логических ядер"
        )

        ram = psutil.virtual_memory()
        self.card_ram.set_value(
            f"{ram.percent:.0f}%",
            f"{format_size(ram.used)} / {format_size(ram.total)}"
        )

        try:
            c = psutil.disk_usage("C:\\")
            self.card_disk.set_value(
                f"{c.percent:.0f}%",
                f"Свободно: {format_size(c.free)}"
            )
        except Exception:
            pass

        self.card_procs.set_value(
            str(len(psutil.pids())),
            "активных задач"
        )

        count, size = get_recycle_bin_size()
        self.card_rb.set_value(
            format_size(size),
            f"{count} объектов"
        )

        self._rebuild_disk_bars()

        import time
        uptime_sec = time.time() - psutil.boot_time()
        h = int(uptime_sec // 3600)
        m = int((uptime_sec % 3600) // 60)
        if "uptime" in self._info_labels:
            self._info_labels["uptime"].setText(f"{h} ч  {m} мин")

    def _rebuild_disk_bars(self):
        while self.disk_vlayout.count():
            item = self.disk_vlayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        parts = [p for p in psutil.disk_partitions(all=False)
                 if "cdrom" not in p.opts and p.fstype]
        for part in parts:
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except (PermissionError, OSError):
                continue
            bar = DiskMiniBar(part.mountpoint, usage)
            self.disk_vlayout.addWidget(bar)
            if part != parts[-1]:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setStyleSheet("color: #1a1a38;")
                self.disk_vlayout.addWidget(sep)

    def _load_static_info(self):
        import platform, socket, datetime
        try:
            ver = platform.version()[:30]
            self._info_labels["os"].setText(
                f"{platform.system()} {platform.release()} ({ver})"
            )
        except Exception:
            pass
        try:
            self._info_labels["hostname"].setText(socket.gethostname())
        except Exception:
            pass
        try:
            self._info_labels["cpu_count"].setText(
                f"{psutil.cpu_count(logical=False)} физ. / {psutil.cpu_count()} лог."
            )
        except Exception:
            pass
        try:
            self._info_labels["ram_total"].setText(
                format_size(psutil.virtual_memory().total)
            )
        except Exception:
            pass
        try:
            boot_dt = __import__('datetime').datetime.fromtimestamp(psutil.boot_time())
            self._info_labels["boot_time"].setText(boot_dt.strftime("%d.%m.%Y  %H:%M"))
        except Exception:
            pass

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)
