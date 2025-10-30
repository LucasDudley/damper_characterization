import os
import csv
import datetime
import numpy as np
from scipy.optimize import minimize_scalar
import warnings

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

def convert_speed_to_duty_cycle(speed_rpm, rpm_range, duty_cycle_range):
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
    slope = 198.38 #N/V
    offset = 0
    return (voltage * slope) + offset

def map_voltage_to_displacement(voltage):
    """
    Maps voltage from a displacement sensor to millimeters.
    """
    slope = 9.64 #mm/V
    offset = 0
    return (voltage * slope) + offset

def map_voltage_to_temperature(voltage):
    """
    Maps voltage from a temperature sensor to Celsius.
    """
    slope = 38.6 #C/V
    offset = 0
    return (voltage * slope) + offset

def required_theta_dot(V_des, Lc, R):
    """
    Calculates the required constant angular speed of a crank to achieve a 
    desired peak linear speed of a piston in a slider-crank mechanism.

    The optimization is performed in two steps: a coarse grid search followed by a
    fine, bounded optimization using SciPy's optimizer.

    Args:
        V_des (float): The desired peak linear speed of the piston.
        Lc (float): The length of the connecting rod.
        R (float): The radius of the crank.

    Returns:
        tuple: A tuple containing:
            - theta_dot_req (float): The required constant angular speed in rad/s.
            - Gmax (float): The maximum value of the geometric function G(theta).
            - theta_at_Gmax (float): The angle theta (in radians) at which G is maximum.
    """
        
    n = Lc / R
    if n < 1:
        warnings.warn(
            f"n = Lc/R = {n:.4g} < 1. This geometry is not physically possible "
            "and will produce imaginary results for some theta."
        )

    def Gfun(th):
        """
        Geometric function G(theta) that relates linear to angular velocity.
        Handles arrays and scalars, and masks invalid theta values.
        """
        # Ensure input is a numpy array
        th = np.asarray(th)
        s = np.sin(th)
        root_term = n**2 - s**2

        # mask for valid inputs (term under sqrt is non-negative)
        mask = root_term >= 0

        # Initialize G (match the input shape)
        G = np.full(th.shape, -np.inf)

        # Calc G for the valid values to avoid sqrt domain errors
        G[mask] = R * (s[mask] + np.sin(2 * th[mask]) / (2 * np.sqrt(root_term[mask])))
        
        # If the input was a scalar, return a scalar for the optimizer
        return G.item() if G.ndim == 0 else G

    # 1. coarse search
    N = 100
    theta_grid = np.linspace(0, 2 * np.pi, N)
    G_vals = Gfun(theta_grid)
    
    # Find the index of the maximum value in the coarse grid
    idx = np.argmax(G_vals)
    theta_coarse = theta_grid[idx]

    # 2. Refine the search around the coarse maximum using a bounded optimizer
    w = 0.15
    a = theta_coarse - w
    b = theta_coarse + w

    # To maximize G(t), we minimize -G(t)
    negG = lambda t: -Gfun(t)

    result = minimize_scalar(negG, bounds=(a, b), method='bounded')

    if not result.success:
        warnings.warn(f"Optimization failed: {result.message}. Falling back to coarse grid result.")
        Gmax = G_vals[idx]
        theta_at_Gmax = theta_coarse
    else:
        theta_at_Gmax = result.x
        Gmax = -result.fun

    # checks and calculation
    if Gmax <= 0:
        warnings.warn(f"Gmax is non-positive ({Gmax:.4g}). Check geometry.", UserWarning)
        # Avoid division by zero or negative speed
        theta_dot_req = np.inf if V_des > 0 else 0
    else:
        # Required angular velocity
        theta_dot_req = V_des / Gmax

    return gearbox_scaling(10, theta_dot_req), Gmax, theta_at_Gmax

def gearbox_scaling(gear_ratio, desired_input):

    # scale the desired speed by the gear ratio
    required_output = gear_ratio * desired_input 

    return required_output

def map_HLFB_pwm_to_torque(HLFB_pwm, motor_speed, settings):
    """
    Calculates motor torque by interpolating max torque from speed 
    and then applying a torque percentage mapped from an HLFB PWM signal.
    """
    motor_params = settings.get('motor_max_torque_map')
    max_torque_at_speed = np.interp(motor_speed, motor_params[0], motor_params[1])

    # interpolate the torque wrt the pwm signal 
    pwm_lims = [[0.5, 0.95], [0, 100]]
    percent_torque = np.interp(HLFB_pwm, pwm_lims[0], pwm_lims[1])

    # calculate final motor torque
    motor_torque = (percent_torque / 100.0) * max_torque_at_speed

    return motor_torque