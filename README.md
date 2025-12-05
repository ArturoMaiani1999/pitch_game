
# Welcome to The Pitch Game

The Pitch Game has one simple goal: **train your pitch awareness using real-time visual feedback**.  
As you sing, you’ll see your pitch traced on screen against a target melody. Watching your voice in motion makes tuning errors and interval jumps *obvious* in a way that pure listening often isn’t.

Someone with perfect pitch could score 100% immediately because they already know what each note sounds like. Most of us don’t. We improve by practicing intervals, learning their sound, and gradually building reliable pitch memory. This game is designed to make that practice clear, measurable, and fun.



## Environment setup

Create and activate a virtual environment first if you like, then install dependencies:

```bash
pip install git+https://git.aubio.org/aubio/aubio/
pip install matplotlib
pip install sounddevice
````

Notes:

* `aubio` provides YIN pitch detection.
* `sounddevice` accesses your microphone.
* `matplotlib` renders the real-time lane + your pitch trace.

---

## Running the prototype

From the project root:

```bash
python main.py
```

The flow is:

1. Calibration (find your comfortable vocal range)
2. Optional scale warm-up
3. Game starts: follow the green lane with your voice

Close the plot window or press Ctrl+C to stop.

---

## Next steps / roadmap

1. **Improve performance and parallelism**
   Pitch detection (YIN) and rendering should run independently so neither blocks the other. The goal is smoother visuals and lower latency.

2. **Upgrade melody generation**
   Current melodies are semi-random. We want a more musical generator: coherent phrases, controlled contour, sensible pauses, and style presets.

3. **Add a harmonizer / playback mode**
   After a level, replay the user’s sung melody on top of a pleasant accompaniment (e.g., piano or orchestral pad) so players can *hear* their performance musically, and be surprised by their own voice.

```
::contentReference[oaicite:0]{index=0}
```
