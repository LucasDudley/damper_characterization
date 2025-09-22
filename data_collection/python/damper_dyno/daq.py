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
        self.ai_task = None
        self.pwm_task = None
        self.acquisition_thread = None            # Keep track of the acquisition thread
        self.stop_event = threading.Event()       # Use an Event for safe thread stopping

    # PWM Control
    def configure_motor_pwm(self, frequency=1000):
        if self.pwm_task:
            self.pwm_task.close()
        self.pwm_task = nidaqmx.Task()
        self.pwm_task.co_channels.add_co_pulse_chan_freq(
            f"{self.device_name}/ctr0",
            name_to_assign_to_channel="PWM",
            freq=frequency,
            duty_cycle=1e-4
        )
        self.pwm_task.timing.cfg_implicit_timing(sample_mode=AcquisitionType.CONTINUOUS)

    def start_motor_pwm(self, duty_cycle: float):
        if self.pwm_task is None:
            self.configure_motor_pwm()
        safe_duty = max(min(duty_cycle / 100.0, 0.999999), 1e-6)
        self.pwm_task.co_channels.all.co_pulse_duty_cyc = safe_duty
        try:
            self.pwm_task.start()
        except nidaqmx.errors.DaqError as e:
            if "already started" not in str(e):
                raise

    def stop_motor_pwm(self):
        if self.pwm_task is not None:
            try:
                self.pwm_task.stop()
                self.pwm_task.close()
            except Exception as e:
                print(f"Warning stopping PWM task: {e}")
            finally:
                self.pwm_task = None
    
    # Data Acquisition
    def _acquisition_callback(self, task_handle, every_n_samples_event_type,
                              number_of_samples, callback_data):
        """
        This function is called by the nidaqmx driver thread when data is ready.
        """
        try:
            # read the available data. The number of samples is provided by the driver.
            raw_data = self.ai_task.read(number_of_samples_per_channel=number_of_samples)
            data = np.array(raw_data)
            if data.ndim == 1:
                data = data.reshape((1, -1))
            
            # Generate timestamps based on the start time and the number of samples acquired so far.
            times = [
                self.start_time + datetime.timedelta(seconds=(self.total_samples_acquired + i) / self.sample_rate)
                for i in range(data.shape[1])
            ]
            self.total_samples_acquired += data.shape[1]

            # Pass the accurately timed data to the main application's callback
            if self.data_callback:
                self.data_callback(times, data)

            return 0 # Required return value for the callback
        
        except Exception as e:
            print(f"Error in DAQ callback: {e}")
            return 1 # Indicate an error occurred

    def start_acquisition(self, analog_channels, sample_rate, chunk_size, callback):
        """
        Configure and start a hardware-timed, callback-driven acquisition.
        """
        if self.ai_task:
            print("An acquisition is already running. Stop it first.")
            return

        self.data_callback = callback
        self.sample_rate = sample_rate
        self.total_samples_acquired = 0
        
        try:
            self.ai_task = nidaqmx.Task()
            for ch in analog_channels:
                self.ai_task.ai_channels.add_ai_voltage_chan(
                    f"{self.device_name}/{ch}",
                    terminal_config=TerminalConfiguration.RSE
                )
            
            self.ai_task.timing.cfg_samp_clk_timing(
                rate=sample_rate,
                sample_mode=AcquisitionType.CONTINUOUS
            )
            
            # Register our function to be called by the driver.
            self.ai_task.register_every_n_samples_acquired_into_buffer_event(
                chunk_size, self._acquisition_callback
            )

            self.start_time = datetime.datetime.now() # Log the start time
            self.ai_task.start()
            print("✅ DAQ acquisition started successfully.")

        except Exception as e:
            print(f"Failed to start DAQ acquisition: {e}")
            if self.ai_task:
                self.ai_task.close()
                self.ai_task = None
    
    def stop_acquisition(self):
        """Stop DAQ analog acquisition safely."""
        if self.ai_task:
            try:
                self.ai_task.stop()
                # Unregistering the event is good practice
                self.ai_task.register_every_n_samples_acquired_into_buffer_event(0, None)
                self.ai_task.close()
                print("🛑 DAQ acquisition stopped.")
            except Exception as e:
                print(f"Warning stopping AI task: {e}")
            finally:
                self.ai_task = None
        self.data_callback = None
    
    def emergency_stop(self):
        """Immediately stops motor and signals acquisition to halt."""
        print("🚨 DAQ E-STOP 🚨")
        self.stop_motor_pwm()   # Stop the dangerous part first
        self.stop_acquisition() # Gracefully stop and clean up the acquisition

