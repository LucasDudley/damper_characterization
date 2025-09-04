function model_params()
    % initial conditions
    assignin('base','theta0',0);
    assignin('base','theta0_dot',0);
    
    % inertial parameters
    M_disk = 1; %[kg]
    disk_diameter = 3 / 39.37; %[m]
    I_disk = (1/2) * M_disk * (disk_diameter/2)^2; %[kg·m^2]
    M_cart = 0.5; %[kg]

    assignin('base','M_disk',M_disk);
    assignin('base','disk_diameter',disk_diameter);
    assignin('base','I_disk',I_disk);
    assignin('base','M_cart',M_cart);
    
    % model params
    c_linear = 5000; %[N·s/m]
    R_crank = 0.75 / 39.37; %[m] 
    
    assignin('base','c_linear',c_linear);
    assignin('base','R_crank',R_crank);
    
    % torque calc inputs
    max_linear_speed = 5 / 39.37; %[m/s]
    theta_dot_const = max_linear_speed / R_crank;
    disp(theta_dot_const * (60/(2*pi))) % RPM
    
    assignin('base','max_linear_speed',max_linear_speed);
    assignin('base','theta_dot_const',theta_dot_const);
    
    % get damper info
    addpath('D:\AME441_Code\damper_characterization\ohlins_model')
    vel_range = linspace(-max_linear_speed, max_linear_speed, 50);
    damping_force = zeros(size(vel_range));
    for idx = 1:length(vel_range)
        damping_force(idx) = ohlins_damper_model(0,4,0,4, vel_range(idx)*39.27 )*4.44 ;
    end
    
    assignin('base','vel_range',vel_range);
    assignin('base','damping_force',damping_force);
end
