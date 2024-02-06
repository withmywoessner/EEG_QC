from mne_bridge_script import mne_bridge_compute_bridges
import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal


class Worker(QThread):
    output = pyqtSignal(str)

    def run(self):
        proc = subprocess.Popen(
            ['python', '-u', 'mne_bridge_script.py',
             self.filename],
            stdout=subprocess.PIPE)
        for line in iter(proc.stdout.readline, b''):
            self.output.emit(line.decode().strip())


class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        self.filename = ''

        self.textbox = QTextEdit(self)
        self.textbox.setReadOnly(True)

        # Add Text to textbox
        self.textbox.append('PLEASE VERIFY THAT FILE DURATION MATCHES THE '
                            'EXPECTED DURATION\nThere is a bug in the mne '
                            'library that causes the duration of the file '
                            'to be ncorrectly calculated. It has been fixed '
                            'in the latest version of the library '
                            'but it has not been released yet.')

        self.upload_button = QPushButton('Upload File', self)
        self.upload_button.clicked.connect(self.upload_file)

        self.start_button = QPushButton('Start', self)
        self.start_button.clicked.connect(self.start)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.upload_button)
        self.layout.addWidget(self.start_button)
        self.layout.addWidget(self.textbox)

        self.worker = Worker()
        self.worker.output.connect(self.handle_output)

    def upload_file(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            self, 'QFileDialog.getOpenFileName()', '',
            'CNT Files (*.cnt)', options=options)
        if filename:
            self.filename = filename
            self.textbox.clear()
            self.textbox.append(f'File selected: {self.filename}')

    def start(self):
        if self.filename:
            self.worker.filename = self.filename
            self.worker.start()

    def handle_output(self, line):
        self.textbox.append(line)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec_())
