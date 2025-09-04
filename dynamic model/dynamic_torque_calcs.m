clear, clc, close all
% run the dynamic model to plot torques

%define the input params
model_params

s = settings;
s.matlab.appearance.figure.GraphicsTheme.TemporaryValue= 'light'; %set figure background to light
set(groot, 'DefaultAxesFontName', 'Times New Roman')
set(groot, 'DefaultTextFontName', 'Times New Roman')

out = sim("torque_calcs.slx");
%%

figure
yyaxis left
plot( out.kinematics.Data(:,2)*39.37, out.forces.Data(:,1)/4.44)
ylabel('Dynamic Accel Force [lbf]')

hold on
yyaxis right
plot( out.kinematics.Data(:,2)*39.37, out.forces.Data(:,2)/4.44)
ylabel('Damping Force [lbf]')

box off
xlabel('Linear Speed [rad/s]')
legend('Dynamic Acceleration Force', 'Damping Force')

%%
figure
plot(out.theta.Data(:,2)*180/pi, out.KPI.Data(:,1), 'LineWidth', 1.5) % Power

% Extract signals
power  = out.KPI.Data(:,1);
torque = out.KPI.Data(:,2);

% Peak values
peakPower  = max(power);
peakTorque = max(torque);

% RMS values
rmsPower  = rms(power);
rmsTorque = rms(torque);

% Add dashed RMS lines
yline(rmsPower,  '--', 'LineWidth',2);

% Print outputs
fprintf('Peak Power:  %.2fW\n', peakPower);
fprintf('RMS  Power:  %.2fW\n', rmsPower);
fprintf('Peak Torque: %.2f Nm\n', peakTorque);
fprintf('RMS  Torque: %.2f Nm\n', rmsTorque);

xlabel('\theta [deg]')
ylabel('Power [W]')
legend('Power Trace','RMS Power','Location','best')
grid on
xlim([0 720])
box off