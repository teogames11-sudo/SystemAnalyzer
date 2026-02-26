from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QTableWidgetSelectionRange,
    QPushButton, QProgressBar, QTabWidget, QMessageBox,
    QCheckBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from app.workers.file_scanner import FileScanner
from app.utils.junk_detector import JUNK_CATEGORIES, format_size
from app.utils.file_utils import delete_to_trash, delete_permanent, get_recycle_bin_size, empty_recycle_bin


class FilesWidget(QWidget):
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scanner = None
        self._category_files: dict[str, list] = {}
        self._large_files: list = []
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 16)
        outer.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("🗑  Файлы / Мусор")
        title.setObjectName("page_title")
        header.addWidget(title)
        header.addStretch()

        self.scan_btn = QPushButton("  Начать сканирование")
        self.scan_btn.clicked.connect(self._start_scan)
        header.addWidget(self.scan_btn)
        outer.addLayout(header)

        # Progress bar + label
        prog_widget = QWidget()
        prog_widget.setObjectName("card")
        prog_vl = QVBoxLayout(prog_widget)
        prog_vl.setContentsMargins(14, 10, 14, 10)
        prog_vl.setSpacing(6)

        self.progress_label = QLabel("Нажмите «Начать сканирование» чтобы найти мусор и большие файлы")
        self.progress_label.setStyleSheet("color: #404060; font-size: 9pt;")
        prog_vl.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.hide()
        prog_vl.addWidget(self.progress_bar)

        outer.addWidget(prog_widget)

        # Summary row
        self.summary_widget = QWidget()
        summary_layout = QHBoxLayout(self.summary_widget)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        self.summary_junk = self._make_summary_card("Найдено мусора", "—", "#e94560")
        self.summary_count = self._make_summary_card("Файлов", "—", "#3498db")
        self.summary_large = self._make_summary_card("Больших файлов", "—", "#f39c12")
        for c in [self.summary_junk, self.summary_count, self.summary_large]:
            summary_layout.addWidget(c)
        summary_layout.addStretch()
        self.summary_widget.hide()
        outer.addWidget(self.summary_widget)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #0f3460; border-radius: 8px; }"
            "QTabBar::tab { background: #16213e; color: #a0a0b0; padding: 8px 16px; border-radius: 4px 4px 0 0; margin-right: 2px; }"
            "QTabBar::tab:selected { background: #0f3460; color: #ffffff; font-weight: bold; }"
            "QTabBar::tab:hover { background: #1a3a70; }"
        )

        # Tab: Junk by category
        self.junk_tab = QWidget()
        junk_layout = QVBoxLayout(self.junk_tab)
        junk_layout.setContentsMargins(8, 8, 8, 8)

        self.junk_table = self._make_file_table()
        junk_layout.addWidget(self.junk_table)

        junk_btn_row = QHBoxLayout()
        self.select_all_junk = QCheckBox("Выбрать всё")
        self.select_all_junk.toggled.connect(self._toggle_select_all_junk)
        junk_btn_row.addWidget(self.select_all_junk)
        junk_btn_row.addStretch()
        self.del_trash_btn = QPushButton("В корзину")
        self.del_trash_btn.setObjectName("secondary_btn")
        self.del_trash_btn.setEnabled(False)
        self.del_trash_btn.clicked.connect(lambda: self._delete_selected(trash=True))
        self.del_perm_btn = QPushButton("Удалить навсегда")
        self.del_perm_btn.setObjectName("danger_btn")
        self.del_perm_btn.setEnabled(False)
        self.del_perm_btn.clicked.connect(lambda: self._delete_selected(trash=False))
        junk_btn_row.addWidget(self.del_trash_btn)
        junk_btn_row.addWidget(self.del_perm_btn)
        junk_layout.addLayout(junk_btn_row)
        self.tabs.addTab(self.junk_tab, "Мусор по категориям")

        # Tab: Large files
        self.large_tab = QWidget()
        large_layout = QVBoxLayout(self.large_tab)
        large_layout.setContentsMargins(8, 8, 8, 8)
        self.large_table = self._make_file_table()
        large_layout.addWidget(self.large_table)

        large_btn_row = QHBoxLayout()
        self.select_all_large = QCheckBox("Выбрать всё")
        self.select_all_large.toggled.connect(self._toggle_select_all_large)
        large_btn_row.addWidget(self.select_all_large)
        large_btn_row.addStretch()
        self.del_large_trash_btn = QPushButton("В корзину")
        self.del_large_trash_btn.setObjectName("secondary_btn")
        self.del_large_trash_btn.setEnabled(False)
        self.del_large_trash_btn.clicked.connect(lambda: self._delete_large(trash=True))
        self.del_large_perm_btn = QPushButton("Удалить навсегда")
        self.del_large_perm_btn.setObjectName("danger_btn")
        self.del_large_perm_btn.setEnabled(False)
        self.del_large_perm_btn.clicked.connect(lambda: self._delete_large(trash=False))
        large_btn_row.addWidget(self.del_large_trash_btn)
        large_btn_row.addWidget(self.del_large_perm_btn)
        large_layout.addLayout(large_btn_row)
        self.tabs.addTab(self.large_tab, "Большие файлы (>200 МБ)")

        # Tab: Recycle bin
        self.recycle_tab = QWidget()
        recycle_layout = QVBoxLayout(self.recycle_tab)
        recycle_layout.setContentsMargins(8, 8, 8, 8)
        self.recycle_label = QLabel("Загрузка...")
        self.recycle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.recycle_label.setFont(QFont("Segoe UI", 14))
        recycle_layout.addWidget(self.recycle_label)
        recycle_layout.addStretch()
        self.empty_bin_btn = QPushButton("Очистить корзину")
        self.empty_bin_btn.setObjectName("danger_btn")
        self.empty_bin_btn.clicked.connect(self._empty_recycle_bin)
        recycle_layout.addWidget(self.empty_bin_btn, 0, Qt.AlignmentFlag.AlignCenter)
        recycle_layout.addStretch()
        self.tabs.addTab(self.recycle_tab, "Корзина")

        outer.addWidget(self.tabs, 1)

    def _make_summary_card(self, title: str, value: str, color: str) -> QWidget:
        card = QWidget()
        card.setObjectName("card")
        card.setMinimumWidth(160)
        layout = QVBoxLayout(card)
        lbl = QLabel(title)
        lbl.setObjectName("card_title")
        val = QLabel(value)
        val.setObjectName("card_value")
        val.setStyleSheet(f"color: {color}; font-size: 18pt; font-weight: bold;")
        val.setProperty("_color", color)
        layout.addWidget(lbl)
        layout.addWidget(val)
        card.setProperty("val_label", val)
        return card

    def _make_file_table(self) -> QTableWidget:
        table = QTableWidget(0, 4)
        table.setHorizontalHeaderLabels(["Файл", "Категория", "Размер", "Путь"])
        hdr = table.horizontalHeader()
        hdr.setSectionResizeMode(0, hdr.ResizeMode.Fixed)
        hdr.setSectionResizeMode(1, hdr.ResizeMode.Fixed)
        hdr.setSectionResizeMode(2, hdr.ResizeMode.Fixed)
        hdr.setSectionResizeMode(3, hdr.ResizeMode.Stretch)
        table.setColumnWidth(0, 200)
        table.setColumnWidth(1, 180)
        table.setColumnWidth(2, 100)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)
        return table

    def on_shown(self):
        self._update_recycle_bin()

    def _update_recycle_bin(self):
        count, size = get_recycle_bin_size()
        self.recycle_label.setText(
            f"В корзине: {count} объектов\nРазмер: {format_size(size)}"
        )

    def _start_scan(self):
        if self._scanner and self._scanner.isRunning():
            self._scanner.stop()
            return

        self.scan_btn.setText("Остановить")
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.junk_table.setRowCount(0)
        self.large_table.setRowCount(0)
        self._category_files.clear()
        self._large_files.clear()
        self.del_trash_btn.setEnabled(False)
        self.del_perm_btn.setEnabled(False)
        self.del_large_trash_btn.setEnabled(False)
        self.del_large_perm_btn.setEnabled(False)
        self.summary_widget.hide()

        self._scanner = FileScanner()
        self._scanner.progress.connect(self._on_progress)
        self._scanner.category_done.connect(self._on_category)
        self._scanner.large_files_done.connect(self._on_large_files)
        self._scanner.scan_complete.connect(self._on_scan_complete)
        self._scanner.start()

    def _on_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.progress_label.setText(msg)
        self.status_message.emit(msg)

    def _on_category(self, cat_key: str, files: list):
        self._category_files[cat_key] = files
        cat = JUNK_CATEGORIES.get(cat_key, {})
        label = cat.get("label", cat_key)
        color = cat.get("color", "#e0e0e0")

        self.junk_table.setSortingEnabled(False)
        for f in files:
            row = self.junk_table.rowCount()
            self.junk_table.insertRow(row)

            name_item = QTableWidgetItem(f["name"])
            cat_item = QTableWidgetItem(label)
            size_item = QTableWidgetItem(format_size(f["size"]))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            path_item = QTableWidgetItem(f["path"])

            q_color = QColor(color)
            for item in [name_item, cat_item, size_item, path_item]:
                item.setForeground(q_color)
            name_item.setData(Qt.ItemDataRole.UserRole, f["path"])

            self.junk_table.setItem(row, 0, name_item)
            self.junk_table.setItem(row, 1, cat_item)
            self.junk_table.setItem(row, 2, size_item)
            self.junk_table.setItem(row, 3, path_item)
        self.junk_table.setSortingEnabled(True)

        if self.junk_table.rowCount() > 0:
            self.del_trash_btn.setEnabled(True)
            self.del_perm_btn.setEnabled(True)

    def _on_large_files(self, files: list):
        self._large_files = files
        self.large_table.setSortingEnabled(False)
        for f in files:
            row = self.large_table.rowCount()
            self.large_table.insertRow(row)

            name_item = QTableWidgetItem(f["name"])
            cat_item = QTableWidgetItem("Большой файл")
            cat_item.setForeground(QColor("#f39c12"))
            size_item = QTableWidgetItem(format_size(f["size"]))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            size_item.setForeground(QColor("#f39c12"))
            path_item = QTableWidgetItem(f["path"])
            name_item.setData(Qt.ItemDataRole.UserRole, f["path"])

            self.large_table.setItem(row, 0, name_item)
            self.large_table.setItem(row, 1, cat_item)
            self.large_table.setItem(row, 2, size_item)
            self.large_table.setItem(row, 3, path_item)
        self.large_table.setSortingEnabled(True)

        if self.large_table.rowCount() > 0:
            self.del_large_trash_btn.setEnabled(True)
            self.del_large_perm_btn.setEnabled(True)

    def _on_scan_complete(self, summary: dict):
        self.scan_btn.setText("Начать сканирование")
        self.progress_bar.hide()

        junk_size = summary.get("junk_size", 0)
        junk_count = summary.get("junk_count", 0)

        # Update summary cards
        self.summary_widget.show()
        junk_val = self.summary_junk.property("val_label")
        if junk_val:
            junk_val.setText(format_size(junk_size))
        count_val = self.summary_count.property("val_label")
        if count_val:
            count_val.setText(str(junk_count))
        large_val = self.summary_large.property("val_label")
        if large_val:
            large_val.setText(str(len(self._large_files)))

        self.progress_label.setText(
            f"Готово! Найдено мусора: {format_size(junk_size)} ({junk_count} файлов)"
        )
        self.status_message.emit(f"Сканирование завершено. Мусор: {format_size(junk_size)}")
        self._update_recycle_bin()

    def _toggle_select_all_junk(self, checked: bool):
        for row in range(self.junk_table.rowCount()):
            self.junk_table.setRangeSelected(
                QTableWidgetSelectionRange(row, 0, row, 3), checked
            )

    def _toggle_select_all_large(self, checked: bool):
        for row in range(self.large_table.rowCount()):
            self.large_table.setRangeSelected(
                QTableWidgetSelectionRange(row, 0, row, 3), checked
            )

    def _collect_selected_paths(self, table: QTableWidget) -> list[str]:
        rows = set(item.row() for item in table.selectedItems())
        paths = []
        for row in rows:
            item = table.item(row, 0)
            if item:
                path = item.data(Qt.ItemDataRole.UserRole)
                if path:
                    paths.append(path)
        return paths

    def _delete_selected(self, trash: bool):
        paths = self._collect_selected_paths(self.junk_table)
        if not paths:
            QMessageBox.information(self, "Нет выбора", "Выберите файлы для удаления")
            return
        self._confirm_and_delete(paths, self.junk_table, trash)

    def _delete_large(self, trash: bool):
        paths = self._collect_selected_paths(self.large_table)
        if not paths:
            QMessageBox.information(self, "Нет выбора", "Выберите файлы для удаления")
            return
        self._confirm_and_delete(paths, self.large_table, trash)

    def _confirm_and_delete(self, paths: list, table: QTableWidget, trash: bool):
        method = "корзину" if trash else "НАВСЕГДА"
        reply = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Удалить {len(paths)} файл(ов) в {method}?\n\nЭто действие нельзя отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if trash:
            ok, failed = delete_to_trash(paths)
        else:
            ok, failed = delete_permanent(paths)

        # Remove deleted rows from table
        rows_to_remove = []
        for row in range(table.rowCount()):
            item = table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) in paths:
                rows_to_remove.append(row)
        for row in reversed(rows_to_remove):
            table.removeRow(row)

        msg = f"Удалено: {ok} файлов"
        if failed:
            msg += f"\nОшибки ({len(failed)}):\n" + "\n".join(failed[:5])
            QMessageBox.warning(self, "Частичное удаление", msg)
        else:
            self.status_message.emit(msg)

    def _empty_recycle_bin(self):
        reply = QMessageBox.question(
            self, "Очистить корзину",
            "Полностью очистить корзину?\nВосстановить файлы будет невозможно.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if empty_recycle_bin():
                self.status_message.emit("Корзина очищена")
                self._update_recycle_bin()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось очистить корзину")
