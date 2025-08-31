clear, clc, close all
% script to compute the piston/crank kinematics

%% Compare sinusoid to piston crank

Lc = 0.1; %[m]
R = 0.05; %[m]
theta = linspace(0, 2*pi, 50);

%compute displacements
x_crank = crank_disp(theta, Lc, R);
x_sin = R*(1 - cos(theta));

figure
plot(theta, x_crank)
hold on
plot(theta, x_sin)
legend('Crank Kinematics', 'Pure sinusoid')
xlabel('Theta [rad]')
ylabel('X-disp [m]')

%get velocity

x_dot_crank = diff(x_crank);
x_dot_sin = diff(x_sin);
figure
plot(theta(1:end-1), x_dot_crank)
hold on
plot(theta(1:end-1), x_dot_sin)
legend('Crank Kinematics', 'Pure sinusoid')
xlabel('Theta [rad]')
ylabel('X-vel [m/s]')


%% Functions

function x_disp = crank_disp(theta, Lc, R)
% compute the x_displacement for a given theta parameter
    n = Lc / R;
    x_disp = R.*(1 - cos(theta) + n  - sqrt(n.^2 - sin(theta).^2));

end