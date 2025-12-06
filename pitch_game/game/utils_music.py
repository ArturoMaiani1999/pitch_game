# utils_music.py
import math
import numpy as np

A4 = 440.0
NOTE_NAMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

def midi_to_hz(midi):
    midi = np.asarray(midi, dtype=float)
    return A4 * (2 ** ((midi - 69) / 12))

def hz_to_midi(hz):
    hz = np.asarray(hz, dtype=float)
    return 69 + 12 * np.log2(hz / A4)

def midi_to_name(midi):
    n = int(round(midi))
    name = NOTE_NAMES[n % 12]
    octave = n // 12 - 1
    return f"{name}{octave}"

def cents_error(hz, target_hz):
    if not np.isfinite(hz) or not np.isfinite(target_hz):
        return np.nan
    return 1200 * math.log2(hz / target_hz)
