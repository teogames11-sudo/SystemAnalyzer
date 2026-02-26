from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel, QFrame,
    QMessageBox, QPushButton
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtCore import QUrl

from app.widgets.dashboard import DashboardWidget
from app.widgets.disk_widget import DiskWidget
from app.widgets.files_widget import FilesWidget
from app.widgets.process_widget import ProcessWidget
from app.widgets.hardware_widget import HardwareWidget
from app.widgets.apps_widget import AppsWidget
from app.workers.update_checker import UpdateChecker
from app.version import VERSION


NAV_ITEMS = [
    ("🏠", "Обзор"),
    ("💾", "Диски"),
    ("🗑", "Файлы / Мусор"),
    ("⚙", "Процессы"),
    ("📦", "Приложения"),
    ("🖥", "Железо"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Analyzer")
        self.setMinimumSize(1050, 680)
        self.resize(1280, 820)

        self._build_ui()
        self._connect_signals()

        # Start on dashboard
        self.nav_list.setCurrentRow(0)

        # Check for updates after 3 seconds (non-blocking)
        QTimer.singleShot(3000, self._start_update_check)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Sidebar ──────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(210)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Logo block
        logo_widget = QWidget()
        logo_widget.setObjectName("logo_block")
        logo_layout = QVBoxLayout(logo_widget)
        logo_layout.setContentsMargins(18, 22, 18, 18)
        logo_layout.setSpacing(2)

        logo_icon = QLabel("⚡")
        logo_icon.setStyleSheet("font-size: 28px; color: #e94560;")
        logo_name = QLabel("SysAnalyzer")
        logo_name.setStyleSheet(
            "font-size: 16pt; font-weight: bold; color: #ffffff; letter-spacing: 1px;"
        )
        logo_sub = QLabel("Системный анализатор")
        logo_sub.setStyleSheet("font-size: 8pt; color: #606080;")
        logo_layout.addWidget(logo_icon)
        logo_layout.addWidget(logo_name)
        logo_layout.addWidget(logo_sub)
        sidebar_layout.addWidget(logo_widget)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("color: #1e2a50; margin: 0 12px;")
        sidebar_layout.addWidget(div)
        sidebar_layout.addSpacing(8)

        # Nav section label
        nav_label = QLabel("НАВИГАЦИЯ")
        nav_label.setStyleSheet(
            "color: #404060; font-size: 8pt; font-weight: bold; "
            "letter-spacing: 2px; padding-left: 20px;"
        )
        sidebar_layout.addWidget(nav_label)
        sidebar_layout.addSpacing(4)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("nav_list")
        self.nav_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        for icon, label in NAV_ITEMS:
            item = QListWidgetItem(f"  {icon}  {label}")
            item.setSizeHint(QSize(200, 46))
            self.nav_list.addItem(item)
        sidebar_layout.addWidget(self.nav_list)
        sidebar_layout.addStretch()

        # Version at bottom
        ver_div = QFrame()
        ver_div.setFrameShape(QFrame.Shape.HLine)
        ver_div.setStyleSheet("color: #1e2a50; margin: 0 12px;")
        sidebar_layout.addWidget(ver_div)

        ver_widget = QWidget()
        ver_layout = QHBoxLayout(ver_widget)
        ver_layout.setContentsMargins(18, 10, 18, 14)
        ver_dot = QLabel("●")
        ver_dot.setStyleSheet("color: #2ecc71; font-size: 8pt;")
        self.ver_txt = QLabel(f"v{VERSION}  ·  Windows")
        self.ver_txt.setStyleSheet("color: #404060; font-size: 8pt;")
        ver_layout.addWidget(ver_dot)
        ver_layout.addWidget(self.ver_txt)
        ver_layout.addStretch()
        sidebar_layout.addWidget(ver_widget)

        root_layout.addWidget(sidebar)

        # ── Content area ─────────────────────────
        right_side = QWidget()
        right_side.setObjectName("right_side")
        right_layout = QVBoxLayout(right_side)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setObjectName("content")

        self.dashboard_page = DashboardWidget()
        self.disk_page = DiskWidget()
        self.files_page = FilesWidget()
        self.process_page = ProcessWidget()
        self.apps_page = AppsWidget()
        self.hardware_page = HardwareWidget()

        for page in [self.dashboard_page, self.disk_page, self.files_page,
                     self.process_page, self.apps_page, self.hardware_page]:
            self.stack.addWidget(page)

        right_layout.addWidget(self.stack, 1)

        # ── Thin status strip (no "Готово") ──────
        self.status_strip = QWidget()
        self.status_strip.setObjectName("status_strip")
        self.status_strip.setFixedHeight(26)
        strip_layout = QHBoxLayout(self.status_strip)
        strip_layout.setContentsMargins(14, 0, 14, 0)
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color: #505070; font-size: 8pt;")
        strip_layout.addWidget(self.status_lbl)
        strip_layout.addStretch()
        right_layout.addWidget(self.status_strip)

        root_layout.addWidget(right_side, 1)

        # Status auto-clear timer
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(lambda: self.status_lbl.setText(""))

    def _connect_signals(self):
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        for page in [self.dashboard_page, self.disk_page, self.files_page,
                     self.process_page, self.apps_page, self.hardware_page]:
            if hasattr(page, "status_message"):
                page.status_message.connect(self._show_status)

    def _show_status(self, msg: str):
        self.status_lbl.setText(msg)
        self._status_timer.start(5000)  # clear after 5 sec

    def _start_update_check(self):
        self._update_checker = UpdateChecker(self)
        self._update_checker.update_available.connect(self._on_update_available)
        self._update_checker.start()

    def _on_update_available(self, new_version: str, release_url: str):
        self.ver_txt.setText(f"v{VERSION} → v{new_version} !")
        self.ver_txt.setStyleSheet("color: #e94560; font-size: 8pt; font-weight: bold;")
        self._update_url = release_url
        self._show_update_dialog(new_version, release_url)

    def _show_update_dialog(self, new_version: str, release_url: str):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Доступно обновление")
        dlg.setText(f"Доступна новая версия <b>v{new_version}</b>.<br>Текущая версия: v{VERSION}")
        dlg.setInformativeText("Открыть страницу загрузки?")
        dlg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        dlg.setDefaultButton(QMessageBox.StandardButton.Yes)
        dlg.button(QMessageBox.StandardButton.Yes).setText("Открыть")
        dlg.button(QMessageBox.StandardButton.No).setText("Позже")
        if dlg.exec() == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl(release_url))

    def _on_nav_changed(self, index: int):
        self.stack.setCurrentIndex(index)
        page = self.stack.currentWidget()
        if hasattr(page, "on_shown"):
            page.on_shown()
