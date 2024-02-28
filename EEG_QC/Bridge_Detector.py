import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal
from mne_bridge_script import mne_bridge_compute_bridges
import mne
import matplotlib.pyplot as plt


class Worker(QThread):
    output = pyqtSignal(str)
    plot_ready = pyqtSignal(object, object, object)

    def __init__(self):
        super().__init__()
        self.filename = ''  # Initialize filename within the worker

    def set_filename(self, filename):
        self.filename = filename

    def run(self):
        stdout = sys.stdout
        sys.stdout = self

        # Compute bridges and prepare plotting data but do not plot here
        fig_data = mne_bridge_compute_bridges(self.filename)

        # Instead of plotting, emit a signal with the necessary data to plot
        # Assuming fig_data is a tuple of (raw.info, bridged_idx, ed_matrix)
        self.plot_ready.emit(*fig_data)

        sys.stdout = stdout

    def write(self, text):
        self.output.emit(text.strip())


class MyApp(QWidget):
    def __init__(self):
        super().__init__()

        self.filename = ''
        self.initUI()
        self.worker = None

    def plot_bridged_electrodes(self, info, bridged_idx, ed_matrix):
        # The plotting now happens in the main thread in response to worker's signal
        plt.ion()
        mne.viz.plot_bridged_electrodes(
            info,
            bridged_idx,
            ed_matrix,
            title=f"bridged: {len(bridged_idx)}",
            topomap_args=dict(vlim=(None, 5))
        )

    def initUI(self):
        self.textbox = QTextEdit(self)
        self.textbox.setReadOnly(True)

        self.textbox.append('PLEASE VERIFY THAT FILE DURATION MATCHES THE '
                            'EXPECTED DURATION\nThere is a bug in the mne '
                            'library that causes the duration of the file '
                            'to be incorrectly calculated...')

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
        self.worker.plot_ready.connect(self.plot_bridged_electrodes)  # Connect to new slot for plotting

    def upload_file(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(
            self, 'Open file', '', 'CNT Files (*.cnt);;All Files (*)',
            options=options)
        if filename:
            self.filename = filename
            self.textbox.clear()
            self.textbox.append(f'File selected: {self.filename}')

    def start(self):
        if self.filename:
            self.worker = Worker()
            self.worker.set_filename(self.filename)  # Set the filename here
            self.worker.output.connect(self.handle_output)
            self.worker.plot_ready.connect(self.plot_bridged_electrodes)
            self.worker.start()

    def handle_output(self, line):
        self.textbox.append(line)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec_())
