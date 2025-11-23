clear, clc, close all

% Load results data
load("G:\.shortcut-targets-by-id\1vCayBu0JWPEaCjSa5KhpGMqdHFvsMCFY\Senior_Design\Data Collection\matfiles\valving_results_data.mat")

%% Extract data from all runs
run_fields = fieldnames(results);
run_fields = run_fields(~cellfun(@isempty, regexp(run_fields, "^r\d+$")));

% Initialize storage arrays
num_runs = numel(run_fields);
hsc_vals = zeros(num_runs, 1);
hsr_vals = zeros(num_runs, 1);
lsc_vals = zeros(num_runs, 1);
lsr_vals = zeros(num_runs, 1);

% Storage for polynomial coefficients
poly_order = [];
coeffs_pos = [];
coeffs_neg = [];
R2_pos = zeros(num_runs, 1);
R2_neg = zeros(num_runs, 1);

for i = 1:num_runs
    rf = run_fields{i};
    
    % Get valve settings
    hsc_vals(i) = results.(rf).valving.hsc;
    hsr_vals(i) = results.(rf).valving.hsr;
    lsc_vals(i) = results.(rf).valving.lsc;
    lsr_vals(i) = results.(rf).valving.lsr;
    
    % Get polynomial coefficients and R2
    if isfield(results.(rf), 'FV_fit_all')
        % Positive velocity (compression)
        if ~isempty(results.(rf).FV_fit_all.pos.coeffs)
            coeffs_pos(i, :) = results.(rf).FV_fit_all.pos.coeffs;
            R2_pos(i) = results.(rf).FV_fit_all.pos.R2;
        else
            coeffs_pos(i, :) = NaN(1, length(coeffs_pos(1,:)));
            R2_pos(i) = NaN;
        end
        
        % Negative velocity (rebound)
        if ~isempty(results.(rf).FV_fit_all.neg.coeffs)
            coeffs_neg(i, :) = results.(rf).FV_fit_all.neg.coeffs;
            R2_neg(i) = results.(rf).FV_fit_all.neg.R2;
        else
            coeffs_neg(i, :) = NaN(1, length(coeffs_neg(1,:)));
            R2_neg(i) = NaN;
        end
        
        if isempty(poly_order)
            poly_order = length(results.(rf).FV_fit_all.pos.coeffs) - 1;
        end
    end
end

%% Create contour plots for COMPRESSION
num_coeffs = size(coeffs_pos, 2);

figure('Name', 'Compression Polynomial Coefficients vs LSC/HSC');
for c = 1:num_coeffs
    subplot(2, ceil(num_coeffs/2), c);
    
    % Create grid for interpolation
    lsc_unique = unique(lsc_vals);
    hsc_unique = unique(hsc_vals);
    [LSC_grid, HSC_grid] = meshgrid(lsc_unique, hsc_unique);
    
    % Interpolate coefficient values onto grid
    coeff_grid = griddata(lsc_vals, hsc_vals, coeffs_pos(:, c), LSC_grid, HSC_grid, 'natural');
    
    % Create contour plot
    contourf(LSC_grid, HSC_grid, coeff_grid, 15, 'LineWidth', 0.5);
    colorbar;
    hold on;
    
    % Plot data points
    scatter(lsc_vals, hsc_vals, 50, coeffs_pos(:, c), 'filled', 'MarkerEdgeColor', 'k', 'LineWidth', 1);
    
    xlabel('LSC Setting');
    ylabel('HSC Setting');
    title(sprintf('Coefficient a_%d', poly_order - c + 1));
    grid on;
end
sgtitle('Compression Polynomial Coefficients');

%% Create contour plots for REBOUND
figure('Name', 'Rebound Polynomial Coefficients vs LSR/HSR');
for c = 1:num_coeffs
    subplot(2, ceil(num_coeffs/2), c);
    
    % Create grid for interpolation
    lsr_unique = unique(lsr_vals);
    hsr_unique = unique(hsr_vals);
    [LSR_grid, HSR_grid] = meshgrid(lsr_unique, hsr_unique);
    
    % Interpolate coefficient values onto grid
    coeff_grid = griddata(lsr_vals, hsr_vals, coeffs_neg(:, c), LSR_grid, HSR_grid, 'natural');
    
    % Create contour plot
    contourf(LSR_grid, HSR_grid, coeff_grid, 15, 'LineWidth', 0.5);
    colorbar;
    hold on;
    
    % Plot data points
    scatter(lsr_vals, hsr_vals, 50, coeffs_neg(:, c), 'filled', 'MarkerEdgeColor', 'k', 'LineWidth', 1);
    
    xlabel('LSR Setting');
    ylabel('HSR Setting');
    title(sprintf('Coefficient a_%d', poly_order - c + 1));
    grid on;
end
sgtitle('Rebound Polynomial Coefficients');

%% Plot R-squared values
figure('Name', 'R-squared Values vs Valve Settings');

% Compression R2
subplot(1, 2, 1);
lsc_unique = unique(lsc_vals);
hsc_unique = unique(hsc_vals);
[LSC_grid, HSC_grid] = meshgrid(lsc_unique, hsc_unique);
R2_grid = griddata(lsc_vals, hsc_vals, R2_pos, LSC_grid, HSC_grid, 'natural');
contourf(LSC_grid, HSC_grid, R2_grid, 15, 'LineWidth', 0.5);
colorbar;
hold on;
scatter(lsc_vals, hsc_vals, 50, R2_pos, 'filled', 'MarkerEdgeColor', 'k', 'LineWidth', 1);
xlabel('LSC Setting');
ylabel('HSC Setting');
title('Compression R²');
grid on;
caxis([min(R2_pos) 1]);

% Rebound R2
subplot(1, 2, 2);
lsr_unique = unique(lsr_vals);
hsr_unique = unique(hsr_vals);
[LSR_grid, HSR_grid] = meshgrid(lsr_unique, hsr_unique);
R2_grid = griddata(lsr_vals, hsr_vals, R2_neg, LSR_grid, HSR_grid, 'natural');
contourf(LSR_grid, HSR_grid, R2_grid, 15, 'LineWidth', 0.5);
colorbar;
hold on;
scatter(lsr_vals, hsr_vals, 50, R2_neg, 'filled', 'MarkerEdgeColor', 'k', 'LineWidth', 1);
xlabel('LSR Setting');
ylabel('HSR Setting');
title('Rebound R²');
grid on;
caxis([min(R2_neg) 1]);

sgtitle('Polynomial Fit Quality (R-squared)');