# config.py

SR = 44100
HOP_SIZE = 512
WIN_SIZE = 4096

# Pitch detection
PITCH_METHOD = "yin"
SILENCE_DB = -60
TOLERANCE = 0.8
CONF_THRESH = 0.6

# Game / melody
DEFAULT_BPM = 70
MODE_NAME = "ionian"   # ionian, dorian, aeolian, mixolydian
PHRASES = 4
DY_SEMITONES = 0.5     # green lane half-width (semitones)

# NEW DIFFICULTY KNOBS
MIN_NOTE_BEATS = 2   # minimum hold duration (beats). Higher = easier.
MAX_JUMP_SEMITONES = 4 # max interval size in semitones. 5 = perfect 4th.

# Calibration
CALIB_SEC_PER_NOTE = 2.0
CALIB_REPEATS = 1
CALIB_PERCENTILE_LOW = 10
CALIB_PERCENTILE_HIGH = 90

# Renderer
WINDOW_SECONDS = 5.0
Y_STEP_SEMITONE = 0.1
ALPHA_GREEN = 0.25
ALPHA_BLUE = 0.06

LOOKAHEAD_SECONDS = 1   # how far ahead to show next target note


PLAY_SCALE_WARMUP = True   # turn off if you want
WARMUP_NOTE_BEATS = 0.2    # scale note length in beats
WARMUP_PAUSE_BEATS = 0.05  # pause between notes in beats
WARMUP_REPEATS = 1

TONIC_NAME = "C"      # pitch class: C, C#, D, Eb, E, F, F#, G, Ab, A, Bb, B
FORCE_TONIC_KEY = True  # if False, tonic is auto-chosen from tessitura center