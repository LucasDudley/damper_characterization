clear, clc, close all
% run the dynamic model to plot torques

%define the input params
model_params

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