import psutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QLineEdit, QMessageBox, QSplitter,
    QTextEdit, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSortFilterProxyModel
from PyQt6.QtGui import QFont, QColor

from app.workers.process_monitor import ProcessMonitor
from app.utils.process_info import get_process_info, IMPORTANCE_LABELS
from app.utils.junk_detector import format_size


class ProcessWidget(QWidget):
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._monitor = None
        self._procs = []
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 16)
        outer.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("⚙  Процессы")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Поиск по имени...")
        self.search_box.setFixedWidth(200)
        self.search_box.textChanged.connect(self._apply_filter)
        header.addWidget(self.search_box)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Все", "Системные", "Важные", "Обычные", "Лишние"])
        self.filter_combo.currentIndexChanged.connect(self._apply_filter)
        header.addWidget(self.filter_combo)

        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.setObjectName("secondary_btn")
        self.refresh_btn.clicked.connect(self._refresh_now)
        header.addWidget(self.refresh_btn)

        outer.addLayout(header)

        # Legend bar
        legend_bar = QWidget()
        legend_bar.setStyleSheet(
            "background-color:#13132a; border:1px solid #1e1e42; border-radius:8px; padding:2px;"
        )
        legend = QHBoxLayout(legend_bar)
        legend.setContentsMargins(12, 6, 12, 6)
        hint = QLabel("Цвет обозначает важность процесса:")
        hint.setStyleSheet("color: #404060; font-size: 8pt;")
        legend.addWidget(hint)
        legend.addSpacing(10)
        for imp, (label, color) in IMPORTANCE_LABELS.items():
            dot = QLabel(f"●  {label}")
            dot.setStyleSheet(f"color: {color}; font-size: 9pt; font-weight: bold;")
            legend.addWidget(dot)
            legend.addSpacing(6)
        legend.addStretch()
        outer.addWidget(legend_bar)

        # Splitter: table + detail panel
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Process table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Процесс", "PID", "CPU %", "RAM", "Статус", "Категория"])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, hdr.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, hdr.ResizeMode.Fixed)
        hdr.setSectionResizeMode(2, hdr.ResizeMode.Fixed)
        hdr.setSectionResizeMode(3, hdr.ResizeMode.Fixed)
        hdr.setSectionResizeMode(4, hdr.ResizeMode.Fixed)
        hdr.setSectionResizeMode(5, hdr.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 100)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget { alternate-background-color: #1e1e38; }"
        )
        self.table.itemSelectionChanged.connect(self._on_selection)
        self.table.setSortingEnabled(True)
        splitter.addWidget(self.table)

        # Detail panel
        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(0, 8, 0, 0)

        detail_header = QHBoxLayout()
        detail_title = QLabel("Информация о процессе")
        detail_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        detail_header.addWidget(detail_title)
        detail_header.addStretch()

        self.kill_btn = QPushButton("Завершить процесс")
        self.kill_btn.setObjectName("danger_btn")
        self.kill_btn.setEnabled(False)
        self.kill_btn.clicked.connect(self._kill_selected)
        detail_header.addWidget(self.kill_btn)
        detail_layout.addLayout(detail_header)

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMinimumHeight(120)
        self.detail_text.setStyleSheet(
            "QTextEdit { background-color: #13132a; border: 1px solid #1e1e42; "
            "border-radius: 8px; color: #c0c0d8; padding: 12px; font-size: 9pt; }"
        )
        self.detail_text.setPlaceholderText("Нажмите на процесс чтобы увидеть информацию о нём...")
        detail_layout.addWidget(self.detail_text)
        splitter.addWidget(detail_widget)

        splitter.setSizes([480, 200])
        outer.addWidget(splitter, 1)

        # Count label
        self.count_lbl = QLabel("")
        self.count_lbl.setStyleSheet("color: #303055; font-size: 8pt; padding: 2px 0;")
        outer.addWidget(self.count_lbl)

    def on_shown(self):
        if self._monitor is None or not self._monitor.isRunning():
            self._monitor = ProcessMonitor(interval_ms=2000)
            self._monitor.data_ready.connect(self._on_data)
            self._monitor.start()

    def _on_data(self, procs: list):
        self._procs = procs
        # Remember selected PID so selection survives table refresh
        selected_pid = self._selected_pid()
        self._apply_filter()
        if selected_pid is not None:
            self._restore_selection(selected_pid)

    def _selected_pid(self) -> int | None:
        for item in self.table.selectedItems():
            proc = self.table.item(item.row(), 0)
            if proc:
                data = proc.data(Qt.ItemDataRole.UserRole)
                if data:
                    return data.get("pid")
        return None

    def _restore_selection(self, pid: int):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                data = item.data(Qt.ItemDataRole.UserRole)
                if data and data.get("pid") == pid:
                    self.table.selectRow(row)
                    return

    def _apply_filter(self):
        search = self.search_box.text().lower()
        filter_idx = self.filter_combo.currentIndex()
        # 0=All, 1=System(0), 2=Important(1), 3=Normal(2), 4=Unnecessary(3)
        imp_filter = filter_idx - 1  # -1 means all

        filtered = []
        for p in self._procs:
            _, imp = get_process_info(p["name"])
            if imp_filter >= 0 and imp != imp_filter:
                continue
            if search and search not in p["name"].lower():
                continue
            filtered.append((p, imp))

        self._fill_table(filtered)

    def _fill_table(self, rows: list):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for proc, imp in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            _, color = IMPORTANCE_LABELS.get(imp, ("Обычный", "#e0e0e0"))
            imp_label, _ = IMPORTANCE_LABELS.get(imp, ("Обычный", "#e0e0e0"))

            name_item = QTableWidgetItem(proc["name"])
            pid_item = QTableWidgetItem(str(proc["pid"]))
            pid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            cpu_item = QTableWidgetItem(f"{proc['cpu']:.1f}")
            cpu_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            ram_item = QTableWidgetItem(format_size(proc["ram"]))
            ram_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            status_item = QTableWidgetItem(proc["status"])
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            imp_item = QTableWidgetItem(imp_label)
            imp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            q_color = QColor(color)
            for item in [name_item, pid_item, cpu_item, ram_item, status_item, imp_item]:
                item.setForeground(q_color)

            # Store proc data in name item
            name_item.setData(Qt.ItemDataRole.UserRole, proc)

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, pid_item)
            self.table.setItem(row, 2, cpu_item)
            self.table.setItem(row, 3, ram_item)
            self.table.setItem(row, 4, status_item)
            self.table.setItem(row, 5, imp_item)

        self.table.setSortingEnabled(True)
        self.count_lbl.setText(f"Показано {len(rows)} из {len(self._procs)} процессов")

    def _on_selection(self):
        selected = self.table.selectedItems()
        if not selected:
            self.detail_text.clear()
            self.kill_btn.setEnabled(False)
            return

        row = selected[0].row()
        name_item = self.table.item(row, 0)
        if not name_item:
            return
        proc = name_item.data(Qt.ItemDataRole.UserRole)
        if not proc:
            return

        desc, imp = get_process_info(proc["name"])
        imp_label, _ = IMPORTANCE_LABELS.get(imp, ("Обычный", "#e0e0e0"))

        text = (
            f"Процесс: {proc['name']}\n"
            f"PID: {proc['pid']}\n"
            f"Пользователь: {proc.get('user', '—')}\n"
            f"Путь: {proc.get('exe', '—') or '—'}\n"
            f"Категория: {imp_label}\n\n"
            f"Описание: {desc}"
        )
        self.detail_text.setPlainText(text)

        # Allow kill only for non-system processes
        can_kill = imp >= 2 and proc.get("user", "").lower() not in ("", "system", "nt authority\\system")
        self.kill_btn.setEnabled(can_kill)

    def _kill_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        name_item = self.table.item(row, 0)
        if not name_item:
            return
        proc = name_item.data(Qt.ItemDataRole.UserRole)
        if not proc:
            return

        reply = QMessageBox.question(
            self, "Завершить процесс",
            f"Завершить процесс {proc['name']} (PID {proc['pid']})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            p = psutil.Process(proc["pid"])
            p.terminate()
            self.status_message.emit(f"Процесс {proc['name']} завершён")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось завершить процесс:\n{e}")

    def _refresh_now(self):
        if self._monitor:
            pass  # monitor updates automatically
        self.status_message.emit("Список процессов обновлён")

    def hideEvent(self, event):
        if self._monitor and self._monitor.isRunning():
            self._monitor.stop()
            self._monitor = None
        super().hideEvent(event)
