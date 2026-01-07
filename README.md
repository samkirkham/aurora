# AURORA

AURORA: Acoustic Understanding and Real-time Observation of Resonant Articulations

## Description

AURORA provides real-time visualization of spectral features with formant tracking and (preliminary) tongue shape estimation. The application captures audio input, performs spectral analysis, and displays spectral peaks and predicted tongue shape in real-time.

## Requirements

- Python 3.12 or higher
- Poetry (for dependency management)

## Installation

### 1. Install Poetry

If you don't have Poetry installed, follow the installation instructions at [https://python-poetry.org/docs/#installation](https://python-poetry.org/docs/#installation).

### 2. Clone and Setup

```bash
# Navigate to the top-level directory
cd aurora

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```


## Usage

Run the main application:

```bash
python aurora/aurora.py
```

Or run the test scripts:

```bash
# Basic test
python tests/Resonance_basic.py

# Audio-only test
python tests/Resonance_audio_only.py
```

## Dependencies

- **numpy**: Numerical computing
- **sounddevice**: Real-time audio I/O
- **scipy**: Scientific computing (signal processing)
- **librosa**: Audio analysis
- **pyqtgraph**: Real-time plotting and GUI
- **polars**: Data manipulation (used in model building)

## Features

- Real-time audio capture and analysis
- Formant tracking using LPC analysis
- Tongue shape modeling and visualization
- Configurable parameters (sampling rate, frame size, LPC order)
- GUI interface with interactive plots

## Configuration

Default parameters can be modified in the main script:

- `fs`: Sampling rate (default: 10000 Hz)
- `frame_size`: Analysis frame size (default: 1024)
- `lpc_order`: LPC analysis order (default: 12)
- `rms_threshold`: RMS threshold for processing (default: 0.03)

## Author

Sam Kirkham (s.kirkham@lancaster.ac.uk)