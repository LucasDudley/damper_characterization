import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import datetime


class RealTimePlot:
    def __init__(self, master, signal_names, y_label="Values", y_range=(-100, 100),
                 figsize=(10,8), x_window=3, plot_freq=5):
        
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.lines = [self.ax.plot([], [], label=name)[0] for name in signal_names]
        self.ax.set_ylim(*y_range)
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel(y_label)
        self.ax.legend(loc='upper right')
        self.ax.grid()
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.x_window = x_window
        self.plot_freq = plot_freq
        self.last_idx = 0

    def update(self, time_q, data_qs, sample_rate):

        if not time_q:
            return

        # Determine how many samples correspond to one plot update
        samples_per_update = max(1, int(sample_rate / self.plot_freq))

        new_idx = len(time_q)
        if new_idx - self.last_idx < samples_per_update:
            return  # Not enough new data yet

        # Grab the new chunk
        times = list(time_q)[self.last_idx:new_idx]
        data_slices = [list(dq)[self.last_idx:new_idx] for dq in data_qs]

        # Append new samples to lines while preserving x_window
        for i, line in enumerate(self.lines):
            xdata, ydata = line.get_data()
            xdata = list(xdata) + times
            ydata = list(ydata) + data_slices[i]

            # Trim to x_window seconds
            cutoff_time = xdata[-1] - datetime.timedelta(seconds=self.x_window)
            idx_start = next((j for j, t in enumerate(xdata) if t >= cutoff_time), 0)
            xdata = xdata[idx_start:]
            ydata = ydata[idx_start:]

            line.set_data(xdata, ydata)

        # Update x-axis limits
        self.ax.set_xlim(xdata[0], xdata[-1])
        self.canvas.draw_idle()
        self.last_idx = new_idx

        # In your RealTimePlot class

    def reset(self):
        """
        Resets the plot for a new test run by clearing all line data
        and resetting the internal index.
        """
        # Reset the index that tracks plotted data
        self.last_idx = 0
        
        # Clear the data from each line on the plot
        for line in self.lines:
            line.set_data([], [])
            
        # Redraw the empty canvas
        self.canvas.draw_idle()




