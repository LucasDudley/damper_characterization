# test_manager.py
import threading
import queue # Import the queue module
from utils import (
    convert_speed_to_duty_cycle, 
    save_test_data,
    map_voltage_to_displacement,
    map_voltage_to_force,
    map_voltage_to_temperature
)

class TestManager:
    def __init__(self, daq_controller):
        """
        Initialize the TestManager.
        """
        self.daq = daq_controller
        
        self.force_plot = None
        self.disp_plot = None
        self.temp_var = None

        # Create a thread-safe queue for GUI updates
        self.gui_queue = queue.Queue()

        self.signal_config = {
            "ai0": ("Force", "N", map_voltage_to_force),
            "ai1": ("Displacement", "mm", map_voltage_to_displacement),
            "ai2": ("Temperature", "C", map_voltage_to_temperature),
        }
        self.channels = ["ai0", "ai1", "ai2"]

    def run_test(self, target_speed, num_cycles, sample_rate=300, chunk_size=100):
        if self.force_plot:
            self.force_plot.reset()
        if self.disp_plot:
            self.disp_plot.reset()

        pwm = convert_speed_to_duty_cycle(target_speed)
        self.daq.configure_motor_pwm()
        self.daq.start_motor(pwm)

        headers = ["Timestamp"]
        for ch in self.channels:
            name, units, _ = self.signal_config[ch]
            headers.append(f"{name}_Voltage (V)")
            headers.append(f"{name} ({units})")
        data_storage = [headers]

        def daq_callback(times, raw_values):
            
            n = min(len(times), raw_values.shape[1])
            times_chunk = times[:n]
            raw_values_chunk = raw_values[:, :n]

            mapped_values = []
            for i, ch in enumerate(self.channels):
                mapping_func = self.signal_config[ch][2]
                mapped_channel_data = [mapping_func(v) for v in raw_values_chunk[i]]
                mapped_values.append(mapped_channel_data)

            #Data Logging
            for i in range(n):
                row = [times_chunk[i]]
                for ch_idx in range(len(self.channels)):
                    row.append(raw_values_chunk[ch_idx][i])
                    row.append(mapped_values[ch_idx][i])
                data_storage.append(row)

            force_data = mapped_values[0]
            disp_data = mapped_values[1]
            temp_data = mapped_values[2]
            
            gui_data_packet = {
                'times': times_chunk,
                'force': force_data,
                'disp': disp_data,
                'temp': temp_data[-1] if temp_data else None
            }
            self.gui_queue.put(gui_data_packet)

        # Start acquisition with the modified callback
        self.daq.start_acquisition(
            analog_channels=self.channels,
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            callback=daq_callback
        )

        def test_thread():
            test_duration = num_cycles / target_speed * 60
            # Use a stoppable event instead of a blind wait, in case of E-STOP
            stop_event = threading.Event()
            stop_event.wait(test_duration) 
            
            # Check if the task is still running before stopping
            if self.daq.ai_task is not None:
                self.daq.stop_motor()
                self.daq.stop_acquisition()
                save_test_data(data_storage)

        threading.Thread(target=test_thread, daemon=True).start()

