clear; clc; close all;
% Script to calculate RMS and Peak Torque/Power for all speeds for a given gear ratio
s = settings;
s.matlab.appearance.figure.GraphicsTheme.TemporaryValue= 'light'; %set figure background to light

% Add damper model to path
addpath('D:\AME441_Code\damper_characterization\ohlins_model')
set(groot, 'DefaultAxesFontName', 'Times New Roman')
set(groot, 'DefaultTextFontName', 'Times New Roman')


%% Define damper setting combinations
% [comp_low, comp_high, reb_low, reb_high]
settings = [
    0 4 0 4
    0 3 0 3
    0 2 0 2
    0 1 0 1
];

%% Piston velocity sweep
piston_vel = linspace(-5,5,200); % [in/s]


%% Plot
figure; hold on; grid on;
colors = lines(size(settings,1));
legend_entries = cell(size(settings,1),1);

for k = 1:size(settings,1)
    comp_low  = settings(k,1);
    comp_high = settings(k,2);
    reb_low   = settings(k,3);
    reb_high  = settings(k,4);

    % Preallocate
    damping_force = zeros(size(piston_vel));

    % Evaluate damper model for each velocity (scalar input)
    for j = 1:length(piston_vel)
        damping_force(j) = ohlins_damper_model(comp_low, comp_high, ...
                                               reb_low, reb_high, ...
                                               piston_vel(j));
    end

    % Plot
    plot(piston_vel, damping_force, 'LineWidth', 1.5, 'Color', colors(k,:));

    % Legend entry
    legend_entries{k} = sprintf('C[%d,%d], R[%d,%d]', ...
                                comp_low, comp_high, reb_low, reb_high);
end

xlabel('Piston Velocity [in/s]');
ylabel('Damping Force [lbf]');
legend(legend_entries, 'Location','best');

