from gui import DamperDynoGUI
from daq import DAQController
from test_manager import TestManager

daq = DAQController("Dev1")         # Create a DAQController object for the NI device
test_manager = TestManager(daq)     # Create a TestManager object and pass it the DAQController instance
app = DamperDynoGUI(test_manager)   # Create the GUI application and link it to the TestManager instance
app.mainloop()                      # Start the GUI event loop (keeps the app running and responsive)

