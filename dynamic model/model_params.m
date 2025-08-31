% Model Parameters
clear, clc, close all

% inital conditions
theta0 = 0;
theta0_dot = 0;

% inertial parameters
M_disk = 1; %[kg]
disk_diameter = 3 / 39.37; %[m]
I_disk = (1/2)* M_disk * (disk_diameter/2)^2; %[kg.m^2]
M_cart = 0.5; %[kg]

% model params
c_linear = 5000; %[N.s/m] maximum expected damping force
R_crank = 1 / 39.37; %[m] assuming 2" total displacement

%torque calc inputs
max_linear_speed = 5 / 39.37; %[m/s]
theta_dot_const = max_linear_speed / R_crank;
disp(theta_dot_const* (60/(2*pi))) % RPM
