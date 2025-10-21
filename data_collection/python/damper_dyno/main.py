import os
import logging
import tkinter as tk
from tkinter import messagebox

try:
    from nidaqmx.errors import DaqError
    NIDAQMX_AVAILABLE = True
except ImportError:
    DaqError = Exception
    NIDAQMX_AVAILABLE = False

from main_gui import DamperDynoGUI
from daq import DAQController
from test_manager import TestManager
from settings_manager import SettingsManager

def setup_logging():
    """Configures logging to print to console and save to a file."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("damper_dyno.log", mode="w"),
            logging.StreamHandler()
        ]
    )

def main():
    """
    Main function to initialize and run the Damper Dyno application.
    """
    setup_logging()
    logging.info("Application starting")
    
    # Check for NI-DAQmx drivers available on device
    if not NIDAQMX_AVAILABLE:
        root = tk.Tk()
        root.withdraw()
        logging.error("NI-DAQmx library not found. install with 'pip install nidaqmx'.")
        messagebox.showerror("Dependency Error", "NI-DAQmx not found.\nPlease ensure its installed to connect to hardware.")
        return

    # Initialize settings manager with config.json
    settings_manager = SettingsManager("config.json")
    
    # Get the DAQ device name from the loaded settings
    daq_device_name = settings_manager.settings.get("daq_device_name", "Dev1")

    # Initialize Hardware
    try:
        logging.info(f"Attempting to connect to DAQ device: '{daq_device_name}'")
        daq = DAQController(daq_device_name)
    except DaqError as e:
        # We need a root to show a messagebox before the main GUI exists (to show error)
        root = tk.Tk()
        root.withdraw()
        logging.error(f"Could not connect to NI DAQ device '{daq_device_name}'. Error: {e}")
        messagebox.showerror(
            "Hardware Connection Error",
            f"Could not connect to NI DAQ device '{daq_device_name}'.\n\n"
            "Please ensure the device is connected and visible in NI-MAX.\n\n"
            f"Error: {e}"
        )
        return
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        logging.error(f"An unexpected error occurred during hardware initialization: {e}")
        messagebox.showerror("Unexpected Error", f"An unexpected error occurred during startup:\n\n{e}")
        return
    
    # Initialize Core Components and Run GUI
    logging.info("Hardware initialized successfully.")
    test_manager = TestManager(daq) # feed daq object into test mangager object
    
    # Inject both the test_manager and settings_manager into the GUI object
    app = DamperDynoGUI(test_manager, settings_manager)
    
    app.mainloop()

    logging.info("Application shut down.")


if __name__ == "__main__":
    main()