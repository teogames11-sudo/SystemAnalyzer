import os
import subprocess
from collections import defaultdict

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QPushButton, QSplitter, QProgressBar, QMessageBox,
    QFrame, QScrollArea, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor

from app.workers.app_scanner import AppInfo, FileEntry, AppFileScanner, get_installed_apps
from app.utils.file_description import CATEGORY_NAMES, CATEGORY_COLORS, CATEGORY_ORDER
from app.utils.file_utils import delete_permanent, delete_to_trash
from app.utils.junk_detector import format_size


# ──────────────────────────────────────────────
# App list item widget
# ──────────────────────────────────────────────

class AppListItem(QWidget):
    def __init__(self, app: AppInfo, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        top = QHBoxLayout()
        name_lbl = QLabel(app.name)
        name_lbl.setStyleSheet("color: #e0e0f0; font-weight: bold; font-size: 10pt;")
        name_lbl.setWordWrap(False)
        top.addWidget(name_lbl, 1)

        if app.size_str:
            sz = QLabel(app.size_str)
            sz.setStyleSheet("color: #404060; font-size: 8pt;")
            sz.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            top.addWidget(sz)
        layout.addLayout(top)

        sub_parts = []
        if app.publisher:
            sub_parts.append(app.publisher)
        if app.version:
            sub_parts.append(f"v{app.version}")
        if sub_parts:
            sub = QLabel("  ·  ".join(sub_parts))
            sub.setStyleSheet("color: #404060; font-size: 8pt;")
            layout.addWidget(sub)


# ──────────────────────────────────────────────
# Main widget
# ──────────────────────────────────────────────

class AppsWidget(QWidget):
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_apps: list[AppInfo] = []
        self._current_app: AppInfo | None = None
        self._scanner: AppFileScanner | None = None
        self._all_files: list[FileEntry] = []
        self._build_ui()

    # ── UI ────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header bar
        header_bar = QWidget()
        header_bar.setStyleSheet("background-color: #0d0d1a; border-bottom: 1px solid #1a1a38;")
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(28, 16, 28, 16)

        title = QLabel("📦  Приложения")
        title.setObjectName("page_title")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.refresh_btn = QPushButton("  Обновить список")
        self.refresh_btn.setObjectName("secondary_btn")
        self.refresh_btn.clicked.connect(self._load_apps)
        header_layout.addWidget(self.refresh_btn)
        root.addWidget(header_bar)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("QSplitter::handle { background-color: #1a1a38; }")

        # ── Left panel: app list ──────────────
        left = QWidget()
        left.setStyleSheet("background-color: #111128;")
        left.setMinimumWidth(260)
        left.setMaximumWidth(360)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Search
        search_wrap = QWidget()
        search_wrap.setStyleSheet("background-color: #111128; padding: 10px 12px;")
        sw_layout = QHBoxLayout(search_wrap)
        sw_layout.setContentsMargins(10, 8, 10, 8)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Найти приложение...")
        self.search_box.textChanged.connect(self._filter_apps)
        sw_layout.addWidget(self.search_box)
        left_layout.addWidget(search_wrap)

        self.app_count_lbl = QLabel("Загрузка...")
        self.app_count_lbl.setStyleSheet(
            "color: #303055; font-size: 8pt; padding: 0 12px 6px 12px;"
        )
        left_layout.addWidget(self.app_count_lbl)

        self.app_list = QListWidget()
        self.app_list.setStyleSheet("""
            QListWidget {
                background-color: #111128;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border-bottom: 1px solid #1a1a38;
                padding: 0;
            }
            QListWidget::item:selected {
                background-color: #1e1040;
                border-left: 3px solid #a060ff;
            }
            QListWidget::item:hover:!selected {
                background-color: #161630;
            }
        """)
        self.app_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.app_list.itemSelectionChanged.connect(self._on_app_selected)
        left_layout.addWidget(self.app_list, 1)
        splitter.addWidget(left)

        # ── Right panel: detail ───────────────
        right = QWidget()
        right.setStyleSheet("background-color: #0d0d1a;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # App info header (hidden until app selected)
        self.app_header = QWidget()
        self.app_header.setStyleSheet(
            "background-color: #13132a; border-bottom: 1px solid #1e1e42;"
        )
        ah_layout = QVBoxLayout(self.app_header)
        ah_layout.setContentsMargins(24, 16, 24, 16)
        ah_layout.setSpacing(4)

        self.app_name_lbl = QLabel("")
        self.app_name_lbl.setStyleSheet(
            "color: #ffffff; font-size: 14pt; font-weight: bold;"
        )
        ah_layout.addWidget(self.app_name_lbl)

        self.app_meta_lbl = QLabel("")
        self.app_meta_lbl.setStyleSheet("color: #404060; font-size: 9pt;")
        ah_layout.addWidget(self.app_meta_lbl)
        self.app_header.hide()
        right_layout.addWidget(self.app_header)

        # Progress bar for scanning
        self.scan_progress = QWidget()
        sp_layout = QVBoxLayout(self.scan_progress)
        sp_layout.setContentsMargins(24, 10, 24, 10)
        sp_layout.setSpacing(6)
        self.scan_lbl = QLabel("Сканирование файлов...")
        self.scan_lbl.setStyleSheet("color: #a060ff; font-size: 9pt;")
        sp_layout.addWidget(self.scan_lbl)
        self.scan_bar = QProgressBar()
        self.scan_bar.setRange(0, 0)  # indeterminate
        self.scan_bar.setFixedHeight(4)
        self.scan_bar.setStyleSheet(
            "QProgressBar { background:#1a1a38; border:none; border-radius:2px; }"
            "QProgressBar::chunk { background:#a060ff; border-radius:2px; }"
        )
        sp_layout.addWidget(self.scan_bar)
        self.scan_progress.hide()
        right_layout.addWidget(self.scan_progress)

        # Summary row (shown after scan)
        self.summary_bar = QWidget()
        self.summary_bar.setStyleSheet(
            "background-color: #13132a; border-bottom: 1px solid #1e1e42;"
        )
        sb_layout = QHBoxLayout(self.summary_bar)
        sb_layout.setContentsMargins(24, 10, 24, 10)
        self.summary_lbl = QLabel("")
        self.summary_lbl.setStyleSheet("color: #606080; font-size: 9pt;")
        sb_layout.addWidget(self.summary_lbl)
        sb_layout.addStretch()
        self.summary_bar.hide()
        right_layout.addWidget(self.summary_bar)

        # File tree
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["ТИП / ФАЙЛ", "ОПИСАНИЕ", "РАЗМЕР"])
        hdr = self.tree.header()
        hdr.setSectionResizeMode(0, hdr.ResizeMode.Interactive)
        hdr.setSectionResizeMode(1, hdr.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, hdr.ResizeMode.Fixed)
        self.tree.setColumnWidth(0, 260)
        self.tree.setColumnWidth(2, 90)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #0d0d1a;
                border: none;
                color: #c0c0d8;
                font-size: 9pt;
                outline: none;
            }
            QTreeWidget::item {
                padding: 4px 6px;
                border: none;
            }
            QTreeWidget::item:selected {
                background-color: #1e1e50;
                color: #ffffff;
            }
            QTreeWidget::item:hover:!selected {
                background-color: #141428;
            }
            QHeaderView::section {
                background-color: #0a0a16;
                color: #404060;
                padding: 6px 10px;
                border: none;
                border-bottom: 1px solid #1a1a38;
                border-right: 1px solid #1a1a38;
                font-size: 8pt;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(False)
        self.tree.itemSelectionChanged.connect(self._on_file_selected)
        right_layout.addWidget(self.tree, 1)

        # File detail panel
        self.file_detail = QWidget()
        self.file_detail.setStyleSheet(
            "background-color: #13132a; border-top: 1px solid #1e1e42;"
        )
        fd_layout = QVBoxLayout(self.file_detail)
        fd_layout.setContentsMargins(24, 12, 24, 12)
        fd_layout.setSpacing(4)
        self.file_name_lbl = QLabel("")
        self.file_name_lbl.setStyleSheet(
            "color: #e0e0f0; font-weight: bold; font-size: 10pt;"
        )
        fd_layout.addWidget(self.file_name_lbl)
        self.file_path_lbl = QLabel("")
        self.file_path_lbl.setStyleSheet("color: #404060; font-size: 8pt;")
        self.file_path_lbl.setWordWrap(True)
        self.file_path_lbl.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        fd_layout.addWidget(self.file_path_lbl)
        self.file_desc_lbl = QLabel("")
        self.file_desc_lbl.setStyleSheet("color: #9090b0; font-size: 9pt;")
        self.file_desc_lbl.setWordWrap(True)
        fd_layout.addWidget(self.file_desc_lbl)
        self.file_detail.setFixedHeight(90)
        right_layout.addWidget(self.file_detail)

        # Bottom action bar
        action_bar = QWidget()
        action_bar.setStyleSheet(
            "background-color: #0a0a16; border-top: 1px solid #1a1a38;"
        )
        ab_layout = QHBoxLayout(action_bar)
        ab_layout.setContentsMargins(24, 12, 24, 12)
        ab_layout.setSpacing(10)

        self.uninstall_std_btn = QPushButton("  Стандартное удаление")
        self.uninstall_std_btn.setObjectName("secondary_btn")
        self.uninstall_std_btn.setEnabled(False)
        self.uninstall_std_btn.setToolTip("Запустить встроенный деинсталлятор программы")
        self.uninstall_std_btn.clicked.connect(self._run_standard_uninstall)
        ab_layout.addWidget(self.uninstall_std_btn)

        self.uninstall_full_btn = QPushButton("🗑  Удалить все найденные файлы")
        self.uninstall_full_btn.setObjectName("danger_btn")
        self.uninstall_full_btn.setEnabled(False)
        self.uninstall_full_btn.setToolTip(
            "Удалить все файлы найденные сканером. "
            "Рекомендуется сначала запустить стандартное удаление."
        )
        self.uninstall_full_btn.clicked.connect(self._delete_all_files)
        ab_layout.addWidget(self.uninstall_full_btn)
        ab_layout.addStretch()

        self.action_info_lbl = QLabel("Выберите приложение слева")
        self.action_info_lbl.setStyleSheet("color: #303055; font-size: 8pt;")
        ab_layout.addWidget(self.action_info_lbl)
        right_layout.addWidget(action_bar)

        # Placeholder (shown when no app selected)
        self.placeholder = QWidget()
        ph_layout = QVBoxLayout(self.placeholder)
        ph_lbl = QLabel("← Выберите приложение для анализа файлов")
        ph_lbl.setStyleSheet("color: #252550; font-size: 14pt;")
        ph_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_layout.addWidget(ph_lbl, 0, Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.placeholder)

        splitter.addWidget(right)
        splitter.setSizes([300, 900])

        root.addWidget(splitter, 1)

        # Placeholder is shown by default (tree hidden)
        self.tree.hide()
        self.file_detail.hide()

    # ── App list loading ───────────────────────

    def on_shown(self):
        if not self._all_apps:
            self._load_apps()

    def _load_apps(self):
        self.app_count_lbl.setText("Загрузка списка...")
        self.app_list.clear()
        self._all_apps = []
        self.refresh_btn.setEnabled(False)

        from PyQt6.QtCore import QThread, pyqtSignal as _sig

        class Loader(QThread):
            done = _sig(list)
            def run(self_):
                self_.done.emit(get_installed_apps())

        self._app_loader = Loader(self)
        self._app_loader.done.connect(self._on_apps_loaded)
        self._app_loader.start()

    def _on_apps_loaded(self, apps: list[AppInfo]):
        self._all_apps = apps
        self.refresh_btn.setEnabled(True)
        self._filter_apps()

    def _filter_apps(self):
        query = self.search_box.text().lower().strip()
        self.app_list.clear()

        filtered = [a for a in self._all_apps
                    if query in a.name.lower()
                    or query in a.publisher.lower()]

        for app in filtered:
            item = QListWidgetItem()
            widget = AppListItem(app)
            item.setSizeHint(QSize(240, 58 if app.publisher else 44))
            item.setData(Qt.ItemDataRole.UserRole, app)
            self.app_list.addItem(item)
            self.app_list.setItemWidget(item, widget)

        total = len(self._all_apps)
        shown = len(filtered)
        if query:
            self.app_count_lbl.setText(f"Найдено: {shown} из {total}")
        else:
            self.app_count_lbl.setText(f"Всего приложений: {total}")

    # ── App selection & scanning ───────────────

    def _on_app_selected(self):
        items = self.app_list.selectedItems()
        if not items:
            return
        app: AppInfo = items[0].data(Qt.ItemDataRole.UserRole)
        if app is None:
            return
        self._current_app = app
        self._start_file_scan(app)

    def _start_file_scan(self, app: AppInfo):
        if self._scanner and self._scanner.isRunning():
            self._scanner.stop()

        # Reset UI
        self.tree.clear()
        self.tree.show()
        self.placeholder.hide()
        self.summary_bar.hide()
        self.file_detail.hide()
        self._all_files = []

        self.app_header.show()
        self.app_name_lbl.setText(app.name)
        meta = []
        if app.publisher:
            meta.append(f"📌 {app.publisher}")
        if app.version:
            meta.append(f"Версия: {app.version}")
        if app.install_date:
            d = app.install_date
            if len(d) == 8:
                meta.append(f"Установлено: {d[6:8]}.{d[4:6]}.{d[:4]}")
        self.app_meta_lbl.setText("   ·   ".join(meta))

        self.scan_progress.show()
        self.scan_lbl.setText("Поиск файлов...")
        self.uninstall_std_btn.setEnabled(bool(app.uninstall_string or app.quiet_uninstall))
        self.uninstall_full_btn.setEnabled(False)
        self.action_info_lbl.setText("Сканирование...")

        self._scanner = AppFileScanner(app, self)
        self._scanner.progress.connect(self._on_scan_progress)
        self._scanner.files_ready.connect(self._on_files_ready)
        self._scanner.start()

    def _on_scan_progress(self, msg: str):
        self.scan_lbl.setText(msg)

    def _on_files_ready(self, files: list[FileEntry]):
        self.scan_progress.hide()
        self._all_files = files
        self._populate_tree(files)

        total_size = sum(f.size for f in files)
        self.summary_lbl.setText(
            f"Найдено файлов: {len(files)}   ·   "
            f"Общий размер: {format_size(total_size)}"
        )
        self.summary_bar.show()
        self.uninstall_full_btn.setEnabled(bool(files))
        self.action_info_lbl.setText(
            f"{len(files)} файлов · {format_size(total_size)}"
        )
        self.status_message.emit(
            f"{self._current_app.name}: найдено {len(files)} файлов "
            f"({format_size(total_size)})"
        )

    # ── Tree population ────────────────────────

    def _populate_tree(self, files: list[FileEntry]):
        self.tree.clear()
        by_cat: dict[str, list[FileEntry]] = defaultdict(list)
        for f in files:
            by_cat[f.category].append(f)

        for cat_key in CATEGORY_ORDER:
            cat_files = by_cat.get(cat_key, [])
            if not cat_files:
                continue

            cat_name = CATEGORY_NAMES.get(cat_key, cat_key)
            cat_color = CATEGORY_COLORS.get(cat_key, "#808080")
            cat_size = sum(f.size for f in cat_files)

            # Category header
            cat_item = QTreeWidgetItem()
            cat_item.setText(0, f"  {cat_name}")
            cat_item.setText(1, f"{len(cat_files)} файлов")
            cat_item.setText(2, format_size(cat_size))
            cat_item.setForeground(0, QColor(cat_color))
            cat_item.setForeground(1, QColor("#404060"))
            cat_item.setForeground(2, QColor(cat_color))
            f0 = cat_item.font(0)
            f0.setBold(True)
            cat_item.setFont(0, f0)
            cat_item.setData(0, Qt.ItemDataRole.UserRole, None)
            self.tree.addTopLevelItem(cat_item)

            # File children
            for fe in sorted(cat_files, key=lambda x: x.name.lower()):
                child = QTreeWidgetItem(cat_item)
                child.setText(0, f"  {fe.emoji}  {fe.name}")
                child.setText(1, fe.description)
                child.setText(2, fe.size_str)
                child.setForeground(0, QColor("#c0c0d8"))
                child.setForeground(1, QColor("#505070"))
                child.setForeground(2, QColor("#606080"))
                child.setData(0, Qt.ItemDataRole.UserRole, fe)
                child.setToolTip(0, fe.path)

            cat_item.setExpanded(cat_key in ("executable", "library", "config"))

    # ── File selection ────────────────────────

    def _on_file_selected(self):
        items = self.tree.selectedItems()
        if not items:
            self.file_detail.hide()
            return
        item = items[0]
        fe: FileEntry | None = item.data(0, Qt.ItemDataRole.UserRole)
        if fe is None:  # category header
            self.file_detail.hide()
            return

        self.file_detail.show()
        self.file_name_lbl.setText(f"{fe.emoji}  {fe.name}  ·  {fe.size_str}")
        self.file_path_lbl.setText(fe.path)
        self.file_desc_lbl.setText(fe.description)

    # ── Actions ───────────────────────────────

    def _run_standard_uninstall(self):
        if not self._current_app:
            return
        cmd = self._current_app.quiet_uninstall or self._current_app.uninstall_string
        if not cmd:
            return
        reply = QMessageBox.question(
            self, "Стандартное удаление",
            f"Запустить деинсталлятор для «{self._current_app.name}»?\n\n{cmd}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                subprocess.Popen(cmd, shell=True)
                self.status_message.emit(f"Запущен деинсталлятор: {self._current_app.name}")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось запустить:\n{e}")

    def _delete_all_files(self):
        if not self._all_files:
            return
        paths = [f.path for f in self._all_files]
        total_size = sum(f.size for f in self._all_files)

        reply = QMessageBox.question(
            self, "Удалить все файлы",
            f"Удалить {len(paths)} файлов ({format_size(total_size)}) "
            f"приложения «{self._current_app.name}»?\n\n"
            f"Файлы будут отправлены в корзину.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        ok, failed = delete_to_trash(paths)
        msg = f"Отправлено в корзину: {ok} файлов"
        if failed:
            msg += f"\nОшибки ({len(failed)}):\n" + "\n".join(failed[:5])
            QMessageBox.warning(self, "Частичное удаление", msg)
        else:
            QMessageBox.information(self, "Готово", msg)
            self.status_message.emit(msg)
            # Clear tree
            self.tree.clear()
            self._all_files = []
            self.summary_lbl.setText("Файлы удалены")
