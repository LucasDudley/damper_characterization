import nidaqmx
import numpy as np
import datetime
import threading
from nidaqmx.constants import TerminalConfiguration, AcquisitionType
from nidaqmx.types import CtrFreq
import time
import logging

class DAQController:
    def __init__(self, device_name="Dev1"):
        """
        Initialize the DAQ controller.
        """
        self.ai_task = None
        self.pwm_task = None
        self.do_task = None
        self.pwm_frequency = None

        # Run-profile related
        self.run_profile = None
        self.current_profile_index = 0
        self.is_profile_running = False
        self._profile_thread = None
        self._profile_stop_event = threading.Event()

        self.device_name = device_name
        self.acquisition_thread = None
        self.stop_event = threading.Event()
        self.motor_enable_pin = f"{self.device_name}/port1/line1"
        self.pwm_output_pin = f"{self.device_name}/ctr0"

    def enable_motor(self):
        if self.do_task:
            self.do_task.close()
        try:
            self.do_task = nidaqmx.Task("MotorEnableTask")
            self.do_task.do_channels.add_do_chan(self.motor_enable_pin)
            self.do_task.start()
            self.do_task.write(True)
        except nidaqmx.errors.DaqError as e:
            logging.info(f"Error enabling motor: {e}")
            if self.do_task:
                self.do_task.close()
            self.do_task = None

    def disable_motor(self):
        if self.do_task:
            try:
                self.do_task.write(False)
            except nidaqmx.errors.DaqError as e:
                logging.info(f"Warning writing LOW to motor enable pin: {e}")
            finally:
                self.do_task.stop()
                self.do_task.close()
                self.do_task = None

    def configure_motor_pwm(self, frequency=1000):
        if self.pwm_task:
            self.pwm_task.close()
        
        self.pwm_frequency = frequency
        self.pwm_task = nidaqmx.Task("MotorPWMTask")
        self.pwm_task.co_channels.add_co_pulse_chan_freq(
            self.pwm_output_pin,
            name_to_assign_to_channel="PWM",
            freq=self.pwm_frequency,
            duty_cycle=1e-4 # Initial dummy value
        )
        self.pwm_task.timing.cfg_implicit_timing(sample_mode=AcquisitionType.CONTINUOUS)

    def start_motor(self, duty_cycle: float):
        """Sets initial duty cycle as a property, then starts the PWM task."""
        self.enable_motor()

        if self.pwm_task is None:
            self.configure_motor_pwm()
            
        # Before starting the task, set the duty cycle as a property.
        safe_duty = max(min(duty_cycle / 100.0, 1.0), 0.0)
        logging.info(f"Setting initial PWM property to Duty Cycle: {safe_duty:.3f}")
        self.pwm_task.co_channels.all.co_pulse_duty_cyc = safe_duty

        try:
            self.pwm_task.start()
        except nidaqmx.errors.DaqError as e:
            if getattr(e, "error_code", None) == -200479:
                logging.info("Warning: Motor task was already running. Updating duty cycle instead.")
                self.update_motor_duty_cycle(duty_cycle)
            else:
                raise

    def update_motor_duty_cycle(self, duty_cycle: float):
        """Updates the duty cycle of an already running task using task.write()."""
        if self.pwm_task is None or self.pwm_frequency is None:
            logging.info("Error: PWM task or frequency is not configured.")
            return

        safe_duty = max(min(duty_cycle / 100.0, 1.0), 0.0) 
        
        logging.info(f"Writing to running task >> Freq: {self.pwm_frequency} Hz, Duty Cycle: {safe_duty:.2f}")
        
        try:
            # Create the required CtrFreq object
            sample = CtrFreq(freq=self.pwm_frequency, duty_cycle=safe_duty)
            # Write the sample to the running task
            self.pwm_task.write(sample, timeout=2.0)
            logging.info("Successfully wrote new CtrFreq sample to PWM task.")
        except nidaqmx.errors.DaqError as e:
            logging.info(f"Error writing new CtrFreq sample: {e}")

    def stop_motor(self, slowdown_time=1.0):
        """
        stops the motor:
        1. Set PWM duty cycle to 0 for a buffer period to allow slowdown.
        2. Then disable motor and stop/close PWM task.
        """
        if self.pwm_task is not None:
            try:
                logging.info(f"Motor Ramp Down")
                # Write a near-zero duty cycle to let it coast down
                self.update_motor_duty_cycle(1e-2)
                time.sleep(slowdown_time)
            except Exception as e:
                logging.info(f"Warning while ramping down PWM: {e}")

        # Disable motor (digital output LOW)
        self.disable_motor()

        # Stop and close PWM task
        if self.pwm_task is not None:
            try:
                self.pwm_task.stop()
                self.pwm_task.close()
            except Exception as e:
                logging.info(f"Warning stopping PWM task: {e}")
            finally:
                self.pwm_task = None

    def _acquisition_callback(self, task_handle, every_n_samples_event_type,
                              number_of_samples, callback_data):
        
        # safeguard
        if self.ai_task is None or self.ai_task.is_task_done():
            return 0

        try:
            raw_data = self.ai_task.read(number_of_samples_per_channel=number_of_samples)
            data = np.array(raw_data)
            if data.ndim == 1:
                data = data.reshape((1, -1))
            
            times = [
                self.start_time + datetime.timedelta(seconds=(self.total_samples_acquired + i) / self.sample_rate)
                for i in range(data.shape[1])
            ]
            self.total_samples_acquired += data.shape[1]

            if self.data_callback:
                self.data_callback(times, data)
            return 0
        except Exception as e:
            logging.info(f"Error in DAQ callback: {e}")
            return 1

    def start_acquisition(self, analog_channels, mode, sample_rate, chunk_size, callback):
        if self.ai_task:
            logging.info("An acquisition is already running. Stop it first.")
            return
        self.data_callback = callback
        self.sample_rate = sample_rate
        self.total_samples_acquired = 0
        try:
            self.ai_task = nidaqmx.Task("AnalogInputTask")
            for idx, ch in enumerate(analog_channels):
                if mode[idx] == 'RSE':
                    self.ai_task.ai_channels.add_ai_voltage_chan(
                        f"{self.device_name}/{ch}",
                        terminal_config=TerminalConfiguration.RSE)
                elif mode[idx] == 'DIFF':
                    self.ai_task.ai_channels.add_ai_voltage_chan(
                        f"{self.device_name}/{ch}",
                        terminal_config=TerminalConfiguration.DIFF)
                else:
                    logging.info("Error: Mode not 'RSE or 'DIFF' ")

            self.ai_task.timing.cfg_samp_clk_timing(
                rate=sample_rate,
                sample_mode=AcquisitionType.CONTINUOUS
            )
            self.ai_task.register_every_n_samples_acquired_into_buffer_event(
                chunk_size, self._acquisition_callback
            )
            self.start_time = datetime.datetime.now()
            self.ai_task.start()
            logging.info("DAQ acquisition started successfully.")
        except Exception as e:
            logging.info(f"Failed to start DAQ acquisition: {e}")
            if self.ai_task:
                self.ai_task.close()
                self.ai_task = None

    def stop_acquisition(self):
        if self.ai_task:
            try:
                self.ai_task.stop() # Stop task
                self.ai_task.register_every_n_samples_acquired_into_buffer_event(0, None) # Unregister callback
                self.ai_task.close() # Close task

                logging.info("DAQ acquisition stopped.")
            except Exception as e:
                logging.info(f"Warning stopping AI task: {e}")
            finally:
                self.ai_task = None
        self.data_callback = None


    def close(self):
        self.stop_motor()
        self.stop_acquisition()

    def emergency_stop(self):
        logging.info("⚠ DAQ E-STOP ⚠")

        # Immediately disable motor 
        self.disable_motor()

        # Stop PWM generation if running
        if self.pwm_task is not None:
            try:
                self.pwm_task.stop()
                self.pwm_task.close()
            except Exception as e:
                logging.info(f"Warning stopping PWM task during E-STOP: {e}")
            finally:
                self.pwm_task = None

        # Stop acquisition as usual
        self.stop_acquisition()

    def load_run_profile_from_matrix(self, matrix):
        """
        Accepts run_profile in the row-wise format:
        matrix = [
            [speed1, speed2, ...],
            [cycles1, cycles2, ...]
        ]
        Produces self.run_profile = [(speed1, cycles1), ...]
        """
        if not isinstance(matrix, (list, tuple)) or len(matrix) < 2:
            raise ValueError("run_profile must be a 2xN list/tuple.")
        speeds = matrix[0]
        cycles = matrix[1]
        if len(speeds) != len(cycles):
            raise ValueError("run_profile rows must be the same length.")
        self.run_profile = [(float(s), float(c)) for s, c in zip(speeds, cycles)]
        self.current_profile_index = 0
        logging.info(f"Loaded run profile: {self.run_profile}")

    def speed_to_duty(self, speed_rpm, settings):
        """
        Default linear mapping from speed_rpm -> duty cycle percentage [0..100].
        Requires settings to contain rpm_min, rpm_max, duty_cycle_min, duty_cycle_max.
        """
        rpm_min = settings.get("rpm_min", 0.0)
        rpm_max = settings.get("rpm_max", 1.0)
        duty_min = settings.get("duty_cycle_min", 0.0)
        duty_max = settings.get("duty_cycle_max", 100.0)

        # linear map, clamp
        if rpm_max == rpm_min:
            frac = 0.0
        else:
            frac = (speed_rpm - rpm_min) / (rpm_max - rpm_min)
        frac = max(0.0, min(1.0, frac))
        duty = duty_min + frac * (duty_max - duty_min)
        return duty

    def start_run_profile(self, settings, speed_to_duty_fn=None, pwm_frequency=1000):
        """
        Start executing self.run_profile in a background thread.
        - settings: dict used by default mapping (rpm_min/rpm_max/duty_cycle_min/duty_cycle_max)
        - speed_to_duty_fn: optional function speed->duty (duty in percent)
        - pwm_frequency: optional frequency for PWM channel
        """
        if self.run_profile is None or len(self.run_profile) == 0:
            logging.info("No run profile loaded.")
            return

        if self.is_profile_running:
            logging.info("Profile already running.")
            return

        # Clear any previous stop event, set running flag
        self._profile_stop_event.clear()
        self.is_profile_running = True

        # ensure pwm is configured
        self.configure_motor_pwm(frequency=pwm_frequency)

        def _profile_worker():
            try:
                for idx, (speed_rpm, cycles) in enumerate(self.run_profile):
                    self.current_profile_index = idx
                    if self._profile_stop_event.is_set():
                        logging.info("Profile stop requested; exiting profile loop.")
                        break

                    # Map speed to duty
                    if speed_to_duty_fn is not None:
                        duty = float(speed_to_duty_fn(speed_rpm))
                    else:
                        duty = float(self.speed_to_duty(speed_rpm, settings))

                    # Clamp duty to [0,100]
                    duty = max(0.0, min(100.0, duty))

                    logging.info(f"Profile step {idx+1}/{len(self.run_profile)}: "
                                 f"speed={speed_rpm} RPM, cycles={cycles}, duty={duty:.3f}%")

                    # Start or update motor duty
                    try:
                        # If PWM not started yet, call start_motor; else update
                        if self.pwm_task is None:
                            self.start_motor(duty)
                        else:
                            # If task is created but not started, start it with property
                            try:
                                self.pwm_task.state
                                # update running task
                                self.update_motor_duty_cycle(duty)
                            except Exception:
                                # fallback to start_motor
                                self.start_motor(duty)
                    except Exception as e:
                        logging.info(f"Error starting/updating motor at profile step {idx+1}: {e}")
                        # if error, stop profile
                        self._profile_stop_event.set()
                        break
                    
                    # compute duration
                    if speed_rpm == 0:
                        step_duration = 0.0
                    else:
                        step_duration = float(cycles) / float(speed_rpm) * 60.0

                    # Wait for step duration but remain responsive to stop requests
                    start_t = time.time()
                    while (time.time() - start_t) < step_duration:
                        if self._profile_stop_event.is_set():
                            logging.info("Profile stop requested during step wait.")
                            break
                        time.sleep(0.1)

                    # if stop requested, break
                    if self._profile_stop_event.is_set():
                        break

                logging.info("Profile thread finished (normal or stop).")
            except Exception as e:
                logging.exception(f"Unhandled exception in profile worker: {e}")
            finally:
                # Stop motor and cleanup PWM task (use your stop_motor with ramp down)
                try:
                    self.stop_motor()
                except Exception as e:
                    logging.info(f"Warning while stopping motor at profile end: {e}")
                self.is_profile_running = False
                self.current_profile_index = 0

        self._profile_thread = threading.Thread(target=_profile_worker, daemon=True)
        self._profile_thread.start()
        logging.info("Run profile started.")

    def stop_run_profile(self):
        """
        Request the run profile thread to stop. This is cooperative and will ramp down motor.
        """
        if not self.is_profile_running:
            logging.info("No profile running.")
            return
        logging.info("Requesting profile stop...")
        self._profile_stop_event.set()
        # Wait briefly for thread to exit
        if self._profile_thread is not None:
            self._profile_thread.join(timeout=5.0)
            if self._profile_thread.is_alive():
                logging.info("Profile thread still alive after join timeout.")
        logging.info("Profile stop requested (thread join attempted).")
