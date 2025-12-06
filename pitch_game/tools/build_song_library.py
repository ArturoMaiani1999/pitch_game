# pitch_game/tools/build_song_library.py
import os, json
from pitch_game.song_gen.generator import generate_song_bundle

def build_library(out_dir, n_songs=10, seed=0, backend="pop"):
    os.makedirs(out_dir, exist_ok=True)
    for i in range(n_songs):
        song_dir = os.path.join(out_dir, f"song_{i:03d}")
        meta = generate_song_bundle(
            out_dir=song_dir,
            fmin_hz=110, fmax_hz=300,
            tonic_name="C",
            backend=backend,
            seed=seed+i
        )
        with open(os.path.join(song_dir, "meta.json"), "w") as f:
            json.dump(meta, f, indent=2)

if __name__ == "__main__":
    build_library(out_dir="pitch_game/assets/songs")
