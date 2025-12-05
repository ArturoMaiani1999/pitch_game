

# audio_pitch.py
import numpy as np
import sounddevice as sd
import aubio
import threading
import queue
from config import SR, HOP_SIZE, WIN_SIZE, PITCH_METHOD, SILENCE_DB, TOLERANCE, CONF_THRESH

class PitchStream:
    def __init__(self):
        # aubio pitch object (used ONLY in worker thread)
        self.pitch_o = aubio.pitch(PITCH_METHOD, WIN_SIZE, HOP_SIZE, SR)
        self.pitch_o.set_unit("Hz")
        self.pitch_o.set_silence(SILENCE_DB)
        self.pitch_o.set_tolerance(TOLERANCE)

        # thread-safe latest pitch
        self._latest_hz = np.nan
        self._latest_conf = 0.0
        self._lock = threading.Lock()

        # hop queue from audio -> worker
        self._q = queue.Queue(maxsize=8)  # small to avoid latency buildup
        self._stop = threading.Event()
        self._worker = None
        self._stream = None

    # ---------- public properties ----------
    @property
    def latest_hz(self):
        with self._lock:
            return float(self._latest_hz)

    @property
    def latest_conf(self):
        with self._lock:
            return float(self._latest_conf)

    # ---------- audio callback ----------
    def _callback(self, indata, frames, time_info, status):
        if status:
            # don't print too much in RT thread
            pass

        hop = indata[:, 0].copy()  # copy so buffer isn't reused
        try:
            self._q.put_nowait(hop)
        except queue.Full:
            # drop hop if worker is behind (keeps latency bounded)
            pass

    # ---------- pitch worker thread ----------
    def _worker_loop(self):
        while not self._stop.is_set():
            try:
                hop = self._q.get(timeout=0.1)
            except queue.Empty:
                continue

            hop = hop.astype(np.float32)
            f0 = float(self.pitch_o(hop)[0])
            conf = float(self.pitch_o.get_confidence())

            if conf >= CONF_THRESH and 20.0 < f0 < 2000.0:
                with self._lock:
                    self._latest_hz = f0
                    self._latest_conf = conf
            else:
                with self._lock:
                    self._latest_hz = np.nan
                    self._latest_conf = conf

    # ---------- context manager ----------
    def open_stream(self):
        """
        Use as:  with pitch_stream.open_stream():
        """
        class _Ctx:
            def __init__(_self, ps): _self.ps = ps
            def __enter__(_self):
                ps = _self.ps
                ps._stop.clear()
                ps._worker = threading.Thread(target=ps._worker_loop, daemon=True)
                ps._worker.start()

                ps._stream = sd.InputStream(
                    channels=1,
                    callback=ps._callback,
                    samplerate=SR,
                    blocksize=HOP_SIZE,
                )
                ps._stream.start()
                return ps

            def __exit__(_self, exc_type, exc, tb):
                ps = _self.ps
                ps._stop.set()
                if ps._stream:
                    ps._stream.stop()
                    ps._stream.close()
                    ps._stream = None
                if ps._worker:
                    ps._worker.join(timeout=1.0)
                    ps._worker = None

        return _Ctx(self)
