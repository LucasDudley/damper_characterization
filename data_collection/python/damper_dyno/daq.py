import nidaqmx
import numpy as np
import datetime
import threading
from nidaqmx.constants import TerminalConfiguration, AcquisitionType

class DAQController:
    def __init__(self, device_name="Dev1"):
        self.device_name = device_name
        self.ai_task = None
        self.pwm_task = None
        self.running = False

    # ---------------- PWM Control ----------------
    def set_motor_pwm(self, duty_cycle: float, frequency=50):
        if self.pwm_task:
            self.pwm_task.close()
        self.pwm_task = nidaqmx.Task()
        self.pwm_task.co_channels.add_co_pulse_chan_freq(
            f"{self.device_name}/ctr0",
            name_to_assign_to_channel="PWM",
            freq=frequency,
            duty_cycle=duty_cycle / 100.0
        )
        self.pwm_task.start()

    def stop_motor_pwm(self):
        if self.pwm_task:
            self.pwm_task.stop()
            self.pwm_task.close()
            self.pwm_task = None

    # ---------------- Analog Acquisition ----------------
    def start_analog_acquisition(self, channels, sample_rate, chunk_size, callback):
        self.running = True
        self.ai_task = nidaqmx.Task()
        for ch in channels:
            self.ai_task.ai_channels.add_ai_voltage_chan(
                f"{self.device_name}/{ch}",
                terminal_config=TerminalConfiguration.RSE
            )
        self.ai_task.timing.cfg_samp_clk_timing(
            rate=sample_rate,
            sample_mode=AcquisitionType.CONTINUOUS
        )
        self.ai_task.start()

        def acquire_loop():
            sample_count = 0
            start_time = datetime.datetime.now()

            while self.running:
                try:
                    available = self.ai_task.in_stream.avail_samp_per_chan
                    if available == 0:
                        continue

                    n_to_read = min(available, chunk_size)
                    raw_data = self.ai_task.read(number_of_samples_per_channel=n_to_read, timeout=0.1)
                    data = np.array(raw_data)
                    if data.ndim == 1:  # single channel
                        data = data.reshape((1, -1))

                    # generate timestamps aligned with data
                    times = [start_time + datetime.timedelta(seconds=(sample_count + i)/sample_rate)
                             for i in range(data.shape[1])]
                    sample_count += data.shape[1]

                    # CALLBACK: truncate in case of misalignment
                    n = min(len(times), data.shape[1])
                    times = times[:n]
                    values = data[:, :n]

                    if callback is not None:
                        callback(times, values)

                except Exception as e:
                    print(f"DAQ error: {e}")
                    self.running = False
                    break

        threading.Thread(target=acquire_loop, daemon=True).start()

    def stop_analog_acquisition(self):
        self.running = False
        if self.ai_task:
            self.ai_task.stop()
            self.ai_task.close()
            self.ai_task = None

