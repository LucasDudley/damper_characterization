function [T, phi, F_connecting_rod] = slider_crank_torque(theta, F_slider, R, Lc)
%   Calculates crank torque required to resist a specified horizontal slider force,
%   and outputs intermediate linkage values.
%
%   Inputs:
%       theta     - Crank angle [rad] (scalar or vector)
%       F_slider  - Horizontal slider force [lbf]
%       R         - Crank radius [in]
%       Lc        - Connecting rod length [in]
%
%   Outputs:
%       T                 - Crank torque required [lbf·in]
%       phi               - Connecting rod angle [rad]
%       F_connecting_rod  - Axial force in connecting rod [lbf]
%
%   Reference:
%       Force equilibrium of a slider-crank linkage:
%       phi = asin((R * sin(theta)) / Lc)
%       F_c = F_slider / cos(phi)
%       T   = F_c * R * sin(theta + phi)

    % --- Compute connecting rod angle phi [rad] ---
    sin_phi = (R .* sin(theta)) ./ Lc;
    phi = asin(sin_phi);

    % --- Axial force in connecting rod ---
    F_connecting_rod = F_slider ./ cos(phi);

    % --- Crank torque ---
    T = F_connecting_rod .* R .* sin(theta + phi);
end

