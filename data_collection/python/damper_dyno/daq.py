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
        logging.info(f"Setting initial PWM property to Duty Cycle: {safe_duty}")
        self.pwm_task.co_channels.all.co_pulse_duty_cyc = safe_duty

        try:
            self.pwm_task.start()
        except nidaqmx.errors.DaqError as e:
            if e.error_code == -200479:
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
        
        logging.info(f"Writing to running task >> Freq: {self.pwm_frequency} Hz, Duty Cycle: {safe_duty}")
        
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
                self.ai_task.stop()
                self.ai_task.register_every_n_samples_acquired_into_buffer_event(0, None)
                self.ai_task.close()
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