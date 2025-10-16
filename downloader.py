from PySide6.QtCore import QThread, Signal
import yt_dlp


class DownloadThread(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(float)

    def __init__(self, url, download_path):
        super().__init__() 
        self.url = url
        self.download_path = download_path  

    def run(self):
        ydl_opts = {
            'outtmpl': str(self.download_path / '%(title).50s.%(ext)s')
        }

        def hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                percent = (downloaded / total * 100) if total else 0
                self.msleep(50)
                self.progress_signal.emit(percent)
            elif d['status'] == 'finished':
                self.progress_signal.emit(100)
                self.log_signal.emit('✅ Загрузка завершена')


        try:
            self.log_signal.emit(f'Скачиваю: {self.url}')
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            self.log_signal.emit('Скачивание успешно завершено!')
        except Exception as e:
            self.log_signal.emit(f'Произошла ошибка: {e}')
