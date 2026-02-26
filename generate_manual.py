"""
Генератор PDF-инструкции для SystemAnalyzer
Запуск: python generate_manual.py
"""

from fpdf import FPDF, XPos, YPos


ACCENT = (233, 69, 96)       # #e94560 — красный акцент
DARK   = (26, 26, 46)        # #1a1a2e — тёмный фон (для шапки/подвала)
WHITE  = (255, 255, 255)
LIGHT  = (245, 245, 250)     # фон секций
GRAY   = (120, 120, 140)
TEXT   = (30, 30, 50)

FONT_R = "C:/Windows/Fonts/arial.ttf"
FONT_B = "C:/Windows/Fonts/arialbd.ttf"
FONT_I = "C:/Windows/Fonts/ariali.ttf"


class ManualPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("Arial", style="",  fname=FONT_R)
        self.add_font("Arial", style="B", fname=FONT_B)
        self.add_font("Arial", style="I", fname=FONT_I)
        self.set_auto_page_break(auto=True, margin=25)

    # ------------------------------------------------------------------ header
    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*DARK)
        self.rect(0, 0, 210, 14, "F")
        self.set_font("Arial", "B", 8)
        self.set_text_color(*ACCENT)
        self.set_xy(10, 4)
        self.cell(0, 6, "SystemAnalyzer — Руководство пользователя", align="L")
        self.set_text_color(*GRAY)
        self.set_xy(0, 4)
        self.cell(200, 6, f"Страница {self.page_no()}", align="R")
        self.ln(10)

    # ------------------------------------------------------------------ footer
    def footer(self):
        self.set_y(-14)
        self.set_fill_color(*DARK)
        self.rect(0, self.get_y(), 210, 20, "F")
        self.set_font("Arial", "", 7.5)
        self.set_text_color(*GRAY)
        self.set_x(10)
        self.cell(90, 8, "© 2024 AStudio Dev. Все права защищены.", align="L")
        self.set_text_color(*ACCENT)
        self.set_x(110)
        self.cell(90, 8, "www.astudiodev.ru", align="R",
                  link="https://www.astudiodev.ru/")

    # ---------------------------------------------------------------- helpers
    def section_title(self, text, num=None):
        self.ln(4)
        self.set_fill_color(*ACCENT)
        self.rect(10, self.get_y(), 3, 9, "F")
        self.set_font("Arial", "B", 13)
        self.set_text_color(*TEXT)
        label = f"{num}.  {text}" if num is not None else text
        self.set_x(16)
        self.cell(0, 9, label, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(2)

    def subsection(self, text):
        self.set_font("Arial", "B", 10.5)
        self.set_text_color(*ACCENT)
        self.set_x(10)
        self.cell(0, 7, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def body(self, text, indent=10):
        self.set_font("Arial", "", 10)
        self.set_text_color(*TEXT)
        self.set_x(indent)
        self.multi_cell(190 - indent, 6, text)

    def bullet(self, text, indent=14):
        self.set_font("Arial", "", 10)
        self.set_text_color(*TEXT)
        self.set_x(indent)
        self.cell(5, 6, "\u2022")
        self.set_x(indent + 5)
        self.multi_cell(185 - indent, 6, text)

    def note_box(self, text):
        self.ln(2)
        y = self.get_y()
        self.set_fill_color(*LIGHT)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.5)
        self.rect(10, y, 190, 1, "")          # top border drawn via rect below
        # Draw full box first with background
        self.set_font("Arial", "I", 9.5)
        self.set_text_color(80, 80, 100)
        # Measure text height
        lines = self.multi_cell(180, 5.5, text, dry_run=True, output="LINES")
        box_h = len(lines) * 5.5 + 6
        self.set_fill_color(*LIGHT)
        self.rect(10, y, 190, box_h, "F")
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.4)
        self.line(10, y, 10, y + box_h)       # left accent line
        self.set_x(16)
        self.set_y(y + 3)
        self.multi_cell(180, 5.5, text)
        self.ln(2)

    def divider(self):
        self.ln(3)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.2)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)


# ======================================================================= BUILD
def build():
    pdf = ManualPDF()

    # ================================================================ COVER
    pdf.add_page()
    # Dark background top block
    pdf.set_fill_color(*DARK)
    pdf.rect(0, 0, 210, 297, "F")

    # Red accent bar
    pdf.set_fill_color(*ACCENT)
    pdf.rect(0, 110, 210, 4, "F")

    # Logo-style title
    pdf.set_font("Arial", "B", 42)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(0, 70)
    pdf.cell(210, 20, "SystemAnalyzer", align="C")

    pdf.set_font("Arial", "", 16)
    pdf.set_text_color(*ACCENT)
    pdf.set_xy(0, 120)
    pdf.cell(210, 10, "Руководство пользователя", align="C")

    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(180, 180, 200)
    pdf.set_xy(0, 140)
    pdf.cell(210, 8, "Версия 1.0.0", align="C")

    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(*GRAY)
    pdf.set_xy(0, 160)
    pdf.cell(210, 7, "Анализ системы · Очистка · Мониторинг", align="C")

    # Website on cover
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(*ACCENT)
    pdf.set_xy(0, 250)
    pdf.cell(210, 8, "astudiodev.ru", align="C", link="https://www.astudiodev.ru/")

    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(100, 100, 120)
    pdf.set_xy(0, 260)
    pdf.cell(210, 6, "© 2024 AStudio Dev", align="C")

    # ================================================================ PAGE 2+
    pdf.add_page()
    pdf.set_margins(10, 20, 10)

    # --- Что это
    pdf.section_title("Что такое SystemAnalyzer")
    pdf.body(
        "SystemAnalyzer — программа для анализа и обслуживания компьютера под управлением Windows. "
        "Показывает состояние системы в реальном времени: загруженность дисков, мусорные файлы, "
        "запущенные процессы, параметры железа. Позволяет находить и удалять ненужные файлы "
        "прямо из интерфейса."
    )

    pdf.divider()

    # --- Системные требования
    pdf.section_title("Системные требования")
    pdf.bullet("Windows 10 / Windows 11 (64-бит)")
    pdf.bullet("Оперативная память: от 512 МБ свободной")
    pdf.bullet("Дисковое пространство: ~50 МБ")
    pdf.bullet("Права администратора (рекомендуется — для полного доступа к данным системы)")

    pdf.divider()

    # --- Запуск
    pdf.section_title("Запуск программы")
    pdf.body(
        "Запустите файл SystemAnalyzer.exe. Никакой установки не требуется — "
        "программа portable, все файлы уже внутри."
    )
    pdf.ln(3)
    pdf.note_box(
        "При первом запуске Windows Defender или антивирус могут показать предупреждение — "
        "это нормально для portable EXE. Нажмите «Подробнее» → «Выполнить в любом случае»."
    )

    pdf.divider()

    # --- Интерфейс
    pdf.section_title("Интерфейс")
    pdf.body(
        "Левая панель — меню навигации с 6 вкладками. "
        "Нажмите на нужный раздел, чтобы перейти к нему. "
        "Данные обновляются автоматически в режиме реального времени."
    )

    pdf.divider()

    # --- Вкладки
    pdf.section_title("Разделы программы")

    tabs = [
        ("0 — Обзор", [
            "Общая картина состояния системы с первого взгляда.",
            "Карточки с ключевыми показателями: загрузка CPU, RAM, диски.",
            "Индикаторы заполненности дисков.",
            "Данные обновляются автоматически.",
        ], None),
        ("1 — Диски", [
            "Детальная информация по каждому диску: объём, использованное и свободное место.",
            "Сканер папок — показывает, какие директории занимают больше всего места.",
            "Выберите диск или папку и нажмите «Сканировать».",
        ], None),
        ("2 — Файлы / Мусор", [
            "Сканер мусора — находит временные файлы, кэши браузеров, старые логи и дубликаты.",
            "Большие файлы — список самых объёмных файлов на выбранном диске.",
            "Корзина — просмотр и очистка содержимого корзины.",
            "Файлы можно удалить в корзину (обратимо) или безвозвратно.",
        ], "Перед удалением убедитесь, что файл действительно не нужен. "
            "Безвозвратное удаление отменить невозможно."),
        ("3 — Процессы", [
            "Список всех запущенных процессов с загрузкой CPU и RAM для каждого.",
            "Нажмите на процесс — появится описание: что это за программа, безопасна ли она.",
            "Кнопка завершения процесса (используйте осторожно).",
            "Список обновляется автоматически; выбранный процесс остаётся выделенным.",
        ], None),
        ("4 — Приложения", [
            "Полный список установленных программ из реестра Windows.",
            "Сканер файлов приложения — показывает все файлы выбранной программы.",
            "Информация о версии, издателе, дате установки.",
        ], None),
        ("5 — Железо", [
            "Процессор: модель, количество ядер, текущая загрузка.",
            "Оперативная память: общий объём, тип (DDR4/DDR5), занято / свободно.",
            "Видеокарта: модель.",
            "Материнская плата: производитель и модель.",
            "BIOS: версия и дата.",
        ], None),
    ]

    for title, bullets, note in tabs:
        pdf.subsection(title)
        for b in bullets:
            pdf.bullet(b, indent=16)
        if note:
            pdf.note_box(note)
        pdf.ln(2)

    pdf.divider()

    # --- FAQ
    pdf.section_title("Частые вопросы")

    faq = [
        ("Программа не показывает данные о железе?",
         "Запустите SystemAnalyzer от имени администратора: правая кнопка мыши на EXE → "
         "«Запуск от имени администратора»."),
        ("Антивирус блокирует файл?",
         "Добавьте SystemAnalyzer.exe в исключения антивируса. "
         "Программа не содержит вредоносного кода."),
        ("Можно ли удалить системные файлы?",
         "Программа не предлагает системные файлы для очистки. Не удаляйте файлы "
         "из папок Windows, System32, Program Files, если не уверены в последствиях."),
        ("Как часто обновляются данные?",
         "Мониторинг CPU, RAM и процессов — в реальном времени. "
         "Сканирование файлов и дисков запускается вручную по кнопке «Сканировать»."),
    ]

    for q, a in faq:
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(*DARK)
        pdf.set_x(10)
        pdf.multi_cell(190, 6.5, q)
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(70, 70, 90)
        pdf.set_x(14)
        pdf.multi_cell(186, 6, a)
        pdf.ln(3)

    pdf.divider()

    # --- Поддержка
    pdf.section_title("Техническая поддержка")
    pdf.body(
        "По всем вопросам обращайтесь к продавцу. При обращении укажите:"
    )
    pdf.bullet("версию Windows")
    pdf.bullet("что именно не работает или отображается некорректно")
    pdf.bullet("скриншот экрана с проблемой (если возможно)")

    pdf.ln(6)

    # Promo block
    pdf.set_fill_color(*DARK)
    y = pdf.get_y()
    pdf.rect(10, y, 190, 28, "F")
    pdf.set_fill_color(*ACCENT)
    pdf.rect(10, y, 4, 28, "F")
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(18, y + 5)
    pdf.cell(0, 7, "Разработано AStudio Dev")
    pdf.set_font("Arial", "", 9.5)
    pdf.set_text_color(180, 180, 200)
    pdf.set_xy(18, y + 13)
    pdf.cell(0, 6, "Программы и сервисы для Windows")
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(*ACCENT)
    pdf.set_xy(18, y + 20)
    pdf.cell(0, 6, "www.astudiodev.ru",
             link="https://www.astudiodev.ru/")

    # ---- save
    out = "SystemAnalyzer_Manual.pdf"
    pdf.output(out)
    print(f"PDF сохранён: {out}")


if __name__ == "__main__":
    build()
