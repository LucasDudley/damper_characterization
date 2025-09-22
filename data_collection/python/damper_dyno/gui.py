import tkinter as tk
from plots import RealTimePlot
import threading

class DamperDynoGUI(tk.Tk):
    def __init__(self, TestManager):
        # Initialize the base Tkinter window
        super().__init__()
        self.test_manager = TestManager     # Store reference to the TestManager instance
        self.title("Damper Dyno")           # Set window title
        self.create_widgets()               # method to build gui widgets

    def create_widgets(self):
        """Create and arrange GUI components."""

        # realtime plot section
        self.realtime_plot = RealTimePlot(self, channels=["AI0", "AI1", "AI2"]) # Create a real-time plot widget

        # Control Frame Section
        frame = tk.Frame(self)  # Container for control widgets
        frame.pack(pady=5)

        # Speed input
        tk.Label(frame, text="Speed (RPM)").pack(side=tk.LEFT)
        self.speed_entry = tk.Entry(frame, width=5)  # Entry box for user to input speed
        self.speed_entry.pack(side=tk.LEFT, padx=5)

        # Cycles input
        tk.Label(frame, text="Cycles").pack(side=tk.LEFT)
        self.cycles_entry = tk.Entry(frame, width=5)  # Entry box for user to input number of cycles
        self.cycles_entry.pack(side=tk.LEFT, padx=5)

        # Start button: begins test
        tk.Button(frame, text="Start", command=self.start_test).pack(side=tk.LEFT, padx=5)

        # Quit button: closes the GUI
        tk.Button(frame, text="Quit", command=self.quit).pack(side=tk.LEFT, padx=5)

    def start_test(self):
        """Retrieve user input and start the test in a separate thread."""
        # Get user inputs
        speed = float(self.speed_entry.get())
        cycles = int(self.cycles_entry.get())

        # pass live plot to the test manager so it can update in real-time
        self.test_manager.realtime_plot = self.realtime_plot

        # run the test in a separate thread (keeps GUI responsive while test runs)
        threading.Thread(
            target=self.test_manager.run_test,
            args=(speed, cycles),
            daemon=True  # Daemon thread will close automatically when GUI closes
        ).start()


