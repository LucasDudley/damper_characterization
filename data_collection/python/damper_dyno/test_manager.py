import threading
from file_io import save_test_data  # your CSV saving function

class TestManager:
    def __init__(self, daq_controller, live_plot=None):
        self.daq = daq_controller
        self.live_plot = live_plot

    def run_test(self, target_speed, num_cycles, sample_rate=300, chunk_size=100):
        from utils import convert_speed_to_duty_cycle
        pwm = convert_speed_to_duty_cycle(target_speed)
        self.daq.set_motor_pwm(pwm)

        # storage for CSV
        data_storage = []

        # queues for live plotting
        time_q = []
        data_qs = [[] for _ in range(3)]  # AI0, AI1, AI2

        def callback(times, values):
            # TRUNCATE arrays to shortest length (safety)
            n = min(len(times), values.shape[1])
            times = times[:n]
            values = values[:, :n]

            # store CSV
            for i in range(n):
                data_storage.append([times[i], *values[:, i]])

            # append to plot queues
            time_q.extend(times)
            for dq, val in zip(data_qs, values):
                dq.extend(val)

            # update live plot safely
            if self.live_plot:
                self.live_plot.update(time_q, data_qs)

        self.daq.start_analog_acquisition(
            channels=["ai0","ai1","ai2"],
            sample_rate=sample_rate,
            chunk_size=chunk_size,
            callback=callback
        )

        # run test duration in background
        def test_thread():
            test_duration = num_cycles / target_speed * 60  # RPM → seconds per cycle
            threading.Event().wait(test_duration)
            self.daq.stop_analog_acquisition()
            self.daq.stop_motor_pwm()
            save_test_data(data_storage)

        threading.Thread(target=test_thread, daemon=True).start()


