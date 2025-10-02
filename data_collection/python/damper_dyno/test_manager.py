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
        
        self.force_plot = None
        self.disp_plot = None
        self.temp_var = None # hold the tk.StringVar

        self.signal_config = {
            "ai0": ("Force", "N", map_voltage_to_force),
            "ai1": ("Displacement", "mm", map_voltage_to_displacement),
            "ai2": ("Temperature", "C", map_voltage_to_temperature),
        }
        self.channels = ["ai0", "ai1", "ai2"]

    def run_test(self, target_speed, num_cycles, sample_rate=300, chunk_size=100):
        # Reset both plots before starting
        if self.force_plot:
            self.force_plot.reset()
        if self.disp_plot:
            self.disp_plot.reset()

        pwm = convert_speed_to_duty_cycle(target_speed)
        self.daq.configure_motor_pwm()
        self.daq.start_motor(pwm)

        # Setup for data logging
        headers = ["Timestamp"]
        for ch in self.channels:
            name, units, _ = self.signal_config[ch]
            headers.append(f"{name}_Voltage (V)")
            headers.append(f"{name} ({units})")
        data_storage = [headers]

        # Separate queues for each plot
        time_q = []
        force_q = []
        disp_q = []

        # The callback function with the new data routing logic
        def callback(times, raw_values):
            n = min(len(times), raw_values.shape[1])
            times = times[:n]
            raw_values = raw_values[:, :n]

            # Map raw voltages to physical values
            mapped_values = []
            for i, ch in enumerate(self.channels):
                mapping_func = self.signal_config[ch][2]
                mapped_channel_data = [mapping_func(v) for v in raw_values[i]]
                mapped_values.append(mapped_channel_data)

            # Data logging to data_storage
            for i in range(n):
                row = [times[i]]
                for ch_idx in range(len(self.channels)):
                    row.append(raw_values[ch_idx][i])
                    row.append(mapped_values[ch_idx][i])
                data_storage.append(row)

            # split data for different destinations
            force_data = mapped_values[0]   # Data from ai0
            disp_data = mapped_values[1]    # Data from ai1
            temp_data = mapped_values[2]    # Data from ai2

            # update the separate queues for plotting
            time_q.extend(times)
            force_q.extend(force_data)
            disp_q.extend(disp_data)

            if self.force_plot:
                self.force_plot.update(time_q, [force_q], sample_rate)
            
            if self.disp_plot:
                self.disp_plot.update(time_q, [disp_q], sample_rate)

            # Update digital readout using the thread-safe StringVar
            if self.temp_var and temp_data:
                latest_temp = temp_data[-1] # Get the most recent temp value
                self.temp_var.set(f"{latest_temp:.1f} °C")

        # Start acquisition
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


