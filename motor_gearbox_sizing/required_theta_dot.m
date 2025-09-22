function [theta_dot_req, Gmax, theta_at_Gmax] = required_theta_dot(V_des, Lc, R)
% required constant angular speed to achieve desired peak linear speed

    n = Lc / R;
    if n < 1
        warning('n = Lc/R < 1. Some theta will produce imaginary sqrt');
    end

    % define G(theta)
    function G = Gfun(th)
        s = sin(th);
        root = n^2 - s.^2;
        mask = root > 0;  % only keep physically valid thetas
        G = -inf(size(th)); % prefill invalid points with -inf
        G(mask) = R .* ( s(mask) + sin(2*th(mask)) ./ (2*sqrt(root(mask))) );
    end

    % Coarse search with fewer points
    N = 2000;
    theta_grid = linspace(0, 2*pi, N);
    Gvals = Gfun(theta_grid);

    [Gmax_coarse, idx] = max(Gvals);
    theta_coarse = theta_grid(idx);

    %Refine around coarse maximum
    w = 0.15; % smaller window because grid is denser
    a = theta_coarse - w;
    b = theta_coarse + w;

    if a < b
        % objective: -G for maximization
        negG = @(t) -Gfun(t);
        theta_at_Gmax = fminbnd(negG, a, b);
        Gmax = Gfun(theta_at_Gmax);
    else
        Gmax = Gmax_coarse;
        theta_at_Gmax = theta_coarse;
    end

    % final check
    if Gmax <= 0
        warning('Gmax is non-positive (%.4g). Check geometry.', Gmax);
    end

    % Required angular velocity
    theta_dot_req = V_des / Gmax;
end
