from pitch_game.song_gen.theory.form import build_form, form_to_beat_timeline
from pitch_game.song_gen.config_songgen import FORM_SEQUENCE, FORM_BARS, TIME_SIGNATURE

def test_form_total_beats():
    form = build_form(FORM_SEQUENCE, FORM_BARS, TIME_SIGNATURE)
    timeline = form_to_beat_timeline(form, TIME_SIGNATURE)

    beats_per_bar = TIME_SIGNATURE[0]
    expected = sum(FORM_BARS[s]*beats_per_bar for s in FORM_SEQUENCE)
    got = timeline[-1][2]
    assert got == expected
