import sys
from pathlib import Path
from PySide6 import QtWidgets, QtCore
from downloader import DownloadThread


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # open MultimediaTryf on center user monitor
        qr = self.frameGeometry()
        cp = QtWidgets.QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        # window size
        self.setMinimumSize(650, 400)
        self.setWindowTitle("MultimediaTryf")

        # === HIGH BLOCK-CONTAINER
        self.container = QtWidgets.QWidget()
        self.container.setStyleSheet("border-radius: 4px;")

        # text-logo
        self.text = QtWidgets.QLabel('MultimediaTryf')
        self.text.setStyleSheet("font-size: 24px; font-weight: bold; color: #3498db;")
        self.text.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)

        # user url for download
        self.user_url = QtWidgets.QLineEdit()
        self.user_url.setPlaceholderText('Вставьте вашу ссылку...')
        self.user_url.setFixedHeight(35)
        self.user_url.setStyleSheet("font-size: 14px; padding: 5px;")

        # bar for progress bar
        self.bar = QtWidgets.QProgressBar()

        # button download
        self.down_btn = QtWidgets.QPushButton('Скачать')
        self.down_btn.setFixedHeight(35)
        self.down_btn.setFixedWidth(100)
        self.down_btn.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                background-color: #3498db;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

        # layout for user_url and down_btn
        input_layout = QtWidgets.QHBoxLayout()
        input_layout.addWidget(self.user_url)
        input_layout.addWidget(self.down_btn)

        # layout for block-container
        container_layout = QtWidgets.QVBoxLayout(self.container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(10)
        container_layout.addWidget(self.text)
        container_layout.addLayout(input_layout)

        # === LOWER BLOCK WITH LOGS ===

        # label logs
        self.logs = QtWidgets.QPlainTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setPlaceholderText('Здесь будет история работы MultimediaTryf...') 
        self.logs.setMinimumHeight(120)
        self.logs.setStyleSheet(
            "background-color: #1e1e1e; color: #00ff99; font-family: Consolas; font-size: 12px;"
        )

        # MAIN LAYOUT
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(15, 20, 15, 15)
        main_layout.setSpacing(15)
        main_layout.addWidget(self.container, alignment=QtCore.Qt.AlignTop)
        main_layout.addWidget(self.bar)
        main_layout.addWidget(self.logs)

        self.add_log("Приложение запущено.")

        # ENTER on user_url
        self.user_url.returnPressed.connect(self.down_btn.click)

        # CLICK BUTTON 'down_btn'
        self.down_btn.clicked.connect(self.download_file)


    def add_log(self, message):
        self.logs.appendPlainText(message)


    def download_file(self):
        url = self.user_url.text().strip()

        if not url or not 'https' in url:
            self.add_log('Введите ссылку для скачивания!')
            return

        # === check dir Downloads ===
        downloads_path = Path(__file__).parent / 'Downloads'
        downloads_path.mkdir(exist_ok=True)

        self.down_btn.setEnabled(False)
        self.down_btn.setStyleSheet('background-color: #36454F')

        self.thread = DownloadThread(url, downloads_path)
        self.thread.log_signal.connect(self.add_log)
        self.thread.progress_signal.connect(
            self.update_progress, QtCore.Qt.QueuedConnection
        )
        self.thread.start() 

        self.add_log("Начинаю загрузку...")
        self.thread.finished.connect(lambda: self.down_btn.setEnabled(True), self.down_btn.setStyleSheet('background-color: #3498db'))


    def update_progress(self, percent):
        self.bar.setValue(int(percent))





if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    widget = MyWidget()
    widget.show()

    sys.exit(app.exec())
