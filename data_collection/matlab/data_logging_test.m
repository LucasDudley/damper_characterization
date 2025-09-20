% NI-DAQ Data Acquisition, Storage, and Plotting Script (Modern Interface)
%
% This script demonstrates the current, recommended workflow for acquiring
% data from a National Instruments DAQ device using the Data Acquisition Toolbox.
clear, clc, close all

% --- User-defined Parameters ---
deviceID    = 'Dev1';     % Replace with your device ID (e.g., 'Dev1', 'cDAQ1Mod1')
channelID   = 'ai0';      % Replace with your analog input channel (e.g., 'ai0', 'ai1')
measurementType = 'Voltage'; % Type of measurement

duration    = 5;          % Acquisition duration in seconds
sampleRate  = 1000;       % Sampling rate in Hz (samples per second)
outputFile  = 'daq_data.mat'; % File name to save the data

% Create a DAQ object for NI devices
d = daq('ni');

% Set the sampling rate
d.Rate = sampleRate;

% Add an analog input channel
try
    ch = addinput(d, deviceID, channelID, measurementType);
    % Optional: Configure channel properties, like terminal configuration
    % ch.TerminalConfiguration = 'Differential'; % or 'SingleEnded', 'RSE', 'NRSE'
catch ME
    fprintf('Error: Could not add channel. Please check your deviceID and channelID.\n');
    fprintf('MATLAB Error Message: %s\n', ME.message);
    return; % Exit the script if the channel cannot be added
end

% Read data for the specified duration. This is a blocking call.
[data, time] = read(d, seconds(duration));


figure; % Create a new figure window
plot(time, data);
grid on; % Add a grid to the plot
title(sprintf('Data from %s - Channel %s', deviceID, channelID));
xlabel('Time (s)');
ylabel(sprintf('%s (%s)', measurementType, ch.Units)); % Use units from channel properties
legend('Acquired Signal');

% The DAQ object is automatically released when cleared from the workspace.
clear d;
fprintf('DAQ object cleared. Script finished.\n');

