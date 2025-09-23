import tkinter as tk
from tkinter import ttk
from tkinter import font
from plots import RealTimePlot
import threading

class DamperDynoGUI(tk.Tk):
    def __init__(self, test_manager):
        super().__init__()
        self.test_manager = test_manager
        self.title("Damper Dyno")

        self.btn_font = font.Font(size=18, weight="bold")
        self.widget_font = font.Font(size=20)
        
        self.create_gui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        """Handles the complete application shutdown sequence."""
        print("Shutdown sequence initiated...")
        plt.close('all')
        self.test_manager.daq.close()
        self.destroy()

    def create_gui(self):
        """Create and arrange the main GUI components, including the tabbed notebook."""

        style = ttk.Style()
        style.configure("Custom.TNotebook.Tab", font=self.btn_font)
        notebook = ttk.Notebook(self, style="Custom.TNotebook")
        notebook.pack(expand=True, fill="both", padx=20, pady=10)

        # create frames for each tab
        self.dyno_tab = ttk.Frame(notebook)
        self.settings_tab = ttk.Frame(notebook)

        # add the frames to the notebook with titles
        notebook.add(self.dyno_tab, text="Run Test")
        notebook.add(self.settings_tab, text="Settings")

        # call separate methods to build the content of each tab
        self._create_dyno_tab(self.dyno_tab)
        self._create_settings_tab(self.settings_tab)

    def _create_dyno_tab(self, parent_tab):
        """Populates the 'Live Dyno' tab with all the controls and plots."""
        
        # Main frame to hold both plots
        plots_frame = tk.Frame(parent_tab)
        plots_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        # Create plot frames
        left_plot_frame = tk.Frame(plots_frame)
        left_plot_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=(0, 5))

        right_plot_frame = tk.Frame(plots_frame)
        right_plot_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=(5, 0))

        # Force plot
        self.force_plot = RealTimePlot(
            master=left_plot_frame,
            signal_names=["Force"],
            y_label="Force [N]",
            y_range=(-1000, 1000)
        )

        # Displacement plot
        self.disp_plot = RealTimePlot(
            master=right_plot_frame,
            signal_names=["Displacement"],
            y_label="Displacement [mm]",
            y_range=(0, 50)
        )
        
        # Frame for digital readouts
        readouts_frame = tk.Frame(parent_tab)
        readouts_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(readouts_frame, text="Temperature:", font=("Helvetica", 20)).pack(side=tk.LEFT, padx=5)
        
        self.temp_var = tk.StringVar(value="-- °C")
        temp_label = tk.Label(readouts_frame, textvariable=self.temp_var, font=self.btn_font)
        temp_label.pack(side=tk.LEFT, padx=5)

        # Attach to task_runner
        self.test_manager.force_plot = self.force_plot
        self.test_manager.disp_plot = self.disp_plot
        self.test_manager.temp_var = self.temp_var

        # Control frame
        control_frame = tk.Frame(parent_tab)
        control_frame.pack(pady=10, padx=10, fill="x")

        # ... (Your Speed, Cycles, Start, E-Stop, and Quit buttons are placed here, unchanged) ...
        # Speed input
        tk.Label(control_frame, text="Speed (RPM)", font=self.widget_font).pack(side=tk.LEFT)
        self.speed_entry = tk.Entry(control_frame, width=8, font=self.widget_font)
        self.speed_entry.pack(side=tk.LEFT, padx=5)
        # Cycles input
        tk.Label(control_frame, text="Cycles", font=self.widget_font).pack(side=tk.LEFT, padx=(10, 0))
        self.cycles_entry = tk.Entry(control_frame, width=8, font=self.widget_font)
        self.cycles_entry.pack(side=tk.LEFT, padx=5)
        # Start button
        tk.Button(control_frame, text="Start", font=self.btn_font, width=8, height=2, bg="green", fg="white", command=self.start_test).pack(side=tk.LEFT, padx=10)
        # E-Stop button
        tk.Button(control_frame, text="E-STOP", font=self.btn_font, width=8, height=2, bg="red", fg="white", command=self.emergency_stop).pack(side=tk.LEFT, padx=10)
        # Quit button (Note: Changed command to on_closing for clean exit)
        tk.Button(control_frame, text="Quit", font=self.btn_font, width=8, height=2, bg="gray", fg="white", command=self.on_closing).pack(side=tk.LEFT, padx=10)

    def _create_settings_tab(self, parent_tab):
        tk.Label(parent_tab, text="PLACEHOLDER FOR SETTINGS", font=self.widget_font).pack(padx=20, pady=20)

        #add calibration info here / defaults for cycle length / warnings

    # ... (start_test and emergency_stop methods are unchanged) ...
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
        self.test_manager.daq.emergency_stop()