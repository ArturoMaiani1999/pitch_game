# calibration.py
import time
import numpy as np
from game.config import (
    CALIB_SEC_PER_NOTE, CALIB_REPEATS,
    CALIB_PERCENTILE_LOW, CALIB_PERCENTILE_HIGH
)

def _collect_pitches(pitch_stream, seconds):
    pitches = []
    t_end = time.time() + seconds
    while time.time() < t_end:
        hz = pitch_stream.latest_hz
        if np.isfinite(hz):
            pitches.append(hz)
        time.sleep(0.01)
    return np.array(pitches)

def run_calibration(pitch_stream, truncate_frac=0.05):
    """
    Returns:
      fmin_raw, fmax_raw, fmin_tess, fmax_tess
    where tessitura is the central range after truncating
    lower/upper truncate_frac of the comfortable range.
    """
    print("\n=== Calibration ===")
    print("We’ll find your comfortable range.")
    print("Sing a LOW comfortable note when prompted, then a HIGH one.\n")

    lows, highs = [], []

    for r in range(CALIB_REPEATS):
        input(f"[{r+1}/{CALIB_REPEATS}] Press Enter, then sing LOW for {CALIB_SEC_PER_NOTE}s...")
        low_p = _collect_pitches(pitch_stream, CALIB_SEC_PER_NOTE)
        if len(low_p): lows.append(np.median(low_p))

        input(f"[{r+1}/{CALIB_REPEATS}] Press Enter, then sing HIGH for {CALIB_SEC_PER_NOTE}s...")
        high_p = _collect_pitches(pitch_stream, CALIB_SEC_PER_NOTE)
        if len(high_p): highs.append(np.median(high_p))

    lows = np.array(lows) if len(lows) else np.array([120.0])
    highs = np.array(highs) if len(highs) else np.array([480.0])

    fmin_raw = float(np.percentile(lows, CALIB_PERCENTILE_LOW))
    fmax_raw = float(np.percentile(highs, CALIB_PERCENTILE_HIGH))

    # Safety clamp
    fmin_raw = max(50.0, fmin_raw)
    fmax_raw = min(1200.0, fmax_raw)
    if fmax_raw <= fmin_raw * 1.3:
        fmax_raw = fmin_raw * 2.0

    # Truncate lower/upper 20% -> tessitura
    span = fmax_raw - fmin_raw
    fmin_tess = fmin_raw + truncate_frac * span
    fmax_tess = fmax_raw - truncate_frac * span

    # Final sanity
    if fmax_tess <= fmin_tess * 1.2:
        fmin_tess = fmin_raw
        fmax_tess = fmax_raw

    print(f"\nEstimated comfortable range: {fmin_raw:.1f}–{fmax_raw:.1f} Hz")
    print(f"Using central tessitura:     {fmin_tess:.1f}–{fmax_tess:.1f} Hz")
    print("===================\n")

    return fmin_raw, fmax_raw, float(fmin_tess), float(fmax_tess)
