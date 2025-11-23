clear, clc, close all
% script to read, parse, and built .mat file with selected data
% FILENAME: Run#_HSC_LSR_LSC_LSR.csv

%% inputs
folder_path = "D:\AME441_Code\damper_characterization\Test_Data\Phase3_all_sweep\Raw Data\Valving Sweeps";
out_path = "G:\.shortcut-targets-by-id\1vCayBu0JWPEaCjSa5KhpGMqdHFvsMCFY\Senior_Design\Data Collection\matfiles";
out_name = "valving_test_data.mat";

fc = 15;  % cutoff freq [Hz]
fc_temp = 1;

%% data handling

% Get list of all CSV files
files = dir(fullfile(folder_path, '*.csv'));
test_data = struct();

for i = 1:length(files)
    fname = files(i).name; % grab current filename
    
    tokens = regexp(fname, '^Run(\d+)_([0-9.]+)_([0-9.]+)_([0-9.]+)_([0-9.]+)', 'tokens');
    if isempty(tokens), continue; end
    tokens = tokens{1};
    
    %extract run info
    runNum = str2double(tokens{1}); 
    runField = sprintf("r%d", runNum);

    test_data.(runField).valving.hsc = str2double(tokens{2});
    test_data.(runField).valving.hsr = str2double(tokens{3});
    test_data.(runField).valving.lsc = str2double(tokens{4});
    test_data.(runField).valving.lsr = str2double(tokens{5});

    % read current data
    curr_data = readtable(fullfile(folder_path, fname), ...
                      "FileType","text", ...
                      "VariableNamingRule","preserve");

    %timestamp handling
    t = curr_data.("Timestamp");                            % datetime array
    t0 = t - t(1);                                       % relative time
    dt = seconds(t0);                                    % seconds vector
    Fs = 1 / mean(diff(dt));                             % sample rate [Hz]
    
    
    % displacment normalization
    disp_in = curr_data.("Displacement (mm)") / 25.4;                  % convert mm → inches
    disp_norm = disp_in - (min(disp_in) + max(disp_in))/2;    % normalize about midpoint
    [b,a] = butter(2, fc/(Fs/2));
    filt_disp = filtfilt(b, a, disp_norm);
    
    % Velocity & Acceleration calcs
    vel = gradient(filt_disp, dt);
    acc = gradient(vel, dt);
    
    % Force
    force = curr_data.("Force (N)");            
    
    % Temperature filtering
    [bT,aT] = butter(2, fc_temp/(Fs/2));
    temp_f = filtfilt(bT, aT, curr_data.("Temperature (C)"));
    
    % Split by RPM groups
    unique_rpms = unique(curr_data.RPM);
    
    for r = 1:length(unique_rpms)
        rpm_raw = unique_rpms(r);
    
        mask = curr_data.RPM == rpm_raw;
    
        % Convert to shaft RPM and Hz
        curr_RPM = rpm_raw / 10;
        curr_HZ  = curr_RPM / 60;
    
        % Field name
        hzFieldRaw = sprintf("f%.3f", curr_HZ);
        hzField = matlab.lang.makeValidName(hzFieldRaw);
    
        % Store directly under runField
        test_data.(runField).(hzField).RPM      = curr_RPM;
        test_data.(runField).(hzField).time     = dt(mask);
        test_data.(runField).(hzField).disp     = filt_disp(mask);
        test_data.(runField).(hzField).velocity = vel(mask);
        test_data.(runField).(hzField).accel    = acc(mask);
        test_data.(runField).(hzField).force    = force(mask);
        test_data.(runField).(hzField).temp     = temp_f(mask);
    end
end

%% store data in matfile
save(fullfile(out_path, out_name), "test_data");
