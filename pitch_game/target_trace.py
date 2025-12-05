# target_trace.py
import numpy as np
from utils_music import midi_to_hz

def events_to_target_trace(events, bpm, hop_size, sr):
    """
    Convert (beats, midi_or_None) events to hop-grid target.
    PIECEWISE CONSTANT (no interpolation), so no sharp artifacts.
    """
    sec_per_beat = 60.0 / bpm
    dt = hop_size / sr

    t_list = []
    hz_list = []
    t = 0.0

    for dur_beats, note_midi in events:
        dur_sec = dur_beats * sec_per_beat
        n_frames = int(np.round(dur_sec / dt))

        hz_val = np.nan if note_midi is None else float(midi_to_hz(note_midi))

        for _ in range(n_frames):
            t_list.append(t)
            hz_list.append(hz_val)
            t += dt

    return np.array(t_list, float), np.array(hz_list, float)
