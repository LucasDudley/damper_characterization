import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import datetime


class RealTimePlot:
    def __init__(self, master, channels=["AI0","AI1","AI2"], figsize=(12,6),
                 y_range=(0,5), x_window=3, plot_freq=5):
        """
        master     : Tkinter root or frame
        channels   : list of channel names
        figsize    : matplotlib figure size
        y_range    : (min, max) y-axis limits
        x_window   : seconds of data to display
        plot_freq  : Hz at which to update the plot
        """
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.lines = [self.ax.plot([], [], label=ch)[0] for ch in channels]
        self.ax.set_ylim(*y_range)
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Voltage (V)")
        self.ax.legend(loc='upper right')
        self.ax.grid()
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.x_window = x_window
        self.plot_freq = plot_freq
        self.last_idx = 0

    def update(self, time_q, data_qs, sample_rate):
        """
        time_q       : list of datetime timestamps
        data_qs      : list of lists of data per channel
        sample_rate  : DAQ samples per second
        """
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




