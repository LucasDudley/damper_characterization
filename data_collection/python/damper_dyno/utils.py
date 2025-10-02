import os
import csv
import datetime
from numbers import Number

def save_test_data(data_to_save, settings):
    """
    Saves the collected test data to a CSV file in the specified output directory.

    Args:
        data_to_save (list): A list of lists containing the data, including a header row.
        settings (dict): The settings dictionary, which must contain the 'output_dir' key.
    """
    try:
        # Get the output directory from the settings dictionary.
        output_dir = settings.get('output_dir')
        if not output_dir:
            print("Error: 'output_dir' not found in settings. Cannot save data.")
            return

        os.makedirs(output_dir, exist_ok=True)

        # Generate a unique filename using the current date and time.
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"dyno_test_{timestamp}.csv"
        
        # Combine the directory and filename into a full path.
        full_filepath = os.path.join(output_dir, filename)

        print(f"Saving test data to: {full_filepath}")

        # Write the data to the CSV file using the 'csv' module.
        with open(full_filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(data_to_save)
        
        print("Data saved successfully.")

    except KeyError:
        print("Error: The provided settings dictionary is missing the 'output_dir' key.")
    except Exception as e:
        print(f"An unexpected error occurred while saving the data: {e}")

def convert_speed_to_duty_cycle(speed_rpm, rpm_range=[0, 100], duty_cycle_range=[10, 90]):
    """
    Convert a angular_speed in RPM to PWM duty cycle (%) using linear interpolation.

    Parameters:
        speed_rpm : float
            Target speed in RPM.
        rpm_range : list of two floats [rpm_min, rpm_max]
            Minimum and maximum RPM values.
        duty_cycle_range : list of two floats [duty_min, duty_max]
            Minimum and maximum PWM duty cycle (%) corresponding to rpm_range.

    Returns:
        float : Duty cycle (%) clipped to duty_cycle_range.
    """

    # Linear interpolation using indices directly
    duty_cycle = duty_cycle_range[0] + (speed_rpm - rpm_range[0]) * \
                 (duty_cycle_range[1] - duty_cycle_range[0]) / (rpm_range[1] - rpm_range[0])

    # Clip to duty cycle range
    return max(min(duty_cycle, duty_cycle_range[1]), duty_cycle_range[0])

def map_voltage_to_force(voltage):
    """
    Maps voltage from a load cell to force in Newtons.
    """
    slope = 392.5 #N/V
    offset = 0
    return (voltage * slope) + offset

def map_voltage_to_displacement(voltage):
    """
    Maps voltage from a displacement sensor to millimeters.
    """
    slope = 10 #mm/V
    offset = 0
    return (voltage * slope) + offset

def map_voltage_to_temperature(voltage):
    """
    Maps voltage from a temperature sensor to Celsius.
    """
    slope = 40 #C/V
    offset = 0
    return (voltage * slope) + offset