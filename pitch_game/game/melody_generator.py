# melody_generator.py
import random
import math
from pitch_game.game.utils_music import hz_to_midi, midi_to_hz

MODES = {
    "ionian":  [0,2,4,5,7,9,11],
    "dorian":  [0,2,3,5,7,9,10],
    "aeolian": [0,2,3,5,7,8,10],
    "mixolydian": [0,2,4,5,7,9,10],
}

NOTE_TO_PC = {
    "C":0, "C#":1, "DB":1,
    "D":2, "D#":3, "EB":3,
    "E":4,
    "F":5, "F#":6, "GB":6,
    "G":7, "G#":8, "AB":8,
    "A":9, "A#":10, "BB":10,
    "B":11
}

def pick_tonic_in_range(tonic_name, midi_min, midi_max):
    """
    Pick the octave of tonic_name (pitch class) that is closest
    to the center of [midi_min, midi_max].
    """
    pc = NOTE_TO_PC[tonic_name.upper()]
    center = 0.5 * (midi_min + midi_max)

    # generate all possible tonics in range
    candidates = []
    for m in range(midi_min, midi_max + 1):
        if m % 12 == pc:
            candidates.append(m)

    if not candidates:
        # fallback: just snap center to pitch class
        snapped = int(round(center))
        return snapped - (snapped % 12) + pc

    return min(candidates, key=lambda m: abs(m - center))




def build_allowed_scale(tonic_midi, mode_offsets, midi_min, midi_max):
    return [
        m for m in range(midi_min, midi_max + 1)
        if (m - tonic_midi) % 12 in mode_offsets
    ]

def weighted_choice(items, weights):
    s = sum(weights)
    r = random.random() * s
    acc = 0.0
    for it, w in zip(items, weights):
        acc += w
        if r <= acc:
            return it
    return items[-1]

# -----------------------------
# Enforce minimum note hold
# -----------------------------
def enforce_min_note_beats(events, min_note_beats=1.0):
    """
    Ensures each voiced segment lasts at least min_note_beats.
    Short voiced notes get tied to the previous voiced pitch.
    Rests are kept as-is.
    """
    if min_note_beats <= 0:
        return events

    out = []
    pending_note = None
    pending_dur = 0.0

    def flush_pending():
        nonlocal pending_note, pending_dur
        if pending_note is not None and pending_dur > 0:
            out.append((pending_dur, pending_note))
        pending_note, pending_dur = None, 0.0

    for dur, note in events:
        if note is None:
            flush_pending()
            out.append((dur, None))
            continue

        if pending_note is None:
            pending_note = note
            pending_dur = dur
        else:
            if pending_dur < min_note_beats:
                # too short -> tie into previous pitch
                pending_dur += dur
            else:
                flush_pending()
                pending_note = note
                pending_dur = dur

    flush_pending()

    # merge consecutive identical notes
    merged = []
    for dur, note in out:
        if note is not None and merged and merged[-1][1] == note:
            merged[-1] = (merged[-1][0] + dur, note)
        else:
            merged.append((dur, note))

    return merged

# -----------------------------
# Generator A
# -----------------------------
def generator_A(
    tonic_midi,
    mode_offsets,
    midi_min,
    midi_max,
    bpm=100,
    phrases=4,
    phrase_beats_choices=(8,12,16),
    rest_prob_inside=0.08,
    max_jump_semitones=5,   # <-- NEW input (difficulty knob)
    min_note_beats=1.0      # <-- NEW input (difficulty knob)
):
    allowed = build_allowed_scale(tonic_midi, mode_offsets, midi_min, midi_max)
    idx_by_midi = {m:i for i,m in enumerate(allowed)}

    start = min(allowed, key=lambda m: abs(m - tonic_midi))
    cur_idx = idx_by_midi[start]
    cur_midi = allowed[cur_idx]

    # center of tessitura
    fmin_hz = float(midi_to_hz(midi_min))
    fmax_hz = float(midi_to_hz(midi_max))
    f_center = math.sqrt(fmin_hz * fmax_hz)
    center_midi = float(hz_to_midi(f_center))

    events = []
    stable_mod12 = {0,4,7}
    bar_templates = [
        [1,1,1,1],
        [2,1,1],
        [1,1,2],
        [1,0.5,0.5,1,1],
        [1,1,0.5,0.5,1],
    ]

        # ---- FORCE START ON TONIC ----
    # Ensure first voiced note is tonic (closest tonic in allowed)
    tonic_start = min(allowed, key=lambda m: abs(m - tonic_midi))
    cur_midi = tonic_start
    cur_idx = idx_by_midi[cur_midi]

    # Put a first note of 1 beat on tonic (no rest before it)
    events.append((1.0, cur_midi))


    for _ in range(phrases):
        phrase_beats = random.choice(phrase_beats_choices)
        contour_target = max(0, min(cur_idx + random.choice([2,3,4]), len(allowed)-1))

        beats_done = 0.0

        while beats_done < phrase_beats - 1e-6:
            remaining = phrase_beats - beats_done
            template = random.choice(bar_templates)
            if sum(template) > remaining + 1e-6:
                template = [1] * int(round(remaining))

            for dur in template:
                if beats_done >= phrase_beats - 1e-6:
                    break

                if random.random() < rest_prob_inside:
                    events.append((dur, None))
                    beats_done += dur
                    continue

                halfway = phrase_beats / 2
                toward = beats_done < halfway

                candidates, weights = [], []
                for ni, note in enumerate(allowed):
                    # HARD max jump in semitones
                    if abs(note - cur_midi) > max_jump_semitones:
                        continue

                    jump = abs(note - cur_midi)
                    if jump == 0:
                        continue
                    if jump == 1: w_jump = 0.55
                    elif jump == 2: w_jump = 0.25
                    elif jump == 3: w_jump = 0.12
                    elif jump == 4: w_jump = 0.07
                    elif jump == 5: w_jump = 0.04
                    else: w_jump = 0.02

                    semitone_from_tonic = (note - tonic_midi) % 12

                    # contour bias
                    contour_factor = 1.0
                    if toward:
                        if abs(contour_target - ni) < abs(contour_target - cur_idx):
                            contour_factor = 1.6
                    else:
                        if abs(tonic_midi - note) < abs(tonic_midi - cur_midi):
                            contour_factor = 1.6

                    # tonal gravity on strong beats
                    strong = (beats_done % 4) in (0,2)
                    gravity = 1.0
                    if strong and semitone_from_tonic in stable_mod12:
                        gravity *= 1.25
                    if semitone_from_tonic == 0:
                        gravity *= 1.2

                    # center bias (keeps melody in middle)
                    dist_center = abs(note - center_midi)
                    center_factor = 1.0 / (1.0 + 0.08 * dist_center**2)

                    candidates.append(ni)
                    weights.append(w_jump * contour_factor * gravity * center_factor)

                if not candidates:
                    candidates = [cur_idx]
                    weights = [1.0]

                cur_idx = weighted_choice(candidates, weights)
                cur_midi = allowed[cur_idx]
                events.append((dur, cur_midi))
                beats_done += dur

        # cadence overwrite last ~2 beats
        cadence = random.choice([
            [(1, tonic_midi + mode_offsets[1]), (1, tonic_midi)],
            [(1, tonic_midi + 7), (1, tonic_midi)],
        ])

        beats_removed = 0.0
        while beats_removed < 2.0 and events:
            dur, _ = events.pop()
            beats_removed += dur

        for dur, note in cadence:
            while note < midi_min: note += 12
            while note > midi_max: note -= 12
            if abs(note - cur_midi) > max_jump_semitones:
                step = 1 if note > cur_midi else -1
                note = cur_midi + step * min(max_jump_semitones, abs(note - cur_midi))
            cur_midi = note
            events.append((dur, note))

        events.append((random.choice([1,2]), None))

    # post-process minimum hold
    events = enforce_min_note_beats(events, min_note_beats=min_note_beats)
    return events, bpm

def generate_melody_for_range(
    mode_name,
    fmin_hz,
    fmax_hz,
    bpm=100,
    phrases=4,
    min_note_beats=1.0,
    max_jump_semitones=5,
    tonic_name=None,          # NEW
    force_tonic_key=False     # NEW
):
    mode_offsets = MODES[mode_name]

    midi_min = int(math.floor(hz_to_midi(fmin_hz)))
    midi_max = int(math.ceil(hz_to_midi(fmax_hz)))

    # center-based default tonic
    f_center = math.sqrt(fmin_hz * fmax_hz)
    tonic_guess = int(round(hz_to_midi(f_center)))

    # NEW: override tonic by config key if requested
    if force_tonic_key and tonic_name is not None:
        tonic_midi = pick_tonic_in_range(tonic_name, midi_min, midi_max)
    else:
        tonic_midi = tonic_guess

    events, bpm = generator_A(
        tonic_midi, mode_offsets,
        midi_min, midi_max,
        bpm=bpm, phrases=phrases,
        min_note_beats=min_note_beats,
        max_jump_semitones=max_jump_semitones
    )
    return events, bpm, midi_min, midi_max, tonic_midi
