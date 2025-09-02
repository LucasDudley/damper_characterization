function damping_force = ohlins_damper_model(lsc_setting, hsc_setting, lsr_setting, hsr_setting, velocity)
%This Fuctions takes in the current LS and HS setting for comp and rebound,
%then checks the velocity direction, linearly interpolates to find the
%correspond force and outputs it (2023)

%NOTE:
%LS is measured in clicks from closed, fully CW (max damping) and HS in measured in
%turns from open, fully CCW (lowest damping)
% HS: 4=max, 0=min / LS: 0=max, 25=min

%INPUT CONVENTION:
%Input LS/HS settings as number from 0-4 or 0-25
%Velocity input in in/sec, force output in lbf

%              VALID INPUTS (LS - HS)
%       LS0 - HS(0:4)  OR LS(0:25) - HS(4)

%% INPUT CHECKS, ENSURE WE HAVE THAT DATA
%we only have data for HS and LS sweeps (HS/LS held at max damping) so we need to make sure that those
%are the only inputs 

% Check number of inputs
if nargin < 5
    error('damper_model requires 5 inputs: lsc_setting, hsc_setting, lsr_setting, hsr_setting, velocity');
end

%check valid ranges
if ~(0 <= hsc_setting && hsc_setting <= 4) || ~(0 <= lsc_setting && lsc_setting <= 25)
    error('Invalid compression settings. Value exceeds range');
elseif ~(0 <= hsr_setting && hsr_setting <= 4) || ~(0 <= lsr_setting && lsr_setting <= 25)
    error('Invalid rebound settings. Value exceeds range');
end

%check compression
if (lsc_setting == 0)
    if ~(hsc_setting >= 0 && hsc_setting <= 4)
        error('Invalid combination of compression settings. When lsc_setting is 0, hsc_setting must be between 0 and 4.');
    end
elseif (lsc_setting >= 0 && lsc_setting <= 25)
    if hsc_setting ~= 4
        error('Invalid combination of compression settings. When lsc_setting is between 0 and 25, hsc_setting must be 4.');
    end
end

%check rebound
if (lsr_setting == 0)
    if ~(hsr_setting >= 0 && hsr_setting <= 4)
        error('Invalid combination of rebound settings. When lsr_setting is 0, hsr_setting must be between 0 and 4.');
    end
elseif (lsr_setting >= 0 && lsr_setting <= 25)
    if hsr_setting ~= 4
        error('Invalid combination of rebound settings. When lsr_setting is between 0 and 25, hsr_setting must be 4.');
    end
end

%if velocity is too high, assume damper is at maximum known velocity to
%prevent NaN response
if abs(velocity) > 9.65
    velocity = 9.65*velocity/abs(velocity); %set to max
end

%% LOAD DATA
%all of the data provided by OHLINS was extracted from the plots and stored
%in cell arrays (see dampinigvalues.m where they are generated)
persistent cdamp rdamp

    if isempty(cdamp) || isempty(rdamp)
        load('cdamp.mat', 'cdamp');
        load('rdamp.mat', 'rdamp');
    end

%% Determine if compression or rebound

if velocity > 0 %assume postive is compression
    type = 1; % compression
    damping_force = NaN;
elseif velocity < 0 
    type = 2; %rebound
    damping_force = NaN;
elseif velocity == 0
    damping_force = 0;
end

%% GET DAMPING FORCE for COMPRESSION
% If the value is between two known curves, we interpolate at a given
% velocity, then interpolate between the two (kinda brutal I know but
% go find a CS major if you dont like it). 

ls0_hsSpace = [0 1 2 3 4];
hs4_lsSpace = [0 2 4 6 10 15 25];

%for compression 
if type == 1 

    if lsc_setting == 0 %we know we are in the HS sweep curve in this case

        i = 1;

        while isnan(damping_force)
                    
            if hsc_setting >= ls0_hsSpace(i) && hsc_setting <= ls0_hsSpace(i+1)
        
                damping_force_low = interp1(cdamp{i}(:,1),cdamp{i}(:,2),velocity, 'linear'); %get values from both curves here and interpolate between them
                damping_force_high = interp1(cdamp{i+1}(:,1),cdamp{i+1}(:,2),velocity, 'linear');
                damping_force = interp1([ls0_hsSpace(i) ls0_hsSpace(i+1)], [damping_force_low damping_force_high], hsc_setting);

            else

                i = i + 1;

            end
            
        end

    elseif hsc_setting == 4 %we know we are in the LS sweep

        i = 5;

        while isnan(damping_force)
            
            if lsc_setting >= hs4_lsSpace(i-4) && lsc_setting <= hs4_lsSpace(i-3)
        
                damping_force_low = interp1(cdamp{i}(:,1),cdamp{i}(:,2),velocity, 'linear');
                damping_force_high = interp1(cdamp{i+1}(:,1),cdamp{i+1}(:,2),velocity, 'linear');
                damping_force = interp1([hs4_lsSpace(i-4) hs4_lsSpace(i-3)], [damping_force_low damping_force_high], lsc_setting);

            else

                i = i + 1;

            end
            
        end

    end

end

%NOTE: Current convention is that damping force for compression is positive

%% GET DAMPING FORCE FOR REBOUND

%for rebound
if type == 2
    %flip velocity sign to make it positive
    velocity = -velocity;
    if lsr_setting == 0 %we know we are in the HS sweep curve

        i = 1;

        while isnan(damping_force)
                    
            if hsr_setting >= ls0_hsSpace(i) && hsr_setting <= ls0_hsSpace(i+1)
        
                damping_force_low = interp1(rdamp{i}(:,1),rdamp{i}(:,2),velocity, 'linear');
                damping_force_high = interp1(rdamp{i+1}(:,1),rdamp{i+1}(:,2),velocity, 'linear');
                damping_force = interp1([ls0_hsSpace(i) ls0_hsSpace(i+1)], [damping_force_low damping_force_high], hsr_setting);

            else

                i = i + 1;

            end
            
        end

    elseif hsr_setting == 4 %we know we are in the LS sweep

        i = 5;

        while isnan(damping_force)
                    
            if lsr_setting >= hs4_lsSpace(i-4) && lsr_setting <= hs4_lsSpace(i-3)
        
                damping_force_low = interp1(rdamp{i}(:,1),rdamp{i}(:,2),velocity, 'linear');
                damping_force_high = interp1(rdamp{i+1}(:,1),rdamp{i+1}(:,2),velocity, 'linear');
                damping_force = interp1([hs4_lsSpace(i-4) hs4_lsSpace(i-3)], [damping_force_low damping_force_high], lsr_setting);

            else

                i = i + 1;

            end
            
        end

    end

end

end