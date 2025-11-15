import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import math
import logging
from plots import RealTimePlot
from utils import required_theta_dot

class RunTestTab(ttk.Frame):
    """The main tab for running tests, displaying plots, and controlling the dyno."""

    def __init__(self, parent, test_manager, settings_manager, fonts, on_quit):
        super().__init__(parent)
        self.test_manager = test_manager
        self.settings_manager = settings_manager
        self.fonts = fonts
        self.on_quit = on_quit

        # Data buffers for plotting
        self.time_q = []
        self.force_q = []
        self.disp_q = []
        self.vel_q = []

        self._create_widgets()

    def _create_widgets(self):
        plots_frame = ttk.Frame(self)
        plots_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        
        left_plot_frame = ttk.Frame(plots_frame)
        left_plot_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        right_plot_frame = ttk.Frame(plots_frame)
        right_plot_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self.force_plot = RealTimePlot(
            master=left_plot_frame, 
            signal_names=["Force"], 
            y_label="Force [N]", 
            y_range=(-1000, 1000)
        )
        self.disp_plot = RealTimePlot(
            master=right_plot_frame,
            signal_names=["Displacement"],
            y_label="Displacement [mm]",
            y_range=(0, 40),
            secondary_signals=["Velocity"],
            secondary_y_label="Velocity [mm/s]",
            secondary_y_range=(-200, 200)
        )

        
        readouts_frame = ttk.Frame(self)
        readouts_frame.pack(side="right", padx=10, pady=5, anchor="e")
        ttk.Label(readouts_frame, text="Temperature:", font=("Helvetica", 20)).pack(side=tk.LEFT, padx=5)
        self.temp_var = tk.StringVar(value="-- °C")
        ttk.Label(readouts_frame, textvariable=self.temp_var, font=self.fonts['btn_font']).pack(side=tk.LEFT, padx=5)

        control_frame = ttk.Frame(self)
        control_frame.pack(pady=10, padx=10)
        
        ttk.Label(control_frame, text="Linear Speed (in/s)", font=self.fonts['widget_font']).pack(side=tk.LEFT)
        ttk.Entry(control_frame, width=8, font=self.fonts['widget_font'], textvariable=self.settings_manager.get_var('default_linear_speed_ips')).pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="Cycles", font=self.fonts['widget_font']).pack(side=tk.LEFT, padx=(10, 0))
        ttk.Entry(control_frame, width=8, font=self.fonts['widget_font'], textvariable=self.settings_manager.get_var('default_num_cycles')).pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Start", style="Big.TButton", command=self.start_test).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="E-STOP", style="Big.TButton", command=self.emergency_stop).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="Quit", style="Big.TButton", command=self.on_quit).pack(side=tk.LEFT, padx=10)

    def start_test(self):
        try:
            settings_for_run = {key: var.get() for key, var in self.settings_manager.setting_vars.items()}
                        
            target_linear_speed = float(settings_for_run['default_linear_speed_ips'])
            crank_radius = float(settings_for_run['crank_radius_in'])
            rod_length = float(settings_for_run['rod_length_in'])

            theta_dot_rad_s, _, __ = required_theta_dot(V_des=target_linear_speed, Lc=rod_length, R=crank_radius)
            calculated_rpm = theta_dot_rad_s * 60 / (2 * math.pi)
            logging.info(f"Target linear speed: {target_linear_speed} in/s => Calculated RPM: {calculated_rpm:.2f}")

            for key, value in settings_for_run.items():
                if key != 'output_dir':
                    try: settings_for_run[key] = float(value) if '.' in str(value) else int(value)
                    except (ValueError, TypeError): pass

            settings_for_run['run_speed_rpm'] = calculated_rpm
            settings_for_run['run_num_cycles'] = int(self.settings_manager.get_var('default_num_cycles').get())

        except (KeyError, ValueError, TypeError) as e:
            messagebox.showerror("Invalid Input or Configuration", f"Please check your inputs and config.json file.\n\nError: {e}")
            return
            
        threading.Thread(target=self.test_manager.run_test, args=(settings_for_run,), daemon=True).start()

    def emergency_stop(self):
        logging.info("⚠ EMERGENCY STOP PRESSED ⚠")
        self.test_manager.daq.emergency_stop()


class SettingsTab(ttk.Frame):
    """The tab for configuring all application and test settings."""
    def __init__(self, parent, settings_manager, fonts):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.fonts = fonts
        
        main_frame = ttk.Frame(self, padding=(20, 10))
        main_frame.pack(expand=True, fill="both")
        self._create_widgets(main_frame)
    
    def _create_widgets(self, parent):
        # File Settings
        file_frame = ttk.LabelFrame(parent, text="File Settings", padding=(15, 10))
        file_frame.pack(fill="x", pady=5)
        file_frame.columnconfigure(1, weight=1)
        ttk.Label(file_frame, text="Output Directory:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(file_frame, textvariable=self.settings_manager.get_var('output_dir')).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(file_frame, text="Browse...", command=self._browse_directory).grid(row=0, column=2, padx=5, pady=5)
        
        # Motor Mapping
        ranges_frame = ttk.LabelFrame(parent, text="Motor Mapping", padding=(15, 10))
        ranges_frame.pack(fill="x", pady=5)
        ttk.Label(ranges_frame, text="RPM Range:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(ranges_frame, textvariable=self.settings_manager.get_var('rpm_min'), width=10).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(ranges_frame, text="to").grid(row=0, column=2, padx=(10, 10))
        ttk.Entry(ranges_frame, textvariable=self.settings_manager.get_var('rpm_max'), width=10).grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(ranges_frame, text="Duty Cycle Range (%):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(ranges_frame, textvariable=self.settings_manager.get_var('duty_cycle_min'), width=10).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(ranges_frame, text="to").grid(row=1, column=2, padx=(10, 10))
        ttk.Entry(ranges_frame, textvariable=self.settings_manager.get_var('duty_cycle_max'), width=10).grid(row=1, column=3, padx=5, pady=5)
        
        # Test Defaults
        defaults_frame = ttk.LabelFrame(parent, text="Test Defaults", padding=(15, 10))
        defaults_frame.pack(fill="x", pady=5)
        ttk.Label(defaults_frame, text="Default Linear Speed (in/s):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(defaults_frame, textvariable=self.settings_manager.get_var('default_linear_speed_ips'), width=15).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(defaults_frame, text="Default Cycle Count:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(defaults_frame, textvariable=self.settings_manager.get_var('default_num_cycles'), width=15).grid(row=1, column=1, padx=5, pady=5)
        
        # Action Buttons
        action_frame = ttk.Frame(parent, padding=(0, 10))
        action_frame.pack(fill="x", side="bottom")
        ttk.Button(action_frame, text="Save Settings", command=self.settings_manager.save).pack(side="right", padx=5)
        ttk.Button(action_frame, text="Revert Changes", command=self.settings_manager.revert).pack(side="right")

    def _browse_directory(self):
        dir_name = filedialog.askdirectory()
        if dir_name:
            self.settings_manager.get_var('output_dir').set(dir_name)