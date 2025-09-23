import tkinter as tk
from plots import RealTimePlot
import threading
from tkinter import font

class DamperDynoGUI(tk.Tk):
    def __init__(self, test_manager): # Corrected the argument name for clarity
        super().__init__()
        self.test_manager = test_manager
        self.title("Damper Dyno")
        self.create_widgets()

    def create_widgets(self):
        """Create and arrange GUI components."""
        # Create a frame for the plot
        plot_frame = tk.Frame(self)
        plot_frame.pack(fill="both", expand=True, padx=10, pady=10)

        signal_names = [self.test_manager.signal_config[ch][0] for ch in self.test_manager.channels]
        
        # Link the plot to the test manager
        self.realtime_plot = RealTimePlot(
            master=plot_frame,
            signal_names=signal_names,
            y_label="Force (N) / Displacement (mm)",
            y_range=(-150, 150)
        )
        self.test_manager.realtime_plot = self.realtime_plot

        btn_font = font.Font(size=12, weight="bold")
        widget_font = font.Font(size=12)

        # Control frame
        control_frame = tk.Frame(self)
        control_frame.pack(pady=10, padx=10, fill="x")

        # Speed input
        tk.Label(control_frame, text="Speed (RPM)", font=widget_font).pack(side=tk.LEFT)
        self.speed_entry = tk.Entry(control_frame, width=8, font=widget_font)
        self.speed_entry.pack(side=tk.LEFT, padx=5)

        # Cycles input
        tk.Label(control_frame, text="Cycles", font=widget_font).pack(side=tk.LEFT, padx=(10, 0))
        self.cycles_entry = tk.Entry(control_frame, width=8, font=widget_font)
        self.cycles_entry.pack(side=tk.LEFT, padx=5)

        # Start button
        tk.Button(
            control_frame, text="Start", font=btn_font, width=8, height=2,
            bg="green", fg="white", command=self.start_test
        ).pack(side=tk.LEFT, padx=10)

        # E-Stop button
        tk.Button(
            control_frame, text="E-STOP", font=btn_font, width=8, height=2,
            bg="red", fg="white", command=self.emergency_stop
        ).pack(side=tk.LEFT, padx=10)

        # Quit button
        tk.Button(
            control_frame, text="Quit", font=btn_font, width=8, height=2,
            bg="gray", fg="white", command=self.destroy # Use self.destroy for clean exit
        ).pack(side=tk.LEFT, padx=10)

    def start_test(self):
        """Retrieve user input and start the test in a separate thread."""
        try:
            speed = float(self.speed_entry.get())
            cycles = int(self.cycles_entry.get())
        except ValueError:
            print("Invalid input for speed or cycles.")
            return

        threading.Thread(
            target=self.test_manager.run_test,
            args=(speed, cycles),
            daemon=True
        ).start()

    def emergency_stop(self):
        """Stop PWM and data acquisition immediately."""
        print("⚠ EMERGENCY STOP PRESSED ⚠")
        # Call the dedicated E-Stop method in the DAQ controller
        self.test_manager.daq.emergency_stop()