import psutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor

from app.workers.file_scanner import DiskScanner
from app.utils.junk_detector import format_size


class DiskBar(QWidget):
    def __init__(self, drive: str, usage, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        pct = usage.percent
        color = "#e74c3c" if pct >= 90 else "#f39c12" if pct >= 75 else "#2ecc71"

        header = QHBoxLayout()
        drive_lbl = QLabel(f"💾  Диск {drive}")
        drive_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        drive_lbl.setStyleSheet("color: #e0e0f0;")
        total_lbl = QLabel(format_size(usage.total))
        total_lbl.setStyleSheet("color: #404060; font-size: 9pt;")
        header.addWidget(drive_lbl)
        header.addStretch()
        header.addWidget(total_lbl)
        layout.addLayout(header)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(int(pct))
        bar.setFixedHeight(8)
        bar.setFormat("")
        bar.setStyleSheet(
            f"QProgressBar {{ background:#1a1a38; border-radius:4px; border:none; }}"
            f"QProgressBar::chunk {{ background:{color}; border-radius:4px; }}"
        )
        layout.addWidget(bar)

        stats = QHBoxLayout()
        used_lbl = QLabel(f"Занято: {format_size(usage.used)}")
        used_lbl.setStyleSheet("color: #606080; font-size: 9pt;")
        free_lbl = QLabel(f"Свободно: {format_size(usage.free)}")
        free_lbl.setStyleSheet(f"color: {color}; font-size: 9pt;")
        pct_lbl = QLabel(f"{pct:.1f}%")
        pct_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        pct_lbl.setStyleSheet(f"color: {color};")
        pct_lbl.setObjectName(
            "danger_label" if pct >= 90
            else "warning_label" if pct >= 75
            else "success_label"
        )
        stats.addWidget(used_lbl)
        stats.addStretch()
        stats.addWidget(free_lbl)
        stats.addWidget(pct_lbl)
        layout.addLayout(stats)


class DiskWidget(QWidget):
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scanner = None
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(18)

        title = QLabel("💾  Диски")
        title.setObjectName("page_title")
        outer.addWidget(title)

        sep_lbl = QLabel("ПОДКЛЮЧЁННЫЕ ДИСКИ")
        sep_lbl.setStyleSheet(
            "color: #303055; font-size: 8pt; font-weight: bold; letter-spacing: 2px;"
        )
        outer.addWidget(sep_lbl)

        # Disk usage summary
        self.drives_container = QWidget()
        self.drives_layout = QHBoxLayout(self.drives_container)
        self.drives_layout.setContentsMargins(0, 0, 0, 0)
        self.drives_layout.setSpacing(12)

        drives_scroll = QScrollArea()
        drives_scroll.setWidget(self.drives_container)
        drives_scroll.setWidgetResizable(True)
        drives_scroll.setMaximumHeight(160)
        drives_scroll.setFrameShape(QFrame.Shape.NoFrame)
        drives_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(drives_scroll)

        # Folder scanner
        sep_lbl2 = QLabel("СОДЕРЖИМОЕ ДИСКА")
        sep_lbl2.setStyleSheet(
            "color: #303055; font-size: 8pt; font-weight: bold; letter-spacing: 2px;"
        )
        outer.addWidget(sep_lbl2)

        scan_header = QHBoxLayout()
        self.drive_combo = QComboBox()
        scan_header.addWidget(self.drive_combo)

        self.scan_btn = QPushButton("  Сканировать папки")
        self.scan_btn.clicked.connect(self._start_scan)
        scan_header.addWidget(self.scan_btn)
        scan_header.addStretch()

        self.scan_status = QLabel("")
        self.scan_status.setStyleSheet("color: #505070; font-size: 9pt;")
        scan_header.addWidget(self.scan_status)
        outer.addLayout(scan_header)

        self.folder_table = QTableWidget(0, 3)
        self.folder_table.setHorizontalHeaderLabels(["ПАПКА", "РАЗМЕР", "%"])
        hdr = self.folder_table.horizontalHeader()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, hdr.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, hdr.ResizeMode.Fixed)
        hdr.setSectionResizeMode(2, hdr.ResizeMode.Fixed)
        self.folder_table.setColumnWidth(1, 120)
        self.folder_table.setColumnWidth(2, 70)
        self.folder_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.folder_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.folder_table.verticalHeader().setVisible(False)
        self.folder_table.setAlternatingRowColors(True)
        self.folder_table.setStyleSheet(
            "QTableWidget { alternate-background-color: #111128; }"
        )
        outer.addWidget(self.folder_table, 1)

    def on_shown(self):
        self._load_drives()

    def _load_drives(self):
        while self.drives_layout.count():
            item = self.drives_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.drive_combo.clear()

        for part in psutil.disk_partitions(all=False):
            if "cdrom" in part.opts or not part.fstype:
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                bar = DiskBar(part.mountpoint, usage)
                bar.setMinimumWidth(200)
                self.drives_layout.addWidget(bar)
                self.drive_combo.addItem(f"  {part.mountpoint}", part.mountpoint)
            except (PermissionError, OSError):
                pass
        self.drives_layout.addStretch()

    def _start_scan(self):
        drive = self.drive_combo.currentData()
        if not drive:
            return
        if self._scanner and self._scanner.isRunning():
            self._scanner.stop()

        self.scan_btn.setEnabled(False)
        self.folder_table.setRowCount(0)
        self.scan_status.setText("Сканирование...")

        self._scanner = DiskScanner(drive)
        self._scanner.progress.connect(lambda pct, msg: self.scan_status.setText(msg))
        self._scanner.results_ready.connect(self._on_scan_done)
        self._scanner.start()

    def _on_scan_done(self, results: list):
        self.scan_btn.setEnabled(True)
        self.folder_table.setRowCount(0)

        if not results:
            self.scan_status.setText("Нет данных")
            return

        total_size = sum(s for _, s in results)
        self.scan_status.setText(f"Найдено {len(results)} папок · Всего: {format_size(total_size)}")
        self.status_message.emit(f"Сканирование диска завершено: {len(results)} папок")

        for path, size in results[:200]:  # show top 200
            row = self.folder_table.rowCount()
            self.folder_table.insertRow(row)

            name_item = QTableWidgetItem(path)
            size_item = QTableWidgetItem(format_size(size))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            pct = (size / total_size * 100) if total_size else 0
            pct_item = QTableWidgetItem(f"{pct:.1f}%")
            pct_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if pct > 20:
                color = QColor("#e74c3c")
            elif pct > 10:
                color = QColor("#f39c12")
            else:
                color = QColor("#e0e0e0")

            for item in [name_item, size_item, pct_item]:
                item.setForeground(color)

            self.folder_table.setItem(row, 0, name_item)
            self.folder_table.setItem(row, 1, size_item)
            self.folder_table.setItem(row, 2, pct_item)
