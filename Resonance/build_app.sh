# NOTES
# - this works in the sense that it builds the app
# - but the app doesn't seem to take any audio input!
# - not a priority for now, just focus on getting the actual python version working properly

pyinstaller --onefile --windowed --add-binary '/opt/homebrew/Cellar/portaudio/19.7.0/lib/libportaudio.2.dylib:.' Resonance/Resonance.py