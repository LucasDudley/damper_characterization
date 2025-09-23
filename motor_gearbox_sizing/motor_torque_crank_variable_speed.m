% Script to calculate RMS and Peak Torque/Power for all speeds for a given gear ratio

clear, clc, close all
s = settings;
s.matlab.appearance.figure.GraphicsTheme.TemporaryValue= 'light'; %set figure background to light

% Add damper model to path
addpath(fullfile(fileparts(pwd), 'ohlins_model'));
set(groot, 'DefaultAxesFontName', 'Times New Roman')
set(groot, 'DefaultTextFontName', 'Times New Roman')

%% Inputs
inputs.max_linear_vel_range = linspace(0.5, 6, 10); %[in/s]
inputs.stroke = 1.5; %[in]
inputs.gear_ratio = 1; %[motor/crank]
inputs.mass = (2) / 32.17; %[slugs]
inputs.Lc = 6; %[in]

% Auxiliary inputs
inputs.r_crank = inputs.stroke / 2;
inputs.theta = linspace(0, 4*pi, 500); %[rad]

%% Preallocate results
crank_torque_rms   = zeros(size(inputs.max_linear_vel_range));
crank_torque_peak  = zeros(size(inputs.max_linear_vel_range));
motor_torque_rms   = zeros(size(inputs.max_linear_vel_range));
motor_torque_peak  = zeros(size(inputs.max_linear_vel_range));
motor_rpm          = zeros(size(inputs.max_linear_vel_range));
motor_power_rms    = zeros(size(inputs.max_linear_vel_range));
motor_power_peak   = zeros(size(inputs.max_linear_vel_range));
rod_force_peak     = zeros(size(inputs.max_linear_vel_range));

%% Compute torque/power stats
torque_stats = arrayfun(@(v) compute_torque_stats(v, inputs), ...
                        inputs.max_linear_vel_range, 'UniformOutput', false);

% Unpack results
for k = 1:numel(torque_stats)
    crank_torque_rms(k)   = torque_stats{k}.crank_rms;
    crank_torque_peak(k)  = torque_stats{k}.crank_peak;
    motor_torque_rms(k)   = torque_stats{k}.motor_rms;
    motor_torque_peak(k)  = torque_stats{k}.motor_peak;
    motor_rpm(k)          = torque_stats{k}.rpm;
    motor_power_rms(k)    = torque_stats{k}.power_rms;
    motor_power_peak(k)   = torque_stats{k}.power_peak;
    rod_force_peak(k)     = torque_stats{k}.rod_force_peak;
end

%% Helper function
function stats = compute_torque_stats(max_linear_vel, inputs)

    % Kinematics (scotch-yoke)
    theta_dot = required_theta_dot(max_linear_vel, inputs.Lc, inputs.r_crank); %[rad/s] determine the angular speed from max linear speed
    [~, linear_vel, linear_accel] = slider_crank_kinematic_fcn(inputs.theta, theta_dot, 0, inputs.Lc, inputs.r_crank); % forward kinematics

    % Damping force calculation
    damping_force = zeros(size(inputs.theta));
    for j = 1:length(inputs.theta)
        damping_force(j) = ohlins_damper_model(0, 4, 0, 4, linear_vel(j));
    end

    % forces
    inertial_force = linear_accel * inputs.mass;
    gravity_force = inputs.mass * 32.17 * ones(size(inputs.theta));
    net_force = damping_force + gravity_force + inertial_force;

    % Crank torque
    [crank_torque, ~, F_rod] = slider_crank_torque(inputs.theta, net_force, inputs.r_crank, inputs.Lc);

    % Stats
    stats.crank_peak = max(abs(crank_torque));
    stats.crank_rms  = sqrt(mean(crank_torque.^2));
    stats.rod_force_peak  = max(abs(F_rod));

    % Motor conversion
    motor_speed      = theta_dot * inputs.gear_ratio; %[rad/s]
    stats.rpm        = motor_speed * 60 / (2*pi);
    stats.motor_peak = stats.crank_peak / inputs.gear_ratio; %[lbf·in]
    stats.motor_rms  = stats.crank_rms / inputs.gear_ratio;  %[lbf·in]

    % Motor power
    stats.power_rms  = stats.motor_rms .* motor_speed * 0.113; %[W]
    stats.power_peak = stats.motor_peak .* motor_speed * 0.113; %[W]
end

%%
figure()
yyaxis left
plot(inputs.max_linear_vel_range, motor_torque_rms * 16,'-o','LineWidth',1.5)
hold on
plot(inputs.max_linear_vel_range, motor_torque_peak * 16,'--o','LineWidth',1.5)
ylabel('Motor Torque [oz·in]')
xlabel('Max Linear Velocity [in/s]')
grid on
legend('RMS Torque','Peak Torque','Location','northwest')

yyaxis right
plot(inputs.max_linear_vel_range, motor_power_rms,'-s','LineWidth',1.5)
hold on
plot(inputs.max_linear_vel_range, motor_power_peak,'--s','LineWidth',1.5)
ylabel('Motor Power [W]')
legend('RMS Torque','Peak Torque','RMS Power','Peak Power','Location','northwest')

box off
xlim([inputs.max_linear_vel_range(1), inputs.max_linear_vel_range(end)])

% Add top x-axis for motor speed [RPM]
ax1 = gca; % current axes
ax1_pos = ax1.Position; % position of main axes

% create new axes on top
ax2 = axes('Position', ax1_pos, ...
           'Color','none', ...
           'XAxisLocation','top', ...
           'YAxisLocation','right', ...
           'XColor','k', 'YColor','none');

% map linear velocity to motor RPM
set(ax2,'XLim',ax1.XLim, 'XTick', ax1.XTick, ...
        'XTickLabel', round(interp1(inputs.max_linear_vel_range, motor_rpm, ax1.XTick)));
xlabel(ax2,'Motor Speed [RPM]')

% Add gear ratio label
gear_ratio_str = sprintf('Gear Ratio = %g [motor/crank]', inputs.gear_ratio);
dim = [0.65 0.15 0.2 0.05]; % [x y w h] in normalized figure units
annotation('textbox', dim, 'String', gear_ratio_str, ...
           'EdgeColor','none', 'HorizontalAlignment','right', ...
           'FontWeight','bold', 'FontSize', 12);


% Export PDF
filename = fullfile('G:\.shortcut-targets-by-id\1vCayBu0JWPEaCjSa5KhpGMqdHFvsMCFY\Senior_Design\Work Updates\Motor_Torque_calcs\torque_and_power', ...
    sprintf('stroke%.2f_max%.2f_gr%d', inputs.stroke, max(inputs.max_linear_vel_range), inputs.gear_ratio));
% save as png and pdf
exportgraphics(gcf, [filename '.pdf'], 'ContentType','vector', 'BackgroundColor','none');

%%
figure
plot(inputs.max_linear_vel_range, rod_force_peak,'-o','LineWidth',1.5)