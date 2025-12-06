# pitch_game/song_gen/midi/arranger.py
import pretty_midi
from typing import List, Tuple, Optional

def events_to_pretty_midi(
    events: List[Tuple[float, Optional[int]]],
    bpm: float,
    program: int = 0,
    is_drum: bool = False,
    velocity: int = 90
) -> pretty_midi.PrettyMIDI:
    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    inst = pretty_midi.Instrument(program=program, is_drum=is_drum)

    sec_per_beat = 60.0 / bpm
    t = 0.0
    for dur_beats, note in events:
        dur_s = dur_beats * sec_per_beat
        if note is not None:
            n = pretty_midi.Note(
                velocity=velocity,
                pitch=int(note),
                start=t,
                end=t + dur_s
            )
            inst.notes.append(n)
        t += dur_s

    pm.instruments.append(inst)
    return pm

def chords_to_instrument(chords: List[List[int]], bpm: float, beats_per_chord: float, program=0, velocity=70):
    sec_per_beat = 60.0 / bpm
    inst = pretty_midi.Instrument(program=program)
    t = 0.0
    for chord in chords:
        dur_s = beats_per_chord * sec_per_beat
        for p in chord:
            inst.notes.append(pretty_midi.Note(
                velocity=velocity, pitch=int(p),
                start=t, end=t+dur_s
            ))
        t += dur_s
    return inst

def bass_from_chords(chords: List[List[int]], bpm: float, beats_per_chord: float, program=32, velocity=80):
    # root in lower octave
    sec_per_beat = 60.0 / bpm
    inst = pretty_midi.Instrument(program=program)
    t = 0.0
    for chord in chords:
        root = chord[0] - 12
        dur_s = beats_per_chord * sec_per_beat
        inst.notes.append(pretty_midi.Note(
            velocity=velocity, pitch=int(root),
            start=t, end=t+dur_s
        ))
        t += dur_s
    return inst

def simple_drums(total_beats: float, bpm: float):
    inst = pretty_midi.Instrument(program=0, is_drum=True)
    sec_per_beat = 60.0 / bpm

    # MIDI drum pitches: 36 kick, 38 snare, 42 hihat
    for b in range(int(total_beats)):
        t = b * sec_per_beat
        # kick on 1 and 3
        if b % 4 in (0,2):
            inst.notes.append(pretty_midi.Note(100, 36, t, t+0.05))
        # snare on 2 and 4
        if b % 4 in (1,3):
            inst.notes.append(pretty_midi.Note(95, 38, t, t+0.05))
        # hihat every beat
        inst.notes.append(pretty_midi.Note(60, 42, t, t+0.03))
    return inst

def build_target_and_template_midis(
    melody_events,
    chords_by_section,
    bpm,
    time_sig=(4,4)
):
    # Target midi: melody only
    target_pm = events_to_pretty_midi(melody_events, bpm, program=54, velocity=95)

    # Template midi: melody + harmony + bass + drums
    template_pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)

    # Add melody
    mel_inst = events_to_pretty_midi(melody_events, bpm, program=54).instruments[0]
    template_pm.instruments.append(mel_inst)

    beats_per_bar = time_sig[0]

    # chords_by_section is list of (section_name, chords, beats)
    all_chords = []
    total_beats = 0.0
    for _, chords, sec_beats in chords_by_section:
        all_chords.extend(chords)
        total_beats += sec_beats

    beats_per_chord = beats_per_bar  # one chord per bar

    template_pm.instruments.append(
        chords_to_instrument(all_chords, bpm, beats_per_chord, program=0, velocity=60)
    )
    template_pm.instruments.append(
        bass_from_chords(all_chords, bpm, beats_per_chord, program=32, velocity=80)
    )
    template_pm.instruments.append(
        simple_drums(total_beats, bpm)
    )

    return target_pm, template_pm
