import sys, os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFileDialog, QProgressBar, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import yt_dlp

class DownloadThread(QThread):
    progress = pyqtSignal(float)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, url, fmt, path, quality):
        super().__init__()
        self.url = url
        self.fmt = fmt
        self.path = path
        self.quality = quality

    def run(self):
        try:
            if self.fmt == 'mp3':
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(self.path, '%(title)s.%(ext)s'),
                    'noplaylist': True,
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'progress_hooks': [self.hook],
                }
            else:
                if self.quality == '최고':
                    fmt_str = 'bestvideo+bestaudio[ext=m4a]'
                else:
                    fmt_str = f'bestvideo[height<={self.quality}]+bestaudio[ext=m4a]'

                ydl_opts = {
                    'format': fmt_str,
                    'merge_output_format': 'mp4',
                    'noplaylist': True,
                    'outtmpl': os.path.join(self.path, '%(title)s.%(ext)s'),
                    'progress_hooks': [self.hook],
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))

    def hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                percent = downloaded / total * 100
                self.progress.emit(percent)

class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader")
        self.setGeometry(300, 300, 500, 330)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 링크 입력
        self.link_label = QLabel("유튜브 링크:")
        self.link_input = QLineEdit()
        layout.addWidget(self.link_label)
        layout.addWidget(self.link_input)

        # 형식 선택
        self.format_label = QLabel("형식 선택:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(['mp4', 'mp3'])
        layout.addWidget(self.format_label)
        layout.addWidget(self.format_combo)

        # 화질 선택 (mp4만 적용)
        self.quality_label = QLabel("화질 선택 (mp4만 적용):")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(['최고', '1440', '1080', '720', '480', '360', '240', '144'])
        layout.addWidget(self.quality_label)
        layout.addWidget(self.quality_combo)

        # 저장 경로
        self.path_label = QLabel("저장 경로:")
        self.path_input = QLineEdit(os.getcwd())
        self.browse_button = QPushButton("찾기")
        self.browse_button.clicked.connect(self.browse_folder)
        layout.addWidget(self.path_label)
        layout.addWidget(self.path_input)
        layout.addWidget(self.browse_button)

        # 다운로드 버튼
        self.download_button = QPushButton("다운로드")
        self.download_button.clicked.connect(self.start_download)
        layout.addWidget(self.download_button)

        # 진행률 표시
        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "저장 경로 선택", os.getcwd())
        if folder:
            self.path_input.setText(folder)

    def start_download(self):
        url = self.link_input.text().strip()
        fmt = self.format_combo.currentText()
        path = self.path_input.text().strip()
        quality = self.quality_combo.currentText()

        if not url:
            QMessageBox.warning(self, "경고", "유튜브 링크를 입력해주세요.")
            return
        if not os.path.isdir(path):
            QMessageBox.warning(self, "경고", "올바른 저장 경로를 선택해주세요.")
            return

        self.download_button.setEnabled(False)
        self.thread = DownloadThread(url, fmt, path, quality)
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.download_finished)
        self.thread.error.connect(self.download_error)
        self.thread.start()

    def update_progress(self, percent):
        self.progress_bar.setValue(int(percent))

    def download_finished(self):
        self.download_button.setEnabled(True)
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "완료", "다운로드가 완료되었습니다!")

    def download_error(self, msg):
        self.download_button.setEnabled(True)
        QMessageBox.critical(self, "에러", f"다운로드 중 오류 발생:\n{msg}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec())
