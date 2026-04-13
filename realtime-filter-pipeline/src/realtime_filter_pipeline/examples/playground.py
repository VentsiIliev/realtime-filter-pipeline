"""Tkinter-based interactive filter playground."""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from realtime_filter_pipeline.examples.playground_support import (
        RollingHistory,
        SignalGenerator,
        SmoothingConfig,
        build_filter_pipeline,
        replay_pipeline,
    )
else:
    from .playground_support import (
        RollingHistory,
        SignalGenerator,
        SmoothingConfig,
        build_filter_pipeline,
        replay_pipeline,
    )


class FilterPlaygroundApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Realtime Filter Playground")
        self.root.geometry("1360x820")
        self.root.minsize(1180, 720)
        self.root.configure(bg="#edf1f5")

        self._build_state()
        self.generator = SignalGenerator()
        self.history = RollingHistory(maxlen=280)
        self.pipeline = build_filter_pipeline(self._read_config_from_state())

        self.running = False
        self.sample_count = 0
        self.plot_update_ms = 100
        self._last_plot_draw_ms = 0

        self._build_ui()
        self._update_labels(0.0, 0.0)
        self._draw_plot()

    def _build_state(self) -> None:
        self.noise_var = tk.DoubleVar(value=0.20)
        self.time_delta_var = tk.DoubleVar(value=0.05)
        self.signal_type_var = tk.StringVar(value="Composite")
        self.average_enabled = tk.BooleanVar(value=True)
        self.average_window = tk.IntVar(value=5)
        self.ema_enabled = tk.BooleanVar(value=True)
        self.ema_alpha = tk.DoubleVar(value=0.20)
        self.median_enabled = tk.BooleanVar(value=False)
        self.median_window = tk.IntVar(value=5)
        self.gaussian_enabled = tk.BooleanVar(value=False)
        self.gaussian_window = tk.IntVar(value=5)
        self.gaussian_std = tk.DoubleVar(value=1.0)
        self.low_pass_enabled = tk.BooleanVar(value=False)
        self.low_pass_window = tk.IntVar(value=5)

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        hero = ttk.Frame(self.root, padding=(20, 18, 20, 10), style="App.TFrame")
        hero.grid(row=0, column=0, sticky="ew")
        hero.columnconfigure(0, weight=1)
        ttk.Label(hero, text="Realtime Filter Playground", style="HeroTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            hero,
            text="Compare raw and filtered signals, switch test scenarios, and tune your smoothing pipeline live.",
            style="HeroBody.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        content = ttk.Frame(self.root, padding=(20, 0, 20, 20), style="App.TFrame")
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=0)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        controls_shell = ttk.Frame(content, padding=(0, 0, 18, 0), style="App.TFrame")
        controls_shell.grid(row=0, column=0, sticky="ns")
        visuals = ttk.Frame(content, padding=0, style="App.TFrame")
        visuals.grid(row=0, column=1, sticky="nsew")
        visuals.columnconfigure(0, weight=1)
        visuals.rowconfigure(2, weight=1)

        self._build_controls(controls_shell)
        self._build_visuals(visuals)

    def _build_controls(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        card = ttk.Frame(parent, style="Panel.TFrame", padding=0)
        card.grid(sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        header = ttk.Frame(card, style="Panel.TFrame", padding=(20, 18, 20, 8))
        header.grid(row=0, column=0, sticky="ew")
        ttk.Label(header, text="Controls", style="SectionTitle.TLabel").grid(sticky="w")
        ttk.Label(
            header,
            text="Shape the input stream, choose a sample cadence, and enable only the filters you want to evaluate.",
            wraplength=280,
            style="Muted.TLabel",
        ).grid(sticky="w", pady=(6, 14))

        scroll_frame = ttk.Frame(card, style="Panel.TFrame", padding=(0, 0, 0, 12))
        scroll_frame.grid(row=1, column=0, sticky="nsew")
        scroll_frame.rowconfigure(0, weight=1)
        scroll_frame.columnconfigure(0, weight=1)

        canvas = tk.Canvas(
            scroll_frame,
            width=380,
            bg="#f8fafc",
            highlightthickness=0,
            borderwidth=0,
        )
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        controls = ttk.Frame(canvas, style="Panel.TFrame", padding=(20, 0, 20, 18))
        controls.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        controls_window = canvas.create_window((0, 0), window=controls, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(controls_window, width=event.width),
        )
        canvas.bind("<Enter>", lambda _event: canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-event.delta / 120), "units")))
        canvas.bind("<Leave>", lambda _event: canvas.unbind_all("<MouseWheel>"))

        buttons = ttk.Frame(controls, style="Panel.TFrame")
        buttons.grid(sticky="ew", pady=(0, 16))
        ttk.Button(buttons, text="Start", command=self.start, style="Accent.TButton").grid(row=0, column=0, padx=(0, 8))
        ttk.Button(buttons, text="Stop", command=self.stop, style="Subtle.TButton").grid(row=0, column=1, padx=(0, 8))
        ttk.Button(buttons, text="Reset", command=self.reset, style="Subtle.TButton").grid(row=0, column=2)

        ttk.Label(controls, text="Stream setup", style="SectionTitle.TLabel").grid(sticky="w", pady=(0, 10))
        self._slider(controls, "Noise level", self.noise_var, 0.0, 1.0, 0.01)
        self._slider(controls, "Time delta (s)", self.time_delta_var, 0.01, 0.50, 0.01)
        signal_row = ttk.Frame(controls, style="Panel.TFrame")
        signal_row.grid(sticky="ew", pady=(0, 10))
        signal_row.columnconfigure(0, weight=1)
        ttk.Label(signal_row, text="Signal type", style="FieldLabel.TLabel").grid(row=0, column=0, sticky="w")
        signal_menu = ttk.Combobox(
            signal_row,
            textvariable=self.signal_type_var,
            values=("Composite", "Sine", "Step", "Ramp", "Spikes"),
            state="readonly",
        )
        signal_menu.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        signal_menu.bind("<<ComboboxSelected>>", lambda _event: self.reset())
        ttk.Separator(controls).grid(sticky="ew", pady=12)
        ttk.Label(controls, text="Filter stack", style="SectionTitle.TLabel").grid(sticky="w", pady=(0, 10))

        self._filter_block(controls, "AverageFilter", self.average_enabled, [("Window", self.average_window, 3, 31, 2)])
        self._filter_block(controls, "EMAFilter", self.ema_enabled, [("Alpha", self.ema_alpha, 0.01, 1.0, 0.01)])
        self._filter_block(controls, "MedianFilter", self.median_enabled, [("Window", self.median_window, 3, 31, 2)])
        self._filter_block(
            controls,
            "GaussianFilter",
            self.gaussian_enabled,
            [("Window", self.gaussian_window, 3, 31, 2), ("Std dev", self.gaussian_std, 0.2, 3.0, 0.1)],
        )
        self._filter_block(controls, "LowPassFilter", self.low_pass_enabled, [("Window", self.low_pass_window, 3, 31, 2)])

    def _filter_block(self, parent: ttk.Frame, title: str, enabled_var: tk.Variable, sliders: list[tuple[str, tk.Variable, float, float, float]]) -> None:
        frame = ttk.LabelFrame(parent, text=title, padding=14, style="Filter.TLabelframe")
        frame.grid(sticky="ew", pady=(0, 10))
        ttk.Checkbutton(frame, text="Enabled", variable=enabled_var, command=self._on_config_changed, style="Filter.TCheckbutton").grid(sticky="w")
        for row_index, (label, variable, start, end, step) in enumerate(sliders, start=1):
            self._slider(frame, label, variable, start, end, step, row=row_index)

    def _slider(
        self,
        parent: ttk.Widget,
        label: str,
        variable: tk.Variable,
        start: float,
        end: float,
        step: float,
        row: int | None = None,
    ) -> None:
        frame = ttk.Frame(parent, style="Panel.TFrame")
        if row is None:
            frame.grid(sticky="ew", pady=(0, 10))
        else:
            frame.grid(row=row, column=0, sticky="ew", pady=(6, 0))
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=label, style="FieldLabel.TLabel").grid(row=0, column=0, sticky="w")
        value_label = ttk.Label(frame, width=6, text=self._format_value(variable.get()), style="Value.TLabel")
        value_label.grid(row=0, column=1, sticky="e", padx=(8, 0))
        scale = tk.Scale(
            frame,
            from_=start,
            to=end,
            orient="horizontal",
            resolution=step,
            variable=variable,
            showvalue=False,
            bg="#f8fafc",
            troughcolor="#d8e2ec",
            activebackground="#1f5f8b",
            highlightthickness=0,
            bd=0,
            fg="#20303f",
            length=260,
            command=lambda _value, var=variable, lbl=value_label: self._on_scale_change(var, lbl),
        )
        scale.grid(row=1, column=0, columnspan=2, sticky="ew")

    def _build_visuals(self, parent: ttk.Frame) -> None:
        summary = ttk.Frame(parent, style="Panel.TFrame", padding=(20, 18))
        summary.grid(row=0, column=0, sticky="ew")
        summary.columnconfigure(0, weight=1)
        ttk.Label(summary, text="Signal response", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            summary,
            text="Watch how the active filter chain reshapes the stream in real time.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        stats = ttk.Frame(parent, style="App.TFrame", padding=(0, 14, 0, 14))
        stats.grid(row=1, column=0, sticky="ew")
        for idx in range(4):
            stats.columnconfigure(idx, weight=1)

        self.raw_label = self._stat_card(stats, 0, "Raw sample", "0.000")
        self.filtered_label = self._stat_card(stats, 1, "Filtered output", "0.000")
        self.delta_label = self._stat_card(stats, 2, "Filter delta", "0.000")
        self.count_label = self._stat_card(stats, 3, "Samples", "0")

        plot_card = ttk.Frame(parent, style="Panel.TFrame", padding=(16, 16, 16, 12))
        plot_card.grid(row=2, column=0, sticky="nsew")
        plot_card.columnconfigure(0, weight=1)
        plot_card.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(plot_card, bg="#f8fafc", highlightthickness=0, borderwidth=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

    def _stat_card(self, parent: ttk.Frame, column: int, label: str, value: str) -> ttk.Label:
        card = ttk.Frame(parent, style="Metric.TFrame", padding=(16, 14))
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))
        card.columnconfigure(0, weight=1)
        ttk.Label(card, text=label, style="MetricLabel.TLabel").grid(row=0, column=0, sticky="w")
        value_label = ttk.Label(card, text=value, style="MetricValue.TLabel")
        value_label.grid(row=1, column=0, sticky="w", pady=(8, 0))
        return value_label

    def _format_value(self, value: float) -> str:
        if isinstance(value, bool):
            return str(value)
        if abs(float(value) - round(float(value))) < 1e-9:
            return str(int(round(float(value))))
        return f"{float(value):.2f}"

    def _on_scale_change(self, variable: tk.Variable, label: ttk.Label) -> None:
        label.config(text=self._format_value(variable.get()))
        self._on_config_changed()

    def _on_config_changed(self) -> None:
        self.pipeline = build_filter_pipeline(self._read_config_from_state())
        filtered_values = replay_pipeline(list(self.history.raw), self._read_config_from_state())
        self.history.filtered.clear()
        self.history.filtered.extend(filtered_values)
        if self.history.raw:
            self._update_labels(self.history.raw[-1], self.history.filtered[-1])
        self._last_plot_draw_ms = 0
        self._draw_plot()

    def _read_config_from_state(self) -> SmoothingConfig:
        return SmoothingConfig(
            average_enabled=self.average_enabled.get(),
            average_window=self.average_window.get(),
            ema_enabled=self.ema_enabled.get(),
            ema_alpha=self.ema_alpha.get(),
            median_enabled=self.median_enabled.get(),
            median_window=self.median_window.get(),
            gaussian_enabled=self.gaussian_enabled.get(),
            gaussian_window=self.gaussian_window.get(),
            gaussian_std_dev=self.gaussian_std.get(),
            low_pass_enabled=self.low_pass_enabled.get(),
            low_pass_window=self.low_pass_window.get(),
            signal_type=self.signal_type_var.get(),
        )

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self._tick()

    def stop(self) -> None:
        self.running = False

    def reset(self) -> None:
        self.stop()
        self.generator.reset()
        self.history.reset()
        self.sample_count = 0
        self.pipeline = build_filter_pipeline(self._read_config_from_state())
        self._last_plot_draw_ms = 0
        self._update_labels(0.0, 0.0)
        self._draw_plot()

    def _tick(self) -> None:
        if not self.running:
            return
        self.generator.dt = self.time_delta_var.get()
        raw_value = self.generator.next_value(
            noise_level=self.noise_var.get(),
            signal_type=self.signal_type_var.get(),
        )
        filtered_value = self.pipeline.update(raw_value)
        self.history.append(raw_value, filtered_value)
        self.sample_count += 1
        self._update_labels(raw_value, filtered_value)
        now_ms = int(self.root.tk.call("clock", "milliseconds"))
        if now_ms - self._last_plot_draw_ms >= self.plot_update_ms:
            self._draw_plot()
            self._last_plot_draw_ms = now_ms
        tick_ms = max(1, int(round(self.time_delta_var.get() * 1000)))
        self.root.after(tick_ms, self._tick)

    def _update_labels(self, raw_value: float, filtered_value: float) -> None:
        self.raw_label.config(text=f"{raw_value:.3f}")
        self.filtered_label.config(text=f"{filtered_value:.3f}")
        self.delta_label.config(text=f"{filtered_value - raw_value:.3f}")
        self.count_label.config(text=f"{self.sample_count}")

    def _draw_plot(self) -> None:
        self.canvas.delete("all")
        width = max(200, self.canvas.winfo_width())
        height = max(200, self.canvas.winfo_height())
        padding = 54
        left = padding
        top = padding
        right = width - padding
        bottom = height - padding

        raw_values = list(self.history.raw)
        filtered_values = list(self.history.filtered)
        if not raw_values:
            plot_left = left
            plot_top = top
            plot_right = right
            plot_bottom = bottom
            plot_center_x = (plot_left + plot_right) / 2
            plot_center_y = (plot_top + plot_bottom) / 2
            card_width = min(620, max(420, (plot_right - plot_left) * 0.72))
            card_height = min(150, max(108, (plot_bottom - plot_top) * 0.26))
            card_left = plot_center_x - card_width / 2
            card_right = plot_center_x + card_width / 2
            card_top = plot_center_y - card_height / 2
            card_bottom = plot_center_y + card_height / 2

            return

        self.canvas.create_rectangle(left, top, right, bottom, outline="#c9d4df", width=1)

        for idx in range(1, 5):
            y = top + idx * (bottom - top) / 5
            self.canvas.create_line(left, y, right, y, fill="#e3eaf1", dash=(2, 4))

        all_values = raw_values + filtered_values
        vmin = min(all_values)
        vmax = max(all_values)
        if abs(vmax - vmin) < 1e-9:
            vmax += 1.0
            vmin -= 1.0

        def to_points(values: list[float]) -> list[float]:
            if len(values) == 1:
                x = (width - 2 * padding) / 2 + padding
                y = self._map_y(values[0], vmin, vmax, height, padding)
                return [x, y]
            points: list[float] = []
            for idx, value in enumerate(values):
                x = padding + (idx / (len(values) - 1)) * (width - 2 * padding)
                y = self._map_y(value, vmin, vmax, height, padding)
                points.extend([x, y])
            return points

        raw_points = to_points(raw_values)
        filtered_points = to_points(filtered_values)
        if len(raw_points) >= 4:
            self.canvas.create_line(*raw_points, fill="#7b8a9a", width=2, smooth=True)
        if len(filtered_points) >= 4:
            self.canvas.create_line(*filtered_points, fill="#1f5f8b", width=3, smooth=True)

        self.canvas.create_text(padding, 20, anchor="w", text="Raw vs filtered stream", fill="#1c2733", font=("Segoe UI", 13, "bold"))
        self.canvas.create_text(
            width - padding,
            20,
            anchor="e",
            text=(
                f"{self.signal_type_var.get()} | "
                f"Noise {self.noise_var.get():.2f} | dt {self.time_delta_var.get():.2f}s"
            ),
            fill="#6a7a89",
            font=("Segoe UI", 11),
        )
        self.canvas.create_text(left - 8, top, anchor="e", text=f"{vmax:.2f}", fill="#7a8a99", font=("Consolas", 9))
        self.canvas.create_text(left - 8, bottom, anchor="e", text=f"{vmin:.2f}", fill="#7a8a99", font=("Consolas", 9))

        self.canvas.create_line(width - 240, height - 20, width - 212, height - 20, fill="#7b8a9a", width=2)
        self.canvas.create_text(width - 202, height - 20, anchor="w", text="Raw", fill="#51606e", font=("Segoe UI", 10))
        self.canvas.create_line(width - 130, height - 20, width - 102, height - 20, fill="#1f5f8b", width=3)
        self.canvas.create_text(width - 92, height - 20, anchor="w", text="Filtered", fill="#51606e", font=("Segoe UI", 10))

    def _map_y(self, value: float, vmin: float, vmax: float, height: int, padding: int) -> float:
        return padding + (vmax - value) / (vmax - vmin) * (height - 2 * padding)


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    style.configure("App.TFrame", background="#edf1f5")
    style.configure("Panel.TFrame", background="#f8fafc")
    style.configure("Metric.TFrame", background="#f8fafc")
    style.configure("HeroTitle.TLabel", background="#edf1f5", foreground="#16202a", font=("Segoe UI", 22, "bold"))
    style.configure("HeroBody.TLabel", background="#edf1f5", foreground="#617181", font=("Segoe UI", 11))
    style.configure("SectionTitle.TLabel", background="#f8fafc", foreground="#1d2935", font=("Segoe UI", 12, "bold"))
    style.configure("Muted.TLabel", background="#f8fafc", foreground="#6f7f8d", font=("Segoe UI", 10))
    style.configure("FieldLabel.TLabel", background="#f8fafc", foreground="#33414e", font=("Segoe UI", 9, "bold"))
    style.configure("Value.TLabel", background="#f8fafc", foreground="#1f5f8b", font=("Consolas", 10, "bold"))
    style.configure("MetricLabel.TLabel", background="#f8fafc", foreground="#6f7f8d", font=("Segoe UI", 9, "bold"))
    style.configure("MetricValue.TLabel", background="#f8fafc", foreground="#17222d", font=("Segoe UI", 18, "bold"))
    style.configure("Filter.TLabelframe", background="#f8fafc")
    style.configure("Filter.TLabelframe.Label", background="#f8fafc", foreground="#21303d", font=("Segoe UI", 10, "bold"))
    style.configure("Filter.TCheckbutton", background="#f8fafc", foreground="#33414e")
    style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=(14, 8))
    style.map("Accent.TButton", background=[("!disabled", "#1f5f8b"), ("active", "#184a6d")], foreground=[("!disabled", "#ffffff")])
    style.configure("Subtle.TButton", padding=(14, 8))
    style.configure("TCombobox", padding=4)
    style.configure("TLabel", background="#edf1f5", foreground="#25313d")
    app = FilterPlaygroundApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
