import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import datetime


class RealTimePlot:
    def __init__(self, master, signal_names, y_label="Values", y_range=(-100, 100),
                 figsize=(10,8), x_window=3, plot_freq=5, 
                 secondary_signals=None, secondary_y_label=None, secondary_y_range=None):
        """
        Parameters:
        -----------
        secondary_signals : list of str, optional
            Names of signals to plot on the secondary y-axis
        secondary_y_label : str, optional
            Label for the secondary y-axis
        secondary_y_range : tuple, optional
            (min, max) range for the secondary y-axis
        """
        
        self.fig, self.ax = plt.subplots(figsize=figsize)
        
        # Primary axis setup
        self.primary_signals = signal_names
        self.lines = [self.ax.plot([], [], label=name)[0] for name in signal_names]
        self.ax.set_ylim(*y_range)
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel(y_label)
        self.ax.grid()
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        # Secondary axis setup (optional)
        self.ax2 = None
        self.secondary_lines = []
        self.secondary_signals = secondary_signals
        
        if secondary_signals is not None:
            self.ax2 = self.ax.twinx()
            self.secondary_lines = [self.ax2.plot([], [], label=name, linestyle='--')[0] 
                                   for name in secondary_signals]
            if secondary_y_range is not None:
                self.ax2.set_ylim(*secondary_y_range)
            if secondary_y_label is not None:
                self.ax2.set_ylabel(secondary_y_label)
        
        # Combine legends
        all_lines = self.lines + self.secondary_lines
        all_labels = [line.get_label() for line in all_lines]
        self.ax.legend(all_lines, all_labels, loc='upper right')
        
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

        # Update primary axis lines
        num_primary = len(self.lines)
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

        # Update secondary axis lines
        if self.ax2 is not None:
            for i, line in enumerate(self.secondary_lines):
                xdata, ydata = line.get_data()
                xdata = list(xdata) + times
                ydata = list(ydata) + data_slices[num_primary + i]

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

    def reset(self):
        """
        Resets the plot for a new test run by clearing all line data
        and resetting the internal index.
        """
        # Reset the index for data
        self.last_idx = 0
        
        # Clear the data from primary axis
        for line in self.lines:
            line.set_data([], [])
        
        # Clear the data from secondary axis
        if self.ax2 is not None:
            for line in self.secondary_lines:
                line.set_data([], [])
            
        # Redraw the empty canvas
        self.canvas.draw_idle()