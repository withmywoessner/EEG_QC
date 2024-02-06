import sys
import mne
import time
import matplotlib.pyplot as plt
# 


def mne_bridge_compute_bridges(file_path):
    file_name = file_path.split("/")[-1]
    raw = mne.io.read_raw_cnt(file_path, preload=True)
    raw.drop_channels(['X', 'BLANK', 'Y'])
    raw.rename_channels(
        {'FP1': 'Fp1', 'FP2': 'Fp2', 'FZ': 'Fz', 'CZ': 'Cz',
        'PZ': 'Pz', 'FPZ': 'Fpz', 'AFZ': 'AFz', 'FCZ': 'FCz',
        'POZ': 'POz', 'OZ': 'Oz', 'CPZ': 'CPz'}
    )

    # wait for 4 seconds
    print(f"Reading file: {file_name}...")
    time.sleep(4)
    montage_1020 = mne.channels.make_standard_montage("standard_1020")
    raw.set_montage(montage_1020)
    print(f"Searching for bridges...")
    bridged_idx, ed_matrix = mne.preprocessing.compute_bridged_electrodes(raw)
    fig = mne.viz.plot_bridged_electrodes(
        raw.info,
        bridged_idx,
        ed_matrix,
        title=f"{file_name} bridged: {len(bridged_idx)}",
        topomap_args=dict(vlim=(None, 5)),
    )

    # Add as image to new plot imshow
    plt.imshow(fig)
    return fig


def main():
    if len(sys.argv) != 2:
        print("Usage: python mne_bridge_compute_bridges.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    fig = mne_bridge_compute_bridges(filename)


if __name__ == "__main__":
    main()
