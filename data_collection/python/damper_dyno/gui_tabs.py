import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import math
import logging
from plots import RealTimePlot, RealTimeScatter
from utils import required_theta_dot
import matplotlib.cm as cm
import random

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
            y_range=(10, 50),
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

        ttk.Button(control_frame, text="Run Single", style="Big.TButton",
           command=self.start_single_test).pack(side=tk.LEFT, padx=10)

        ttk.Button(control_frame, text="Run Profile", style="Big.TButton",
                command=self.start_profile_test).pack(side=tk.LEFT, padx=10)

        ttk.Button(control_frame, text="E-STOP", style="Big.TButton",
                command=self.emergency_stop).pack(side=tk.LEFT, padx=10)

        ttk.Button(control_frame, text="Quit", style="Big.TButton",
                command=self.on_quit).pack(side=tk.LEFT, padx=10)


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

    def start_single_test(self):
        """Run a single constant-speed test."""
        try:
            settings_for_run = {key: var.get() for key, var in self.settings_manager.setting_vars.items()}
                            
            target_linear_speed = float(settings_for_run['default_linear_speed_ips'])
            crank_radius = float(settings_for_run['crank_radius_in'])
            rod_length = float(settings_for_run['rod_length_in'])

            theta_dot_rad_s, _, __ = required_theta_dot(V_des=target_linear_speed, Lc=rod_length, R=crank_radius)
            calculated_rpm = theta_dot_rad_s * 60 / (2 * math.pi)
            logging.info(f"[Single] Linear speed {target_linear_speed} in/s -> RPM {calculated_rpm:.2f}")

            for key, value in settings_for_run.items():
                if key != 'output_dir':
                    try: settings_for_run[key] = float(value) if '.' in str(value) else int(value)
                    except: pass

            settings_for_run['run_speed_rpm'] = calculated_rpm
            settings_for_run['run_num_cycles'] = int(self.settings_manager.get_var('default_num_cycles').get())
            settings_for_run['run_profile'] = None  # force single mode

        except Exception as e:
            messagebox.showerror("Invalid Input", str(e))
            return

        threading.Thread(target=self.test_manager.run_test,
                        args=(settings_for_run,), daemon=True).start()

    def start_profile_test(self):
        """Run a full profile defined in config.json.

        Interprets the first row of run_profile as linear speed (in/s) by default,
        and converts each speed to RPM using the same required_theta_dot logic
        that start_single_test uses. If settings contains
        'run_profile_speeds_are_rpm' == True, the speeds are treated as RPM already.
        """
        try:
            # crerate dictionary of settings for profile run
            settings_for_run = {key: var.get() for key, var in self.settings_manager.setting_vars.items()}

            for key, value in settings_for_run.items(): # convert numeric
                if key != 'output_dir':
                    try:
                        settings_for_run[key] = float(value) if '.' in str(value) else int(value)
                    except Exception:
                        pass

            # get the inital run profile from ettings namanger
            raw_profile = self.settings_manager.settings.get("run_profile", None)
            if not raw_profile:
                messagebox.showerror("Missing Profile", "No run_profile found in config.json.")
                return

            # Optionally treat speeds as RPM directly
            speeds_are_rpm = bool(self.settings_manager.settings.get("run_profile_speeds_are_rpm", False))

            speeds_row = raw_profile[0]
            durations_row = raw_profile[1]

            # Convert speeds -> RPM if they are linear speeds (in/s)
            if not speeds_are_rpm:
                try:
                    crank_radius = float(settings_for_run.get('crank_radius_in', self.settings_manager.get_var('crank_radius_in').get()))
                    rod_length   = float(settings_for_run.get('rod_length_in', self.settings_manager.get_var('rod_length_in').get()))
                except Exception as e:
                    messagebox.showerror("Missing Geometry", f"Crank or rod geometry missing or invalid: {e}")
                    return

                rpm_list = []
                for v in speeds_row:
                    # assume v is linear speed in in/s
                    try:
                        v_float = float(v)
                    except Exception:
                        messagebox.showerror("Invalid profile value", f"Invalid speed value in profile: {v}")
                        return

                    theta_dot_rad_s, _, _ = required_theta_dot(V_des=v_float, Lc=rod_length, R=crank_radius)
                    rpm = theta_dot_rad_s * 60.0 / (2.0 * math.pi)
                    rpm_list.append(rpm)
            else:
                # speeds are already RPM
                rpm_list = [float(s) for s in speeds_row]

            # build the converted profile in the same 2xN row-wise format
            converted_profile = [rpm_list, durations_row]

            # attach to settings_for_run and start
            settings_for_run['run_profile'] = converted_profile

            logging.info("Starting profile test (converted speeds to RPM)...")
            threading.Thread(target=self.test_manager.run_test,
                            args=(settings_for_run,), daemon=True).start()

        except Exception as e:
            messagebox.showerror("Profile Start Error", f"Failed to start profile test: {e}")
            logging.exception("Failed to start profile test")
            return


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


class AnalysisTab(ttk.Frame):
    """Analysis tab with Force vs Displacement and Force vs Velocity plots."""
    
    def __init__(self, parent, run_tab, fonts):
        super().__init__(parent)
        self.run_tab = run_tab
        self.fonts = fonts
        self._create_widgets()
    
    def _create_widgets(self):
        # Force vs Displacement
        force_disp_frame = ttk.LabelFrame(self, text="Force vs Displacement", padding=(10, 10))
        force_disp_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        self.force_disp_plot = RealTimeScatter(
            master=force_disp_frame,
            x_label="Displacement [mm]",
            y_label="Force [N]",
            x_range=(0, 50),
            y_range=(-1000, 1000),
            color='blue'
        )

        # Force vs Velocity
        force_vel_frame = ttk.LabelFrame(self, text="Force vs Velocity", padding=(10, 10))
        force_vel_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        self.force_vel_plot = RealTimeScatter(
            master=force_vel_frame,
            x_label="Velocity [mm/s]",
            y_label="Force [N]",
            x_range=(-200, 200),
            y_range=(-1000, 1000),
            color='blue'
        )

    def reset_plots(self):
        """Call at the start of a new run to clear plots."""
        self.force_disp_plot.reset()
        self.force_vel_plot.reset()

    def update_plots(self):
        """Update plots with data from run_tab."""
        if self.run_tab.time_q:
            self.force_disp_plot.update(self.run_tab.disp_q, self.run_tab.force_q)
            self.force_vel_plot.update(self.run_tab.vel_q, self.run_tab.force_q)

