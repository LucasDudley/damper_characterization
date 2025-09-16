function T = slider_crank_torque(theta, F_slider, R, Lc)
%SLIDER_CRANK_TORQUE  Compute crank torque for a given horizontal slider force.
%
%   T = slider_crank_torque(theta, F_slider, R, L)
%
%   Inputs:
%       theta     - Crank angle [rad] (scalar or vector)
%       F_slider  - Horizontal slider force [lbf] (scalar or vector same size as theta)
%       R         - Crank radius [in]
%       Lc         - Connecting rod length [in]
%
%   Output:
%       T         - Crank torque required [lbf·in]

    % Ensure force vector matches theta
    if numel(F_slider) == 1
        F_slider = F_slider * ones(size(theta));
    elseif ~isequal(size(F_slider), size(theta))
        error('F_slider must be scalar or same size as theta.');
    end

    % Avoid complex numbers near singularity
    under_sqrt = Lc^2 - (R .* sin(theta)).^2;
    if any(under_sqrt < 0)
        warning('Some theta values give impossible geometry (R > L or too large angle).');
        under_sqrt = max(under_sqrt, 0);
    end

    % dx/dtheta
    dx_dtheta = -R.*sin(theta) - (R^2 .* sin(theta) .* cos(theta)) ./ sqrt(under_sqrt);

    % Torque
    T = F_slider .* dx_dtheta; % [lbf·in]
end
