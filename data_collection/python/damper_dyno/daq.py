import nidaqmx
import numpy as np
import datetime
import threading
from nidaqmx.constants import TerminalConfiguration, AcquisitionType

class DAQController:
    def __init__(self, device_name="Dev1"):
        """
        Initialize the DAQ controller.
        """
        self.device_name = device_name
        self.ai_task = None             # Task object for analog input acquisition
        self.pwm_task = None            # Task object for PWM motor control
        self.running = False            # Flag to indicate if acquisition is running

    # PWM Control
    def set_motor_pwm(self, duty_cycle: float, frequency=1000):
        """
        Configure and start a PWM signal to control a motor.
        """

        # close existing PWM task before creating a new one
        if self.pwm_task:
            self.pwm_task.close()

        # create new counter output task for PWM generation
        self.pwm_task = nidaqmx.Task()
        self.pwm_task.co_channels.add_co_pulse_chan_freq(
            f"{self.device_name}/ctr0",             # use counter 0 on the device
            name_to_assign_to_channel="PWM",        # assign name to the channel
            freq=frequency,                         # set PWM frequency
            duty_cycle=duty_cycle / 100.0           # convert % duty cycle to 0–1 range
        )
        self.pwm_task.start()                       # start PWM output

    def stop_motor_pwm(self):
        """Stop and close the PWM task if it exists."""
        if self.pwm_task:
            self.pwm_task.stop()
            self.pwm_task.close()
            self.pwm_task = None

    # Data Acquisition
    def start_acquisition(self, analog_channels, sample_rate, chunk_size, callback):
        """
        Start continuous acquisition in a separate thread.

        channels (list): List of channel nmes, e.g., ["ai0" "ai1"]
        sample_rate (float): Samples per second per channel
        chunk_size (int): Number of samples to read at a time
        callback (function): Function to call with new data (times, values)
        """
        self.running = True

        # Create and configure an analog input task
        self.ai_task = nidaqmx.Task()
        for ch in analog_channels:
            self.ai_task.ai_channels.add_ai_voltage_chan(
                f"{self.device_name}/{ch}",                 # Add channel to task
                terminal_config=TerminalConfiguration.RSE   # Use referenced single-ended mode
            )

        # Configure continuous sampling clock
        self.ai_task.timing.cfg_samp_clk_timing(
            rate=sample_rate,
            sample_mode=AcquisitionType.CONTINUOUS
        )
        self.ai_task.start()

        # Background acquisition loop
        def acquire_loop():
            sample_count = 0
            start_time = datetime.datetime.now()

            while self.running:
                try:
                    available = self.ai_task.in_stream.avail_samp_per_chan # Check how many samples are available
                    if available == 0:
                        continue  # no data yet

                    # Read up to chunk_size samples per channel
                    n_to_read = min(available, chunk_size)
                    raw_data = self.ai_task.read(number_of_samples_per_channel=n_to_read, timeout=0.1)

                    data = np.array(raw_data) # convert to NumPy array
                    if data.ndim == 1:
                        data = data.reshape((1, -1))

                    # generate timestamps for each sample
                    times = [start_time + datetime.timedelta(seconds=(sample_count + i)/sample_rate)
                             for i in range(data.shape[1])]
                    sample_count += data.shape[1]

                    # Truncate in case of mismatch between times and data
                    n = min(len(times), data.shape[1])
                    times = times[:n]
                    values = data[:, :n]

                    # pass data to user-provided callback function
                    if callback is not None:
                        callback(times, values)

                except Exception as e:
                    print(f"DAQ error: {e}")
                    self.running = False  # stop acquisition loop on error
                    break

        # Run acquisition loop in a separate thread (non-blocking)
        threading.Thread(target=acquire_loop, daemon=True).start()

    def stop_acquisition(self):
        """Stop analog acquisition and safely close the task."""
        self.running = False
        if self.ai_task:
            try:
                self.ai_task.stop()
                self.ai_task.close()
            except Exception as e:
                print(f"DAQ stop warning: {e}")
            self.ai_task = None



