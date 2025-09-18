import nidaqmx
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import datetime
import matplotlib.dates as mdates

# --- Configuration ---
DEVICE_NAME = "Dev1"
CHANNEL = "ai1"
SAMPLE_RATE = 1000  # Hz
CHUNK_SIZE = 200    # Samples per read
PLOT_WINDOW_SECONDS = 5 # How many seconds of data to display on the plot

# --- Global Data Buffers and Timestamps ---
max_plot_points = int(PLOT_WINDOW_SECONDS * SAMPLE_RATE)
time_q = deque(maxlen=max_plot_points)
data_q = deque(maxlen=max_plot_points)
sample_count = 0
start_time = datetime.datetime.now() # Capture the script's start time

# --- Plot Setup ---
fig, ax = plt.subplots(figsize=(10, 5))
line, = ax.plot([], [], marker='.')
ax.set_xlabel("Time")
ax.set_ylabel("Voltage (V)")
ax.set_title("Real-Time NI-DAQmx Data")
ax.grid(True)

# Format the x-axis to display time in HH:MM:SS format
formatter = mdates.DateFormatter('%H:%M:%S')
ax.xaxis.set_major_formatter(formatter)
fig.autofmt_xdate() # Rotate date labels to prevent overlap

# --- NI-DAQmx Task and Animation ---
try:
    with nidaqmx.Task() as task:
        task.ai_channels.add_ai_voltage_chan(f"{DEVICE_NAME}/{CHANNEL}")
        task.timing.cfg_samp_clk_timing(
            rate=SAMPLE_RATE,
            sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS
        )

        def update(frame):
            """Reads new data and updates the plot."""
            global sample_count
            
            new_data = task.read(number_of_samples_per_channel=CHUNK_SIZE)

            seconds_elapsed = np.arange(sample_count, sample_count + CHUNK_SIZE) / SAMPLE_RATE
            new_times = [start_time + datetime.timedelta(seconds=s) for s in seconds_elapsed]
            sample_count += CHUNK_SIZE

            data_q.extend(new_data)
            time_q.extend(new_times)
            line.set_data(time_q, data_q)

            if time_q:
                ax.set_xlim(
                    time_q[-1] - datetime.timedelta(seconds=PLOT_WINDOW_SECONDS),
                    time_q[-1]
                )
            
            ax.relim()
            ax.autoscale_view(scalex=False, scaley=True)

        # Create the animation, explicitly disabling the frame data cache
        ani = animation.FuncAnimation(
            fig,
            update,
            interval=0,
            blit=False,
            cache_frame_data=False
        )

        print("Streaming and plotting data.")
        plt.show()

except KeyboardInterrupt:
    print("\nInterrupted by user. Stopping.")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    print("Script finished.")