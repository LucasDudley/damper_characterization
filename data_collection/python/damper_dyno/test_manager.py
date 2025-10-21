import threading
import queue
from utils import (
    convert_speed_to_duty_cycle, 
    save_test_data,
    gearbox_scaling
    )

class TestManager:
    def __init__(self, daq_controller):
        """
        Initialize the TestManager.
        """
        self.daq = daq_controller
        self.gui_queue = queue.Queue()
        
        self.force_plot = None
        self.disp_plot = None
        self.temp_var = None

        self.channels = ["ai0", "ai1", "ai2"] # LOAD CELL / LINPOT / IR TEMP
        self.mode = ['DIFF', 'RSE', 'RSE']

    # In class TestManager:

    def run_test(self, settings):
        """
        Runs a complete test cycle based on the provided settings dictionary.
        """
        # Extract run parameters from the settings dictionary
        target_speed = settings['run_speed_rpm']
        num_cycles = gearbox_scaling(10, settings['run_num_cycles'])
        
        print(f"Starting test with speed: {target_speed} RPM (M), Cycles: {num_cycles} (M)" )
        
        self.gui_queue.put({'command': 'reset_plots'})

        # Configure and start the motor
        pwm = convert_speed_to_duty_cycle(target_speed, 
                                          [settings["rpm_min"], settings["rpm_max"]],
                                          [settings["duty_cycle_min"], settings["duty_cycle_max"]])
        self.daq.configure_motor_pwm()
        self.daq.start_motor(pwm)

        # Setup for data logging
        headers = ["Timestamp", "Force (V)", "Force (N)", "Displacement (V)", "Displacement (mm)", "Temperature (V)", "Temperature (C)"]
        data_storage = [headers]

        # This callback function runs in the DAQ's background thread
        def daq_callback(times, raw_values):
            n = min(len(times), raw_values.shape[1])
            times_chunk = times[:n]
            raw_values_chunk = raw_values[:, :n]

            # Use the passed-in settings from the GUI for mapping
            force_v = raw_values_chunk[0]
            disp_v = raw_values_chunk[1]
            temp_v = raw_values_chunk[2]

            # The calculation is now dynamic based on the settings dictionary
            force_physical = (force_v * settings['force_slope']) + settings['force_offset']
            disp_physical = (disp_v * settings['disp_slope']) + settings['disp_offset']
            temp_physical = (temp_v * settings['temp_slope']) + settings['temp_offset']
            
            # Log the data
            for i in range(n):
                row = [times_chunk[i], force_v[i], force_physical[i], disp_v[i], disp_physical[i], temp_v[i], temp_physical[i]]
                data_storage.append(row)
            
            # Put data onto the queue for the GUI thread to process
            gui_data_packet = {
                'times': times_chunk,
                'force': force_physical.tolist(),
                'disp': disp_physical.tolist(),
                'temp': temp_physical[-1] if len(temp_physical) > 0 else None
            }
            self.gui_queue.put(gui_data_packet)

        # Start the DAQ acquisition
        self.daq.start_acquisition(
            self.channels,
            self.mode,
            sample_rate=settings['sample_rate'],
            chunk_size=settings['chunk_size'],
            callback=daq_callback
        )

        # This thread controls the duration of the test
        def test_thread():
            test_duration = num_cycles / target_speed * 60.0
            threading.Event().wait(test_duration)

            if self.daq.ai_task is not None:
                print("Test duration finished. Stopping motor and acquisition.")
                self.daq.stop_motor()
                self.daq.stop_acquisition()
                
                # Make sure the save utility can handle the settings dictionary
                save_test_data(data_storage, settings) 

        # Run the duration controller in the background
        threading.Thread(target=test_thread, daemon=True).start()