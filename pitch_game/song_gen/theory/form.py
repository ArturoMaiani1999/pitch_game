# pitch_game/song_gen/theory/form.py
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Section:
    name: str
    bars: int

def build_form(sequence: List[str], bars_map: dict, time_sig=(4,4)) -> List[Section]:
    return [Section(name=s, bars=bars_map[s]) for s in sequence]

def form_to_beat_timeline(form: List[Section], time_sig=(4,4)) -> List[Tuple[str, float, float]]:
    """
    Returns list of (section_name, start_beat, end_beat)
    """
    beats_per_bar = time_sig[0]
    t = 0.0
    out = []
    for sec in form:
        start = t
        end = t + sec.bars * beats_per_bar
        out.append((sec.name, start, end))
        t = end
    return out
