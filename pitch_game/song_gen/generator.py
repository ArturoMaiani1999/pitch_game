# pitch_game/song_gen/generator.py
import random
import math
from typing import Optional, Tuple, List

from pitch_game.game.utils_music import hz_to_midi

from pitch_game.song_gen.config_songgen import (
    DEFAULT_BPM_RANGE, TIME_SIGNATURE,
    FORM_SEQUENCE, FORM_BARS, PROGRESSIONS,
    REST_PROB, STEPWISE_BIAS, CHORD_TONE_BIAS, PASSING_TONE_PROB,
    ALLOW_RANDOM_DEBUG
)

from pitch_game.song_gen.theory.form import build_form, form_to_beat_timeline
from pitch_game.song_gen.theory.harmony import chords_for_section
from pitch_game.song_gen.theory.melody import generate_section_melody
from pitch_game.song_gen.midi.arranger import build_target_and_template_midis
from pitch_game.song_gen.midi.exporter import save_pretty_midi
from pitch_game.song_gen.theory.melody import enforce_max_jump


# Random/debug backend
from pitch_game.game.melody_generator import generate_melody_for_range as random_backend

def pick_tonic_in_range(tonic_pc_name: str, midi_min: int, midi_max: int):
    NOTE_TO_PC = {
        "C":0, "C#":1, "DB":1,
        "D":2, "D#":3, "EB":3,
        "E":4,
        "F":5, "F#":6, "GB":6,
        "G":7, "G#":8, "AB":8,
        "A":9, "A#":10, "BB":10,
        "B":11
    }
    pc = NOTE_TO_PC[tonic_pc_name.upper()]
    center = 0.5 * (midi_min + midi_max)
    candidates = [m for m in range(midi_min, midi_max+1) if m % 12 == pc]
    if not candidates:
        snapped = int(round(center))
        return snapped - (snapped % 12) + pc
    return min(candidates, key=lambda m: abs(m-center))

def generate_pop_song(
    fmin_hz: float,
    fmax_hz: float,
    tonic_name="C",
    bpm: Optional[int]=None,
    max_jump_semitones=4,
    min_note_beats=2.0,
    seed=None,
):
    if seed is not None:
        random.seed(seed)

    midi_min = int(math.floor(hz_to_midi(fmin_hz)))
    midi_max = int(math.ceil(hz_to_midi(fmax_hz)))

    tonic_midi = pick_tonic_in_range(tonic_name, midi_min, midi_max)

    if bpm is None:
        bpm = random.randint(*DEFAULT_BPM_RANGE)

    # build form
    form = build_form(FORM_SEQUENCE, FORM_BARS, TIME_SIGNATURE)
    timeline = form_to_beat_timeline(form, TIME_SIGNATURE)

    melody_events = []
    chords_by_section = []

    for sec_name, start_b, end_b in timeline:
        sec_beats = end_b - start_b

        chords, progression = chords_for_section(sec_name, tonic_midi, PROGRESSIONS)

        sec_events = generate_section_melody(
            section_beats=int(sec_beats),
            chords=chords,
            tonic_midi=tonic_midi,
            midi_min=midi_min,
            midi_max=midi_max,
            max_jump_semitones=max_jump_semitones,
            min_note_beats=min_note_beats,
            rest_prob=REST_PROB,
            stepwise_bias=STEPWISE_BIAS,
            chord_tone_bias=CHORD_TONE_BIAS,
            passing_tone_prob=PASSING_TONE_PROB,
        )

        melody_events.extend(sec_events)
        chords_by_section.append((sec_name, chords, sec_beats))

    # ✅ GLOBAL safety net across section boundaries
    melody_events = enforce_max_jump(melody_events, max_jump_semitones)

    return melody_events, chords_by_section, bpm, midi_min, midi_max, tonic_midi



def generate_song_bundle(
    out_dir: str,
    fmin_hz: float,
    fmax_hz: float,
    tonic_name="C",
    backend="pop",
    mode_name="ionian",   # only used for random backend
    bpm=None,
    phrases=4,            # random backend
    min_note_beats=2.0,
    max_jump_semitones=4,
    seed=None
):
    """
    Creates target.mid + template.mid in out_dir.
    backend:
      - "pop": new structured generator
      - "random": your old generator (debug)
    """
    if backend == "random":
        if not ALLOW_RANDOM_DEBUG:
            raise ValueError("Random backend disabled in config_songgen.py")
        events, bpm2, midi_min, midi_max, tonic_midi = random_backend(
            mode_name, fmin_hz, fmax_hz,
            bpm=bpm or 90,
            phrases=phrases,
            min_note_beats=min_note_beats,
            max_jump_semitones=max_jump_semitones,
            tonic_name=tonic_name,
            force_tonic_key=True
        )
        chords_by_section = []  # none for debug
        bpm = bpm2
    else:
        events, chords_by_section, bpm, midi_min, midi_max, tonic_midi = generate_pop_song(
            fmin_hz, fmax_hz, tonic_name=tonic_name,
            bpm=bpm,
            max_jump_semitones=max_jump_semitones,
            min_note_beats=min_note_beats,
            seed=seed
        )

    # export midis
    target_pm, template_pm = build_target_and_template_midis(
        events, chords_by_section, bpm
    )
    save_pretty_midi(target_pm, f"{out_dir}/target.mid")
    save_pretty_midi(template_pm, f"{out_dir}/template.mid")

    meta = {
        "bpm": bpm,
        "tonic_midi": tonic_midi,
        "midi_range": [midi_min, midi_max],
        "backend": backend
    }
    return meta
