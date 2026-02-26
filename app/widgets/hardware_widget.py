from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QGroupBox, QScrollArea, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from app.workers.hardware_monitor import HardwareMonitor, StaticHardwareLoader
from app.utils.junk_detector import format_size


# ──────────────────────────────────────────────
# Small reusable components
# ──────────────────────────────────────────────

class GaugeBar(QWidget):
    """Labelled progress bar with percent readout."""
    def __init__(self, label: str, color: str = "#a060ff", parent=None):
        super().__init__(parent)
        self._color = color
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 8)
        layout.setSpacing(4)

        row = QHBoxLayout()
        self._title = QLabel(label)
        self._title.setStyleSheet("color: #c0c0d8; font-weight: bold; font-size: 10pt;")
        self._pct_lbl = QLabel("—")
        self._pct_lbl.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11pt;")
        self._pct_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self._title)
        row.addWidget(self._pct_lbl)
        layout.addLayout(row)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setFixedHeight(8)
        self._bar.setFormat("")
        self._set_color(color)
        layout.addWidget(self._bar)

        self._sub = QLabel("")
        self._sub.setStyleSheet("color: #404060; font-size: 8pt;")
        layout.addWidget(self._sub)

    def _set_color(self, color: str):
        self._bar.setStyleSheet(
            f"QProgressBar {{ background:#1a1a38; border:none; border-radius:4px; }}"
            f"QProgressBar::chunk {{ background:{color}; border-radius:4px; }}"
        )

    def update_value(self, pct: float, sub: str = ""):
        self._bar.setValue(int(pct))
        self._pct_lbl.setText(f"{pct:.0f}%")
        # Dynamic color based on load
        if pct >= 90:
            c = "#e74c3c"
        elif pct >= 70:
            c = "#f39c12"
        else:
            c = self._color
        self._pct_lbl.setStyleSheet(f"color: {c}; font-weight: bold; font-size: 11pt;")
        self._set_color(c)
        if sub:
            self._sub.setText(sub)


class PropRow(QWidget):
    """Key → Value row."""
    def __init__(self, key: str, value: str = "—", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(0)

        k = QLabel(key)
        k.setFixedWidth(175)
        k.setStyleSheet("color: #404060; font-size: 9pt;")
        self._val = QLabel(value)
        self._val.setStyleSheet("color: #c0c0d8; font-size: 9pt;")
        self._val.setWordWrap(True)
        layout.addWidget(k)
        layout.addWidget(self._val, 1)

    def set(self, v: str):
        self._val.setText(v)


class SectionBox(QGroupBox):
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)


# ──────────────────────────────────────────────
# Main widget
# ──────────────────────────────────────────────

class HardwareWidget(QWidget):
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._monitor: HardwareMonitor | None = None
        self._loader:  StaticHardwareLoader | None = None
        self._static_loaded = False
        self._build_ui()

    # ── Build UI ──────────────────────────────

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)
        scroll.setWidget(page)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll)

        # Title
        title = QLabel("🖥  Железо")
        title.setObjectName("page_title")
        layout.addWidget(title)

        # ── Live metrics ─────────────────────
        live_box = SectionBox("Текущая нагрузка")
        live_layout = QVBoxLayout(live_box)
        live_layout.setSpacing(2)

        self.cpu_gauge  = GaugeBar("Процессор (CPU)",       "#a060ff")
        self.ram_gauge  = GaugeBar("Оперативная память",    "#3498db")
        self.swap_gauge = GaugeBar("Файл подкачки (Swap)",  "#2ecc71")
        for g in [self.cpu_gauge, self.ram_gauge, self.swap_gauge]:
            live_layout.addWidget(g)
        layout.addWidget(live_box)

        # ── CPU info ─────────────────────────
        cpu_box = SectionBox("Процессор (CPU)")
        cpu_gl = QGridLayout(cpu_box)
        cpu_gl.setColumnStretch(1, 1)
        cpu_gl.setColumnStretch(3, 1)
        cpu_gl.setSpacing(8)

        self.r_cpu_name  = PropRow("Модель")
        self.r_cpu_cores = PropRow("Ядра")
        self.r_cpu_freq  = PropRow("Частота")
        cpu_gl.addWidget(self.r_cpu_name,  0, 0, 1, 2)
        cpu_gl.addWidget(self.r_cpu_cores, 1, 0)
        cpu_gl.addWidget(self.r_cpu_freq,  1, 1)
        layout.addWidget(cpu_box)

        # ── RAM info ─────────────────────────
        ram_box = SectionBox("Оперативная память (RAM)")
        ram_vl = QVBoxLayout(ram_box)
        self.r_ram_total = PropRow("Объём")
        self.r_ram_type  = PropRow("Тип")
        self.r_ram_free  = PropRow("Свободно")
        for r in [self.r_ram_total, self.r_ram_type, self.r_ram_free]:
            ram_vl.addWidget(r)
        layout.addWidget(ram_box)

        # ── GPU info ─────────────────────────
        gpu_box = SectionBox("Видеокарта (GPU)")
        self.gpu_vl = QVBoxLayout(gpu_box)
        self.gpu_vl.addWidget(_muted("Загрузка..."))
        layout.addWidget(gpu_box)

        # ── Motherboard ──────────────────────
        board_box = SectionBox("Материнская плата")
        board_vl = QVBoxLayout(board_box)
        self.r_board = PropRow("Модель")
        self.r_bios  = PropRow("BIOS версия")
        board_vl.addWidget(self.r_board)
        board_vl.addWidget(self.r_bios)
        layout.addWidget(board_box)

        # ── Disks ────────────────────────────
        disk_box = SectionBox("Диски (физические)")
        self.disk_vl = QVBoxLayout(disk_box)
        self.disk_vl.addWidget(_muted("Загрузка..."))
        layout.addWidget(disk_box)

        # ── Battery ──────────────────────────
        self.bat_box = SectionBox("Аккумулятор")
        bat_vl = QVBoxLayout(self.bat_box)
        self.bat_gauge  = GaugeBar("Заряд", "#2ecc71")
        self.r_bat_stat = PropRow("Статус")
        bat_vl.addWidget(self.bat_gauge)
        bat_vl.addWidget(self.r_bat_stat)
        self.bat_box.hide()
        layout.addWidget(self.bat_box)

        layout.addStretch()

    # ── Lifecycle ─────────────────────────────

    def on_shown(self):
        if not self._static_loaded:
            self._load_static()
        if self._monitor is None or not self._monitor.isRunning():
            self._start_live()

    def _load_static(self):
        self._static_loaded = True
        self.status_message.emit("Загружаю информацию о железе...")
        self._loader = StaticHardwareLoader(self)
        self._loader.finished.connect(self._on_static_ready)
        self._loader.start()

    def _start_live(self):
        self._monitor = HardwareMonitor(interval_ms=1500)
        self._monitor.data_ready.connect(self._on_live_data)
        self._monitor.start()

    # ── Data handlers ─────────────────────────

    def _on_static_ready(self):
        if self._loader is None:
            return
        info = self._loader.result

        self.r_cpu_name.set(info.get("cpu_name", "—"))

        # RAM
        try:
            import psutil
            ram = psutil.virtual_memory()
            self.r_ram_total.set(format_size(ram.total))
            self.r_ram_free.set(format_size(ram.available))
        except Exception:
            pass
        self.r_ram_type.set(info.get("ram_type", "—") or "—")

        # Board
        self.r_board.set(info.get("board", "—") or "—")
        self.r_bios.set(info.get("bios",  "—") or "—")

        # GPU
        _clear_layout(self.gpu_vl)
        gpus = info.get("gpu", [])
        if gpus:
            for g in gpus:
                vram = format_size(g["vram"]) if g.get("vram") else "—"
                row = PropRow(g.get("name", "GPU"), f"VRAM: {vram}")
                self.gpu_vl.addWidget(row)
        else:
            self.gpu_vl.addWidget(_muted("Нет данных"))

        # Disks
        _clear_layout(self.disk_vl)
        disks = info.get("disk_models", [])
        if disks:
            for d in disks:
                sz = format_size(d["size"]) if d.get("size") else "—"
                name = d.get("model", "Unknown")[:50]
                iface = d.get("interface", "")
                sub = f"{sz}" + (f"  ·  {iface}" if iface else "")
                self.disk_vl.addWidget(PropRow(name, sub))
        else:
            self.disk_vl.addWidget(_muted("Нет данных"))

        self.status_message.emit("Информация о железе загружена")

    def _on_live_data(self, data: dict):
        cpu  = data.get("cpu",  {})
        ram  = data.get("ram",  {})
        swap = data.get("swap", {})
        bat  = data.get("battery")

        # CPU gauge
        pct = cpu.get("percent", 0)
        freq = cpu.get("freq_mhz", 0)
        fmax = cpu.get("freq_max_mhz", 0)
        freq_str = f"{freq:.0f} МГц" + (f" / {fmax:.0f} МГц макс" if fmax else "")
        self.cpu_gauge.update_value(pct, freq_str)

        cp = cpu.get("count_physical", 0)
        cl = cpu.get("count_logical", 0)
        self.r_cpu_cores.set(f"{cp} физических  /  {cl} логических")
        self.r_cpu_freq.set(freq_str)

        # RAM gauge
        ram_pct = ram.get("percent", 0)
        used = ram.get("used", 0)
        total = ram.get("total", 0)
        avail = ram.get("available", 0)
        self.ram_gauge.update_value(
            ram_pct,
            f"{format_size(used)} занято  ·  {format_size(avail)} свободно  /  {format_size(total)}"
        )
        self.r_ram_free.set(format_size(avail))

        # Swap gauge
        sw_pct   = swap.get("percent", 0)
        sw_used  = swap.get("used",  0)
        sw_total = swap.get("total", 0)
        if sw_total:
            self.swap_gauge.update_value(
                sw_pct,
                f"{format_size(sw_used)} из {format_size(sw_total)}"
            )
        else:
            self.swap_gauge.update_value(0, "Не используется")

        # Battery
        if bat:
            self.bat_box.show()
            self.bat_gauge.update_value(bat["percent"])
            status = "Зарядка ⚡" if bat["plugged"] else "От батареи 🔋"
            self.r_bat_stat.set(f"{status}  ·  {bat['percent']:.0f}%")

    def hideEvent(self, event):
        if self._monitor:
            self._monitor.stop()
            # Don't wait — let it finish on its own
            self._monitor = None
        super().hideEvent(event)


# ── Helpers ───────────────────────────────────

def _muted(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color: #404060; font-size: 9pt; padding: 4px 0;")
    return lbl


def _clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w:
            w.deleteLater()
