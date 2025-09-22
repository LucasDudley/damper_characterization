import tkinter as tk
from plots import RealTimePlot
import threading

class DamperDynoGUI(tk.Tk):
    def __init__(self, TestManager):
        super().__init__()
        self.test_manager = TestManager
        self.title("Damper Dyno")
        self.create_widgets()

    def create_widgets(self):
        # Live plot
        self.live_plot = RealTimePlot(self, channels=["AI0","AI1","AI2"])

        # Control frame
        frame = tk.Frame(self)
        frame.pack(pady=5)

        tk.Label(frame, text="Speed (RPM)").pack(side=tk.LEFT)
        self.speed_entry = tk.Entry(frame, width=5)
        self.speed_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(frame, text="Cycles").pack(side=tk.LEFT)
        self.cycles_entry = tk.Entry(frame, width=5)
        self.cycles_entry.pack(side=tk.LEFT, padx=5)

        tk.Button(frame, text="Start", command=self.start_test).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Quit", command=self.quit).pack(side=tk.LEFT, padx=5)

    def start_test(self):
        speed = float(self.speed_entry.get())
        cycles = int(self.cycles_entry.get())
        # Run test in background with live plot
        self.test_manager.live_plot = self.live_plot
        threading.Thread(target=self.test_manager.run_test, args=(speed, cycles), daemon=True).start()

