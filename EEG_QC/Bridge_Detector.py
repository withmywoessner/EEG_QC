import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QTextEdit
from PyQt5.QtCore import QThread, pyqtSignal
import mne
import time
import matplotlib.pyplot as plt
import os
from pathlib import Path
import tempfile
import zipfile


def file_name_parser(file_path):
    if '\\' in file_path:
        file_path = file_path.replace('\\', '/')
    file_name = file_path.split("/")[-1]
    return file_name


def find_vhdr_files(start_path):
    """
    Recursively search for files with a .vhdr extension starting from start_path.
    :param start_path: The directory path to start the search from.
    :return: A list of paths to files with a .vhdr extension.
    """
    start_path = Path(start_path)
    vhdr_files = [str(file) for file in start_path.rglob('*.vhdr')]
    if not vhdr_files:
        return None
    return vhdr_files


def mne_bridge_compute_bridges(file_path):
    file_name = file_name_parser(file_path)
    if file_name.endswith('.cnt'):
        print(f"Reading file: {file_name}...")
        raw = mne.io.read_raw_cnt(file_path, preload=True)
    elif file_name.endswith('.vhdr'):
        print(f"Reading file: {file_name}...")    
        raw = mne.io.read_raw_brainvision(file_path, preload=True)
    elif file_name.endswith('.zip'):
        print(f"Unzipping file: {file_name}...")
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            with tempfile.TemporaryDirectory() as tmpdirname:
                # Extract all the necessary files
                zip_ref.extractall(tmpdirname)
                # Find the .vhdr file
                vhdr_file = None
                vhdr_file = find_vhdr_files(tmpdirname)[0]
                if vhdr_file:
                    print(f"Reading file: {file_name}...")
                    raw = mne.io.read_raw_brainvision(vhdr_file, preload=True)
                else:
                    print(f"No .vhdr file found in {file_name}...")

    montage_1020 = mne.channels.make_standard_montage("standard_1020")
    raw.set_montage(montage_1020, match_case=False, match_alias=True, on_missing='warn')
    print(f"Searching for bridges...")
    bridged_idx, ed_matrix = mne.preprocessing.compute_bridged_electrodes(raw)

    return raw.info, bridged_idx, ed_matrix

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
        file_name = file_name_parser(self.filename)
        mne.viz.plot_bridged_electrodes(
            info,
            bridged_idx,
            ed_matrix,
            title=f"File: {file_name}\nBridged Electrodes: {len(bridged_idx)}",
            topomap_args=dict(vlim=(None, 5))
        )

    def initUI(self):
        self.textbox = QTextEdit(self)
        self.textbox.setReadOnly(True)

        self.textbox.append('IF USING CNT FILE TYPE PLEASE VERIFY THAT FILE'
                            'DURATION MATCHES THE '
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
        filters = 'CNT Files (*.cnt);;Brain Vision Zip (*.zip);;Brain Vision Header Files (*.vhdr);;All Files (*)'
        filename, _ = QFileDialog.getOpenFileName(
            self, 'Open file', '', filters,
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
