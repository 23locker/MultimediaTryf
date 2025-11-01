from PySide6.QtCore import QThread, Signal
import yt_dlp


class FormatsThread(QThread):
    formats_ready = Signal(list)
    log_signal = Signal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self._is_running = True

    def run(self):
        if not self.url or "https" not in self.url:
            return

        try:
            if not self._is_running:
                return

            self.log_signal.emit("Получаю доступные форматы...")

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "socket_timeout": 30,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if not self._is_running:
                    return

                info = ydl.extract_info(self.url, download=False)

                if not self._is_running:
                    return

                formats = info.get("formats", [])
                format_list = []

                # собираем уникальные форматы
                seen = set()

                for f in formats:
                    if not self._is_running:
                        return

                    vcodec = f.get("vcodec", "none")
                    acodec = f.get("acodec", "none")
                    height = f.get("height")
                    ext = f.get("ext", "unknown")

                    if vcodec != "none" and acodec != "none" and height:
                        # видео + аудио
                        key = f"{height}p_{ext}"
                        if key not in seen:
                            seen.add(key)
                            name = f"{height}p video+audio ({ext})"
                            format_list.append((name, f["format_id"]))

                    elif acodec != "none" and vcodec == "none":
                        # только аудио
                        abr = f.get("abr", "unknown")
                        key = f"audio_{abr}_{ext}"
                        if key not in seen:
                            seen.add(key)
                            name = f"audio only {abr}kbps ({ext})"
                            format_list.append((name, f["format_id"]))

                if self._is_running:
                    self.formats_ready.emit(format_list)

                    if len(format_list) == 0:
                        self.log_signal.emit("Видео и его форматы не найдены!")
                    else:
                        self.log_signal.emit(f"Найдено {len(format_list)} форматов")

        except Exception as e:
            if self._is_running:
                self.log_signal.emit(f"Ошибка: {str(e)[:100]}")
                self.formats_ready.emit([])

    def stop(self):
        """Остановка потока"""
        self._is_running = False
