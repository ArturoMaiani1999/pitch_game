import numpy as np
from pitch_game.song_gen.generator import generate_pop_song
from pitch_game.game.utils_music import midi_to_name

def test_melody_respects_max_jump():
    events, chords_by_section, bpm, midi_min, midi_max, tonic = generate_pop_song(
        fmin_hz=110, fmax_hz=300, tonic_name="C",
        max_jump_semitones=4, min_note_beats=2, seed=0
    )

    last = None
    for dur, note in events:
        if note is None: 
            continue
        if last is not None:
            assert abs(note-last) <= 4, f"jump {midi_to_name(last)}->{midi_to_name(note)}"
        last = note
