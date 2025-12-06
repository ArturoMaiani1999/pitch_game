# The Pitch Game

The Pitch Game has one simple goal: **train pitch awareness through real-time visual feedback**.

As you sing, your pitch is traced on a scrolling time-vs-note plot and compared to a target melody. Seeing your voice in motion makes tuning drift, unstable notes, and interval mistakes *immediately obvious*—often more clearly than listening alone.

Someone with perfect pitch could score 100% right away because they already know what every note sounds like. Most of us don’t. We improve by practicing intervals, learning their “feel,” and building reliable pitch memory over time. This game is designed to make that practice **clear, measurable, and fun**.


---

## Features (current prototype)

- Real-time pitch tracking from your laptop microphone (aubio YIN)
- Automatic vocal range calibration
- Log-spaced note axis with labeled pitches
- Target melody “lane” (green) and free space (blue)
- Look-ahead forecast of the next note / pause and interval
- Optional scale warm-up before the game starts


---

## Environment setup

Create and activate a virtual environment if you want, then install dependencies:

```bash
pip install git+https://git.aubio.org/aubio/aubio/
pip install matplotlib
pip install sounddevice
pip install pretty_midi mido
