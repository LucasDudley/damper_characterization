clear, clc, close all
s = settings;
s.matlab.appearance.figure.GraphicsTheme.TemporaryValue= 'light'; %set figure background to light


% Inputs
folder = "D:\AME441_Code\damper_characterization\Test_Data\Phase1_temp_sensitivity";
file   = "t1_1_1_18_18_s6_n10_100psi";
filename = fullfile(folder, file);

%read data
all_data = readtable(filename);

%% process data
data = struct();

%normalize displacement
disp = all_data.Displacement_mm_/ 25.4; % convert to in

%calc Fs
data.time = second(all_data.Timestamp); % get time
Fs = 1 / abs(mean(diff(data.time(~isnan(data.time)))));

%filter disp
fc = 10; % disp cutoff frequency
[b,a] = butter(2, fc/(Fs/2));
data.raw_disp = disp - min(disp);
data.disp = filtfilt(b, a, data.raw_disp); %normalize and filter

% calcualte velocity
dt = seconds(all_data.Timestamp - all_data.Timestamp(1));
data.velocity = gradient(data.disp) ./ gradient(dt);

% calc accel
data.accel = gradient(data.velocity, dt);

% extract force
data.force = all_data.Force_N_; % flip sign and change to lbf

% filter temperature
fc = 1; % temp cutoff frequency
[b,a] = butter(2, fc/(Fs/2));
temp = filtfilt(b, a, all_data.Temperature_C_);
data.temp = temp;


%% plot

%get plot data
V = data.velocity;
F = data.force;
T = data.temp;
D = data.disp - (1.46/2);

% Remove NaNs
valid = ~(isnan(V) | isnan(F) | isnan(T)) | isnan(D);

%F-V
figure();
hold on;
scatter(V(valid), F(valid), 10, T(valid), 'filled'); % color by temperature

xlabel('\bfVelocity [in/s]', 'FontName', 'Times New Roman', 'FontSize', 14);
ylabel('\bfForce [N]', 'FontName', 'Times New Roman', 'FontSize', 14);
cb = colorbar;
ylabel(cb, '\bfTemperature [°C]', 'FontName', 'Times New Roman', 'FontSize', 14);
colormap turbo
box off;
grid off;

% Add light dashed lines at x=0 and y=0
yl = ylim;
xl = xlim;
plot([0 0], yl, 'k--', 'LineWidth', 1, 'Color', [0 0 0 0.3], 'HandleVisibility','off'); % x=0
plot(xl, [0 0], 'k--', 'LineWidth', 1, 'Color', [0 0 0 0.3], 'HandleVisibility','off'); % y=0

% F-D
figure();
hold on;
scatter(D(valid), F(valid), 10, T(valid), 'filled'); % color by temperature

xlabel('\bfDisplacement [in/s]', 'FontName', 'Times New Roman', 'FontSize', 14);
ylabel('\bfForce [N]', 'FontName', 'Times New Roman', 'FontSize', 14);
cb = colorbar;
ylabel(cb, '\bfTemperature [°C]', 'FontName', 'Times New Roman', 'FontSize', 14);
colormap turbo
box off;
grid off;

% Add light dashed lines at x=0 and y=0
yl = ylim;
xl = xlim;
plot([0 0], yl, 'k--', 'LineWidth', 1, 'Color', [0 0 0 0.3], 'HandleVisibility','off'); % x=0
plot(xl, [0 0], 'k--', 'LineWidth', 1, 'Color', [0 0 0 0.3], 'HandleVisibility','off'); % y=0


%%
figure
plot(data.time, data.raw_disp);
hold on
plot(data.time, data.disp);