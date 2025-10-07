import os
import json
import tkinter as tk
from tkinter import (ttk, font, filedialog, messagebox)
from ttkthemes import ThemedTk
from plots import RealTimePlot
import threading
import queue
import math

from utils import required_theta_dot

class DamperDynoGUI(ThemedTk):
    def __init__(self, test_manager):
        super().__init__(theme="arc")

        self.test_manager = test_manager
        self.title("Damper Dyno")

        # Data buffers for plotting
        self.time_q = []
        self.force_q = []
        self.disp_q = []
        
        # --- FONT & STYLE DEFINITIONS ---
        self.btn_font = font.Font(family="Helvetica", size=18, weight="bold")
        self.widget_font = font.Font(family="Helvetica", size=18)
        self.header_font = font.Font(family="Helvetica", size=13, weight="bold")
        self.label_font = font.Font(family="Helvetica", size=12)
        self.entry_font = font.Font(family="Helvetica", size=12)

        # configure style
        style = ttk.Style()
        style.configure("TLabelFrame.Label", font=self.header_font)
        style.configure("TLabel", font=self.label_font)
        style.configure("TButton", font=self.label_font)
        style.configure("TEntry", font=self.entry_font, padding=(5, 5, 5, 5))
        style.configure("Big.TButton", font=self.btn_font, padding=(10, 10))


        # --- INITIALIZATION ---
        self._after_id = None
        self._setup_settings() # This creates and loads all settings and StringVars
        self.create_gui(style) # Create the GUI
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.process_daq_queue()


    def _setup_settings(self):
        """
        Loads the mandatory config.json file. Exits if the file is missing or corrupt.
        This is the single source of truth for the application's state.
        """
        self.config_filepath = "config.json"
        self._load_and_apply_settings()


    def _load_and_apply_settings(self):
        """
        Reads config.json and populates/updates all Tkinter variables.
        """
        try:
            with open(self.config_filepath, 'r') as f:
                self.settings = json.load(f)
            print(f"Successfully loaded settings from '{self.config_filepath}'")
        except FileNotFoundError:
            messagebox.showerror("Fatal Error: Configuration Missing", f"The required configuration file was not found.\n\nExpected location: {os.path.abspath(self.config_filepath)}\n\nThe application cannot start without this file.")
            self.destroy()
            os._exit(1)
            return
        except json.JSONDecodeError as e:
            messagebox.showerror("Fatal Error: Configuration Corrupt", f"The configuration file '{self.config_filepath}' is corrupt or not valid JSON.\n\nPlease fix the file or restore it from version control.\n\nError: {e}")
            self.destroy()
            os._exit(1)
            return

        # Create the Tkinter StringVars if they don't exist, otherwise update them
        if not hasattr(self, 'setting_vars'):
            self.setting_vars = {key: tk.StringVar(value=val) for key, val in self.settings.items()}
        else:
            for key, val in self.settings.items():
                self.setting_vars[key].set(val)
                
        # Also create/update the main tab's StringVars
        if not hasattr(self, 'run_speed_var'):
            self.run_speed_var = tk.StringVar(value=self.settings['default_max_speed'])
            self.run_cycles_var = tk.StringVar(value=self.settings['default_num_cycles'])
        else:
            self.run_speed_var.set(self.settings['default_max_speed'])
            self.run_cycles_var.set(self.settings['default_num_cycles'])


    def _save_settings(self):
        """Saves the current GUI values directly to the config.json file."""
        current_string_values = {key: var.get() for key, var in self.setting_vars.items()}
        
        settings_to_save = {}
        for key, value in current_string_values.items():
            if key == 'output_dir':
                settings_to_save[key] = value
                continue
            try:
                if '.' in str(value):
                    settings_to_save[key] = float(value)
                else:
                    settings_to_save[key] = int(value)
            except (ValueError, TypeError):
                settings_to_save[key] = value

        if self._write_config_file(settings_to_save):
            messagebox.showinfo("Settings Saved", "Configuration file has been updated successfully.")


    def _write_config_file(self, settings_dict):
        """Writes the given dictionary to the config.json file."""
        try:
            with open(self.config_filepath, 'w') as f:
                # Use indent=4 for a human-readable JSON file
                json.dump(settings_dict, f, indent=4)
            return True # Indicate success
        except Exception as e:
            messagebox.showerror("File Write Error", f"Could not write to config file.\n\nError: {e}")
            return False # Indicate failure


    def _revert_settings(self):
        """Discards any unsaved changes in the GUI by reloading from config.json."""
        is_confirmed = messagebox.askyesno("Revert Unsaved Changes", "Are you sure you want to discard unsaved changes and reload from 'config.json'?")
        if is_confirmed:
            print("Reverting settings to last saved state.")
            self._load_and_apply_settings()


    def start_test(self):
        """Reads values from the GUI, consolidates them, and starts the test."""
        self.time_q.clear()
        self.force_q.clear()
        self.disp_q.clear()
        
        try:
            # Get all settings from the config file
            settings_for_run = {key: var.get() for key, var in self.setting_vars.items()}

            target_linear_speed = float(self.setting_vars['default_linear_speed_ips'].get())
            crank_radius = float(settings_for_run['crank_radius_in'])
            rod_length = float(settings_for_run['rod_length_in'])

            if crank_radius <= 0 or rod_length <= 0:
                messagebox.showerror("Invalid Geometry", "Check your config.json file.")
                return

            theta_dot_rad_s, _, _ = required_theta_dot(
                V_des=target_linear_speed,
                Lc=rod_length,
                R=crank_radius
            )

            # Convert rad/s to RPM
            calculated_rpm = theta_dot_rad_s * 60 / (2 * math.pi)
            print(f"Target linear speed: {target_linear_speed} in/s => Calculated RPM: {calculated_rpm:.2f}")

            # Add to the settings dictionary for the TestManager
            settings_for_run['run_speed_rpm'] = calculated_rpm
            
            run_speed = settings_for_run['default_max_speed']
            run_cycles = settings_for_run['default_num_cycles']
            
            # prepare the dictionary that will be passed to the test manager.
            for key, value in settings_for_run.items():
                if key != 'output_dir': # Keep output_dir as a string
                    try:
                        if '.' in str(value):
                            settings_for_run[key] = float(value)
                        elif str(value):
                            settings_for_run[key] = int(value)
                    except (ValueError, TypeError):
                        pass

            # Explicitly set the final run parameters in the dictionary
            settings_for_run['run_speed_rpm'] = calculated_rpm
            settings_for_run['run_num_cycles'] = int(self.setting_vars['default_num_cycles'].get())
            

        except (ValueError, TypeError) as e:
            messagebox.showerror("Invalid Input", f"Please check the Speed and Cycles fields for valid numbers.\n\nError: {e}")
            return
            
        threading.Thread(
            target=self.test_manager.run_test,
            args=(settings_for_run,),
            daemon=True
        ).start()


    def emergency_stop(self):
        """Stop PWM and data acquisition immediately."""
        print("⚠ EMERGENCY STOP PRESSED ⚠")
        self.test_manager.daq.emergency_stop()


    def _browse_directory(self):
        """Opens a dialog to select a directory."""
        dir_name = filedialog.askdirectory()
        if dir_name:
            self.setting_vars['output_dir'].set(dir_name)


    def create_gui(self, style):
        """Create and arrange the main GUI components."""
        style.configure("Custom.TNotebook.Tab", font=self.btn_font, padding=[10, 0])
        style.configure("Custom.TNotebook", tabmargins=[10, 5, 10, 0])
        notebook = ttk.Notebook(self, style="Custom.TNotebook")
        notebook.pack(expand=True, fill="both", padx=20, pady=10)

        self.dyno_tab = ttk.Frame(notebook)
        self.settings_tab = ttk.Frame(notebook)
        self.analysis_tab = ttk.Frame(notebook)
        notebook.add(self.dyno_tab, text="Run Test")
        notebook.add(self.analysis_tab, text="Analysis")
        notebook.add(self.settings_tab, text="Settings")

        self._create_dyno_tab(self.dyno_tab)
        self._create_settings_tab(self.settings_tab)
        self._create_analysis_tab(self.analysis_tab)


    def _create_dyno_tab(self, parent_tab):
        """Populates the 'Live Dyno' tab with all the controls and plots."""
        plots_frame = ttk.Frame(parent_tab)
        plots_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        left_plot_frame = ttk.Frame(plots_frame)
        left_plot_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        right_plot_frame = ttk.Frame(plots_frame)
        right_plot_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))

        self.force_plot = RealTimePlot(master=left_plot_frame, signal_names=["Force"], y_label="Force [N]", y_range=(-1000, 1000))
        self.disp_plot = RealTimePlot(master=right_plot_frame, signal_names=["Displacement"], y_label="Displacement [mm]", y_range=(0, 50))
        
        readouts_frame = ttk.Frame(parent_tab)
        readouts_frame.pack(side="right", padx=10, pady=5, anchor="e")
        ttk.Label(readouts_frame, text="Temperature:", font=("Helvetica", 20)).pack(side=tk.LEFT, padx=5)
        
        self.temp_var = tk.StringVar(value="-- °C")
        ttk.Label(readouts_frame, textvariable=self.temp_var, font=self.btn_font).pack(side=tk.LEFT, padx=5)

        self.test_manager.force_plot = self.force_plot
        self.test_manager.disp_plot = self.disp_plot
        self.test_manager.temp_var = self.temp_var

        control_frame = ttk.Frame(parent_tab)
        control_frame.pack(pady=10, padx=10)

        # Speed input
        ttk.Label(control_frame, text="Linear Speed (in/s)", font=self.widget_font).pack(side=tk.LEFT)
        self.linear_speed_entry = ttk.Entry(
            control_frame, 
            width=8, 
            font=self.widget_font, 
            textvariable=self.setting_vars['default_linear_speed_ips']
        )
        self.linear_speed_entry.pack(side=tk.LEFT, padx=5)

        # Cycles input
        ttk.Label(control_frame, text="Cycles", font=self.widget_font).pack(side=tk.LEFT, padx=(10, 0))
        self.cycles_entry = ttk.Entry(control_frame, width=8, font=self.widget_font, textvariable=self.setting_vars['default_num_cycles'])
        self.cycles_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Start", style="Big.TButton", command=self.start_test).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="E-STOP", style="Big.TButton", command=self.emergency_stop).pack(side=tk.LEFT, padx=10)
        ttk.Button(control_frame, text="Quit", style="Big.TButton", command=self.on_closing).pack(side=tk.LEFT, padx=10)


    def _create_settings_tab(self, parent_tab):
        """Populates the 'Settings' tab with styled configuration options."""
        main_frame = ttk.Frame(parent_tab, padding=(20, 10))
        main_frame.pack(expand=True, fill="both")

        file_frame = ttk.LabelFrame(main_frame, text="File Settings", padding=(15, 10))
        file_frame.pack(fill="x", pady=10)
        file_frame.columnconfigure(1, weight=1)
        ttk.Label(file_frame, text="Output Directory:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(file_frame, textvariable=self.setting_vars['output_dir']).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(file_frame, text="Browse...", command=self._browse_directory).grid(row=0, column=2, padx=5, pady=5)

        ranges_frame = ttk.LabelFrame(main_frame, text="Motor Mapping", padding=(15, 10))
        ranges_frame.pack(fill="x", pady=10)
        ttk.Label(ranges_frame, text="RPM Range:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(ranges_frame, textvariable=self.setting_vars['rpm_min'], width=10).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(ranges_frame, text="to").grid(row=0, column=2, padx=(10, 10))
        ttk.Entry(ranges_frame, textvariable=self.setting_vars['rpm_max'], width=10).grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(ranges_frame, text="Duty Cycle Range (%):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(ranges_frame, textvariable=self.setting_vars['duty_cycle_min'], width=10).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(ranges_frame, text="to").grid(row=1, column=2, padx=(10, 10))
        ttk.Entry(ranges_frame, textvariable=self.setting_vars['duty_cycle_max'], width=10).grid(row=1, column=3, padx=5, pady=5)

        cal_frame = ttk.LabelFrame(main_frame, text="Sensor Calibration (Voltage Mapping)", padding=(15, 10))
        cal_frame.pack(fill="x", pady=10)
        ttk.Label(cal_frame, text="Sensor", font=self.header_font).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(cal_frame, text="Slope", font=self.header_font).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(cal_frame, text="Offset", font=self.header_font).grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(cal_frame, text="Force:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(cal_frame, textvariable=self.setting_vars['force_slope'], width=15).grid(row=1, column=1, padx=5, pady=5)
        ttk.Entry(cal_frame, textvariable=self.setting_vars['force_offset'], width=15).grid(row=1, column=2, padx=5, pady=5)
        ttk.Label(cal_frame, text="Displacement:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(cal_frame, textvariable=self.setting_vars['disp_slope'], width=15).grid(row=2, column=1, padx=5, pady=5)
        ttk.Entry(cal_frame, textvariable=self.setting_vars['disp_offset'], width=15).grid(row=2, column=2, padx=5, pady=5)
        ttk.Label(cal_frame, text="Temperature:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(cal_frame, textvariable=self.setting_vars['temp_slope'], width=15).grid(row=3, column=1, padx=5, pady=5)
        ttk.Entry(cal_frame, textvariable=self.setting_vars['temp_offset'], width=15).grid(row=3, column=2, padx=5, pady=5)

        defaults_frame = ttk.LabelFrame(main_frame, text="Test Defaults", padding=(15, 10))
        defaults_frame.pack(fill="x", pady=10)
        ttk.Label(defaults_frame, text="Default Linear Speed (in/s):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(defaults_frame, textvariable=self.setting_vars['default_linear_speed_ips'], width=15).grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(defaults_frame, text="Default Cycle Count:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(defaults_frame, textvariable=self.setting_vars['default_num_cycles'], width=15).grid(row=1, column=1, padx=5, pady=5)


        action_frame = ttk.Frame(main_frame, padding=(0, 10))
        action_frame.pack(fill="x", side="bottom")
        save_button = ttk.Button(action_frame, text="Save Settings", command=self._save_settings)
        save_button.pack(side="right", padx=5)
        revert_button = ttk.Button(action_frame, text="Revert Changes", command=self._revert_settings)
        revert_button.pack(side="right")
        

    def _create_analysis_tab(self, parent_tab):
        ttk.Label(parent_tab, text="PLACEHOLDER FOR ANALYSIS", font=self.widget_font).pack(padx=20, pady=20)


    def on_closing(self):
        """Handles the complete application shutdown sequence robustly."""
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None
        try:
            self.test_manager.daq.close() 
        except Exception as e:
            print(f"Error during DAQ cleanup: {e}")
        finally:
            self.destroy()
            os._exit(0)


    def process_daq_queue(self):
        """Check the queue for new data from the DAQ and update the GUI."""
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
            self._after_id = self.after(100, self.process_daq_queue)