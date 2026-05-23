import tkinter as tk
import winsound
import math

WORK_TIME = 25 * 60
SHORT_BREAK = 5 * 60
LONG_BREAK = 15 * 60
LONG_BREAK_INTERVAL = 4

BG = "#0F0F1A"
SURFACE = "#1A1A2E"
SURFACE_HOVER = "#252540"
TEXT = "#E8E8F0"
SUBTEXT = "#8888A0"
RING_TRACK = "#252538"
RING_GLOW = "#3A3A55"

MODE_COLORS = {
    "work":       ("#FF6B6B", "#FF8787"),
    "short_break": ("#51CF66", "#69DB7C"),
    "long_break":  ("#4DABF7", "#74C0FC"),
}

MODE_LABELS = {
    "work": "专注",
    "short_break": "短休息",
    "long_break": "长休息",
}


class PomodoroTimer:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("番茄钟")
        self.window.geometry("360x500")
        self.window.configure(bg=BG)
        self.window.resizable(False, False)
        self.window.attributes("-topmost", True)

        self.mode = "work"
        self.time_left = WORK_TIME
        self.total_time = WORK_TIME
        self.running = False
        self.completed = 0
        self.timer_id = None
        self.pulse_phase = 0.0

        self._setup_ui()
        self._bind_keys()

    # ── keyboard shortcuts ──────────────────────────────────────────

    def _bind_keys(self):
        self.window.bind("<space>", lambda e: self._on_start_pause())
        self.window.bind("r", lambda e: self.reset())
        self.window.bind("s", lambda e: self.skip())
        self.window.bind("t", lambda e: self._toggle_top())

    # ── UI construction ─────────────────────────────────────────────

    def _setup_ui(self):
        w, h = 360, 500
        self.cv = tk.Canvas(
            self.window, width=w, height=h,
            bg=BG, highlightthickness=0, bd=0,
        )
        self.cv.pack()

        # decorative dots around the ring
        self.cv.create_oval(24, 24, 28, 28, fill="#2A2A40", outline="")
        self.cv.create_oval(332, 24, 336, 28, fill="#2A2A40", outline="")
        self.cv.create_oval(24, 88, 28, 92, fill="#1E1E35", outline="")
        self.cv.create_oval(332, 88, 336, 92, fill="#1E1E35", outline="")

        # buttons
        self._make_button(40, 410, 85, 38, "开始", self._on_start_pause, "start")
        self._make_button(137, 410, 85, 38, "重置", self.reset, "reset")
        self._make_button(234, 410, 85, 38, "跳过", self.skip, "skip")

        # topmost checkbox area
        self.top_var = tk.BooleanVar(value=True)
        top_cb = tk.Checkbutton(
            self.window, text="置顶", variable=self.top_var,
            font=("Microsoft YaHei", 8), fg=SUBTEXT, bg=BG,
            selectcolor=SURFACE, activebackground=BG,
            activeforeground=SUBTEXT, relief="flat",
            command=self._toggle_top,
        )
        top_cb.place(x=150, y=462)

        self._render()

    def _make_button(self, x, y, w, h, text, cmd, tag):
        r = 12
        items = self._round_rect(x, y, x + w, y + h, r,
                                 fill=SURFACE, outline="", tags=(tag, "btn"))
        tid = self.cv.create_text(
            x + w // 2, y + h // 2, text=text,
            font=("Microsoft YaHei", 11), fill=TEXT, tags=(tag, "btn"),
        )
        for event in ("<Enter>", "<Leave>", "<Button-1>"):
            self.cv.tag_bind(tag, event, lambda e, t=tag, c=cmd: self._btn_event(e, t, c))
        setattr(self, f"btn_{tag}_bg", items)
        setattr(self, f"btn_{tag}_text", tid)

    def _round_rect(self, x1, y1, x2, y2, r, **kw):
        items = []
        items.append(self.cv.create_rectangle(x1 + r, y1, x2 - r, y2, **kw))
        items.append(self.cv.create_rectangle(x1, y1 + r, x2, y2 - r, **kw))
        d = 2 * r
        for cx, cy in [(x1 + r, y1 + r), (x2 - r, y1 + r),
                        (x1 + r, y2 - r), (x2 - r, y2 - r)]:
            items.append(self.cv.create_oval(cx - r, cy - r, cx + r, cy + r, **kw))
        return items

    def _btn_event(self, event, tag, cmd):
        bg_items = getattr(self, f"btn_{tag}_bg")
        if event.type == tk.EventType.Enter:
            for item_id in bg_items:
                self.cv.itemconfig(item_id, fill=SURFACE_HOVER)
        elif event.type == tk.EventType.Leave:
            for item_id in bg_items:
                self.cv.itemconfig(item_id, fill=SURFACE)
        elif event.type == tk.EventType.ButtonPress:
            cmd()

    # ── rendering ───────────────────────────────────────────────────

    def _render(self):
        self.cv.delete("ring", "time_text", "mode_text",
                        "cycle_text", "stage_text")
        cx, cy, r = 180, 215, 124

        # track ring
        self.cv.create_oval(
            cx - r, cy - r, cx + r, cy - r, cx + r, cy + r, cx - r, cy + r,
            outline=RING_TRACK, width=14, tags="ring",
        )

        # progress arc
        ratio = self.time_left / self.total_time if self.total_time > 0 else 0
        base_color, _ = MODE_COLORS[self.mode]

        # warn color when ≤ 60s left in work mode
        if self.mode == "work" and self.time_left <= 60 and self.time_left > 0:
            base_color = "#FFD43B"

        # pulse effect when running
        color = base_color
        if self.running:
            self.pulse_phase += 0.25
            bright = 1.0 + 0.06 * math.sin(self.pulse_phase)
            color = self._adjust_brightness(base_color, bright)

        if ratio > 0:
            angle = 90
            extent = 360 * ratio
            self.cv.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=angle - extent, extent=extent,
                outline=color, width=14, style="arc",
                tags="ring",
            )

        # leading dot
        if ratio > 0 and self.time_left > 0:
            rad = math.radians(angle - 360 * ratio)
            dx = cx + (r - 1) * math.cos(rad)
            dy = cy - (r - 1) * math.sin(rad)
            dot_r = 7 if self.running else 5
            self.cv.create_oval(
                dx - dot_r, dy - dot_r, dx + dot_r, dy + dot_r,
                fill=color, outline=BG, width=2, tags="ring",
            )

        # time text
        m, s = divmod(self.time_left, 60)
        self.cv.create_text(
            cx, cy - 4, text=f"{m:02d}:{s:02d}",
            font=("Consolas", 48, "bold"), fill=TEXT, tags="time_text",
        )

        # mode label
        self.cv.create_text(
            cx, cy - 54, text=MODE_LABELS[self.mode],
            font=("Microsoft YaHei", 13), fill=base_color, tags="mode_text",
        )

        # cycle / stage info
        rounds = self.completed // LONG_BREAK_INTERVAL
        current = (self.completed % LONG_BREAK_INTERVAL) + 1
        self.cv.create_text(
            cx, cy + 48,
            text=f"第 {current} 个番茄 · 已完成 {rounds} 轮",
            font=("Microsoft YaHei", 9), fill=SUBTEXT,
            tags="cycle_text",
        )

    def _adjust_brightness(self, hex_color, factor):
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    # ── timer control ───────────────────────────────────────────────

    def _on_start_pause(self):
        if self.running:
            self.pause()
        else:
            self.start()

    def start(self):
        if self.timer_id:
            return
        self.running = True
        self._update_start_btn()
        self._tick()

    def pause(self):
        self.running = False
        if self.timer_id:
            self.window.after_cancel(self.timer_id)
            self.timer_id = None
        self._update_start_btn()
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
        self.pulse_phase = 0.0
        self._render()

    def skip(self):
        self.pause()
        self._switch_mode()

    def _update_start_btn(self):
        text = "暂停" if self.running else "开始"
        self.cv.itemconfig(self.btn_start_text, text=text)

    # ── core loop ───────────────────────────────────────────────────

    def _tick(self):
        if not self.running:
            return

        self.time_left -= 1
        self._render()

        if self.time_left <= 0:
            self._notify()
            self.running = False
            if self.timer_id:
                self.window.after_cancel(self.timer_id)
                self.timer_id = None
            self._update_start_btn()
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

        self.pulse_phase = 0.0
        self._render()

    # ── notification ────────────────────────────────────────────────

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

    # ── topmost toggle ──────────────────────────────────────────────

    def _toggle_top(self):
        self.window.attributes("-topmost", self.top_var.get())

    # ── launch ──────────────────────────────────────────────────────

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    PomodoroTimer().run()
