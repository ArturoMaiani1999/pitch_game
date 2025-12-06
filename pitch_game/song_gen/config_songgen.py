# pitch_game/song_gen/config_songgen.py

# --- Global song defaults ---
DEFAULT_BPM_RANGE = (80, 105)
TIME_SIGNATURE = (4, 4)

# Form: number of bars per section
FORM_BARS = {
    "intro": 4,
    "verse": 8,
    "chorus": 8,
    "outro": 4,
}

FORM_SEQUENCE = ["intro", "verse", "chorus", "verse", "chorus", "outro"]

# --- Pop harmony templates (Roman numerals relative to tonic) ---
# We'll map these to scale degrees later.
PROGRESSIONS = {
    "intro":  [
        ["I", "V", "vi", "IV"],
        ["I", "IV", "V", "I"],
    ],
    "verse": [
        ["I", "V", "vi", "IV"],   # classic pop
        ["vi", "IV", "I", "V"],   # axis progression
        ["I", "vi", "IV", "V"],
    ],
    "chorus": [
        ["vi", "IV", "I", "V"],
        ["I", "V", "IV", "V"],
        ["I", "IV", "vi", "V"],
    ],
    "outro": [
        ["I", "V", "vi", "IV"],
        ["I", "IV", "I", "V"],
    ]
}

# --- Melody style knobs ---
REST_PROB = 0.10              # probability of rest at eligible positions
STEPWISE_BIAS = 1.6           # weight multiplier for stepwise motion
CHORD_TONE_BIAS = 1.8         # weight multiplier for chord tones on strong beats
PASSING_TONE_PROB = 0.25      # allow non-chord diatonic tone on weak beats

# For debugging: allow old random generator
ALLOW_RANDOM_DEBUG = True
