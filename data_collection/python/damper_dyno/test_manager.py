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
        self.daq = daq_controller
        self.gui_queue = queue.Queue()

        self.force_plot = None
        self.disp_plot = None
        self.temp_var = None

        self.channels = ["ai0", "ai1", "ai2"]
        self.mode = ['DIFF', 'DIFF', 'DIFF']
        
        self.current_target_rpm = 0 
        
    def run_test(self, settings):

        # Either a single-speed test OR a multi-step run profile
        run_profile = settings.get("run_profile", None)

        if run_profile is not None:
            self._run_profile_test(settings, run_profile)
        else:
            self._run_single_speed_test(settings)

    # OPTION A: SINGLE-SPEED TEST
    def _run_single_speed_test(self, settings):
        target_speed = settings['run_speed_rpm']
        num_cycles = gearbox_scaling(10, settings['run_num_cycles'])

        logging.info(f"Starting SINGLE test: speed={target_speed} RPM, cycles={num_cycles}")

        self.gui_queue.put({'command': 'reset_plots'})
        
        # SET the target RPM before starting acquisition
        self.current_target_rpm = target_speed

        pwm = convert_speed_to_duty_cycle(
            target_speed,
            [settings["rpm_min"], settings["rpm_max"]],
            [settings["duty_cycle_min"], settings["duty_cycle_max"]]
        )

        self.daq.configure_motor_pwm()
        self.daq.start_motor(pwm)

        self._start_acquisition(settings)

        duration = num_cycles / target_speed * 60.0

        def thread_fcn():
            threading.Event().wait(duration)
            self._end_test(settings)

        threading.Thread(target=thread_fcn, daemon=True).start()

    # OPTION B: RUN PROFILE
    def _run_profile_test(self, settings, run_profile):
        speeds = run_profile[0]  # RPM values
        cycles = run_profile[1]  # CYCLE COUNTS

        assert len(speeds) == len(cycles), "run_profile rows must be equal length"

        self.gui_queue.put({'command': 'reset_plots'})

        logging.info(f"Starting PROFILE test with {len(speeds)} segments.")

        # Initialize with first segment's RPM
        self.current_target_rpm = speeds[0]

        # Start DAQ once
        self._start_acquisition(settings)

        self.daq.configure_motor_pwm()

        def profile_thread():
            for i, (rpm, cycle_count) in enumerate(zip(speeds, cycles)):
                # Calculate duration from cycles and RPM
                if rpm <= 0:
                    logging.warning(f"[Segment {i+1}] RPM={rpm} is invalid, skipping.")
                    continue
                
                # current target RPM for this segment
                self.current_target_rpm = rpm

                # Apply gearbox scaling to cycles
                scaled_cycles = gearbox_scaling(10, cycle_count)
                duration = (scaled_cycles / rpm) * 60.0
                
                logging.info(f"[Segment {i+1}/{len(speeds)}] RPM={rpm:.2f}, Cycles={cycle_count}, Duration={duration:.2f}s")

                pwm = convert_speed_to_duty_cycle(
                    rpm,
                    [settings["rpm_min"], settings["rpm_max"]],
                    [settings["duty_cycle_min"], settings["duty_cycle_max"]]
                )

                if i == 0:
                    self.daq.start_motor(pwm)
                else:
                    self.daq.update_motor_duty_cycle(pwm)

                threading.Event().wait(duration)

            # End of all segments -> stop system
            self._end_test(settings)

        threading.Thread(target=profile_thread, daemon=True).start()

    def _start_acquisition(self, settings):
        fs = settings['sample_rate']
        fc = settings['lpf_cutoff']
        b, a = butter(2, fc / (fs / 2), btype='low')
        lpf_state = np.zeros(max(len(a), len(b)) - 1)
        prev_disp = None

        data_storage = [[
            "RPM",
            "Timestamp",
            "Force (V)", "Force (N)",
            "Displacement (V)", "Displacement (mm)",
            "Temperature (V)", "Temperature (C)",
            "Velocity (mm/s)"
        ]]

        def daq_callback(times, raw_values):
            nonlocal lpf_state, prev_disp

            n = min(len(times), raw_values.shape[1])
            t = times[:n]
            vals = raw_values[:, :n]

            force_v = vals[0]
            disp_v = vals[1]
            temp_v = vals[2]

            force_val = map_voltage_to_force(force_v, settings['force_slope'], settings['force_offset'])
            disp_val = map_voltage_to_displacement(disp_v, settings['disp_slope'], settings['disp_offset'])
            temp_val = map_voltage_to_temperature(temp_v, settings['temp_slope'], settings['temp_offset'])

            # Filtered displacement
            disp_filt, lpf_state = lfilter(b, a, disp_val, zi=lpf_state)

            # Derivative velocity
            if prev_disp is None:
                x_prev = np.concatenate(([disp_filt[0]], disp_filt[:-1]))
            else:
                x_prev = np.concatenate(([prev_disp], disp_filt[:-1]))

            vel = (disp_filt - x_prev) * fs
            prev_disp = disp_filt[-1]

            # Get current target RPM from instance variable
            current_rpm = self.current_target_rpm  # ADD THIS LINE

            # Log rows
            for i in range(n):
                data_storage.append([
                    f"{current_rpm:.2f}",           # target motor speed
                    t[i],                           # timestamp
                    f"{force_v[i]:.4f}",            # load cell voltage
                    f"{force_val[i]:.4f}",          # force (N)
                    f"{disp_v[i]:.4f}",             # linpot voltage
                    f"{disp_val[i]:.4f}",           # displacement (mm)
                    f"{temp_v[i]:.4f}",             # IR temp voltage
                    f"{temp_val[i]:.4f}",           # temperature (C)
                    f"{vel[i]:.4f}"                 # velocity (mm/s)
                ])

            # GUI update packet
            self.gui_queue.put({
                "times": t,
                "force": force_val.tolist(),
                "disp": disp_val.tolist(),
                "vel": vel.tolist(),
                "temp": temp_val[-1]
            })

        self.data_storage = data_storage
        self.daq.start_acquisition(
            self.channels,
            self.mode,
            sample_rate=settings['sample_rate'],
            chunk_size=settings['chunk_size'],
            callback=daq_callback
        )

    def _end_test(self, settings):
        logging.info("Test finished -> stopping motor and acquisition.")
        self.daq.stop_motor()
        self.daq.stop_acquisition()
        save_test_data(self.data_storage, settings)