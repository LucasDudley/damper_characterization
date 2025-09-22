import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import datetime

class RealTimePlot:
    def __init__(self, master, channels=["AI0","AI1","AI2"], figsize=(12,6), y_range=(0,5), x_window=3, plot_chunk_size=10):
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.lines = [self.ax.plot([], [], label=ch)[0] for ch in channels]
        self.ax.set_ylim(*y_range)
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Voltage (V)")
        self.ax.legend()
        self.ax.grid()
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.x_window = x_window
        self.plot_chunk_size = plot_chunk_size
        self.last_idx = 0  # keep track of last plotted sample

    def update(self, time_q, data_qs):
        if not time_q:
            return

        # Only plot new samples in chunks
        new_idx = len(time_q)
        if new_idx - self.last_idx < self.plot_chunk_size:
            return  # not enough new data yet

        times = list(time_q)[self.last_idx:new_idx]
        data_slices = [list(dq)[self.last_idx:new_idx] for dq in data_qs]

        # Limit to x_window seconds
        cutoff_time = times[-1] - datetime.timedelta(seconds=self.x_window)
        idx_start = next((i for i, t in enumerate(times) if t >= cutoff_time), 0)
        times = times[idx_start:]
        data_slices = [dq[idx_start:] for dq in data_slices]

        # Update lines
        for line, dq in zip(self.lines, data_slices):
            line.set_data(times, dq)

        self.ax.set_xlim(times[0], times[-1])
        self.canvas.draw_idle()
        self.last_idx = new_idx


