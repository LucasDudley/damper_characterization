import tkinter as tk
from plots import RealTimePlot
import threading
from tkinter import font

class DamperDynoGUI(tk.Tk):
    def __init__(self, TestManager):
        super().__init__()
        self.test_manager = TestManager
        self.title("Damper Dyno")
        self.create_widgets()

    def create_widgets(self):
        """Create and arrange GUI components with bigger buttons and an E-Stop."""
        # realtime plot
        self.realtime_plot = RealTimePlot(self, channels=["AI0", "AI1", "AI2"])
        
        # custom font for bigger buttons
        btn_font = font.Font(size=12, weight="bold")

        # control frame
        frame = tk.Frame(self)
        frame.pack(pady=5)

        # Speed input
        tk.Label(frame, text="Speed (RPM)").pack(side=tk.LEFT)
        self.speed_entry = tk.Entry(frame, width=6)
        self.speed_entry.pack(side=tk.LEFT, padx=5)

        # Cycles input
        tk.Label(frame, text="Cycles").pack(side=tk.LEFT)
        self.cycles_entry = tk.Entry(frame, width=6)
        self.cycles_entry.pack(side=tk.LEFT, padx=5)

        # Start button
        tk.Button(
            frame, text="Start", font=btn_font, width=8, height=2,
            bg="green", fg="white", command=self.start_test
        ).pack(side=tk.LEFT, padx=10)

        # E-Stop button (bright red)
        tk.Button(
            frame, text="E-STOP", font=btn_font, width=8, height=2,
            bg="red", fg="white", command=self.emergency_stop
        ).pack(side=tk.LEFT, padx=10)

        # Quit button
        tk.Button(
            frame, text="Quit", font=btn_font, width=8, height=2,
            bg="gray", fg="white", command=self.quit
        ).pack(side=tk.LEFT, padx=10)

    def start_test(self):
        """Retrieve user input and start the test in a separate thread."""
        try:
            speed = float(self.speed_entry.get())
            cycles = int(self.cycles_entry.get())
        except ValueError:
            print("Invalid input for speed or cycles.")
            return

        self.test_manager.realtime_plot = self.realtime_plot

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