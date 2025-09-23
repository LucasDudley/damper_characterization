import tkinter as tk
from plots import RealTimePlot
import threading
from tkinter import font

class DamperDynoGUI(tk.Tk):
    def __init__(self, test_manager): # Corrected the argument name for clarity
        super().__init__()
        self.test_manager = test_manager
        self.title("Damper Dyno")
        self.btn_font = font.Font(size=18, weight="bold")
        self.widget_font = font.Font(size=20)
        self.create_widgets()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Handles the application shutdown sequence."""
        self.test_manager.daq.close()
        self.destroy()

    def create_widgets(self):
        """Create and arrange GUI components with two plots and a digital readout."""

        #main frame to hold both plots
        plots_frame = tk.Frame(self)
        plots_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        # create plot frames
        left_plot_frame = tk.Frame(plots_frame)
        left_plot_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=(0, 5))

        right_plot_frame = tk.Frame(plots_frame)
        right_plot_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=(5, 0))

        # force plot
        self.force_plot = RealTimePlot(
            master=left_plot_frame,
            signal_names=["Force"],
            y_label="Force [N]",
            y_range=(-1000, 1000)
        )

        # displacement plot
        self.disp_plot = RealTimePlot(
            master=right_plot_frame,
            signal_names=["Displacement"],
            y_label="Displacement [mm]",
            y_range=(0, 50)
        )
        
        # frame for digital readouts
        readouts_frame = tk.Frame(self)
        readouts_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(readouts_frame, text="Temperature:", font=("Helvetica", 20)).pack(side=tk.LEFT, padx=5)
        
        self.temp_var = tk.StringVar(value="-- °C") # Use a tkinter StringVar for thread-safe text updates
        temp_label = tk.Label(readouts_frame, textvariable=self.temp_var, font=self.btn_font)
        temp_label.pack(side=tk.LEFT, padx=5)

        # attach to task_runner
        self.test_manager.force_plot = self.force_plot
        self.test_manager.disp_plot = self.disp_plot
        self.test_manager.temp_var = self.temp_var

        # Control frame
        control_frame = tk.Frame(self)
        control_frame.pack(pady=10, padx=10, fill="x")

        # Speed input
        tk.Label(control_frame, text="Speed (RPM)", font=self.widget_font).pack(side=tk.LEFT)
        self.speed_entry = tk.Entry(control_frame, width=8, font=self.widget_font)
        self.speed_entry.pack(side=tk.LEFT, padx=5)

        # Cycles input
        tk.Label(control_frame, text="Cycles", font=self.widget_font).pack(side=tk.LEFT, padx=(10, 0))
        self.cycles_entry = tk.Entry(control_frame, width=8, font=self.widget_font)
        self.cycles_entry.pack(side=tk.LEFT, padx=5)

        # Start button
        tk.Button(
            control_frame, text="Start", font=self.btn_font, width=8, height=2,
            bg="green", fg="white", command=self.start_test
        ).pack(side=tk.LEFT, padx=10)

        # E-Stop button
        tk.Button(
            control_frame, text="E-STOP", font=self.btn_font, width=8, height=2,
            bg="red", fg="white", command=self.emergency_stop
        ).pack(side=tk.LEFT, padx=10)

        # Quit button
        tk.Button(
            control_frame, text="Quit", font=self.btn_font, width=8, height=2,
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