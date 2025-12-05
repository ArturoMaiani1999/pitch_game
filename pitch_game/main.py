# main.py
import time
import numpy as np
from collections import deque

from config import SR, HOP_SIZE, DEFAULT_BPM, MODE_NAME, PHRASES, DY_SEMITONES, WINDOW_SECONDS
from scale_playback import play_scale_warmup
from config import PLAY_SCALE_WARMUP, WARMUP_NOTE_BEATS, WARMUP_PAUSE_BEATS, WARMUP_REPEATS

from audio_pitch import PitchStream
from calibration import run_calibration
from melody_generator import generate_melody_for_range
from target_trace import events_to_target_trace
from renderer import GameRenderer

from config import TONIC_NAME, FORCE_TONIC_KEY, MIN_NOTE_BEATS, MAX_JUMP_SEMITONES


def main():
    pitch_stream = PitchStream()

    with pitch_stream.open_stream():
        # 1) Calibration
        fmin_raw, fmax_raw, fmin_tess, fmax_tess = run_calibration(pitch_stream, truncate_frac=0.05)

        # Use tessitura for melody + UI
        fmin_plot = fmin_tess
        fmax_plot = fmax_tess

        # 2) Melody generation in central tessitura
        events, bpm, midi_min, midi_max, tonic = generate_melody_for_range(
                MODE_NAME, fmin_plot, fmax_plot,
                bpm=DEFAULT_BPM, phrases=PHRASES,
                min_note_beats=MIN_NOTE_BEATS,
                max_jump_semitones=MAX_JUMP_SEMITONES,
                tonic_name=TONIC_NAME,
                force_tonic_key=FORCE_TONIC_KEY
            )



        # NEW: scale warm-up playback
        if PLAY_SCALE_WARMUP:
            play_scale_warmup(
                tonic_midi=tonic,
                mode_name=MODE_NAME,
                midi_min=midi_min,
                midi_max=midi_max,
                bpm=bpm,
                sr=SR,
                note_beats=WARMUP_NOTE_BEATS,
                pause_beats=WARMUP_PAUSE_BEATS,
                repeats=WARMUP_REPEATS,
            )


        # 3) Target trace
        t_target, hz_target = events_to_target_trace(events, bpm, HOP_SIZE, SR)
        total_duration = t_target[-1]
        print(f"Generated melody length: {total_duration:.1f}s @ {bpm} bpm in {MODE_NAME}")

        # 4) Renderer
        renderer = GameRenderer(fmin_plot, fmax_plot, DY_SEMITONES)
        renderer.draw_background_map(t_target, hz_target)

        # 5) Game loop
        max_points = int(WINDOW_SECONDS * SR / HOP_SIZE)
        user_times = deque(maxlen=max_points)
        user_pitches = deque(maxlen=max_points)

        t0 = time.time()

        print("Game start! Sing along with the green lane. Close window/Ctrl+C to stop.")

        while renderer.still_open():
            now = time.time() - t0
            if now > total_duration:
                renderer.score_text.set_text("Level complete! 🎉")
                renderer.fig.canvas.draw()
                renderer.fig.canvas.flush_events()
                time.sleep(0.1)
                continue

            user_times.append(now)
            user_pitches.append(pitch_stream.latest_hz)

            renderer.update(
                now,
                user_times, user_pitches,
                t_target, hz_target,
                pitch_stream.latest_hz
            )

            time.sleep(0.02)

if __name__ == "__main__":
    main()
