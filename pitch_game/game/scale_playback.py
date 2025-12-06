# scale_playback.py
import numpy as np
import sounddevice as sd
import math
from game.utils_music import midi_to_hz
from game.melody_generator import MODES  # reuse the same modes dict

def _sine_note(freq, dur_s, sr=44100, fade_ms=15):
    """Generate a sine tone with a short fade in/out."""
    n = int(dur_s * sr)
    t = np.arange(n) / sr
    x = 0.2 * np.sin(2 * np.pi * freq * t)

    fade_n = int(sr * fade_ms / 1000)
    if fade_n > 0 and fade_n * 2 < n:
        fade = np.linspace(0, 1, fade_n)
        x[:fade_n] *= fade
        x[-fade_n:] *= fade[::-1]
    return x.astype(np.float32)

def play_scale_warmup(
    tonic_midi,
    mode_name,
    midi_min,
    midi_max,
    bpm=100,
    sr=44100,
    note_beats=0.6,
    pause_beats=0.15,
    repeats=1,
):
    """
    Warm-up pattern:
      tonic -> 2nd -> 3rd -> 4th -> 5th -> 4th -> 3rd -> 2nd -> tonic
    i.e., go up to the 5th and back down in the chosen mode.
    Notes are clamped into [midi_min, midi_max] by octave wrapping if needed.
    """
    mode_offsets = MODES[mode_name]

    sec_per_beat = 60.0 / bpm
    note_dur = note_beats * sec_per_beat
    pause_dur = pause_beats * sec_per_beat

    # scale degrees 1..5 in this mode (offsets[0..4])
    degree_offsets = mode_offsets[:5]

    # build MIDI pitches for degrees in current tonic octave
    asc_midis = [tonic_midi + off for off in degree_offsets]

    # if any note falls outside tessitura, octave-wrap it back in range
    def wrap_into_range(m):
        while m < midi_min:
            m += 12
        while m > midi_max:
            m -= 12
        return m

    asc_midis = [wrap_into_range(m) for m in asc_midis]

    # descending back to tonic (exclude repeated 5th)
    desc_midis = asc_midis[-2::-1]

    pattern = asc_midis + desc_midis

    print("\n=== Scale warm-up (tonic → fifth → tonic) ===")
    print(f"Mode: {mode_name}, tonic MIDI: {tonic_midi}")
    print("Listen and match these notes to prepare your ear.")
    print("===========================================\n")

    audio = []
    for _ in range(repeats):
        for m in pattern:
            hz = float(midi_to_hz(m))
            audio.append(_sine_note(hz, note_dur, sr))
            if pause_dur > 0:
                audio.append(np.zeros(int(pause_dur * sr), dtype=np.float32))

    audio = np.concatenate(audio) if len(audio) else np.zeros(1, dtype=np.float32)
    sd.play(audio, sr)
    sd.wait()
