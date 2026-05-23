import tkinter as tk
import winsound
import math

WORK_TIME = 25 * 60
SHORT_BREAK = 5 * 60
LONG_BREAK = 15 * 60
LONG_BREAK_INTERVAL = 4

# Gold-on-black luxury palette
GOLD_BRIGHT = "#C8A96E"
GOLD_LIGHT  = "#D4BC8B"
GOLD_MED    = "#A89050"
GOLD_TRACK  = "#4A3822"
GOLD_INNER  = "#2A2018"
GOLD_TICK_S = "#1F1810"
GOLD_TICK_L = "#3A2A18"
GOLD_DOT_ON = "#C8A96E"
GOLD_DOT_OFF = "#2A2018"
GOLD_GLOW   = "#3A2A15"
BG = "#000000"
TEXT_COLOR = "#E8DDD0"
TEXT_DIM   = "#605848"
TEXT_HOVER = "#E8DDD0"
CONTROL_DIM = "#4A4038"
CONTROL_HOVER = "#C8A96E"

MODE_LABELS = {"work": "Focus", "short_break": "Short Break", "long_break": "Long Break"}


class PomodoroTimer:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Pomodoro")
        self.window.geometry("360x520")
        self.window.configure(bg=BG)
        self.window.resizable(False, False)
        self.window.attributes("-topmost", True)

        self.mode = "work"
        self.time_left = WORK_TIME
        self.total_time = WORK_TIME
        self.running = False
        self.completed = 0
        self.timer_id = None
        self.pulse_t = 0.0
        self.controls_visible = False

        self._setup_ui()
        self._bind_keys()

    # ── keyboard shortcuts ──────────────────────────────────────

    def _bind_keys(self):
        self.window.bind("<space>", lambda e: self._on_start_pause())
        self.window.bind("r", lambda e: self.reset())
        self.window.bind("s", lambda e: self.skip())
        self.window.bind("t", lambda e: self._toggle_top())

    # ── UI setup ────────────────────────────────────────────────

    def _setup_ui(self):
        w, h = 360, 520
        self.cv = tk.Canvas(self.window, width=w, height=h,
                            bg=BG, highlightthickness=0, bd=0)
        self.cv.pack()

        # Click zones
        self.cv.tag_bind("dial", "<Button-1>", lambda e: self._on_start_pause())
        self.cv.tag_bind("dial", "<Double-Button-1>", lambda e: self.reset())
        self.cv.tag_bind("dial", "<Button-3>", lambda e: self.skip())

        # Control hints at bottom — drawn in _render_controls
        self._make_control("start",  80, 450, "Start", self._on_start_pause)
        self._make_control("reset", 180, 450, "Reset", self.reset)
        self._make_control("skip",  280, 450, "Skip",  self.skip)

        self._start_btn_text = "Start"

        # Initial draw
        self._render()

    def _make_control(self, tag, x, y, text, cmd):
        tid = self.cv.create_text(x, y, text=text,
                                   font=("Microsoft YaHei", 10),
                                   fill=CONTROL_DIM, tags=(tag, "ctrl"))
        for ev in ("<Enter>", "<Leave>", "<Button-1>"):
            self.cv.tag_bind(tag, ev, lambda e, t=tag, c=cmd: self._ctrl_event(e, t, c))
        setattr(self, f"ctrl_{tag}", tid)

    def _ctrl_event(self, event, tag, cmd):
        tid = getattr(self, f"ctrl_{tag}")
        if event.type == tk.EventType.Enter:
            self.cv.itemconfig(tid, fill=CONTROL_HOVER)
        elif event.type == tk.EventType.Leave:
            self.cv.itemconfig(tid, fill=CONTROL_DIM)
        elif event.type == tk.EventType.ButtonPress:
            cmd()

    # ── rendering ───────────────────────────────────────────────

    def _render(self):
        self.cv.delete("dial", "mode_lbl")

        cx, cy = 180, 230
        r_tick = 130    # tick marks start here
        r_track = 114   # outer track ring
        r_inner = 108   # inner track ring
        r_prog  = 111   # progress arc sits between tracks
        r_dots  = 84    # pomodoro indicator dots

        # ── 60 tick marks ──
        for i in range(60):
            angle = math.radians(90 - i * 6)
            is_major = (i % 5 == 0)
            outer = r_tick
            inner = r_tick - (14 if is_major else 7)
            color = GOLD_TICK_L if is_major else GOLD_TICK_S
            width = 2 if is_major else 1
            x1 = cx + outer * math.cos(angle)
            y1 = cy - outer * math.sin(angle)
            x2 = cx + inner * math.cos(angle)
            y2 = cy - inner * math.sin(angle)
            self.cv.create_line(x1, y1, x2, y2, fill=color,
                                width=width, tags="dial")

        # ── outer track ring (1px) ──
        self.cv.create_oval(cx - r_track, cy - r_track,
                            cx + r_track, cy + r_track,
                            outline=GOLD_TRACK, width=1, tags="dial")

        # ── inner track ring (2px) ──
        self.cv.create_oval(cx - r_inner, cy - r_inner,
                            cx + r_inner, cy + r_inner,
                            outline=GOLD_INNER, width=2, tags="dial")

        # ── progress arc ──
        ratio = self.time_left / self.total_time if self.total_time > 0 else 0
        arc_color = GOLD_BRIGHT

        if ratio > 0:
            extent = 360 * ratio
            start = 90 - extent

            # glow layer — wide, dark
            self.cv.create_arc(cx - r_prog, cy - r_prog,
                               cx + r_prog, cy + r_prog,
                               start=start, extent=extent,
                               outline=GOLD_GLOW, width=14,
                               style="arc", tags="dial")

            # main arc — thin, bright
            self.cv.create_arc(cx - r_prog, cy - r_prog,
                               cx + r_prog, cy + r_prog,
                               start=start, extent=extent,
                               outline=arc_color, width=3,
                               style="arc", tags="dial")

            # leading dot
            rad = math.radians(90 - extent)
            dx = cx + r_prog * math.cos(rad)
            dy = cy - r_prog * math.sin(rad)
            dot_r = 5
            # outer glow dot
            self.cv.create_oval(dx - 7, dy - 7, dx + 7, dy + 7,
                                fill=GOLD_GLOW, outline="", tags="dial")
            # core dot
            self.cv.create_oval(dx - dot_r, dy - dot_r,
                                dx + dot_r, dy + dot_r,
                                fill=GOLD_BRIGHT, outline="", tags="dial")

        # ── pomodoro indicator dots (4 dots) ──
        current = self.completed % LONG_BREAK_INTERVAL
        dot_spacing = 16
        dot_y = cy + 56
        start_x = cx - int(1.5 * dot_spacing)
        for i in range(4):
            dx_pos = start_x + i * dot_spacing
            fill = GOLD_DOT_ON if i < current else GOLD_DOT_OFF
            r_dot = 3.5
            self.cv.create_oval(dx_pos - r_dot, dot_y - r_dot,
                                dx_pos + r_dot, dot_y + r_dot,
                                fill=fill, outline="", tags="dial")

        # ── time text ──
        m, s = divmod(self.time_left, 60)
        self.cv.create_text(cx, cy, text=f"{m:02d}:{s:02d}",
                            font=("Consolas", 52, "bold"),
                            fill=TEXT_COLOR, tags="dial")

        # ── mode label at 12 o'clock ──
        self.cv.create_text(cx, cy - 70, text=MODE_LABELS[self.mode],
                            font=("Microsoft YaHei", 10),
                            fill=TEXT_DIM, tags="mode_lbl")

        # ── control labels ──
        self._render_controls()

    def _render_controls(self):
        text = "Pause" if self.running else "Start"
        self.cv.itemconfig(self.ctrl_start, text=text)
        self.cv.tag_raise("ctrl")

    # ── timer control ───────────────────────────────────────────

    def _on_start_pause(self):
        if self.running:
            self.pause()
        else:
            self.start()

    def start(self):
        if self.timer_id:
            return
        self.running = True
        self._render_controls()
        self._tick()

    def pause(self):
        self.running = False
        if self.timer_id:
            self.window.after_cancel(self.timer_id)
            self.timer_id = None
        self._render_controls()
        self._render()

    def reset(self):
        self.pause()
        if self.mode == "work":
            self.time_left = WORK_TIME
            self.total_time = WORK_TIME
        elif self.mode == "short_break":
            self.time_left = SHORT_BREAK
            self.total_time = SHORT_BREAK
        else:
            self.time_left = LONG_BREAK
            self.total_time = LONG_BREAK
        self.pulse_t = 0.0
        self._render()

    def skip(self):
        self.pause()
        self._switch_mode()

    # ── core loop ───────────────────────────────────────────────

    def _tick(self):
        if not self.running:
            return

        self.time_left -= 1
        self.pulse_t += 0.3
        self._render()

        if self.time_left <= 0:
            self._notify()
            self.running = False
            if self.timer_id:
                self.window.after_cancel(self.timer_id)
                self.timer_id = None
            self._render_controls()
            self._switch_mode()
            return

        self.timer_id = self.window.after(1000, self._tick)

    def _switch_mode(self):
        if self.mode == "work":
            self.completed += 1
            if self.completed % LONG_BREAK_INTERVAL == 0:
                self.mode = "long_break"
                self.time_left = LONG_BREAK
                self.total_time = LONG_BREAK
            else:
                self.mode = "short_break"
                self.time_left = SHORT_BREAK
                self.total_time = SHORT_BREAK
        else:
            self.mode = "work"
            self.time_left = WORK_TIME
            self.total_time = WORK_TIME

        self.pulse_t = 0.0
        self._render()

    # ── notification ────────────────────────────────────────────

    def _notify(self):
        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass
        try:
            self.window.attributes("-topmost", True)
            self.window.focus_force()
        except Exception:
            pass

    # ── topmost ─────────────────────────────────────────────────

    def _toggle_top(self):
        cur = self.window.attributes("-topmost")
        self.window.attributes("-topmost", not cur)

    # ── launch ──────────────────────────────────────────────────

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    PomodoroTimer().run()
