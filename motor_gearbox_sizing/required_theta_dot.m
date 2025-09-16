function [theta_dot_req, Gmax, theta_at_Gmax] = required_theta_dot(V_des, Lc, R)
    % REQUIRED_THETA_DOT  required constant angular speed to achieve desired peak linear speed
    %   [theta_dot_req, Gmax, theta_at_Gmax] = required_theta_dot(V_des, Lc, R)
    %
    % Inputs:
    %   V_des - desired maximum linear speed (same units as R * theta_dot)
    %   Lc    - connecting length (m)
    %   R     - crank radius (m)
    %
    % Outputs:
    %   theta_dot_req  - required constant angular speed (rad/s)
    %   Gmax           - maximum geometric gain G(theta)
    %   theta_at_Gmax  - theta (rad) where Gmax occurs
    %
    % Notes:
    %   - G(theta) = R*( sin(theta) + sin(2*theta)/(2*sqrt(n^2 - sin(theta)^2)) )
    %   - requires n = Lc/R; if n < 1 some theta produce imaginary sqrt; those are ignored.
    
    n = Lc ./ R;
    Gfun = @(th) R .* ( sin(th) + (sin(2.*th)) ./ (2.*sqrt(max(0, n.^2 - sin(th).^2))) );
    
    % coarse search on [0, 2*pi)
    theta_grid = linspace(0, 2*pi, 20000);
    Gvals = Gfun(theta_grid);
    
    % invalidate points where sqrt argument was zero and led to inf/nan
    valid = isfinite(Gvals) & ~isnan(Gvals);
    Gvals(~valid) = -Inf;
    
    % coarse maximum
    [Gmax_coarse, idx] = max(Gvals);
    theta_coarse = theta_grid(idx);
    
    % refine near the coarse maximum with fminbnd on negative G (local maximization)
    % choose small interval around theta_coarse
    w = 0.2; % search half-width (rad), adjust if necessary
    a = max(0, theta_coarse - w);
    b = min(2*pi, theta_coarse + w);
    
    % objective for minimizer (negative G)
    negG = @(t) - ( R .* ( sin(t) + (sin(2.*t)) ./ (2.*sqrt(max(1e-12, n.^2 - sin(t).^2)))) );
    
    % ensure a < b; if not, skip refine
    if a < b
        opts = optimset('TolX',1e-10,'Display','off');
        [theta_refined, fval] = fminbnd(negG, a, b, opts);
        Gmax = -fval;
        theta_at_Gmax = theta_refined;
    else
        Gmax = Gmax_coarse;
        theta_at_Gmax = theta_coarse;
    end
    
    % final check: if Gmax <= 0, warn (geometry might not produce positive forward velocity)
    if Gmax <= 0
        warning('Gmax is non-positive (%.4g). Check geometry Lc/R (n) and desired V_des.', Gmax);
    end
    
    % required angular speed
    theta_dot_req = V_des ./ Gmax;

end
