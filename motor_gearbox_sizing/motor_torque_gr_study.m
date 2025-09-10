% Create plots trading motor torque and rpm for specified speed

clear, clc, close all
s = settings;
s.matlab.appearance.figure.GraphicsTheme.TemporaryValue= 'light'; %set figure background to light


% add damper model to path
addpath('D:\AME441_Code\damper_characterization\ohlins_model')
set(groot, 'DefaultAxesFontName', 'Times New Roman')
set(groot, 'DefaultTextFontName', 'Times New Roman')

%% Determine Torque Requirements for Scotch-Yoke & Gearbox
inputs.max_linear_vel = 5; %[in\s]
inputs.stroke = 1.5; %[in]
inputs.theta = linspace(0, 4*pi, 500); %[rad]
inputs.mass = (2) / 32.17; %[slugs]

% kinematics (scotch yoke)
r_crank = inputs.stroke / 2; 
linear_disp = r_crank .* sin(inputs.theta); % [in] linear displacement from theta
theta_dot = inputs.max_linear_vel ./ r_crank; %[rad/s] determine the angular speed from max linear speed
linear_vel = r_crank .* theta_dot .* cos(inputs.theta); %[in/s] determine the linear speed from angular speed
linear_accel = r_crank * theta_dot^2 * sin(inputs.theta); %[in/s^2] linear angular accel

% extract maximum displacement and maximium damper velocity
[disp_max, i_disp] = max(linear_disp);
[vel_max, i_vel] = max(linear_vel);

% torque calcs
damping_force = zeros(size(inputs.theta));
for idx = 1:length(inputs.theta)
    temp_linear_vel = linear_vel(idx);
    damping_force(idx) = ohlins_damper_model(0,4,0,4, temp_linear_vel); %[lbf] invert speed due to sign converntion (extension here is positive)
end

%forces
inertial_force = linear_accel * inputs.mass;
gravity_force = inputs.mass * 32.17 * ones(size(inputs.theta));
net_force = damping_force + gravity_force + inertial_force;

Tp_crank = r_crank.* cos(inputs.theta) .* net_force; % [lbf*in] crank toque required

% calcualte the peak and RMS torque required
[Tp_crank_max, i_Tp_crank] = max(abs(Tp_crank));
Tp_crank_rms = sqrt(mean(Tp_crank.^2));

%%
% plot kinematics
figure
yyaxis left
plot(inputs.theta, linear_disp, 'LineWidth', 1.5)
ylabel('Linear Disp. [in]')
hold on
plot(inputs.theta(i_disp), disp_max, 'ko', 'MarkerFaceColor','k')
text(inputs.theta(i_disp), disp_max, ...
    sprintf('  Max = %.2f in', disp_max), 'VerticalAlignment','bottom')

yyaxis right
plot(inputs.theta, linear_vel, 'LineWidth', 1.5)
ylabel('Linear Vel. [in/s]')
plot(inputs.theta(i_vel), vel_max, 'ko', 'MarkerFaceColor','k')
text(inputs.theta(i_vel), vel_max, ...
    sprintf('  Max = %.2f in/s', vel_max), 'VerticalAlignment','bottom')

xlabel('\theta [rad]')
grid on
box off

% plot torque at crank
figure
plot(inputs.theta, Tp_crank, 'LineWidth', 1.5)
xlabel('\theta [rad]')
ylabel('Torque [lbf·in]')
grid on
hold on
plot(inputs.theta(i_Tp_crank), Tp_crank(i_Tp_crank), 'ko', 'MarkerFaceColor','k')
text(inputs.theta(i_Tp_crank), Tp_crank(i_Tp_crank), ...
    sprintf('  Max = %.1f lbf·in', Tp_crank(i_Tp_crank)), 'VerticalAlignment','bottom')
box off

%% Gearbox study
% Define gearbox ratios (motor_speed : crank_speed)
gear_ratios = linspace(1, 15, 100); % ratios

% Preallocate
motor_speed_rpm = zeros(size(gear_ratios));
motor_torque_max = zeros(size(gear_ratios));
motor_torque_rms = zeros(size(gear_ratios));

for idx = 1:length(gear_ratios)
    GR = gear_ratios(idx);

    % Motor angular speed [rad/s], then convert to RPM
    motor_speed_rpm(idx) = (theta_dot * GR) * 60 / (2*pi);

    % Motor torque [lbf·in]
    motor_torque_rms(idx) = Tp_crank_rms / GR;
    motor_torque_max(idx) = Tp_crank_max / GR;
end

% Plot torque vs speed relationship
figure
yyaxis left
h1 = plot(gear_ratios, motor_speed_rpm, 'LineWidth', 1.5);
ylabel('Motor Speed [RPM]')
set(gca, 'YScale', 'log')   % log scale for motor speed

yyaxis right
h2 = plot(gear_ratios, motor_torque_max * 16, 'LineWidth', 1.5); hold on
h3 = plot(gear_ratios, motor_torque_rms * 16, 'LineWidth', 1.5);
ylabel('Motor Torque [oz·in]')
set(gca, 'YScale', 'log')   % log scale for torque

xlabel('Gear Ratio')
title(sprintf('Motor Requirements (Stroke = %.3f in, Max Linear Speed = %d in/s)', ...
    inputs.stroke, inputs.max_linear_vel));
grid on
box off

% Legend only for main curves
legend([h1 h2 h3], {'Motor Speed','Peak Torque','RMS Torque'}, 'Location','best')
xlim([1 15])

% Pick a gear ratio value directly
g_val = 10;

yyaxis right
y_peak = interp1(gear_ratios, motor_torque_max*16, g_val);
y_rms  = interp1(gear_ratios, motor_torque_rms*16, g_val);
xr = xlim;

% Horizontal lines to right axis (black, no legend entry)
plot([g_val xr(2)], [y_peak y_peak], '--k', 'LineWidth', 1, 'HandleVisibility','off');
plot([g_val xr(2)], [y_rms y_rms], '--k', 'LineWidth', 1, 'HandleVisibility','off');

% Labels
text(xr(2), y_peak, sprintf(' Peak Torque = %.1f', y_peak), ...
    'Color','k','VerticalAlignment','bottom','HorizontalAlignment','right');
text(xr(2), y_rms, sprintf(' RMS Torque = %.1f', y_rms), ...
    'Color','k','VerticalAlignment','top','HorizontalAlignment','right');

yyaxis left
y_rpm = interp1(gear_ratios, motor_speed_rpm, g_val);
xl = xlim;

% Horizontal line to left axis 
plot([g_val xl(1)], [y_rpm y_rpm], '--k', 'LineWidth', 1, 'HandleVisibility','off');

% Label
text(xl(1), y_rpm, sprintf(' Motor Speed = %.0f RPM', y_rpm), ...
    'Color','k','VerticalAlignment','bottom','HorizontalAlignment','left');
