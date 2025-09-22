
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


