function [x, x_dot, x_ddot] = slider_crank_kinematic_fcn(theta, theta_dot, Lc, R)
%   This function calculates the slider position, velocity, and acceleration 
%   for a standard in-line slider-crank mechanism given crank angle(s) θ 
%   and crank angular velocity θ̇. The connecting rod length (Lc) and 
%   crank radius (R) are used to derive the kinematic relationships.
%
%   Inputs:
%       theta      - Crank angle [rad] (scalar or vector)
%       theta_dot  - Crank angular velocity [rad/s]
%       Lc         - Connecting rod length [in or consistent units]
%       R          - Crank radius [in or consistent units]
%
%   Outputs:
%       x          - Slider displacement [same units as R]
%       x_dot      - Slider velocity [units of x/s]
%       x_ddot     - Slider acceleration [units of x/s²]
%
%   Assumptions:
%       - θ is measured from crank aligned with slider axis.
%       - θ̇ is constant (θ̈ = 0).

    n = Lc / R;
    denom = sqrt(n.^2 - sin(theta).^2);

    % Position
    x = R .* (1 - cos(theta) + n - denom);

    % First derivative dx/dθ
    dx_dtheta = R .* (sin(theta) + (sin(2*theta)) ./ (2 .* denom));
    x_dot = theta_dot .* dx_dtheta;

    % Second derivative d²x/dθ²
    numerator_accel = n.^2 .* cos(2.*theta) + sin(theta).^4;
    denom_accel = (n.^2 - sin(theta).^2).^(3/2);
    x_ddot = theta_dot.^2 .* R .* (cos(theta) + numerator_accel ./ denom_accel);
end
