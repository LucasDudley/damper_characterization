from gui import DamperDynoGUI
from daq import DAQController
from test_manager import TestManager

daq = DAQController("Dev1")
test_manager = TestManager(daq)
app = DamperDynoGUI(test_manager)
app.mainloop()
