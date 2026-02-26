DARK_THEME = """
/* ===== GLOBAL ===== */
QMainWindow, QWidget {
    background-color: #0d0d1a;
    color: #d0d0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}

/* ===== SIDEBAR ===== */
#sidebar {
    background-color: #111128;
    border-right: 1px solid #1a1a3a;
}

#logo_block {
    background-color: #111128;
}

#right_side {
    background-color: #0d0d1a;
}

/* ===== NAV LIST ===== */
#nav_list {
    background-color: transparent;
    border: none;
    padding: 4px 8px;
    outline: none;
}

#nav_list::item {
    padding: 10px 14px;
    border-radius: 8px;
    margin: 2px 0;
    color: #707090;
    font-size: 10pt;
    border: 1px solid transparent;
}

#nav_list::item:hover {
    background-color: #1a1a38;
    color: #c0c0d8;
    border: 1px solid #252550;
}

#nav_list::item:selected {
    background-color: #1e1040;
    color: #ffffff;
    font-weight: bold;
    border: 1px solid #4040a0;
}

/* ===== STATUS STRIP ===== */
#status_strip {
    background-color: #0a0a16;
    border-top: 1px solid #1a1a3a;
}

/* ===== CONTENT ===== */
#content {
    background-color: #0d0d1a;
}

/* ===== PAGE TITLE ===== */
#page_title {
    font-size: 18pt;
    font-weight: bold;
    color: #ffffff;
    padding-bottom: 2px;
    letter-spacing: 0.5px;
}

/* ===== SECTION SEPARATOR LABEL ===== */
#section_lbl {
    color: #252550;
    font-size: 8pt;
    font-weight: bold;
    letter-spacing: 2px;
    padding: 2px 0;
}

/* ===== CARDS ===== */
#card {
    background-color: #13132a;
    border: 1px solid #1e1e42;
    border-radius: 12px;
    padding: 16px;
}

#card:hover {
    border: 1px solid #303070;
}

#card_title {
    color: #606080;
    font-size: 8pt;
    font-weight: bold;
    letter-spacing: 1px;
}

#card_value {
    color: #ffffff;
    font-size: 22pt;
    font-weight: bold;
}

#card_sub {
    color: #505070;
    font-size: 8pt;
}

/* ===== TABLES ===== */
QTableWidget {
    background-color: #13132a;
    border: 1px solid #1e1e42;
    border-radius: 10px;
    gridline-color: #1a1a38;
    color: #c0c0d8;
    selection-background-color: #1e1e50;
    outline: none;
    font-size: 9pt;
}

QTableWidget::item {
    padding: 5px 10px;
    border: none;
}

QTableWidget::item:selected {
    background-color: #252560;
    color: #ffffff;
}

QTableWidget::item:hover {
    background-color: #1a1a40;
}

QHeaderView::section {
    background-color: #0d0d1a;
    color: #505075;
    padding: 7px 10px;
    border: none;
    border-bottom: 1px solid #1e1e42;
    border-right: 1px solid #1a1a38;
    font-weight: bold;
    font-size: 8pt;
    letter-spacing: 1px;
}

QHeaderView::section:last {
    border-right: none;
}

QHeaderView {
    background-color: #0d0d1a;
}

/* ===== PROGRESS BAR ===== */
QProgressBar {
    background-color: #1a1a38;
    border: none;
    border-radius: 5px;
    height: 8px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6030c0, stop:1 #e94560);
    border-radius: 5px;
}

/* ===== BUTTONS ===== */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6030c0, stop:1 #e94560);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: bold;
    font-size: 9pt;
    letter-spacing: 0.5px;
}

QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7040d0, stop:1 #ff5570);
}

QPushButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #5020a0, stop:1 #c03050);
}

QPushButton:disabled {
    background: #1e1e38;
    color: #404055;
}

QPushButton#secondary_btn {
    background: #1e1e42;
    color: #9090b0;
    border: 1px solid #2a2a55;
}

QPushButton#secondary_btn:hover {
    background: #252558;
    color: #c0c0d8;
    border: 1px solid #4040a0;
}

QPushButton#danger_btn {
    background: transparent;
    color: #e94560;
    border: 1px solid #e94560;
    border-radius: 8px;
}

QPushButton#danger_btn:hover {
    background: #e94560;
    color: #ffffff;
}

/* ===== SCROLLBAR ===== */
QScrollBar:vertical {
    background-color: #111128;
    width: 6px;
    border-radius: 3px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #252550;
    border-radius: 3px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4040a0;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

QScrollBar:horizontal {
    background-color: #111128;
    height: 6px;
    border-radius: 3px;
}

QScrollBar::handle:horizontal {
    background-color: #252550;
    border-radius: 3px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover { background-color: #4040a0; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ===== LABELS ===== */
QLabel { color: #c0c0d8; }
#accent_label  { color: #e94560; font-weight: bold; }
#muted_label   { color: #505070; }
#success_label { color: #2ecc71; }
#warning_label { color: #f39c12; }
#danger_label  { color: #e74c3c; }

/* ===== CHECKBOX ===== */
QCheckBox {
    color: #9090b0;
    spacing: 8px;
    font-size: 9pt;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #2a2a55;
    border-radius: 4px;
    background-color: #13132a;
}

QCheckBox::indicator:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #6030c0, stop:1 #e94560);
    border-color: #6030c0;
}

QCheckBox::indicator:hover { border-color: #6030c0; }

/* ===== TOOLTIP ===== */
QToolTip {
    background-color: #1e1e42;
    color: #e0e0f0;
    border: 1px solid #4040a0;
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 9pt;
}

/* ===== SPLITTER ===== */
QSplitter::handle {
    background-color: #1a1a38;
    height: 2px;
}

/* ===== COMBOBOX ===== */
QComboBox {
    background-color: #13132a;
    border: 1px solid #2a2a55;
    border-radius: 8px;
    padding: 6px 12px;
    color: #c0c0d8;
    min-width: 100px;
    font-size: 9pt;
}

QComboBox:hover { border-color: #4040a0; }

QComboBox::drop-down {
    border: none;
    width: 24px;
    subcontrol-origin: padding;
    subcontrol-position: top right;
}

QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #606080;
    width: 0;
    height: 0;
}

QComboBox QAbstractItemView {
    background-color: #1a1a38;
    border: 1px solid #2a2a55;
    color: #c0c0d8;
    selection-background-color: #252565;
    border-radius: 6px;
    outline: none;
}

/* ===== LINE EDIT ===== */
QLineEdit {
    background-color: #13132a;
    border: 1px solid #2a2a55;
    border-radius: 8px;
    padding: 6px 12px;
    color: #c0c0d8;
    font-size: 9pt;
}

QLineEdit:focus { border-color: #6030c0; }

/* ===== GROUP BOX ===== */
QGroupBox {
    border: 1px solid #1e1e42;
    border-radius: 12px;
    margin-top: 16px;
    padding: 14px 14px 12px 14px;
    background-color: #13132a;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    color: #6060a0;
    font-weight: bold;
    font-size: 8pt;
    letter-spacing: 1px;
    left: 12px;
    background-color: #0d0d1a;
    border-radius: 4px;
}

/* ===== TAB WIDGET ===== */
QTabWidget::pane {
    border: 1px solid #1e1e42;
    border-radius: 10px;
    background-color: #13132a;
}

QTabBar::tab {
    background: #111128;
    color: #505075;
    padding: 8px 18px;
    border-radius: 6px 6px 0 0;
    margin-right: 2px;
    font-size: 9pt;
    border: 1px solid transparent;
    border-bottom: none;
}

QTabBar::tab:selected {
    background: #13132a;
    color: #ffffff;
    font-weight: bold;
    border: 1px solid #1e1e42;
    border-bottom: 1px solid #13132a;
}

QTabBar::tab:hover:!selected {
    background: #1a1a38;
    color: #c0c0d8;
}

/* ===== TEXT EDIT ===== */
QTextEdit {
    background-color: #13132a;
    border: 1px solid #1e1e42;
    border-radius: 8px;
    color: #c0c0d8;
    padding: 8px;
    font-size: 9pt;
}
"""


def get_progress_color(percent: float) -> str:
    if percent >= 90:
        return "#e74c3c"
    elif percent >= 75:
        return "#f39c12"
    return "#6030c0"
