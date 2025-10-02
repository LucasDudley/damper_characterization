from gui import DamperDynoGUI
from daq import DAQController
from test_manager import TestManager
from nidaqmx.errors import DaqError

def main():
    """
    Main function to initialize and run the Damper Dyno application.
    """
    print("Starting Damper Dyno App")

    try:
        # Initialize the hardware controller.
        daq = DAQController("Dev1")
    except DaqError as e:
        print(f"Could not connect to NI DAQ device 'Dev1'. ")
        print(f"NI-DAQmx Error: {e}")
        return 
    except Exception as e:
        print(f"An unexpected error occurred during startup: {e}")
        input("Press Enter to exit.")
        return

    test_manager = TestManager(daq)
    app = DamperDynoGUI(test_manager)
    app.mainloop()

if __name__ == "__main__":
    main()