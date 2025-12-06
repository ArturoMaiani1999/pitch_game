# pitch_game/tools/test_ai_backing_render.py
"""
End-to-end test:
1) generate pop song target+template MIDI
2) save template.mid
3) render AI backing from chords
"""

from pathlib import Path

from pitch_game.song_gen.generator import generate_pop_song
from pitch_game.song_gen.midi.arranger import build_target_and_template_midis
from pitch_game.song_gen.midi.exporter import save_pretty_midi
from pitch_game.song_gen.ai.render_backing import render_backing_musicgen_chord


def main():
    out_dir = Path("pitch_game/assets/songs/_ai_test")
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- 1) Generate pop song (symbolic) ---
    events, chords_by_section, bpm, midi_min, midi_max, tonic = generate_pop_song(
        fmin_hz=110, fmax_hz=300,
        tonic_name="C",
        max_jump_semitones=4,
        min_note_beats=2.0,
        seed=0
    )
    print(f"Generated pop song @ {bpm} bpm, tonic MIDI={tonic}")

    # --- 2) Export midis ---
    target_pm, template_pm = build_target_and_template_midis(events, chords_by_section, bpm)
    target_mid = out_dir / "target.mid"
    template_mid = out_dir / "template.mid"

    save_pretty_midi(target_pm, str(target_mid))
    save_pretty_midi(template_pm, str(template_mid))
    print("Saved:", target_mid, template_mid)

    # --- 3) Render backing wav from chords ---
    backing_wav, backing_meta = render_backing_musicgen_chord(
        chords_by_section=chords_by_section,
        out_wav_path=str(out_dir / "backing.wav"),
        bpm=bpm,
        duration_sec=120.0,
        style_prompt="instrumental pop backing track, light drums, warm pad, bassline, no vocals",
        model_name="facebook/musicgen-melody",  # replace with chord-fork checkpoint if you have one
        device="cpu",  # "cuda" if you have GPU
        seed=0
    )

    print("Back­ing rendered to:", backing_wav)
    print("Meta saved to:", backing_meta)
    print("DONE. Play backing.wav while matching target.mid!")


if __name__ == "__main__":
    main()
