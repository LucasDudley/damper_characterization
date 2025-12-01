clear, clc, close all
s = settings;
s.matlab.appearance.figure.GraphicsTheme.TemporaryValue = 'light';

load("G:\.shortcut-targets-by-id\1vCayBu0JWPEaCjSa5KhpGMqdHFvsMCFY\Senior_Design\Data Collection\matfiles\valving_test_data.mat", 'test_data');

%% Define runs to analyze
runs = [3, 4];
lissajous_freq = 'f1_053';
num_temp_bins = 10;
v_knee_fixed = 1;
poly_order = 2;
opp_vel_perc = 0.15;

%% plot
% Collect all data from specified runs and get valving settings
all_temp = [];
all_velocity = [];
all_force = [];
valving_settings = struct();

for r = 1:length(runs)
    runNum = runs(r);
    runField = sprintf("r%d", runNum);
    
    if ~isfield(test_data, runField)
        warning("Run %d not found in test_data.", runNum);
        continue;
    end
    
    if ~isfield(test_data.(runField), lissajous_freq)
        warning("Frequency %s not found in run %d", lissajous_freq, runNum);
        continue;
    end
    
    run_data = test_data.(runField).(lissajous_freq);
    
    % Get valving settings from the parent structure
    if isfield(test_data.(runField), 'valving')
        valving_settings.(runField) = test_data.(runField).valving;
    end
    
    % Concatenate data
    all_temp = [all_temp; run_data.temp(:)];
    all_velocity = [all_velocity; run_data.velocity(:)];
    all_force = [all_force; run_data.force(:)];
end

% Create temperature bins
temp_edges = linspace(min(all_temp), max(all_temp), num_temp_bins + 1);
temp_centers = (temp_edges(1:end-1) + temp_edges(2:end)) / 2;

% Initialize arrays for results
C_LS_comp = nan(num_temp_bins, 1);
C_HS_comp = nan(num_temp_bins, 1);
C_LS_reb = nan(num_temp_bins, 1);
C_HS_reb = nan(num_temp_bins, 1);

unc_LS_comp = nan(num_temp_bins, 1);
unc_HS_comp = nan(num_temp_bins, 1);
unc_LS_reb = nan(num_temp_bins, 1);
unc_HS_reb = nan(num_temp_bins, 1);

temp_uncertainty = nan(num_temp_bins, 1);

% Process each temperature bin
for b = 1:num_temp_bins
    % Get data in this temperature bin
    if b < num_temp_bins
        mask = all_temp >= temp_edges(b) & all_temp < temp_edges(b+1);
    else
        mask = all_temp >= temp_edges(b) & all_temp <= temp_edges(b+1);
    end
    
    if sum(mask) < 20  % Need enough points for fitting
        continue;
    end
    
    v_bin = all_velocity(mask);
    f_bin = all_force(mask);
    t_bin = all_temp(mask);
    
    % Calculate temperature uncertainty for this bin
    temp_uncertainty(b) = uncertainty_tn(t_bin);
    
    % Separate compression and rebound
    v_comp = v_bin(v_bin > 0);
    f_comp = f_bin(v_bin > 0);
    v_reb = v_bin(v_bin < 0);
    f_reb = f_bin(v_bin < 0);
    
    % Calculate Vmax for this bin
    Vmax_bin = max(abs([v_comp; v_reb]));
    
    % Add opposite velocity data for better fitting
    V_threshold = Vmax_bin * opp_vel_perc;
    v_opp_comp_mask = (v_reb > -V_threshold);
    v_comp_all = [v_comp; v_reb(v_opp_comp_mask)];
    f_comp_all = [f_comp; f_reb(v_opp_comp_mask)];
    
    v_opp_reb_mask = (v_comp < V_threshold);
    v_reb_all = [v_reb; v_comp(v_opp_reb_mask)];
    f_reb_all = [f_reb; f_comp(v_opp_reb_mask)];
    
    % Fit compression (positive velocity)
    if ~isempty(v_comp_all)
        [fit_comp, unc_comp] = fit_piecewise_linear_with_uncertainty(v_comp_all, f_comp_all, Vmax_bin, v_knee_fixed, opp_vel_perc);
        C_LS_comp(b) = fit_comp.C_LS;
        C_HS_comp(b) = fit_comp.C_HS;
        unc_LS_comp(b) = unc_comp.C_LS;
        unc_HS_comp(b) = unc_comp.C_HS;
    end
    
    % Fit rebound (negative velocity)
    if ~isempty(v_reb_all)
        [fit_reb, unc_reb] = fit_piecewise_linear_with_uncertainty(v_reb_all, f_reb_all, Vmax_bin, v_knee_fixed, opp_vel_perc);
        C_LS_reb(b) = fit_reb.C_LS;
        C_HS_reb(b) = fit_reb.C_HS;
        unc_LS_reb(b) = unc_reb.C_LS;
        unc_HS_reb(b) = unc_reb.C_HS;
    end
end

% Create figure with single plot
figure();
hold on; grid off;

colors = get(gca, 'ColorOrder');


h1 = errorbar(temp_centers, C_LS_comp, ...
              unc_LS_comp, unc_LS_comp, ...          % Y-error (Vertical)
              temp_uncertainty, temp_uncertainty, ... % X-error (Horizontal)
              'o:', 'LineWidth', 1, 'MarkerSize', 8, ...
              'MarkerFaceColor', colors(1,:), ...
              'MarkerEdgeColor', 'k', 'Color', 'k', ...
              'CapSize', 6, 'DisplayName', 'Compression C_{LS}');

h2 = errorbar(temp_centers, C_HS_comp, ...
              unc_HS_comp, unc_HS_comp, ...          % Y-error
              temp_uncertainty, temp_uncertainty, ... % X-error
              's:', 'LineWidth', 1, 'MarkerSize', 8, ...
              'MarkerFaceColor', colors(2,:), ...
              'MarkerEdgeColor', 'k', 'Color', 'k', ...
              'CapSize', 6, 'DisplayName', 'Compression C_{HS}');

h3 = errorbar(temp_centers, C_LS_reb, ...
              unc_LS_reb, unc_LS_reb, ...            % Y-error
              temp_uncertainty, temp_uncertainty, ... % X-error
              'd:', 'LineWidth', 1, 'MarkerSize', 8, ...
              'MarkerFaceColor', colors(3,:), ...
              'MarkerEdgeColor', 'k', 'Color', 'k', ...
              'CapSize', 6, 'DisplayName', 'Rebound C_{LS}');

h4 = errorbar(temp_centers, C_HS_reb, ...
              unc_HS_reb, unc_HS_reb, ...            % Y-error
              temp_uncertainty, temp_uncertainty, ... % X-error
              '^:', 'LineWidth', 1, 'MarkerSize', 8, ...
              'MarkerFaceColor', colors(4,:), ...
              'MarkerEdgeColor', 'k', 'Color', 'k', ...
              'CapSize', 6, 'DisplayName', 'Rebound C_{HS}');

% Add zero line
plot(xlim, [0 0], 'k--', 'LineWidth', 0.8, 'HandleVisibility', 'off');

% Labels and formatting
set(gca, 'FontName', 'Times New Roman', 'FontSize', 11);
xlabel('\bfTemperature\rm [\it°C\rm]', 'FontSize', 13);
ylabel('\bfDamping Coefficient\rm [\itlbf·s/in\rm]', 'FontSize', 13);


% Legend
legend([h1, h2, h3, h4], 'Location', 'northwest', 'FontSize', 10, 'FontName', 'Times New Roman');
hold off;

% limits
xlim([28 54])

%% Percet Change
C_LS_comp_norm = 100 * (C_LS_comp - C_LS_comp(1)) / C_LS_comp(1);
C_HS_comp_norm = 100 * (C_HS_comp - C_HS_comp(1)) / C_HS_comp(1);
C_LS_reb_norm  = 100 * (C_LS_reb  - C_LS_reb(1))  / C_LS_reb(1);
C_HS_reb_norm  = 100 * (C_HS_reb  - C_HS_reb(1))  / C_HS_reb(1);

% Normalize uncertainties the same way
unc_LS_comp_norm = 100 * unc_LS_comp ./ C_LS_comp(1);
unc_HS_comp_norm = 100 * unc_HS_comp ./ C_HS_comp(1);
unc_LS_reb_norm  = 100 * unc_LS_reb  ./ C_LS_reb(1);
unc_HS_reb_norm  = 100 * unc_HS_reb  ./ C_HS_reb(1);

% X-uncertainty unchanged
temp_unc = temp_uncertainty;

figure(); hold on; grid off;
blue_dark   = [0   76 153] / 255;   % LS comp
blue_light  = [102 178 255] / 255;  % LS rebound
orange_dark = [204 102 0] / 255;    % HS comp
orange_light= [255 178 102] / 255;  % HS rebound

% --- LS Compression (dark blue)
errorbar(temp_centers, C_LS_comp_norm, unc_LS_comp_norm, unc_LS_comp_norm, ...
         temp_unc, temp_unc, 'o', 'LineWidth', 1.3, ...
         'MarkerSize', 8, 'MarkerFaceColor', blue_dark, ...
         'MarkerEdgeColor', 'k', ...
         'Color', blue_dark, 'CapSize', 6, ...
         'DisplayName','Compression C_{LS}');

% --- HS Compression (dark orange)
errorbar(temp_centers, C_HS_comp_norm, unc_HS_comp_norm, unc_HS_comp_norm, ...
         temp_unc, temp_unc, 'o', 'LineWidth', 1.3, ...
         'MarkerSize', 8, 'MarkerFaceColor', orange_dark, ...
         'MarkerEdgeColor', 'k', ...
         'Color', orange_dark, 'CapSize', 6, ...
         'DisplayName','Compression C_{HS}');

% --- LS Rebound (light blue)
errorbar(temp_centers, C_LS_reb_norm, unc_LS_reb_norm, unc_LS_reb_norm, ...
         temp_unc, temp_unc, 'd', 'LineWidth', 1.3, ...
         'MarkerSize', 8, 'MarkerFaceColor', blue_light, ...
         'MarkerEdgeColor', 'k', ...
         'Color', blue_light, 'CapSize', 6, ...
         'DisplayName','Rebound C_{LS}');

% --- HS Rebound (light orange)
errorbar(temp_centers, C_HS_reb_norm, unc_HS_reb_norm, unc_HS_reb_norm, ...
         temp_unc, temp_unc, 'd', 'LineWidth', 1.3, ...
         'MarkerSize', 8, 'MarkerFaceColor', orange_light, ...
         'MarkerEdgeColor', 'k', ...
         'Color', orange_light, 'CapSize', 6, ...
         'DisplayName','Rebound C_{HS}');

set(gca,'FontName','Times New Roman','FontSize',11);
xlabel('\bfTemperature\rm [\it°C\rm]', 'FontSize', 13);
ylabel('\bf\DeltaC / C_{0}\rm [%]', 'FontSize', 13);

legend('Location','southwest','FontSize',10,'FontName','Times New Roman');
hold off;
xlim([28 55])



%% Helper Functions

function [model_results, uncertainty] = fit_piecewise_linear_with_uncertainty(v_data, f_data, v_fit_max, v_knee_fixed, opp_vel_perc)
    v_abs = abs(v_data);
    mask = v_abs <= v_fit_max;
    v = v_data(mask);
    f = f_data(mask);
    v_a = v_abs(mask);
    
    if isempty(v) || numel(v) < 5
        model_results = initialize_nan_pw_results();
        uncertainty.C_LS = NaN;
        uncertainty.C_HS = NaN;
        return;
    end
    
    is_positive_vel = mean(v) > 0;
    
    % Determine F0
    V_threshold = v_fit_max * opp_vel_perc;
    f0_mask = v_a < V_threshold;
    
    if any(f0_mask)
        F0_mean = mean(f(f0_mask));
    else
        F0_mean = mean(f);
    end
    
    f_prime = f - F0_mean;
    
    % Build design matrix
    vk = v_knee_fixed;
    M = zeros(numel(v), 2);
    M(:, 1) = min(v_a, vk);
    M(:, 2) = max(0, v_a - vk);
    
    % Solve for coefficients
    % Use matrix division instead of inv() for better stability
    P = M \ f_prime;
    C_LS = P(1);
    C_HS = P(2);
    
    % --- SLOPE UNCERTAINTY CALCULATION ---
    % Compute residuals
    f_prime_pred = M * P;
    residuals = f_prime - f_prime_pred;
    
    % Estimate variance of the error (MSE)
    n = numel(v);
    p = 2; % number of parameters
    dof = n - p;
    MSE = sum(residuals.^2) / dof;
    
    % Covariance matrix of parameters: Var(P) = MSE * (M'M)^-1
    % using \ operator for (M'M)^-1 is numerically safer than inv()
    MtM = M' * M;
    Cov_P = MSE * (MtM \ eye(size(MtM)));
    
    % Standard Errors of coefficients
    se_P = sqrt(diag(Cov_P));
    
    % 95% Confidence Interval (Standard practice)
    % 0.975 for 2-tailed 95%
    t_crit = tinv(0.975, dof); 
    
    uncertainty.C_LS = t_crit * se_P(1);
    uncertainty.C_HS = t_crit * se_P(2);
    
    % Validate fit
    valid_fit = true;
    if is_positive_vel
        if C_LS < 0 || C_HS < 0
            valid_fit = false;
        end
    else
        if C_LS > 0 || C_HS > 0
            valid_fit = false;
        end
    end
    
    if abs(C_LS) < 1e-6 && abs(C_HS) < 1e-6
        valid_fit = false;
    end
    
    SS_res = sum(residuals.^2);
    SS_tot = sum((f_prime - mean(f_prime)).^2);
    
    if SS_tot < 1e-10
        valid_fit = false;
    end
    
    if valid_fit
        R2 = 1 - (SS_res / SS_tot);
        model_results.F0 = F0_mean;
        model_results.C_LS = C_LS;
        model_results.C_HS = C_HS;
        model_results.v_knee = vk;
        model_results.R2 = R2;
    else
        model_results = initialize_nan_pw_results();
        uncertainty.C_LS = NaN;
        uncertainty.C_HS = NaN;
    end
end

function res = initialize_nan_pw_results()
    res.F0 = NaN;
    res.C_LS = NaN;
    res.C_HS = NaN;
    res.v_knee = NaN;
    res.R2 = NaN;
end

function unc = uncertainty_tn(data)
    % --- TEMP UNCERTAINTY CALCULATION ---
    % Calculates the spread of temperature within the bin
    n = numel(data);
    if n <= 1
        unc = NaN;
        return;
    end
    
    % Use 2 * Standard Deviation (approx 95% of data spread)
    % We do NOT divide by sqrt(n) because we want the physical 
    % width of the bin, not the precision of the mean.
    unc = 2 * std(data);
end