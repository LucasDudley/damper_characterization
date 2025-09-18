import nidaqmx
import time
import numpy as np

device_name = "Dev1"
channel = "ai0"
sample_rate = 1000
chunk_size = 100  # number of samples per read

with nidaqmx.Task() as task:
    # Add analog input channel
    task.ai_channels.add_ai_voltage_chan(f"{device_name}/{channel}")
    task.timing.cfg_samp_clk_timing(rate=sample_rate)

    print("Streaming data (Ctrl+C to stop)...")
    try:
        while True:
            data = task.read(number_of_samples_per_channel=chunk_size)
            if isinstance(data, list):  # multiple samples returned
                latest = data[-1]
            else:
                latest = data  # single sample mode
            print(f"Latest sample: {latest:.4f} V")
            time.sleep(chunk_size / sample_rate)  # match read rate
    except KeyboardInterrupt:
        print("\nStopped.")
