import threading
import queue
import logging
from scipy.signal import butter, lfilter
import numpy as np
from utils import (
    convert_speed_to_duty_cycle, 
    save_test_data,
    gearbox_scaling,
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
        self.gui_queue = queue.Queue()
        
        self.force_plot = None
        self.disp_plot = None
        self.temp_var = None

        self.channels = ["ai0", "ai1", "ai2"] # Load cell / Linpot / IR temp
        self.mode = ['DIFF', 'DIFF', 'DIFF']

    def run_test(self, settings):
        """
        Runs a complete test cycle based on the provided settings dictionary.
        """
        # Extract run parameters from the settings dictionary
        target_speed = settings['run_speed_rpm']
        num_cycles = gearbox_scaling(10, settings['run_num_cycles'])
        
        logging.info(f"Starting test with speed: {target_speed} RPM (M), Cycles: {num_cycles} (M)" )
        
        self.gui_queue.put({'command': 'reset_plots'})

        # Configure and start the motor
        pwm = convert_speed_to_duty_cycle(target_speed, 
            [settings["rpm_min"], settings["rpm_max"]],
            [settings["duty_cycle_min"], settings["duty_cycle_max"]])
        self.daq.configure_motor_pwm()
        self.daq.start_motor(pwm)

        # Setup for data logging
        headers = ["Timestamp",
                   "Force (V)", "Force (N)", 
                   "Displacement (V)", "Displacement (mm)", 
                   "Temperature (V)", "Temperature (C)",
                   "Velocity (mm/s)"]
        data_storage = [headers]

        # Low-pass filter for displacement → velocity pipeline
        fs = settings['sample_rate']
        fc = settings['lpf_cutoff']  # Hz
        b, a = butter(2, fc / (fs / 2), btype='low') # Butterworth 2nd-order LPF
        lpf_state = np.zeros(max(len(a), len(b)) - 1) # Filter state (persist across callback chunks)

        # prev filtered displacement sample for velocity numerical derivative
        prev_disp = None

        # This callback fcn runs in the DAQ's background thread
        def daq_callback(times, raw_values):
            n = min(len(times), raw_values.shape[1])
            times_chunk = times[:n]
            raw_values_chunk = raw_values[:, :n]
            force_v = raw_values_chunk[0]
            disp_v = raw_values_chunk[1]
            temp_v = raw_values_chunk[2]

            # scale values using mapping functions
            force_val = map_voltage_to_force(force_v, settings['force_slope'], settings['force_offset'])
            disp_val = map_voltage_to_displacement(disp_v, settings['disp_slope'], settings['disp_offset'])
            temp_val = map_voltage_to_temperature(temp_v, settings['temp_slope'], settings['temp_offset'])

            # low-pass filter
            nonlocal lpf_state, prev_disp

            disp_filt, lpf_state = lfilter(b, a, disp_val, zi=lpf_state)

            # build previous-sample vector for numerical derivative
            if prev_disp is None:
                x_prev = np.concatenate(([disp_filt[0]], disp_filt[:-1]))
            else:
                x_prev = np.concatenate(([prev_disp], disp_filt[:-1]))

            vel = (disp_filt - x_prev) * fs
            prev_disp = disp_filt[-1]

            
            # Log the data
            for i in range(n):
                row = [
                        times_chunk[i],
                        force_v[i], force_val[i],
                        disp_v[i], disp_val[i],
                        temp_v[i], temp_val[i],
                        vel[i] 
                    ]
                data_storage.append(row)
            
            # Put data onto the queue for the GUI thread
            gui_data_packet = {
                'times': times_chunk,
                'force': force_val.tolist(),
                'disp': disp_val.tolist(),
                'vel': vel.tolist(),
                'temp': temp_val[-1] if len(temp_val) > 0 else None
            }
            self.gui_queue.put(gui_data_packet)

        # Start DAQ acquisition
        self.daq.start_acquisition(
            self.channels,
            self.mode,
            sample_rate=settings['sample_rate'],
            chunk_size=settings['chunk_size'],
            callback=daq_callback
        )

        # thread to control test duration
        def test_thread():
            test_duration = num_cycles / target_speed * 60.0
            threading.Event().wait(test_duration)

            if self.daq.ai_task is not None:
                logging.info("Test duration finished. Stopping motor and acquisition.")
                self.daq.stop_motor()
                self.daq.stop_acquisition()
                
                # Make sure the save fcn can handle the settings dictionary
                save_test_data(data_storage, settings) 

        # Run the duration controller in the background
        threading.Thread(target=test_thread, daemon=True).start()