clear, clc, close all
% script to compute the piston/crank kinematics

% Parameters (inches)
R  = 0.75;  %[in] 
theta = linspace(0, 2*pi, 400); % crank angle [rad]
Lc_vals = [2, 4, 8];            % different connecting rod lengths

%Preallocate storage
x_crank_all = zeros(length(Lc_vals), length(theta));
x_dot_crank_all = x_crank_all;
x_ddot_crank_all = x_crank_all;

% Pure sinusoid reference
x_sin = R*(1 - cos(theta));
dtheta = theta(2) - theta(1);
x_dot_sin  = gradient(x_sin, dtheta);
x_ddot_sin = gradient(x_dot_sin, dtheta);

% Loop through Lc values
for i = 1:length(Lc_vals)
    Lc = Lc_vals(i);

    % displacement
    x_crank = crank_disp(theta, Lc, R);

    % derivatives
    x_dot_crank  = gradient(x_crank, dtheta); 
    x_ddot_crank = gradient(x_dot_crank, dtheta);

    % store
    x_crank_all(i,:)   = x_crank;
    x_dot_crank_all(i,:)  = x_dot_crank;
    x_ddot_crank_all(i,:) = x_ddot_crank;
end

%% Plot position, velocity, acceleration as subplots
figure

subplot(1,3,1)
plot(theta, x_sin, 'k', 'LineWidth', 1.5); hold on
for i = 1:length(Lc_vals)
    plot(theta, x_crank_all(i,:), 'LineWidth', 1.5)
end
legend(['Pure sinusoid', "Lc = 2 in", "Lc = 4 in", "Lc = 8 in"])
ylabel('Displacement [in]')
xlabel('\theta [rad]')
box off

subplot(1,3,2)
plot(theta, x_dot_sin, 'k', 'LineWidth', 1.5); hold on
for i = 1:length(Lc_vals)
    plot(theta, x_dot_crank_all(i,:), 'LineWidth', 1.5)
end
ylabel('Velocity [in/rad]')
xlabel('\theta [rad]')
box off

subplot(1,3,3)
plot(theta, x_ddot_sin, 'k', 'LineWidth', 1.5); hold on
for i = 1:length(Lc_vals)
    plot(theta, x_ddot_crank_all(i,:), 'LineWidth', 1.5)
end
xlabel('\theta [rad]')
ylabel('Acceleration [in/rad^2]')
box off

%% Functions
function x_disp = crank_disp(theta, Lc, R)
    % compute piston displacement given crank angle theta
    n = Lc / R;
    x_disp = R.*(1 - cos(theta) + n - sqrt(n.^2 - sin(theta).^2));
end
