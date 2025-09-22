function T = slider_crank_torque(theta, F_slider, R, Lc)
%   This function calculates the torque required at the crank of a slider-crank
%   mechanism to resist a specified horizontal slider force.
%
%   Inputs:
%       theta     - Crank angle [rad] (scalar or vector)
%                   Measured from inner dead center (IDC), CCW positive.
%       F_slider  - Horizontal slider force [lbf] (same size as theta)
%                   Positive force resists slider motion away from crank.
%       R         - Crank radius [in]
%       Lc        - Connecting rod length [in]
%
%   Output:
%       T         - Crank torque required [lbf·in]
%
%   Reference:
%       Derived from force equilibrium of a slider-crank linkage:
%       T = F_s * R * sin(theta + phi) / cos(phi)
%       where phi = asin((R * sin(theta)) / Lc) is the connecting rod angle.

    % Compute connecting rod angle phi [rad]
    sin_phi = (R .* sin(theta)) ./ Lc;
    phi = asin(sin_phi);  % connecting rod angle relative to slider axis

    %Compute crank torque
    % T = F_slider * R * sin(theta + phi) / cos(phi)
    T = F_slider .* R .* sin(theta + phi) ./ cos(phi);

end
