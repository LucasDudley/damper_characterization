import tkinter as tk
from tkinter import ttk
from tkinter import font
from ttkthemes import ThemedTk
from plots import RealTimePlot
import threading
import queue

class DamperDynoGUI(ThemedTk):
    def __init__(self, test_manager):
        super().__init__(theme="arc")

        self.test_manager = test_manager
        self.title("Damper Dyno")

        # Data buffers for plotting
        self.time_q = []
        self.force_q = []
        self.disp_q = []
        
        # Initialize a variable to hold the 'after' job ID
        self._after_id = None

        self.btn_font = font.Font(family="Helvetica", size=18, weight="bold")
        self.widget_font = font.Font(family="Helvetica", size=18)
        
        self.create_gui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.process_daq_queue()

    def process_daq_queue(self):
        """
        Check the queue for new data from the DAQ and update the GUI.
        """
        try:
            while not self.test_manager.gui_queue.empty():
                data_packet = self.test_manager.gui_queue.get_nowait()
                
                self.time_q.extend(data_packet['times'])
                self.force_q.extend(data_packet['force'])
                self.disp_q.extend(data_packet['disp'])

                if self.temp_var and data_packet['temp'] is not None:
                    self.temp_var.set(f"{data_packet['temp']:.1f} °C")
            
            if self.force_plot:
                self.force_plot.update(self.time_q, [self.force_q], sample_rate=1000)
            if self.disp_plot:
                self.disp_plot.update(self.time_q, [self.disp_q], sample_rate=1000)

        except queue.Empty:
            pass
        finally:
            #Store the 'after' job ID
            self._after_id = self.after(100, self.process_daq_queue)

    def on_closing(self):
        """
        Handles the complete application shutdown sequence robustly.
        """
        print("Closing App")
        
        #Cancel the pending 'after' job before destroying anything
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

        try:
            self.test_manager.daq.close() 
        except Exception as e:
            print(f"Error during DAQ cleanup: {e}")
        finally:
            self.destroy()


    def create_gui(self):
        """Create and arrange the main GUI components, including the tabbed notebook."""
        
        style = ttk.Style()

        # Configure the notebook tabs
        style.configure("Custom.TNotebook.Tab",
                font=self.btn_font,
                padding=[10, 0])   

        style.configure("Custom.TNotebook", tabmargins=[10, 5, 10, 0])         # add space around the tab area

        # apply the custom style to the Notebook
        notebook = ttk.Notebook(self, style="Custom.TNotebook")
        notebook.pack(expand=True, fill="both", padx=20, pady=10)

        # create frames for each tab
        self.dyno_tab = ttk.Frame(notebook)
        self.settings_tab = ttk.Frame(notebook)
        self.analysis_tab = ttk.Frame(notebook)

        # add the frames to the notebook with titles
        notebook.add(self.dyno_tab, text="Run Test")
        notebook.add(self.analysis_tab, text="Analysis")
        notebook.add(self.settings_tab, text="Settings")

        # call separate methods to build the content of each tab
        self._create_dyno_tab(self.dyno_tab)
        self._create_settings_tab(self.settings_tab)
        self._create_analysis_tab(self.analysis_tab)

    def _create_dyno_tab(self, parent_tab):
        """Populates the 'Live Dyno' tab with all the controls and plots."""
        
        # main frame to hold both plots
        plots_frame = tk.Frame(parent_tab)
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
        readouts_frame = tk.Frame(parent_tab)
        readouts_frame.pack(side="right", padx=10, pady=5, anchor="e")
        tk.Label(readouts_frame, text="Temperature:", font=("Helvetica", 20)).pack(side=tk.LEFT, padx=5)
        
        self.temp_var = tk.StringVar(value="-- °C")
        temp_label = tk.Label(readouts_frame, textvariable=self.temp_var, font=self.btn_font)
        temp_label.pack(side=tk.LEFT, padx=5)

        # attach to test_manager
        self.test_manager.force_plot = self.force_plot
        self.test_manager.disp_plot = self.disp_plot
        self.test_manager.temp_var = self.temp_var

        # control frame
        control_frame = tk.Frame(parent_tab)
        control_frame.pack(pady=10, padx=10)

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

        # Quit button
        tk.Button(control_frame, text="Quit", font=self.btn_font, width=8, height=2, bg="gray", fg="white", command=self.on_closing).pack(side=tk.LEFT, padx=10)

    def _create_settings_tab(self, parent_tab):
        
        tk.Label(parent_tab, text="PLACEHOLDER FOR SETTINGS", font=self.widget_font).pack(padx=20, pady=20)
        # add calibration info here / defaults for cycle length / warnings

    def _create_analysis_tab(self, parent_tab):
        
        tk.Label(parent_tab, text="PLACEHOLDER FOR ANALYSIS", font=self.widget_font).pack(padx=20, pady=20)
        # placeholder to generate characterstic plots

    def start_test(self):
        # *** NEW: Clear plotting buffers before a new test ***
        self.time_q.clear()
        self.force_q.clear()
        self.disp_q.clear()

        # This part remains the same
        try:
            speed = float(self.speed_entry.get())
            cycles = int(self.cycles_entry.get())
        except ValueError:
            print("Invalid input for speed or cycles.")
            return

        threading.Thread(
            target=self.test_manager.run_test,
            args=(speed, cycles),
            daemon=True # This is correct, it won't block exit
        ).start()

    def emergency_stop(self):
        """Stop PWM and data acquisition immediately."""
        print("⚠ EMERGENCY STOP PRESSED ⚠")
        self.test_manager.daq.emergency_stop()