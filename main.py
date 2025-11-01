import sys
import json
from pathlib import Path
from datetime import datetime
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import QTimer, Qt
from Threads.downloader import DownloadThread
from Threads.formatsthread import FormatsThread


class HistoryCard(QtWidgets.QFrame):
    # карточка загруженного видео
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
                padding: 12px;
            }
            QFrame:hover {
                background-color: #222222;
                border: 1px solid #3498db;
            }
        """)
        self.setMinimumHeight(90)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # превью-заглушка
        thumbnail = QtWidgets.QLabel()
        thumbnail.setFixedSize(120, 68)
        thumbnail.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #2c3e50, stop:1 #34495e);
            border-radius: 6px;
            color: #ecf0f1;
            font-size: 24px;
        """)
        thumbnail.setAlignment(Qt.AlignCenter)
        thumbnail.setText("▶")
        thumbnail.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )

        # инфо о видео
        info_widget = QtWidgets.QWidget()
        info_layout = QtWidgets.QVBoxLayout(info_widget)
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(0, 0, 0, 0)

        title = QtWidgets.QLabel(self.data.get("title", "Без названия"))
        title.setStyleSheet("color: #ecf0f1; font-size: 13px; font-weight: bold;")
        title.setWordWrap(True)
        title.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )

        format_label = QtWidgets.QLabel(
            f"Формат: {self.data.get('format', 'не указан')}"
        )
        format_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")

        date_label = QtWidgets.QLabel(f"Дата: {self.data.get('date', 'не указана')}")
        date_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")

        info_layout.addWidget(title)
        info_layout.addWidget(format_label)
        info_layout.addWidget(date_label)
        info_layout.addStretch()

        # кнопка открыть папку
        open_btn = QtWidgets.QPushButton("Открыть")
        open_btn.setFixedSize(70, 45)
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                border-radius: 8px;
                font-size: 13px;
                border: 1px solid #34495e;
                color: #ecf0f1;
            }
            QPushButton:hover {
                background-color: #34495e;
                border: 1px solid #3498db;
            }
            QPushButton:pressed {
                background-color: #1a252f;
            }
        """)
        open_btn.clicked.connect(self.open_folder)
        open_btn.setCursor(Qt.PointingHandCursor)

        layout.addWidget(thumbnail)
        layout.addWidget(info_widget, 1)
        layout.addWidget(open_btn)

    def open_folder(self):
        downloads_path = Path(__file__).parent / "Downloads"
        if downloads_path.exists():
            QtGui.QDesktopServices.openUrl(
                QtCore.QUrl.fromLocalFile(str(downloads_path))
            )


class CurrentDownloadWidget(QtWidgets.QFrame):
    # блок текущей загрузки
    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_progress = 0
        self.setup_ui()
        self.hide()

    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 12px;
            }
        """)
        self.setMinimumHeight(200)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # превью
        thumbnail_container = QtWidgets.QWidget()
        thumbnail_layout = QtWidgets.QVBoxLayout(thumbnail_container)
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)

        self.thumbnail = QtWidgets.QLabel()
        self.thumbnail.setMinimumSize(200, 120)
        self.thumbnail.setMaximumSize(400, 225)
        self.thumbnail.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.thumbnail.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #2c3e50, stop:1 #34495e);
            border-radius: 8px;
            color: #ecf0f1;
            font-size: 48px;
        """)
        self.thumbnail.setAlignment(Qt.AlignCenter)
        self.thumbnail.setText("▶")

        thumbnail_layout.addWidget(self.thumbnail, alignment=Qt.AlignCenter)

        # заголовок видео
        self.title_label = QtWidgets.QLabel("Подготовка к загрузке...")
        self.title_label.setStyleSheet(
            "color: #ecf0f1; font-size: 15px; font-weight: bold;"
        )
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignCenter)

        # прогресс
        self.progress = QtWidgets.QProgressBar()
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #0a0a0a;
                border-radius: 5px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #3498db);
                border-radius: 5px;
            }
        """)

        # процент
        self.percent_label = QtWidgets.QLabel("0%")
        self.percent_label.setStyleSheet(
            "color: #3498db; font-size: 28px; font-weight: bold;"
        )
        self.percent_label.setAlignment(Qt.AlignCenter)

        # статус
        self.status_label = QtWidgets.QLabel("Ожидание...")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignCenter)

        main_layout.addWidget(thumbnail_container, 1)
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.progress)
        main_layout.addWidget(self.percent_label)
        main_layout.addWidget(self.status_label)

    def set_video_info(self, title):
        self.title_label.setText(title)
        self.show()

    def update_progress(self, percent):
        # обновляем прогресс только если разница заметна
        if abs(percent - self.last_progress) >= 0.5:
            self.last_progress = percent
            self.progress.setValue(int(percent))
            self.percent_label.setText(f"{int(percent)}%")

    def set_status(self, status):
        self.status_label.setText(status)


class MyWidget(QtWidgets.QWidget):
    # основное окно
    def __init__(self):
        super().__init__()
        self.history_file = Path(__file__).parent / "history.json"
        self.download_thread = None
        self.formats_thread = None
        self.current_video_title = ""
        self.load_history()
        self.setup_ui()
        self.center_window()

    def center_window(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def setup_ui(self):
        self.setMinimumSize(700, 550)
        self.setWindowTitle("MultimediaTryf")
        self.setStyleSheet("background-color: #0a0a0a;")

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # шапка
        header = QtWidgets.QLabel("MultimediaTryf")
        header.setStyleSheet(
            "font-size: 26px; font-weight: bold; color: #ecf0f1; padding: 8px;"
        )
        header.setAlignment(Qt.AlignCenter)

        # блок ввода
        input_container = QtWidgets.QFrame()
        input_container.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 10px;
            }
        """)
        input_container.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )

        input_layout = QtWidgets.QVBoxLayout(input_container)
        input_layout.setSpacing(10)
        input_layout.setContentsMargins(15, 15, 15, 15)

        # ввод ссылки
        url_layout = QtWidgets.QHBoxLayout()
        self.user_url = QtWidgets.QLineEdit()
        self.user_url.setPlaceholderText("Вставь ссылку на видео...")
        self.user_url.setFixedHeight(42)
        self.user_url.setStyleSheet("""
            QLineEdit {
                background-color: #0a0a0a;
                color: #ecf0f1;
                font-size: 13px;
                padding: 0 12px;
                border: 2px solid #2c3e50;
                border-radius: 6px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        self.user_url.editingFinished.connect(self.fetch_formats)
        self.user_url.returnPressed.connect(self.download_file)
        url_layout.addWidget(self.user_url)

        # выбор формата
        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.setFixedHeight(42)
        self.format_combo.setStyleSheet("""
            QComboBox {
                background-color: #0a0a0a;
                color: #ecf0f1;
                font-size: 12px;
                padding: 0 12px;
                border: 2px solid #2c3e50;
                border-radius: 6px;
            }
            QComboBox:hover {
                border: 2px solid #3498db;
            }
        """)

        # кнопка скачать
        self.down_btn = QtWidgets.QPushButton("Скачать видео")
        self.down_btn.setFixedHeight(42)
        self.down_btn.setCursor(Qt.PointingHandCursor)
        self.down_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                background-color: #2c3e50;
                color: #ecf0f1;
                border-radius: 6px;
                border: 1px solid #34495e;
            }
            QPushButton:hover {
                background-color: #34495e;
                border: 1px solid #3498db;
            }
            QPushButton:pressed {
                background-color: #1a252f;
            }
        """)
        self.down_btn.clicked.connect(self.download_file)

        input_layout.addLayout(url_layout)
        input_layout.addWidget(self.format_combo)
        input_layout.addWidget(self.down_btn)

        # текущая загрузка
        self.current_download = CurrentDownloadWidget()

        # история
        history_header_layout = QtWidgets.QHBoxLayout()
        history_header = QtWidgets.QLabel("История загрузок")
        history_header.setStyleSheet(
            "color: #ecf0f1; font-size: 16px; font-weight: bold;"
        )

        history_count = QtWidgets.QLabel(f"({len(self.history)})")
        history_count.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        self.history_count_label = history_count

        history_header_layout.addWidget(history_header)
        history_header_layout.addWidget(history_count)
        history_header_layout.addStretch()

        self.history_scroll = QtWidgets.QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        self.history_scroll.setMinimumHeight(150)

        self.history_container = QtWidgets.QWidget()
        self.history_layout = QtWidgets.QVBoxLayout(self.history_container)
        self.history_layout.setSpacing(8)
        self.history_layout.setContentsMargins(0, 0, 0, 0)
        self.history_layout.addStretch()

        self.history_scroll.setWidget(self.history_container)

        if len(self.history) == 0:
            empty_label = QtWidgets.QLabel("История пока пуста")
            empty_label.setStyleSheet("color: #555; font-size: 13px;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.history_layout.insertWidget(0, empty_label)

        main_layout.addWidget(header)
        main_layout.addWidget(input_container)
        main_layout.addWidget(self.current_download)
        main_layout.addLayout(history_header_layout)
        main_layout.addWidget(self.history_scroll, 1)

        self.load_history_ui()

    def load_history(self):
        # читаем историю из файла
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except:
                self.history = []
        else:
            self.history = []

    def save_history(self):
        # сохраняем историю
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения истории: {e}")

    def load_history_ui(self):
        # очищаем старые карточки
        for i in reversed(range(self.history_layout.count() - 1)):
            widget = self.history_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # добавляем новые
        for item in reversed(self.history):
            card = HistoryCard(item)
            self.history_layout.insertWidget(0, card)

        if hasattr(self, "history_count_label"):
            self.history_count_label.setText(f"({len(self.history)})")

    def add_to_history(self, title, format_name, url):
        entry = {
            "title": title[:80] + ("..." if len(title) > 80 else ""),
            "format": format_name,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "url": url,
        }
        self.history.insert(0, entry)
        if len(self.history) > 20:
            self.history = self.history[:20]
        self.save_history()
        self.load_history_ui()

    # !! проверить это !!
    def fetch_formats(self):
        url = self.user_url.text().strip()
        if not url or "https" not in url:
            return

        # останавливаем предыдущий поток
        if self.formats_thread and self.formats_thread.isRunning():
            self.formats_thread.stop()
            self.formats_thread.wait(500)

        self.format_combo.clear()
        self.current_download.set_status("Ищу форматы...")
        self.current_download.show()

        self.formats_thread = FormatsThread(url)
        self.formats_thread.log_signal.connect(self.handle_format_log)
        self.formats_thread.formats_ready.connect(self.update_format_combo)
        self.formats_thread.start()

    def handle_format_log(self, message):
        self.current_download.set_status(message)

    def update_format_combo(self, formats):
        for name, fmt_id in formats:
            self.format_combo.addItem(name, fmt_id)

        if formats:
            self.current_download.set_status(f"Найдено {len(formats)} форматов")
            QTimer.singleShot(2000, self.current_download.hide)
        else:
            self.current_download.set_status("Форматы не найдены")

    def download_file(self):
        url = self.user_url.text().strip()
        if not url or "https" not in url:
            self.current_download.set_status("Некорректная ссылка")
            self.current_download.show()
            QTimer.singleShot(2000, self.current_download.hide)
            return

        if self.format_combo.count() == 0:
            self.current_download.set_status("Сначала выбери формат")
            self.current_download.show()
            QTimer.singleShot(2000, self.current_download.hide)
            return

        downloads_path = Path(__file__).parent / "Downloads"
        downloads_path.mkdir(exist_ok=True)

        self.down_btn.setEnabled(False)
        self.current_video_title = "Загрузка видео..."
        self.current_download.set_video_info(self.current_video_title)
        self.current_download.update_progress(0)
        self.current_download.set_status("Начинаю загрузку...")

        selected_format_id = self.format_combo.currentData()
        format_name = self.format_combo.currentText()

        self.download_thread = DownloadThread(url, downloads_path, selected_format_id)
        self.download_thread.log_signal.connect(
            lambda msg: self.handle_download_log(msg, format_name, url)
        )
        self.download_thread.progress_signal.connect(
            self.current_download.update_progress
        )
        self.download_thread.finished.connect(self.download_thread_finished)
        self.download_thread.start()

    def handle_download_log(self, message, format_name, url):
        self.current_download.set_status(message)

        if "Скачиваю:" in message:
            title = message.replace("Скачиваю:", "").strip()
            self.current_video_title = title
            self.current_download.set_video_info(title[:80])
        elif "успешно завершено" in message:
            self.add_to_history(self.current_video_title, format_name, url)

    def download_thread_finished(self):
        self.down_btn.setEnabled(True)
        QTimer.singleShot(3000, self.current_download.hide)

    def closeEvent(self, event):
        # корректно завершаем потоки
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.stop()
            self.download_thread.wait(2000)
            if self.download_thread.isRunning():
                self.download_thread.terminate()

        # останавливаем поток форматов
        if self.formats_thread and self.formats_thread.isRunning():
            self.formats_thread.stop()
            self.formats_thread.wait(2000)
            if self.formats_thread.isRunning():
                self.formats_thread.terminate()

        event.accept()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    widget = MyWidget()
    widget.show()
    sys.exit(app.exec())
