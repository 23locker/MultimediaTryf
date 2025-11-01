from PySide6.QtCore import QThread, Signal
import yt_dlp


class DownloadThread(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(float)

    def __init__(self, url, download_path, video_format):
        super().__init__()
        self.video_format = video_format
        self.url = url
        self.download_path = download_path
        self._is_running = True

    def progress_hook(self, d):
        """Хук для отслеживания прогресса загрузки"""
        if not self._is_running:
            return

        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            percent = (downloaded / total * 100) if total else 0
            self.progress_signal.emit(percent)
        elif d["status"] == "finished":
            self.progress_signal.emit(100)
            self.log_signal.emit("Загрузка завершена")

    def run(self):
        ydl_opts = {
            "format": self.video_format,
            "outtmpl": str(self.download_path / "%(title).50s.%(ext)s"),
            "progress_hooks": [self.progress_hook],
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 30,
            "retries": 3,
        }

        try:
            self.log_signal.emit(f"Скачиваю: {self.url}")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if self._is_running:
                    ydl.download([self.url])
                    self.log_signal.emit("Скачивание успешно завершено!")
        except Exception as e:
            if self._is_running:
                self.log_signal.emit(f"Ошибка: {str(e)[:100]}")

    def stop(self):
        """Остановка потока"""
        self._is_running = False
