import csv
import datetime

def save_test_data(data, filename=None):
    """
    Save test data to CSV. Assumes the first row of 'data' is the header.
    """
    if not data:
        print("Warning: No data to save.")
        return

    if filename is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"damper_test_{timestamp}.csv"

    try:
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(data)
            
        print(f"Test data successfully saved to {filename}")

    except IOError as e:
        print(f"Error saving data to {filename}: {e}")

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