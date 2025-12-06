# pitch_game/song_gen/ai/render_backing.py
"""
Minimal interface to render a backing track with chord conditioning.

Assumes you have MusicGen / MusicGen-Chord installed.
We keep it offline: takes chords + prompt + bpm, outputs wav + meta.
"""

import json
from pathlib import Path
from typing import List, Optional

import numpy as np

# --- OPTIONAL: audiocraft / musicgen-chord ---
# If you use Meta AudioCraft + chord-conditioned fork:
# pip install audiocraft
try:
    from audiocraft.models import MusicGen
    from audiocraft.data.audio import audio_write
except Exception:
    MusicGen = None
    audio_write = None


def chords_to_prompt(chords_by_section: List, tonic_name="C"):
    """
    chords_by_section is what generate_pop_song returns:
      [(sec_name, chords, sec_beats), ...]
    chords = list of chord midi lists, e.g. [[48,52,55], [55,59,62], ...]
    We'll convert to coarse text: "C:maj | G:maj | Am | F:maj ..."
    Super naive name mapping for now, good enough for conditioning.
    """
    NOTE_NAMES = ["C","C#","D","Eb","E","F","F#","G","Ab","A","Bb","B"]

    def chord_name(midi_notes):
        if not midi_notes:
            return "N"
        pcs = sorted({m % 12 for m in midi_notes})
        root = pcs[0]
        # detect triad quality in rough way
        # (root, third, fifth)
        intervals = sorted(((p - root) % 12 for p in pcs))
        quality = ""
        if intervals[:3] == [0, 4, 7]:
            quality = "maj"
        elif intervals[:3] == [0, 3, 7]:
            quality = "min"
        elif intervals[:3] == [0, 3, 6]:
            quality = "dim"
        else:
            quality = "triad"
        return f"{NOTE_NAMES[root]}:{quality}"

    chunks = []
    for sec_name, chords, _sec_beats in chords_by_section:
        sec_str = " | ".join(chord_name(c) for c in chords)
        chunks.append(f"{sec_name}: {sec_str}")

    return " ; ".join(chunks)


def render_backing_musicgen_chord(
    chords_by_section: List,
    out_wav_path: str,
    bpm: int,
    duration_sec: float = 120.0,
    style_prompt: str = "pop backing track, clean drums, warm pad, no vocals",
    model_name: str = "facebook/musicgen-melody",
    device: str = "cpu",
    seed: Optional[int] = None,
):
    """
    Renders backing wav using chord-conditioning prompt.

    out_wav_path: full path to write .wav (no extension needed; audio_write adds it)
    chords_by_section: from generate_pop_song()
    """

    if MusicGen is None:
        raise ImportError(
            "audiocraft not installed. Run: pip install audiocraft"
        )

    out_wav_path = Path(out_wav_path)
    out_wav_path.parent.mkdir(parents=True, exist_ok=True)

    chord_prompt = chords_to_prompt(chords_by_section)

    full_prompt = (
        f"{style_prompt}. "
        f"Tempo {bpm} bpm. "
        f"Chord progression: {chord_prompt}."
    )

    if seed is not None:
        np.random.seed(seed)

    model = MusicGen.get_pretrained(model_name, device=device)
    model.set_generation_params(
        duration=duration_sec,
        top_k=250,
        temperature=1.0,
        cfg_coef=3.0
    )

    wavs = model.generate([full_prompt])
    wav = wavs[0].cpu()

    # audiocraft helper writes wav properly
    audio_write(
        str(out_wav_path.with_suffix("")),
        wav,
        model.sample_rate,
        strategy="loudness",
        loudness_compressor=True
    )

    meta = {
        "bpm": bpm,
        "duration_sec": duration_sec,
        "style_prompt": style_prompt,
        "chord_prompt": chord_prompt,
        "full_prompt": full_prompt,
        "model_name": model_name,
        "seed": seed,
    }

    meta_path = out_wav_path.with_suffix(".json")
    meta_path.write_text(json.dumps(meta, indent=2))

    return str(out_wav_path.with_suffix(".wav")), str(meta_path)
