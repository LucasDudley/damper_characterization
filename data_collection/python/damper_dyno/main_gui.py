import os
import logging
import queue
import tkinter as tk
from tkinter import ttk, font
from ttkthemes import ThemedTk
from gui_tabs import RunTestTab, SettingsTab

class DamperDynoGUI(ThemedTk):
    def __init__(self, test_manager, settings_manager):
        super().__init__(theme="arc")
        
        self.test_manager = test_manager
        self.settings_manager = settings_manager
        self.title("Damper Dyno")

        # font style
        self.fonts = {
            'btn_font': font.Font(family="Helvetica", size=18, weight="bold"),
            'widget_font': font.Font(family="Helvetica", size=18),
            'header_font': font.Font(family="Helvetica", size=13, weight="bold"),
            'label_font': font.Font(family="Helvetica", size=12),
            'entry_font': font.Font(family="Helvetica", size=12)
        }
        self._configure_styles()

        # init
        self.settings_manager.initialize_tk_vars(master=self)
        self._after_id = None
        self.create_gui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.process_daq_queue()

    def _configure_styles(self):
        style = ttk.Style()
        style.configure("TLabelFrame.Label", font=self.fonts['header_font'])
        style.configure("TLabel", font=self.fonts['label_font'])
        style.configure("TButton", font=self.fonts['label_font'])
        style.configure("TEntry", font=self.fonts['entry_font'], padding=(5, 5, 5, 5))
        style.configure("Big.TButton", font=self.fonts['btn_font'], padding=(10, 10))
        style.configure("Custom.TNotebook.Tab", font=self.fonts['btn_font'], padding=[10, 0])
        style.configure("Custom.TNotebook", tabmargins=[10, 5, 10, 0])

    def create_gui(self):
        notebook = ttk.Notebook(self, style="Custom.TNotebook")
        notebook.pack(expand=True, fill="both", padx=20, pady=10)

        self.run_tab = RunTestTab(notebook, self.test_manager, self.settings_manager, self.fonts, on_quit=self.on_closing)
        settings_tab = SettingsTab(notebook, self.settings_manager, self.fonts)
        analysis_tab = ttk.Frame(notebook)

        notebook.add(self.run_tab, text="Run Test")
        notebook.add(settings_tab, text="Settings")
        notebook.add(analysis_tab, text="Analysis")
        ttk.Label(analysis_tab, text="ANALYSIS TAB PLACEHOLDER", font=self.fonts['widget_font']).pack(padx=20, pady=20)

    def process_daq_queue(self):
        """
        Drains the DAQ queue, processes commands, and updates plots.
        This runs in the main GUI thread.
        """
        MAX_POINTS = 5000  # Max number of data points to keep in memory for plotting

        try:
            sample_rate = int(self.settings_manager.get_var('sample_rate').get())
        except (ValueError, tk.TclError):
            sample_rate = 1000 # fallback

        try:
            new_data_received = False
            while not self.test_manager.gui_queue.empty():
                packet = self.test_manager.gui_queue.get_nowait()
                
                if isinstance(packet, dict) and 'command' in packet:
                    if packet['command'] == 'reset_plots':
                        logging.info("GUI: Received reset_plots command.")
                        # reset the plots (clear)
                        self.run_tab.force_plot.reset()
                        self.run_tab.disp_plot.reset()

                        #clear plot buffers
                        self.run_tab.time_q.clear()
                        self.run_tab.force_q.clear()
                        self.run_tab.disp_q.clear()
                        self.run_tab.vel_q.clear()
                
                elif isinstance(packet, dict) and 'times' in packet:
                    # data packet
                    new_data_received = True
                    self.run_tab.time_q.extend(packet['times'])
                    self.run_tab.force_q.extend(packet['force'])
                    self.run_tab.disp_q.extend(packet['disp'])
                    self.run_tab.vel_q.extend(packet['vel'])


                    if self.run_tab.temp_var and packet['temp'] is not None:
                        self.run_tab.temp_var.set(f"{packet['temp']:.1f} °C")
                
            if new_data_received:
                #trim data buffers but keep history for the plot window
                if len(self.run_tab.time_q) > MAX_POINTS:
                    trim_amount = len(self.run_tab.time_q) - MAX_POINTS
                    
                    self.run_tab.time_q = self.run_tab.time_q[trim_amount:]
                    self.run_tab.force_q = self.run_tab.force_q[trim_amount:]
                    self.run_tab.disp_q = self.run_tab.disp_q[trim_amount:]
                    self.run_tab.vel_q = self.run_tab.vel_q[trim_amount:]
                    
                    #update the plot's tracking index
                    self.run_tab.force_plot.last_idx = max(0, self.run_tab.force_plot.last_idx - trim_amount)
                    self.run_tab.disp_plot.last_idx = max(0, self.run_tab.disp_plot.last_idx - trim_amount)
                
                # update plots with the trimmed data
                self.run_tab.force_plot.update(
                    self.run_tab.time_q, 
                    [self.run_tab.force_q], 
                    sample_rate=sample_rate
                )
                self.run_tab.disp_plot.update(
                    self.run_tab.time_q, 
                    [self.run_tab.disp_q, self.run_tab.vel_q], 
                    sample_rate=sample_rate
                )
        
        except queue.Empty:
            pass
        finally:
            self._after_id = self.after(100, self.process_daq_queue)

    def on_closing(self):
        """Handles the complete application shutdown sequence."""
        if self._after_id: self.after_cancel(self._after_id)
        try: self.test_manager.daq.close()
        except Exception as e: logging.error(f"Error during DAQ cleanup: {e}")
        finally:
            self.destroy()
            os._exit(0)