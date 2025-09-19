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
CHANNEL = "ai1"
SAMPLE_RATE = 300     # Hz
CHUNK_SIZE = 50        # Samples per read
PLOT_WINDOW_SECONDS = 3 # How many seconds of data to display

def setup_plot():
    """Creates and configures the Matplotlib figure and axes."""

    fig, ax = plt.subplots(figsize=(10, 5))
    line, = ax.plot([], [], marker='.')
    ax.set_xlabel("Time")
    ax.set_ylabel("Voltage (V)")
    ax.set_title("Real-Time NI-DAQmx Data")
    ax.grid(True)
    formatter = mdates.DateFormatter('%H:%M:%S')
    ax.xaxis.set_major_formatter(formatter)
    fig.autofmt_xdate()
    return fig, ax, line

def setup_daq_task():
    """Creates and configures the NI-DAQmx analog input task for RSE."""

    task = nidaqmx.Task()
    
    # Add the terminal_config argument here
    task.ai_channels.add_ai_voltage_chan(
        f"{DEVICE_NAME}/{CHANNEL}",
        terminal_config=TerminalConfiguration.RSE
    )
    
    task.timing.cfg_samp_clk_timing(
        rate=SAMPLE_RATE,
        sample_mode=AcquisitionType.CONTINUOUS
    )
    
    return task

def create_update_function(task, line, data_q, time_q):
    """Creates the update function for the animation, capturing necessary state."""

    # Use a dictionary to hold state, avoiding global variables in the update loop
    state = {
        "sample_count": 0,
        "start_time": datetime.datetime.now()
    }

    def update(frame):
        """Reads new data from the DAQ and updates the plot."""
        new_data = task.read(number_of_samples_per_channel=CHUNK_SIZE)

        seconds_elapsed = np.arange(
            state["sample_count"], state["sample_count"] + CHUNK_SIZE
        ) / SAMPLE_RATE
        
        new_times = [
            state["start_time"] + datetime.timedelta(seconds=s) for s in seconds_elapsed
        ]
        state["sample_count"] += CHUNK_SIZE

        data_q.extend(new_data)
        time_q.extend(new_times)
        line.set_data(time_q, data_q)

        # Update axis limits for a scrolling view
        if time_q:
            ax = line.axes
            ax.set_xlim(
                time_q[-1] - datetime.timedelta(seconds=PLOT_WINDOW_SECONDS),
                time_q[-1]
            )
            ax.relim()
            ax.autoscale_view(scalex=False, scaley=True)

    return update

def main():
    """Main function to orchestrate the setup and execution of the DAQ plot."""

    fig, ax, line = setup_plot()

    # Create data buffers
    max_plot_points = int(PLOT_WINDOW_SECONDS * SAMPLE_RATE)
    data_q = deque(maxlen=max_plot_points)
    time_q = deque(maxlen=max_plot_points)

    task = setup_daq_task()

    try:
        with task:
            update_func = create_update_function(task, line, data_q, time_q)

            ani = animation.FuncAnimation(
                fig,
                update_func,
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

if __name__ == "__main__":
    main()