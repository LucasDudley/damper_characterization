import nidaqmx
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import datetime
import matplotlib.dates as mdates
from nidaqmx.constants import TerminalConfiguration, AcquisitionType

# --- Configuration Constants ---
DEVICE_NAME = "Dev1"
CHANNELS = ["ai0", "ai1"]  # <-- Multiple channels
SAMPLE_RATE = 300      # Hz
CHUNK_SIZE = 50        # Samples per read
PLOT_WINDOW_SECONDS = 3 # How many seconds of data to display

def setup_plot():
    """Creates and configures the Matplotlib figure and axes."""
    fig, ax = plt.subplots(figsize=(10, 5))
    line1, = ax.plot([], [], marker='.', label="ai0")
    line2, = ax.plot([], [], marker='.', label="ai1")
    ax.set_xlabel("Time")
    ax.set_ylabel("Voltage (V)")
    ax.grid(True)
    ax.legend()
    formatter = mdates.DateFormatter('%H:%M:%S')
    ax.xaxis.set_major_formatter(formatter)
    fig.autofmt_xdate()
    return fig, ax, line1, line2

def setup_daq_task():
    """Creates and configures the NI-DAQmx analog input task for RSE."""
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

def create_update_function(task, line1, line2, data_qs, time_q):
    """Creates the update function for the animation."""
    state = {
        "sample_count": 0,
        "start_time": datetime.datetime.now()
    }

    def update(frame):
        """Reads new data from the DAQ and updates the plot."""
        new_data = task.read(number_of_samples_per_channel=CHUNK_SIZE)
        # new_data is a list of lists: [[ai0_samples], [ai1_samples]]
        new_data = np.array(new_data)

        seconds_elapsed = np.arange(
            state["sample_count"], state["sample_count"] + CHUNK_SIZE
        ) / SAMPLE_RATE
        
        new_times = [
            state["start_time"] + datetime.timedelta(seconds=s) for s in seconds_elapsed
        ]
        state["sample_count"] += CHUNK_SIZE

        time_q.extend(new_times)
        for i, data_q in enumerate(data_qs):
            data_q.extend(new_data[i])

        line1.set_data(time_q, data_qs[0])
        line2.set_data(time_q, data_qs[1])

        # Update axis limits for a scrolling view
        if time_q:
            ax = line1.axes
            ax.set_xlim(
                time_q[-1] - datetime.timedelta(seconds=PLOT_WINDOW_SECONDS),
                time_q[-1]
            )
            ax.relim()
            ax.autoscale_view(scalex=False, scaley=True)

    return update

def main():
    """Main function to orchestrate the setup and execution of the DAQ plot."""
    fig, ax, line1, line2 = setup_plot()

    max_plot_points = int(PLOT_WINDOW_SECONDS * SAMPLE_RATE)
    data_qs = [deque(maxlen=max_plot_points) for _ in CHANNELS]
    time_q = deque(maxlen=max_plot_points)

    task = setup_daq_task()

    try:
        with task:
            update_func = create_update_function(task, line1, line2, data_qs, time_q)

            ani = animation.FuncAnimation(
                fig,
                update_func,
                interval=0,
                blit=False,
                cache_frame_data=False
            )

            print("Streaming and plotting data from ai0 and ai1.")
            plt.show()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Script finished.")

if __name__ == "__main__":
    main()
