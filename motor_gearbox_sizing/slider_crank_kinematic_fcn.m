function [x, x_dot, x_ddot] = slider_crank_kinematic_fcn(theta, theta_dot, Lc, R)
%SLIDER_CRANK_KINEMATIC_FCN Compute position, velocity, and acceleration of a slider in a slider-crank mechanism.
%
%   [x, x_dot, x_ddot] = slider_crank_kinematic_fcn(theta, theta_dot, Lc, R)
%
%   This function calculates the slider position, velocity, and acceleration 
%   for a standard in-line slider-crank mechanism given crank angle(s) θ 
%   and crank angular velocity θ̇. The connecting rod length (Lc) and 
%   crank radius (R) are used to derive the kinematic relationships.
%
%   Inputs:
%       theta      - Crank angle [rad] (scalar or vector)
%       theta_dot  - Crank angular velocity [rad/s] (scalar or vector same size as theta)
%       Lc         - Connecting rod length [in or consistent units]
%       R          - Crank radius [in or consistent units]
%
%   Outputs:
%       x          - Slider displacement relative to crank pin [same units as R]
%       x_dot      - Slider linear velocity [units of x / s]
%       x_ddot     - Slider linear acceleration [units of x / s^2]
%
%   Notes:
%       - θ is measured from crank angle reference where θ=0 corresponds 
%         to the crank aligned with slider axis.
%       - The equations assume constant crank angular velocity θ̇.
%       - Works with scalar or vector θ.

    % Dimensionless ratio
    n = Lc / R;

    % Position: x(θ)
    x = R .* (1 - cos(theta) + n - sqrt(n.^2 - sin(theta).^2));

    % Velocity: dx/dt = (dx/dθ)*θ̇
    dx_dtheta = R .* (sin(theta) + (sin(2*theta)) ./ (2 .* sqrt(n.^2 - sin(theta).^2)));
    x_dot = theta_dot .* dx_dtheta;

    % Acceleration: d²x/dt² = (d²x/dθ²)*(θ̇²)
    denom = sqrt(n.^2 - sin(theta).^2);
    d2x_dtheta2 = R .* (cos(theta) + (cos(2*theta)) ./ denom + ...
                        (sin(theta).^2 .* cos(theta).^2) ./ (denom.^3));
    x_ddot = (theta_dot).^2 .* d2x_dtheta2;
end
