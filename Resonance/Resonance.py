"""
Resonance: real-time spectral feedback

TODO
-----
- updating frame_size or sampling_rate on GUI causes system to freeze
- LPC order also needs to be constrained, because past a certain point it also causes system to freeze (b/c it's too high relative to sampling rate). This could be capped at the highest feasible value for fs/frame_size directly in the button toggle.
- might be best to either fix them or provide a reset button (or auto-reset if changing those values)

NOTES
-----
- note: threshold is very important; 0.05 works much better for than 0.01, as it seems to pick up more of the resonance rather than the details that cause big shifts
- if you want continuous real-time feedback then a lower threshold is better (0.01), if you want more stable resonances for sustained vowels then a higher threshold is beter (0.05) -> will obviously depend on mic settings
- Note that the GUI (at least in app mode) allows you to drag the axes if you want the y-axis to be bigger or smaller (very cool)
"""

import numpy as np
import sounddevice as sd
import scipy.signal
import librosa
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
from collections import deque
import sys
import pickle

"""
Load pre-computed lookup dictionary from file (created by Resonance/build_model.py)
"""

with open("Resonance/tongue_model.pkl", "rb") as f:
    tongue_lookup = pickle.load(f)


"""
Default parameters
"""

params = {
    "fs": 10000,  # fs = 10000 is ok
    "frame_size": 1024,  # 1024 is pretty good (2048 quite slow, 512 too jittery and rapid)
    "lpc_order": 12,  # will need changing (if 10,000 Hz then 8-10 F, 10-12 M)
    "rms_threshold": 0.03,
}


"""
Visualiser window
"""

# Config visuals
pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")

# Setup PyQtGraph window
app = QtWidgets.QApplication([])

# Create main app window with layout
main_window = QtWidgets.QWidget()
layout = QtWidgets.QHBoxLayout(main_window)

# Plot widget inside a GraphicsLayoutWidget
plot_widget = pg.GraphicsLayoutWidget()
plot = plot_widget.addPlot(title="")
plot.setLabel("left", "Magnitude (dB)")
plot.setLabel("bottom", "Frequency", units="Hz")
plot.setYRange(-20, 60)
plot.setXRange(0, params["fs"] / 2)
layout.addWidget(plot_widget, stretch=3)

# Light blue filled curve, cornflower blue line
curve = plot.plot(
    fillLevel=-60, brush=(135, 206, 250, 150), pen=pg.mkPen((100, 149, 237), width=2)
)

# Frequency axis for plotting
freq_axis = np.linspace(0, params["fs"] / 2, params["frame_size"] // 2)

# Prepare formant lines (vertical lines, modified in update loop)
formant_lines = [
    pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("gray", width=1))
    for _ in range(4)
]
for line in formant_lines:
    plot.addItem(line)


"""
Add visualization panel + update function for estimated tongue shape
"""

# get min/max values of tongue shape to set plot axes
all_points = np.vstack(list(tongue_lookup.values()))
x_min, x_max = np.min(all_points[:, 0]), np.max(all_points[:, 0])
y_min, y_max = np.min(all_points[:, 1]), np.max(all_points[:, 1])

# plot tongue shape
tongue_plot = plot_widget.addPlot(title="") # optional title
tongue_plot.setXRange(x_min, x_max)
tongue_plot.setYRange(y_min, y_max)
tongue_plot.setAspectLocked(True) # False allows you to reorient the window better, but not ideal!
tongue_plot.setMouseEnabled(x=False, y=False)
tongue_curve = tongue_plot.plot(pen=pg.mkPen('black', width=7))

def update_tongue(formant_freqs):
    """ Function for real-time tongue plot update """
    f1_rounded = int(round(formant_freqs[0] / 10.0) * 10)  # Assuming 10Hz steps in data
    f2_rounded = int(round(formant_freqs[1] / 10.0) * 10)
    tongue_points = tongue_lookup.get((f1_rounded, f2_rounded)) # lookup from dict
    if tongue_points is not None:
        tongue_curve.setData(tongue_points[:, 0], tongue_points[:, 1])


"""
Add option to change parameter settings in real-time
- note that sampling rate may need to reset the program?
"""

# Controls (in a VBox inside a container)
controls = QtWidgets.QWidget()
controls_layout = QtWidgets.QVBoxLayout(controls)

# Add collapsible toggle button
toggle_btn = QtWidgets.QPushButton("Show Controls")
toggle_btn.setFixedHeight(30)  # Smaller height
toggle_btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

def toggle_controls():
    visible = controls_group.isVisible()
    controls_group.setVisible(not visible)
    toggle_btn.setText("Show Controls" if visible else "Hide Controls")

toggle_btn.clicked.connect(toggle_controls)
controls_layout.addWidget(toggle_btn)

# Group box to hold control widgets
controls_group = QtWidgets.QGroupBox("Parameters")
controls_group_layout = QtWidgets.QFormLayout(controls_group)

# Hide by default
controls_group.setVisible(False)


"""
Add controls for fs, frame_size, lpc_order, lpc_order
"""

fs_box = QtWidgets.QSpinBox()
fs_box.setRange(4000, 48000)
fs_box.setValue(params["fs"])
fs_box.valueChanged.connect(lambda val: params.update({"fs": val}))

frame_box = QtWidgets.QSpinBox()
frame_box.setRange(128, 4096)
frame_box.setValue(params["frame_size"])
frame_box.valueChanged.connect(lambda val: params.update({"frame_size": val}))

lpc_box = QtWidgets.QSpinBox()
lpc_box.setRange(4, 50)
lpc_box.setValue(params["lpc_order"])
lpc_box.valueChanged.connect(lambda val: params.update({"lpc_order": val}))

threshold_box = QtWidgets.QDoubleSpinBox()
threshold_box.setRange(0.0, 0.1)
threshold_box.setSingleStep(0.01)
threshold_box.setDecimals(3)
threshold_box.setValue(params["rms_threshold"])
threshold_box.valueChanged.connect(lambda val: params.update({"rms_threshold": val}))

"""
Option to higlight one or more formants
"""

highlighted_formants = [False, False, False, False]
highlight_labels = ["F1", "F2", "F3", "F4"]
highlight_checkboxes = []
formant_checkbox_widget = QtWidgets.QWidget()
formant_checkbox_layout = QtWidgets.QHBoxLayout()
formant_checkbox_layout.setContentsMargins(0, 0, 0, 0)  # make it compact
formant_checkbox_widget.setLayout(formant_checkbox_layout)


def update_highlight(index, state):
    highlighted_formants[index] = state == QtCore.Qt.Checked


for i, label in enumerate(highlight_labels):
    cb = QtWidgets.QCheckBox(label)
    cb.stateChanged.connect(lambda state, i=i: update_highlight(i, state))
    formant_checkbox_layout.addWidget(cb)
    highlight_checkboxes.append(cb)


"""
Select audio interface
"""

device_dropdown = QtWidgets.QComboBox()
input_devices = [d for d in sd.query_devices() if d["max_input_channels"] > 0]
device_dropdown.addItems([f"{i}: {d['name']}" for i, d in enumerate(input_devices)])
selected_device_index = [0]  # Store in a list so it can be mutated

def restart_stream():
    """ Function to restart stream when changing audio input device """
    global stream
    try:
        if stream:
            stream.stop()
            stream.close()
    except Exception as e:
        print("Error stopping stream:", e)

    try:
        selected_device = input_devices[selected_device_index[0]]["name"]
        stream = sd.InputStream(
            device=selected_device,
            callback=process_audio,
            channels=1,
            samplerate=params["fs"],
            blocksize=params["frame_size"],
        )
        stream.start()
        print(f"Stream restarted with device: {selected_device}")
    except Exception as e:
        print("Error starting stream:", e)

def change_device(index):
    selected_device_index[0] = index
    restart_stream()


device_dropdown.currentIndexChanged.connect(change_device)


"""
add all of above elements to control group layout
"""

controls_group_layout.addRow("Input Device", device_dropdown)
controls_group_layout.addRow("Sampling Rate (Hz)", fs_box)
controls_group_layout.addRow("Frame Size", frame_box)
controls_group_layout.addRow("LPC Order", lpc_box)
controls_group_layout.addRow("Threshold", threshold_box)
controls_group_layout.addRow("Highlight:", formant_checkbox_widget)


"""
render window with main display and controls
"""

# Add group box to layout
controls_layout.addWidget(controls_group)
layout.addWidget(controls, stretch=1)

main_window.setWindowTitle("Resonance: Real-Time Formant Biofeedback")
main_window.resize(1200, 700)
main_window.show()


"""
Audio processing and plot update
"""

# Buffer for audio
audio_buffer = deque(maxlen=params["frame_size"])


def update_spectrum(spectrum, formant_freqs):
    curve.setData(freq_axis, spectrum)
    # Update formant lines positions or hide if no formant
    for i in range(4):
        if i < len(formant_freqs):
            formant_lines[i].setPos(formant_freqs[i])
            # Highlight style
            if highlighted_formants[i]:
                formant_lines[i].setPen(pg.mkPen("r", width=4))
            else:
                formant_lines[i].setPen(pg.mkPen("gray", width=1))
            formant_lines[i].setVisible(True)
        else:
            formant_lines[i].setVisible(False)


def process_audio(indata, frames, time, status):
    try:
        audio_buffer.extend(indata[:, 0])
        if len(audio_buffer) == params["frame_size"]:
            frame = np.array(audio_buffer)
            rms = np.sqrt(np.mean(frame**2))  # get rms in frame
            if rms < params["rms_threshold"]:  # # check if audio is above RMS threshold
                return  # if below threshold, do nothing
            else:
                frame *= np.hamming(len(frame))
                a = librosa.lpc(y=frame, order=params["lpc_order"])  # LPC coefficients
                w, h = scipy.signal.freqz(
                    [1], a, worN=params["frame_size"] // 2, fs=params["fs"]
                )  # freq response
                spectrum = 20 * np.log10(np.abs(h) + 1e-10)  # spectrum
                # Find formant peaks (higher distance = less sensitive to small bumps)
                peaks, properties = scipy.signal.find_peaks(
                    spectrum, height=-40, distance=20
                )
                formant_freqs = freq_axis[peaks]
                formant_freqs = np.sort(formant_freqs)[
                    :4
                ]  # sort by freq. + return 4 fms
                
                # update spectrum + tongue plots
                update_spectrum(spectrum, formant_freqs)
                update_tongue(formant_freqs)

    except Exception as e:
        print("LPC error:", repr(e))


"""
Start audio stream and run GUI
"""

# Start audio stream

selected_device = input_devices[selected_device_index[0]]["name"]
# this block is now inside restart_stream() -> can delete
#stream = sd.InputStream(
#    device=selected_device,
#    callback=process_audio,
#    channels=1,
#    samplerate=params["fs"],
#    blocksize=params["frame_size"],
#)
stream = None
restart_stream()

# Qt timer to keep GUI responsive
timer = QtCore.QTimer()
timer.timeout.connect(lambda: None)
timer.start(30)


"""
Run via command line
"""

if __name__ == "__main__":
    if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
        QtWidgets.QApplication.instance().exec_()
