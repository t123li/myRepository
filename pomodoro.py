import tkinter as tk
import winsound
import math

WORK_TIME = 25 * 60
SHORT_BREAK = 5 * 60
LONG_BREAK = 15 * 60
LONG_BREAK_INTERVAL = 4

COLORS = {
    "work": "#E74C3C",
    "short_break": "#2ECC71",
    "long_break": "#3498DB",
    "bg": "#1E1E2E",
    "surface": "#2D2D3F",
    "text": "#CDD6F4",
    "subtext": "#9399B2",
    "ring_bg": "#3D3D55",
}


class PomodoroTimer:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("番茄钟")
        self.window.geometry("380x520")
        self.window.configure(bg=COLORS["bg"])
        self.window.resizable(False, False)

        self.mode = "work"  # work | short_break | long_break
        self.time_left = WORK_TIME
        self.total_time = WORK_TIME
        self.running = False
        self.completed = 0
        self.timer_id = None

        self._setup_ui()
        self._draw()

    def _setup_ui(self):
        self.canvas = tk.Canvas(
            self.window,
            width=280,
            height=280,
            bg=COLORS["bg"],
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(pady=(30, 0))

        self.time_label = tk.Label(
            self.window,
            text="25:00",
            font=("Consolas", 44, "bold"),
            fg=COLORS["text"],
            bg=COLORS["bg"],
        )
        self.time_label.place(x=190, y=152, anchor="center")

        self.mode_label = tk.Label(
            self.window,
            text="专注",
            font=("Microsoft YaHei", 14),
            fg=COLORS["work"],
            bg=COLORS["bg"],
        )
        self.mode_label.pack(pady=(10, 4))

        info_frame = tk.Frame(self.window, bg=COLORS["bg"])
        info_frame.pack()

        self.cycle_label = tk.Label(
            info_frame,
            text="已完成: 0 轮",
            font=("Microsoft YaHei", 10),
            fg=COLORS["subtext"],
            bg=COLORS["bg"],
        )
        self.cycle_label.pack(side="left", padx=6)

        self.stage_label = tk.Label(
            info_frame,
            text="第 1 个番茄",
            font=("Microsoft YaHei", 10),
            fg=COLORS["subtext"],
            bg=COLORS["bg"],
        )
        self.stage_label.pack(side="left", padx=6)

        btn_frame = tk.Frame(self.window, bg=COLORS["bg"])
        btn_frame.pack(pady=(20, 10))

        self.start_btn = tk.Button(
            btn_frame,
            text="开始",
            font=("Microsoft YaHei", 12),
            width=8,
            bg=COLORS["ring_bg"],
            fg=COLORS["text"],
            activebackground=COLORS["surface"],
            activeforeground=COLORS["text"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            command=self._on_start_pause,
        )
        self.start_btn.pack(side="left", padx=4)

        self.reset_btn = tk.Button(
            btn_frame,
            text="重置",
            font=("Microsoft YaHei", 12),
            width=8,
            bg=COLORS["ring_bg"],
            fg=COLORS["text"],
            activebackground=COLORS["surface"],
            activeforeground=COLORS["text"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            command=self.reset,
        )
        self.reset_btn.pack(side="left", padx=4)

        self.skip_btn = tk.Button(
            btn_frame,
            text="跳过",
            font=("Microsoft YaHei", 12),
            width=8,
            bg=COLORS["ring_bg"],
            fg=COLORS["text"],
            activebackground=COLORS["surface"],
            activeforeground=COLORS["text"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            command=self.skip,
        )
        self.skip_btn.pack(side="left", padx=4)

        self.top_var = tk.BooleanVar(value=True)
        self.top_check = tk.Checkbutton(
            self.window,
            text="窗口置顶",
            variable=self.top_var,
            font=("Microsoft YaHei", 9),
            fg=COLORS["subtext"],
            bg=COLORS["bg"],
            selectcolor=COLORS["surface"],
            activebackground=COLORS["bg"],
            activeforeground=COLORS["subtext"],
            command=self._toggle_top,
        )
        self.top_check.pack(pady=(4, 0))
        self.window.attributes("-topmost", True)

    def _draw(self):
        self.canvas.delete("all")
        cx, cy, r = 140, 140, 120
        ratio = self.time_left / self.total_time if self.total_time > 0 else 0
        color = COLORS[self.mode]
        angle = 90 - (360 * ratio)

        self.canvas.create_oval(
            cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6,
            outline=COLORS["ring_bg"],
            width=10,
        )

        if ratio > 0:
            self.canvas.create_arc(
                cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6,
                start=angle,
                extent=360 * ratio,
                outline=color,
                width=10,
                style="arc",
            )

    def _on_start_pause(self):
        if self.running:
            self.pause()
        else:
            self.start()

    def start(self):
        if self.timer_id:
            return
        self.running = True
        self.start_btn.config(text="暂停")
        self._tick()

    def pause(self):
        self.running = False
        if self.timer_id:
            self.window.after_cancel(self.timer_id)
            self.timer_id = None
        self.start_btn.config(text="开始")

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
        self._update_display()

    def skip(self):
        self.pause()
        self._switch_mode()

    def _tick(self):
        if not self.running:
            return

        self.time_left -= 1
        self._update_display()

        if self.time_left <= 0:
            self._notify()
            self.pause()
            self._switch_mode()

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

        self._update_mode_labels()
        self._update_display()

    def _update_display(self):
        m, s = divmod(self.time_left, 60)
        self.time_label.config(text=f"{m:02d}:{s:02d}")
        self._draw()

    def _update_mode_labels(self):
        labels = {"work": "专注", "short_break": "短休息", "long_break": "长休息"}
        self.mode_label.config(text=labels[self.mode], fg=COLORS[self.mode])
        rounds = self.completed // LONG_BREAK_INTERVAL
        self.cycle_label.config(text=f"已完成: {rounds} 轮")
        current = (self.completed % LONG_BREAK_INTERVAL) + 1
        self.stage_label.config(text=f"第 {current} 个番茄")

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

    def _toggle_top(self):
        self.window.attributes("-topmost", self.top_var.get())

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    PomodoroTimer().run()
