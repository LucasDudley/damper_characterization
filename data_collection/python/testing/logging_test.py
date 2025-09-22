import nidaqmx
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import tkinter as tk
from collections import deque
import datetime
import threading
import csv
from nidaqmx.constants import TerminalConfiguration, AcquisitionType

# --- Configuration ---
DEVICE_NAME = "Dev1"
CHANNELS = ["ai0", "ai1"]
SAMPLE_RATE = 300
CHUNK_SIZE = 50
PLOT_WINDOW_SECONDS = 3

# --- Shared State ---
data_qs = [deque(maxlen=SAMPLE_RATE * PLOT_WINDOW_SECONDS) for _ in CHANNELS]
time_q = deque(maxlen=SAMPLE_RATE * PLOT_WINDOW_SECONDS)
running = False

# --- Tkinter Root (must be first for Variables) ---
root = tk.Tk()
root.title("NI-DAQmx Live Plot")
log_to_csv = tk.BooleanVar(master=root, value=False)

# --- DAQ Setup ---
def setup_daq_task():
    task = nidaqmx.Task()
    for ch in CHANNELS:
        task.ai_channels.add_ai_voltage_chan(
            f"{DEVICE_NAME}/{ch}",
            terminal_config=TerminalConfiguration.RSE
        )
    task.timing.cfg_samp_clk_timing(
        rate=SAMPLE_RATE,
        sample_mode=AcquisitionType.CONTINUOUS
    )
    return task

# --- Data Acquisition Thread ---
def acquire_data():
    global running
    task = setup_daq_task()
    with task:
        start_time = datetime.datetime.now()
        sample_count = 0
        while running:
            try:
                new_data = np.array(task.read(number_of_samples_per_channel=CHUNK_SIZE))
                seconds_elapsed = np.arange(sample_count, sample_count + CHUNK_SIZE) / SAMPLE_RATE
                new_times = [start_time + datetime.timedelta(seconds=s) for s in seconds_elapsed]
                sample_count += CHUNK_SIZE

                # Update queues
                time_q.extend(new_times)
                for i, dq in enumerate(data_qs):
                    dq.extend(new_data[i])

                # Schedule plot update in main thread
                root.after(0, update_plot)

                # Write to CSV if enabled
                if log_to_csv.get():
                    with open("daq_log.csv", "a", newline="") as f:
                        writer = csv.writer(f)
                        for t, *values in zip(new_times, *new_data):
                            writer.writerow([t.isoformat()] + list(values))

            except Exception as e:
                print(f"DAQ error: {e}")
                running = False

# --- Logging Controls ---
def start_logging():
    global running
    if not running:
        running = True
        # Clear old data
        for dq in data_qs:
            dq.clear()
        time_q.clear()
        if log_to_csv.get():
            with open("daq_log.csv", "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp"] + CHANNELS)
        threading.Thread(target=acquire_data, daemon=True).start()

def stop_logging():
    global running
    running = False
    print("Logging stopped.")

# --- Plot Update ---
def update_plot():
    for line, dq in zip(lines, data_qs):
        line.set_data(time_q, dq)
    if time_q:
        ax.set_xlim(
            time_q[-1] - datetime.timedelta(seconds=PLOT_WINDOW_SECONDS),
            time_q[-1]
        )
    canvas.draw_idle()

# --- Matplotlib Figure ---
fig, ax = plt.subplots(figsize=(14, 10)) 
lines = [ax.plot([], [], label=ch)[0] for ch in CHANNELS]
ax.set_ylim(0, 5)
ax.set_xlabel("Time")
ax.set_ylabel("Voltage (V)")
ax.legend()
ax.grid()

# Limit digits on x-axis
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))  # HH:MM:SS
fig.autofmt_xdate()


canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

# --- Tkinter Controls ---
control_frame = tk.Frame(root)
control_frame.pack()

def quit_program():
    global running
    running = False      # stop DAQ thread
    root.destroy()       # close Tkinter window

tk.Button(control_frame, text="Quit", command=quit_program).pack(side=tk.LEFT, padx=5)
tk.Button(control_frame, text="Start", command=start_logging).pack(side=tk.LEFT, padx=5)
tk.Button(control_frame, text="Stop", command=stop_logging).pack(side=tk.LEFT, padx=5)
tk.Checkbutton(control_frame, text="Log to CSV", variable=log_to_csv).pack(side=tk.LEFT, padx=5)

# RUN GUI
root.mainloop()
root.protocol("WM_DELETE_WINDOW", quit_program)



