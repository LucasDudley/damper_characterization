clear, clc, close all

deviceName = 'Dev1'; 
counterChannel = 'ctr0'; 
frequency = 1000; % 1 kHz
dutyCycles = [0.25, 0.5, 0.75, 0.5, 0.25]; 
holdDuration = 2; % 2 seconds

try
    dq = daq('ni'); % create the data aq object
    ch = addoutput(dq, deviceName, counterChannel, 'PulseGeneration'); % add the counter output channel
    ch.Frequency = frequency; % set the frequency
    

    for i = 1:length(dutyCycles)
        currentDutyCycle = dutyCycles(i);
        
        ch.DutyCycle = currentDutyCycle; % set the duty cycle
        start(dq, 'continuous'); % start signal generation
        pause(holdDuration); %pause script to wait
        stop(dq); %stop the signal generation before changing duty cycle
    end
    
    disp('PWM signal sequence finished.');

catch e
    fprintf('An error occurred:\n%s\n', e.message);
end

