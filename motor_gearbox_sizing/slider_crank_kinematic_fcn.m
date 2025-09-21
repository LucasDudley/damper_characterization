function [x, x_dot, x_ddot] = slider_crank_kinematic_fcn(theta, theta_dot, theta_ddot, Lc, R)
%   Calculates slider position, velocity, and acceleration for an
%   in-line slider-crank mechanism given crank angle(s) θ, crank angular
%   velocity θ̇, connecting rod length Lc, and crank radius R.
%
%   Inputs:
%       theta      - Crank angle [rad] (scalar or vector)
%       theta_dot  - Crank angular velocity [rad/s]
%       Lc         - Connecting rod length [consistent units]
%       R          - Crank radius [consistent units]
%
%   Outputs:
%       x          - Slider displacement [same units as R]
%       x_dot      - Slider velocity [units of x/s]
%       x_ddot     - Slider acceleration [units of x/s²]


    % Parameters
    n = Lc / R;
    denom = sqrt(n.^2 - sin(theta).^2);

    % Slider Pos
    x = R .* (1 - cos(theta) + n - denom);

    % (dx/dθ)
    dx_dtheta = R .* (sin(theta) + (sin(2*theta)) ./ (2 .* denom));

    % Slider velocity: ẋ = dx/dθ * θ̇
    x_dot = theta_dot .* dx_dtheta;

    % (d²x/dθ²)
    d2x_dtheta2 = R .* (cos(theta) + (cos(2*theta)) ./ denom + ...
                        (sin(2*theta).^2) ./ (2 .* denom.^3));

    % Slider acceleration
    % Full expression: ẍ = R*θ̈*[bracket] + R*θ̇²*[d/dθ bracket]
    x_ddot = theta_ddot .* dx_dtheta + (theta_dot).^2 .* d2x_dtheta2;

end
