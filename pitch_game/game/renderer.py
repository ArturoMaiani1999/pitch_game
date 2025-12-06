# renderer.py
import numpy as np
import matplotlib.pyplot as plt
import math

from game.utils_music import hz_to_midi, midi_to_name, cents_error
from game.config import (
    WINDOW_SECONDS, Y_STEP_SEMITONE,
    ALPHA_GREEN, ALPHA_BLUE,
    LOOKAHEAD_SECONDS, DY_SEMITONES
)

INTERVAL_NAMES = {
    1: "semitone",
    2: "tone",
    3: "minor third",
    4: "major third",
    5: "fourth",
    7: "fifth",
}

def interval_label(semitones_signed):
    if not np.isfinite(semitones_signed):
        return None
    direction = (
        "ascending" if semitones_signed > 0
        else "descending" if semitones_signed < 0
        else "unison"
    )
    st = int(round(abs(semitones_signed)))
    name = INTERVAL_NAMES.get(st, f"{st} semitones")
    return "unison" if direction == "unison" else f"{name} {direction}"


class GameRenderer:
    def __init__(self, fmin_plot, fmax_plot, dy_semitones):
        self.fmin_plot_hz = fmin_plot
        self.fmax_plot_hz = fmax_plot
        self.dy_semitones = dy_semitones
        self.window_seconds = WINDOW_SECONDS

        self.map_im = None
        self._t_target_full = None
        self._hz_target_full = None
        self._midi_target_full = None
        self._midi_target_q_full = None
        self._rgba_full = None
        self._y_bins_midi = None

        self._setup_axes()

    def _setup_axes(self):
        midi_min = float(hz_to_midi(self.fmin_plot_hz))
        midi_max = float(hz_to_midi(self.fmax_plot_hz))

        midi_ticks = list(range(int(math.floor(midi_min)), int(math.ceil(midi_max)) + 1))
        tick_labels = [midi_to_name(m) for m in midi_ticks]

        plt.ion()
        self.fig, self.ax = plt.subplots(figsize=(10, 6))

        (self.line_user,) = self.ax.plot([], [], lw=2, label="You", zorder=3)

        (self.line_target,) = self.ax.plot(
            [], [], lw=2, alpha=0.9, label="Target",
            drawstyle="steps-post", zorder=2
        )

        self.ax.set_title("Pitch Game — sing the green lane!")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Pitch (notes)")
        self.ax.set_ylim(midi_min, midi_max)
        self.ax.set_yticks(midi_ticks)
        self.ax.set_yticklabels(tick_labels)

        self.ax.set_xlim(-self.window_seconds, 0)
        self.ax.grid(True, which="major", axis="both", alpha=0.25, zorder=1)
        self.ax.legend(loc="lower left")

        self.score_text = self.ax.text(0.02, 0.95, "", transform=self.ax.transAxes, va="top")

        self.ax_right = self.ax.twinx()
        self.ax_right.set_ylim(self.ax.get_ylim())
        self.ax_right.set_yticks(midi_ticks)
        self.ax_right.set_yticklabels(tick_labels)
        self.ax_right.set_ylabel("Pitch (notes)")

        self.forecast_dot, = self.ax.plot(
            [0], [np.nan], marker="o", markersize=10, linestyle="None",
            color="green", alpha=0.9, label="_nolegend_", zorder=4
        )

        # pause rectangle (create once, toggle visibility only)
        self.pause_rect_width = 0.18
        self.pause_rect = self.ax.axvspan(
            -self.pause_rect_width, 0, color="red", alpha=0.18, zorder=1
        )
        self.pause_rect.set_visible(False)

        self.forecast_label = self.ax.text(
                0.98, 0.05, "", transform=self.ax.transAxes,
                ha="right", va="bottom"
            )


    def _sync_right_axis(self):
        y0, y1 = self.ax.get_ylim()
        self.ax_right.set_ylim(y0, y1)

        midi_ticks = list(range(int(math.floor(y0)), int(math.ceil(y1)) + 1))
        tick_labels = [midi_to_name(m) for m in midi_ticks]

        self.ax.set_yticks(midi_ticks)
        self.ax.set_yticklabels(tick_labels)
        self.ax_right.set_yticks(midi_ticks)
        self.ax_right.set_yticklabels(tick_labels)

    def make_map_rgba_midi(self, t_target, midi_target_q):
        midi_min = float(hz_to_midi(self.fmin_plot_hz))
        midi_max = float(hz_to_midi(self.fmax_plot_hz))

        y_bins_midi = np.arange(midi_min, midi_max + Y_STEP_SEMITONE, Y_STEP_SEMITONE)
        self._y_bins_midi = y_bins_midi

        T = len(t_target)
        Y = len(y_bins_midi)
        rgba = np.zeros((Y, T, 4), dtype=np.float32)

        # blue everywhere
        rgba[..., 2] = 1.0
        rgba[..., 3] = ALPHA_BLUE

        # green lane
        for k in range(T):
            m = midi_target_q[k]
            if not np.isfinite(m):
                continue
            mask = np.abs(y_bins_midi - m) <= self.dy_semitones
            rgba[mask, k, 0] = 0.0
            rgba[mask, k, 1] = 1.0
            rgba[mask, k, 2] = 0.0
            rgba[mask, k, 3] = ALPHA_GREEN

        return rgba

    def draw_background_map(self, t_target, hz_target):
        self._t_target_full = t_target
        self._hz_target_full = hz_target

        self._midi_target_full = hz_to_midi(hz_target)
        self._midi_target_q_full = np.where(
            np.isfinite(self._midi_target_full),
            np.round(self._midi_target_full),
            np.nan
        )

        voiced = self._midi_target_q_full[np.isfinite(self._midi_target_q_full)]
        if len(voiced) > 0:
            m_lo, m_hi = float(voiced.min()), float(voiced.max())
            pad = max(2.0 * DY_SEMITONES, 1.0)
            self.ax.set_ylim(m_lo - pad, m_hi + pad)
            self._sync_right_axis()

        self._rgba_full = self.make_map_rgba_midi(t_target, self._midi_target_q_full)

        self.map_im = self.ax.imshow(
            self._rgba_full[:, :1, :],
            origin="lower",
            aspect="auto",
            extent=[-self.window_seconds, 0, self._y_bins_midi[0], self._y_bins_midi[-1]],
            zorder=0
        )

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def _next_target_any(self, k_start, midi_target_q):
        if k_start >= len(midi_target_q):
            return None, np.nan
        return k_start, midi_target_q[k_start]

    def _current_target_midi(self, k_now):
        if self._midi_target_q_full is None:
            return np.nan
        k_now = min(max(k_now, 0), len(self._midi_target_q_full) - 1)

        if np.isfinite(self._midi_target_q_full[k_now]):
            return self._midi_target_q_full[k_now]

        for k in range(k_now, -1, -1):
            if np.isfinite(self._midi_target_q_full[k]):
                return self._midi_target_q_full[k]
        return np.nan

    def update(self, now, user_times, user_pitches_hz, t_target, hz_target, latest_pitch_hz):
        if len(user_times) < 2:
            return

        # user line
        p_arr_hz = np.array(user_pitches_hz)
        p_arr_midi = hz_to_midi(p_arr_hz)

        t_arr = np.array(user_times)
        t_rel = t_arr - t_arr[-1]
        self.line_user.set_data(t_rel, p_arr_midi)

        # target window indices
        dt = (t_target[1] - t_target[0]) if len(t_target) > 1 else 0.01
        t_win_start = max(0.0, now - self.window_seconds)
        i0 = int(t_win_start / dt)
        i1 = int(now / dt)

        i0 = max(0, min(i0, len(t_target) - 1))
        i1 = max(0, min(i1, len(t_target)))

        # target line
        t_t = t_target[i0:i1] - now
        midi_t_q = self._midi_target_q_full[i0:i1]
        self.line_target.set_data(t_t, midi_t_q)

        # background map update (skip empty slice)
        if self.map_im is not None and self._rgba_full is not None:
            if i1 > i0:
                rgba_win = self._rgba_full[:, i0:i1, :]
                x0 = self._t_target_full[i0] - now
                x1 = self._t_target_full[i1 - 1] - now
                self.map_im.set_data(rgba_win)
                self.map_im.set_extent([x0, x1, self._y_bins_midi[0], self._y_bins_midi[-1]])

        # scoring
        k_now = int(now / dt)
        target_now_hz = hz_target[k_now] if k_now < len(hz_target) else np.nan
        err = cents_error(latest_pitch_hz, target_now_hz)
        self.score_text.set_text(f"Error: {err:+.0f} cents" if np.isfinite(err) else "Error: —")

        # forecast
        k_look = int((now + LOOKAHEAD_SECONDS) / dt)
        k_next, midi_next_q = self._next_target_any(k_look, self._midi_target_q_full)

        if k_next is None:
            self.forecast_dot.set_data([0.0], [np.nan])
            self.forecast_dot.set_alpha(0.0)
            self.pause_rect.set_visible(False)
            self.forecast_label.set_text("")
        else:
            if np.isfinite(midi_next_q):
                self.pause_rect.set_visible(False)
                self.forecast_dot.set_data([0.0], [midi_next_q])
                self.forecast_dot.set_color("green")
                self.forecast_dot.set_alpha(0.9)

                midi_curr_q = self._current_target_midi(k_now)
                if np.isfinite(midi_curr_q):
                    semitones_signed = midi_next_q - midi_curr_q
                    int_lbl = interval_label(semitones_signed)
                    txt = f"Next: {midi_to_name(midi_next_q)}"
                    if int_lbl:
                        txt += f"  |  {int_lbl}"
                else:
                    txt = f"Next: {midi_to_name(midi_next_q)}"

                self.forecast_label.set_color("green")
                self.forecast_label.set_text(txt)

            else:
                self.forecast_dot.set_data([0.0], [np.nan])
                self.forecast_dot.set_alpha(0.0)
                self.pause_rect.set_visible(True)
                self.forecast_label.set_color("red")
                self.forecast_label.set_text("Next: pause")

        self.ax.set_xlim(-self.window_seconds, 0)

        # flicker-free repaint
        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

    def still_open(self):
        return plt.fignum_exists(self.fig.number)
