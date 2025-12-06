# pitch_game/song_gen/theory/melody.py
import random
import math
from typing import List, Tuple, Optional

from pitch_game.game.utils_music import hz_to_midi, midi_to_hz

NOTE_OFFSETS_IONIAN = [0, 2, 4, 5, 7, 9, 11]


def build_allowed_scale(tonic_midi, midi_min, midi_max, mode_offsets=NOTE_OFFSETS_IONIAN):
    return [
        m for m in range(midi_min, midi_max + 1)
        if (m - tonic_midi) % 12 in mode_offsets
    ]


def weighted_choice(cands, weights):
    s = sum(weights)
    r = random.random() * s
    a = 0.0
    for c, w in zip(cands, weights):
        a += w
        if r <= a:
            return c
    return cands[-1]


# -----------------------------
# Enforce minimum note hold
# -----------------------------
def enforce_min_note_beats(events, min_note_beats):
    if min_note_beats <= 0:
        return events

    out = []
    pending_note = None
    pending_dur = 0.0

    def flush():
        nonlocal pending_note, pending_dur
        if pending_note is not None and pending_dur > 0:
            out.append((pending_dur, pending_note))
        pending_note, pending_dur = None, 0.0

    for dur, note in events:
        if note is None:
            flush()
            out.append((dur, None))
            continue

        if pending_note is None:
            pending_note, pending_dur = note, dur
        else:
            if pending_dur < min_note_beats:
                pending_dur += dur
            else:
                flush()
                pending_note, pending_dur = note, dur

    flush()

    merged = []
    for dur, note in out:
        if note is not None and merged and merged[-1][1] == note:
            merged[-1] = (merged[-1][0] + dur, note)
        else:
            merged.append((dur, note))

    return merged


# -----------------------------
# Enforce max jump AFTER merges
# -----------------------------
def enforce_max_jump(events, max_jump_semitones):
    if max_jump_semitones <= 0:
        return events

    out = []
    last_note = None

    for dur, note in events:
        if note is None:
            out.append((dur, None))
            continue

        if last_note is None:
            out.append((dur, note))
            last_note = note
            continue

        jump = note - last_note
        if abs(jump) <= max_jump_semitones:
            out.append((dur, note))
            last_note = note
        else:
            # clamp to maximum allowed jump
            step = 1 if jump > 0 else -1
            clamped = last_note + step * max_jump_semitones
            out.append((dur, clamped))
            last_note = clamped

    return out


def generate_section_melody(
    section_beats: int,
    chords: List[List[int]],
    tonic_midi: int,
    midi_min: int,
    midi_max: int,
    max_jump_semitones: int,
    min_note_beats: float,
    rest_prob: float,
    stepwise_bias: float,
    chord_tone_bias: float,
    passing_tone_prob: float,
) -> List[Tuple[float, Optional[int]]]:
    """
    Returns events [(dur_beats, midi_note_or_None)]
    Duration quantized to simple pop rhythms.
    """
    allowed = build_allowed_scale(tonic_midi, midi_min, midi_max)

    # start near tonic but NOT forced
    start = min(allowed, key=lambda m: abs(m - tonic_midi))
    cur_midi = start

    bar_templates = [
        [1, 1, 1, 1],
        [2, 1, 1],
        [1, 1, 2],
        [1, 0.5, 0.5, 1, 1],
        [1, 1, 0.5, 0.5, 1],
    ]

    events = []
    beats_done = 0.0
    chord_len = section_beats / len(chords)

    while beats_done < section_beats - 1e-6:
        remaining = section_beats - beats_done
        template = random.choice(bar_templates)
        if sum(template) > remaining + 1e-6:
            template = [1] * int(round(remaining))

        chord_i = min(int(beats_done / chord_len), len(chords) - 1)
        chord = chords[chord_i]
        chord_tones = set(chord)

        for dur in template:
            if beats_done >= section_beats - 1e-6:
                break

            strong = (beats_done % 4) in (0, 2)

            if (not strong) and random.random() < rest_prob:
                events.append((dur, None))
                beats_done += dur
                continue

            cands, weights = [], []
            for note in allowed:
                jump = abs(note - cur_midi)
                if jump == 0 or jump > max_jump_semitones:
                    continue

                w = 1.0

                if jump <= 2:
                    w *= stepwise_bias

                if strong and note in chord_tones:
                    w *= chord_tone_bias
                elif (not strong) and (note not in chord_tones):
                    if random.random() > passing_tone_prob:
                        continue

                dist_center = abs(note - (midi_min + midi_max) / 2)
                w *= 1.0 / (1.0 + 0.03 * dist_center**2)

                cands.append(note)
                weights.append(w)

            if not cands:
                cands = [cur_midi]
                weights = [1.0]

            nxt = weighted_choice(cands, weights)
            events.append((dur, nxt))
            cur_midi = nxt
            beats_done += dur

    # 1) enforce min hold by tying short notes
    events = enforce_min_note_beats(events, min_note_beats)

    # 2) enforce max jump AFTER merges
    events = enforce_max_jump(events, max_jump_semitones)

    return events
