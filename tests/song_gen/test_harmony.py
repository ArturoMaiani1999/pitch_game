from pitch_game.song_gen.theory.harmony import progression_to_chords
from pitch_game.game.utils_music import midi_to_name

def test_chords_are_triadic():
    tonic = 48  # C3
    prog = ["I","V","vi","IV"]
    chords = progression_to_chords(prog, tonic)
    for ch in chords:
        assert len(ch) == 3
        assert ch[0] < ch[1] < ch[2]

def test_chords_in_key_c_major():
    tonic = 48
    prog = ["I","V","vi","IV"]
    chords = progression_to_chords(prog, tonic)
    allowed_pc = {0,2,4,5,7,9,11}  # ionian
    for ch in chords:
        for n in ch:
            assert (n-tonic) % 12 in allowed_pc, f"{midi_to_name(n)} out of key"
