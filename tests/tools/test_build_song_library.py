import os, json
import pytest
from pitch_game.tools.build_song_library import build_library

@pytest.mark.slow
def test_build_song_library(tmp_path):
    out_dir = tmp_path / "songs"
    build_library(out_dir=str(out_dir), n_songs=3, seed=0)

    folders = sorted(out_dir.iterdir())
    assert len(folders) == 3

    for f in folders:
        assert (f / "target.mid").exists()
        assert (f / "template.mid").exists()
        assert (f / "meta.json").exists()

        meta = json.loads((f/"meta.json").read_text())
        assert "bpm" in meta
        assert "midi_range" in meta
