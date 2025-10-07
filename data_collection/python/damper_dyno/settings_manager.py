import os
import json
import tkinter as tk
from tkinter import messagebox

class SettingsManager:
    """Handles loading, saving, and managing application settings from a JSON file."""

    def __init__(self, filepath="config.json"):
        self.filepath = filepath
        self.settings = {}
        self.setting_vars = {}
        self._load_data_from_file()

    def _load_data_from_file(self):
        """Reads the config file into a standard Python dictionary."""
        try:
            with open(self.filepath, 'r') as f:
                self.settings = json.load(f)
            print(f"Successfully loaded settings from '{self.filepath}'")
        except FileNotFoundError:
            messagebox.showerror("Fatal Error: Configuration Missing", f"The required configuration file was not found.\n\nExpected location: {os.path.abspath(self.filepath)}")
            os._exit(1)
        except json.JSONDecodeError as e:
            messagebox.showerror("Fatal Error: Configuration Corrupt", f"The configuration file is not valid JSON.\n\nError: {e}")
            os._exit(1)

    def initialize_tk_vars(self, master):
        """Creates the tkinter StringVars. Must be called AFTER the main window exists."""
        for key, val in self.settings.items():
            self.setting_vars[key] = tk.StringVar(master=master, value=val)

    def save(self):
        """Saves the current values from the StringVars back to the config file."""
        settings_to_save = {}
        for key, var in self.setting_vars.items():
            value = var.get()
            try:
                if '.' in str(value):
                    settings_to_save[key] = float(value)
                else:
                    settings_to_save[key] = int(value)
            except (ValueError, TypeError):
                settings_to_save[key] = value

        try:
            with open(self.filepath, 'w') as f:
                json.dump(settings_to_save, f, indent=4)
            messagebox.showinfo("Settings Saved", "Configuration has been updated successfully.")
        except Exception as e:
            messagebox.showerror("File Write Error", f"Could not write to config file.\n\nError: {e}")

    def revert(self):
        """Discards unsaved changes by reloading from the config file."""
        if messagebox.askyesno("Revert Unsaved Changes", "Are you sure you want to discard unsaved changes?"):
            print("Reverting settings to last saved state.")
            self._load_data_from_file()
            for key, val in self.settings.items():
                if key in self.setting_vars:
                    self.setting_vars[key].set(val)

    def get_var(self, key):
        """Safely gets a StringVar."""
        return self.setting_vars.get(key, tk.StringVar(value=""))