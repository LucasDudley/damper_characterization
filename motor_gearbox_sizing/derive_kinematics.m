clear, clc, close all

syms theta theta_dot R n


% Define the Position Equation
% This is the exact analytical equation for the slider's displacement
% measured from its position at theta = 0 (Top Dead Center).
x = R * (1 - cos(theta) + n - sqrt(n^2 - sin(theta)^2));

fprintf('Original Position Equation, x(theta):\n');
pretty(x);
fprintf('\n');


%Compute Velocity
% dx/d(theta)
dx_dtheta = diff(x, theta);

% The velocity (x_dot) is found using the chain rule:
% x_dot = (dx/d(theta)) * (d(theta)/dt)
x_dot = dx_dtheta * theta_dot;

fprintf('-----------------------------------------------------\n');
fprintf('Derived Velocity Equation, x_dot(theta):\n');
pretty(simplify(x_dot));
fprintf('\n');


% Compute Acceleration
% d^2x/d(theta)^2
d2x_dtheta2 = diff(dx_dtheta, theta);

% The acceleration (x_ddot) is found assuming a constant angular velocity (theta_ddot = 0):
% x_ddot = (d^2x/d(theta)^2) * (d(theta)/dt)^2
x_ddot = d2x_dtheta2 * theta_dot^2;


fprintf('Derived Acceleration Equation, x_ddot(theta):\n');
simplified_x_ddot = simplify(x_ddot);
pretty(simplified_x_ddot);
fprintf('\n');
