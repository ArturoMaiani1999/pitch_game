# pitch_game/song_gen/theory/harmony.py
import random
from typing import List, Dict, Tuple

# scale degrees in Ionian/C major style:
DEGREE_TO_OFFSET = {
    "I": 0,
    "ii": 2,
    "iii": 4,
    "IV": 5,
    "V": 7,
    "vi": 9,
    "vii0": 11,
}

# triad quality for pop (major/minor only)
TRIADS = {
    "I":  [0, 4, 7],
    "ii": [0, 3, 7],
    "iii":[0, 3, 7],
    "IV": [0, 4, 7],
    "V":  [0, 4, 7],
    "vi": [0, 3, 7],
}

def pick_progression(section_name: str, prog_bank: Dict[str, List[List[str]]]) -> List[str]:
    return random.choice(prog_bank[section_name])

def progression_to_chords(prog: List[str], tonic_midi: int) -> List[List[int]]:
    """
    Map roman numerals to MIDI triads near tonic.
    """
    chords = []
    for rn in prog:
        degree_offset = DEGREE_TO_OFFSET[rn]
        triad = TRIADS[rn]
        root = tonic_midi + degree_offset
        chord = [root + t for t in triad]
        chords.append(chord)
    return chords

def chords_for_section(section_name: str, tonic_midi: int, prog_bank) -> List[List[int]]:
    prog = pick_progression(section_name, prog_bank)
    return progression_to_chords(prog, tonic_midi), prog
