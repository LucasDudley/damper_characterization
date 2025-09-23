import threading
from utils import (
    convert_speed_to_duty_cycle, 
    save_test_data,
    map_voltage_to_displacement,
    map_voltage_to_force,
    map_voltage_to_temperature
    )

class TestManager:
    def __init__(self, daq_controller, realtime_plot=None):
        """
        Initialize the TestManager.
        """
        self.daq = daq_controller
        self.realtime_plot = realtime_plot

        self.signal_config = {
            # DAQ Channel: (Signal Name, Units, Mapping Function)
            "ai0": ("Force", "N", map_voltage_to_force),
            "ai1": ("Displacement", "mm", map_voltage_to_displacement),
            "ai2": ("Temperature", "°C", map_voltage_to_temperature),
        }
        # Ordered list of channels for consistent data processing
        self.channels = ["ai0", "ai1", "ai2"]

    def run_test(self, target_speed, num_cycles, sample_rate=300, chunk_size=100):
        """
        Run a damper test with specified speed and number of cycles.
        """
        # reset the realtime plot if rerunning test
        if self.realtime_plot:
            self.realtime_plot.reset()

        pwm = convert_speed_to_duty_cycle(target_speed)
        self.daq.configure_motor_pwm()
        self.daq.start_motor(pwm)

        # Create headers for the CSV file
        headers = ["Timestamp"]
        for ch in self.channels:
            name, units, _ = self.signal_config[ch]
            headers.append(f"{name}_Voltage (V)")
            headers.append(f"{name} ({units})")

        # Storage list ([timestamp, AI0, AI1, AI2...])
        data_storage = []

        # Queues for real-time plotting
        time_q = []                         # Stores timestamps
        mapped_data_qs = [[] for _ in self.channels]

        # callback function executed every time new data is read from DAQ
        def callback(times, raw_values):
            n = min(len(times), raw_values.shape[1])
            times = times[:n]
            raw_values = raw_values[:, :n]

            # map raw voltages to physical values
            mapped_values = []
            for i, ch in enumerate(self.channels):
                mapping_func = self.signal_config[ch][2]
                mapped_channel_data = [mapping_func(v) for v in raw_values[i]]
                mapped_values.append(mapped_channel_data)

            # store raw and mapped data for CSV export
            for i in range(n):
                row = [times[i]]
                for ch_idx in range(len(self.channels)):
                    row.append(raw_values[ch_idx][i])   # Append raw voltage
                    row.append(mapped_values[ch_idx][i]) # Append mapped value
                data_storage.append(row)

            # Update queues with MAPPED data for plotting
            time_q.extend(times)
            for dq, mapped_data in zip(mapped_data_qs, mapped_values):
                dq.extend(mapped_data)

            # update live plot with latest MAPPED data
            if self.realtime_plot:
                # Pass the mapped data queues to the plot
                self.realtime_plot.update(time_q, mapped_data_qs, sample_rate)

        self.daq.start_acquisition(
            analog_channels=self.channels,
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            callback=callback
        )

        # background thread to control test duration
        def test_thread():
            # wait for test duration to complete
            test_duration = num_cycles / target_speed * 60
            threading.Event().wait(test_duration)

            # stop PWM but keep task alive in case you want to restart quickly
            self.daq.stop_motor()
            self.daq.stop_acquisition()

            # save collected data to CSV
            save_test_data(data_storage)

        # run test duration thread in the background
        threading.Thread(target=test_thread, daemon=True).start()


