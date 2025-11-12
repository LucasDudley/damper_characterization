clear, clc, close all
s = settings;
s.matlab.appearance.figure.GraphicsTheme.TemporaryValue= 'light'; % set figure background to light

% load data
all_data = load("G:\.shortcut-targets-by-id\1vCayBu0JWPEaCjSa5KhpGMqdHFvsMCFY\Senior_Design\Damper_Info\2025_endurance_data.mat");

%% Motion ratios: shock travel / wheel travel
f_mr = 1.03;
r_mr = 1.16;

% time window
t_start = 1480;
t_end   = 2950;

% logical mask for the time range
mask = all_data.Shock_Pots_FL_Lin_Pot_Value.Time >= t_start & ...
       all_data.Shock_Pots_FL_Lin_Pot_Value.Time <= t_end;

% apply to each signal
data.time  = all_data.Shock_Pots_FL_Lin_Pot_Value.Time(mask);
data.FL_pos = all_data.Shock_Pots_FL_Lin_Pot_Value.Value(mask) / f_mr;
data.FR_pos = all_data.Shock_Pots_FR_Lin_Pot_Value.Value(mask) / f_mr;
data.RL_pos = all_data.Shock_Pots_RL_Lin_Pot_Value.Value(mask) / r_mr;
data.RR_pos = all_data.Shock_Pots_RR_Lin_Pot_Value.Value(mask) / r_mr;

%%
% sampling
dt = mean(diff(data.time));
Fs = 1/dt; 

% design zero-phase lowpass filter
cutoffHz = 20;
[b,a] = butter(4, cutoffHz/(Fs/2));  

fields = {'FL','FR','RL','RR'};
for i = 1:numel(fields)
    pos = data.([fields{i} '_pos']); % wheel travel
    
    % filter positions
    pos_f = filtfilt(b,a,pos);
    
    % differentiate filtered positions
    vel = diff(pos_f)./diff(data.time);
    
    data.([fields{i} '_pos_f'])  = pos_f;
    data.([fields{i} '_vel'])    = vel;
end

%% histogram of wheel velocities
figure
for i = 1:numel(fields)
    vel = data.([fields{i} '_vel']);
    
    subplot(2,2,i)
    
    binWidth = 0.5; % in/s
    h = histogram(vel,'BinWidth',binWidth,'Normalization','probability', ...
              'HandleVisibility','off');
    hold on
    
    % stats
    mu = mean(vel);
    sigma = std(vel);
    p1 = mean(abs(vel-mu) <= sigma) * 100;   % within ±1σ
    p2 = mean(abs(vel-mu) <= 3*sigma) * 100; % within ±2σ
    
    % vertical lines
    xline(mu,'k--','LineWidth',1.5, ...
        'DisplayName',sprintf('Mean = %.2f',mu));
    
    xline(mu+sigma,'r--','LineWidth',1.2, ...
        'DisplayName',sprintf('+1σ = %.2f (%.1f%%)',mu+sigma,p1));
    xline(mu-sigma,'r--','LineWidth',1.2,'HandleVisibility','off');
    
    xline(mu+3*sigma,'b--','LineWidth',1.2, ...
        'DisplayName',sprintf('+3σ = %.2f (%.1f%%)',mu+3*sigma,p2));
    xline(mu-3*sigma,'b--','LineWidth',1.2,'HandleVisibility','off');
    
    % format
    xlabel('Wheel Velocity [in/s]'); 
    ylabel('Percentage [%]')
    ylim([0 max(h.Values)*1.2]) % pad a bit
    yt = yticks; 
    yticklabels(yt*100); % convert to percent
    grid on
    title([fields{i}])
    legend('Location','NorthWest')
    xlim([-3*sigma*1.1, 3*sigma*1.1])
    box off
end
set(findall(gcf,'-property','FontName'),'FontName','Times New Roman')
set(findall(gcf,'-property','FontSize'),'FontSize',12)

%% Global 3-sigma envelope across all wheels
all_vel = [data.FL_vel(:); data.FR_vel(:); data.RL_vel(:); data.RR_vel(:)];  % force column vectors
global_mu = mean(all_vel);
global_sigma = std(all_vel);

envelope = [global_mu - 3*global_sigma, global_mu + 3*global_sigma];
p_covered = mean(all_vel >= envelope(1) & all_vel <= envelope(2)) * 100;

fprintf('3σ envelope: [%.3f , %.3f] in/s\n', envelope(1), envelope(2));
fprintf('Coverange within 3σ: %.2f%%\n', p_covered);

% plot enveloped

figure
enveloped_vel = all_vel(all_vel >= envelope(1) & all_vel <= envelope(2));

binWidth = 0.5; % in/s
h = histogram(enveloped_vel,'BinWidth',binWidth,'Normalization','probability'...
    ,'HandleVisibility','off');
hold on

% stats
mu_env = mean(enveloped_vel);
sigma_env = std(enveloped_vel);

% vertical lines
xline(mu_env,'k--','LineWidth',1.5, ...
    'DisplayName',sprintf('Mean = %.2f',mu_env));

xline(mu_env+sigma_env,'r--','LineWidth',1.2, ...
    'DisplayName',sprintf('+1σ = %.2f',mu_env+sigma_env));
xline(mu_env-sigma_env,'r--','LineWidth',1.2,'HandleVisibility','off');

xline(mu_env+3*sigma_env,'b--','LineWidth',1.2, ...
    'DisplayName',sprintf('+3σ = %.2f',mu_env+3*sigma_env));
xline(mu_env-3*sigma_env,'b--','LineWidth',1.2,'HandleVisibility','off');

% format
ylabel('\bfWheel Velocity \rm[\itin/s\rm]', 'Color', 'k');
xlabel('\bfPercentage \rm[\it%\rm]', 'Color', 'k');
ylim([0 max(h.Values)*1.2])
yt = yticks; 
yticklabels(yt*100)
grid off
legend('Location','NorthWest')
xlim([envelope(1), envelope(2)])
box off

set(findall(gcf,'-property','FontName'),'FontName','Times New Roman')
set(findall(gcf,'-property','FontSize'),'FontSize',12)