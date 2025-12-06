# pitch_game/song_gen/midi/exporter.py
import os

def save_pretty_midi(pm, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pm.write(path)
