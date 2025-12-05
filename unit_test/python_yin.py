import numpy as np
import sounddevice as sd
import aubio
import matplotlib.pyplot as plt
import time
from collections import deque
import math

sr = 44100
hop_size = 512
win_size = 4096

# Pitch detector (your setup)
pitch_o = aubio.pitch("yin", win_size, hop_size, sr)
pitch_o.set_unit("Hz")
pitch_o.set_silence(-60)
pitch_o.set_tolerance(0.8)

# ----------------------------
# Musical helpers
# ----------------------------
A4 = 440.0
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def midi_to_hz(midi):
    return A4 * (2 ** ((midi - 69) / 12))

def hz_to_midi(hz):
    return 69 + 12 * math.log2(hz / A4)

def midi_to_name(midi):
    n = int(round(midi))
    name = NOTE_NAMES[n % 12]
    octave = n // 12 - 1
    return f"{name}{octave}"

# ----------------------------
# Plot/window config
# ----------------------------
window_seconds = 5.0
max_points = int(window_seconds * sr / hop_size)

times  = deque(maxlen=max_points)
pitches = deque(maxlen=max_points)

t0 = time.time()

# Pick a good singing range (adjust if you like)
fmin_plot = 60
fmax_plot = 1000

# Precompute semitone ticks in range
midi_min = int(math.floor(hz_to_midi(fmin_plot)))
midi_max = int(math.ceil(hz_to_midi(fmax_plot)))
midi_ticks = list(range(midi_min, midi_max + 1))
hz_ticks = [midi_to_hz(m) for m in midi_ticks]
tick_labels = [midi_to_name(m) for m in midi_ticks]

# ----------------------------
# Matplotlib live plot setup
# ----------------------------
plt.ion()
fig, ax = plt.subplots(figsize=(9, 5))
(line,) = ax.plot([], [], lw=2)

ax.set_title("Real-time Pitch (aubio YIN) — Note Accuracy")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Pitch (notes)")

# Log scale so semitones are evenly spaced visually
ax.set_yscale("log", base=2)
ax.set_ylim(fmin_plot, fmax_plot)

# Note-labeled y ticks
ax.set_yticks(hz_ticks)
ax.set_yticklabels(tick_labels)

ax.set_xlim(-window_seconds, 0)
ax.grid(True, which="both", axis="y", alpha=0.3)
ax.grid(True, which="major", axis="x", alpha=0.3)

# ----------------------------
# Audio callback (your logic)
# ----------------------------
def callback(indata, frames, time_info, status):
    if status:
        print(status)

    samples = indata[:, 0].astype(np.float32)

    f0 = float(pitch_o(samples)[0])
    conf = float(pitch_o.get_confidence())

    if conf > 0.6 and fmin_plot < f0 < fmax_plot:
        pitch_hz = f0
        print(f"F0: {f0:7.2f} Hz  conf: {conf:.2f}")
    else:
        pitch_hz = np.nan
        print("unvoiced")

    t = time.time() - t0
    times.append(t)
    pitches.append(pitch_hz)

# ----------------------------
# Stream + render loop
# ----------------------------
with sd.InputStream(
    channels=1,
    callback=callback,
    samplerate=sr,
    blocksize=hop_size
):
    print("Listening... close plot window or Ctrl+C to stop.")
    try:
        while plt.fignum_exists(fig.number):
            if len(times) > 1:
                t_arr = np.array(times)
                p_arr = np.array(pitches)

                # Latest point at x=0, older to the left
                t_rel = t_arr - t_arr[-1]

                line.set_data(t_rel, p_arr)
                ax.set_xlim(-window_seconds, 0)

                fig.canvas.draw()
                fig.canvas.flush_events()

            time.sleep(0.02)

    except KeyboardInterrupt:
        print("Stopped.")
