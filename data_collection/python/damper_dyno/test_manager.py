import threading
from file_io import save_test_data
from utils import convert_speed_to_duty_cycle

class TestManager:
    def __init__(self, daq_controller, realtime_plot=None):
        """
        Initialize the TestManager.
        """
        self.daq = daq_controller
        self.realtime_plot = realtime_plot

    def run_test(self, target_speed, num_cycles, sample_rate=300, chunk_size=100):
        """
        Run a damper test with specified speed and number of cycles.
        """

        # convert target speed to motor PWM duty cycle
        pwm = convert_speed_to_duty_cycle(target_speed)
        self.daq.set_motor_pwm(pwm)

        # Storage list ([timestamp, AI0, AI1, AI2...])
        data_storage = []

        # Queues for real-time plotting
        time_q = []                         # Stores timestamps
        data_qs = [[] for _ in range(3)]    # Separate lists for analog inputs

        # callback function executed every time new data is read from DAQ
        def callback(times, values):
            # ensure time and data arrays have the same length
            n = min(len(times), values.shape[1])
            times = times[:n]
            values = values[:, :n]

            # store data for CSV export
            for i in range(n):
                data_storage.append([times[i], *values[:, i]])

            # append data to queues for live plotting
            time_q.extend(times)
            for dq, val in zip(data_qs, values):
                dq.extend(val)

            # update live plot with latest data
            if self.realtime_plot:
                self.realtime_plot.update(time_q, data_qs, sample_rate)

        # start continuous analog acquisition with callback for processing data
        self.daq.start_acquisition(
            analog_channels=["ai0", "ai1", "ai2"],
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            callback=callback
        )

        # background thread to control test duration
        def test_thread():
            # compute total test duration in seconds
            test_duration = num_cycles / target_speed * 60

            # wait for test duration to complete
            threading.Event().wait(test_duration)

            # stop data acquisition and motor PWM
            self.daq.stop_acquisition()
            self.daq.stop_motor_pwm()

            # save collected data to CSV
            save_test_data(data_storage)

        # run test duration thread in the background
        threading.Thread(target=test_thread, daemon=True).start()


