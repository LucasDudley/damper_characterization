clear, clc, close all
%% PLOTTING PARAMETERS 
GRID_RESOLUTION = 20;         % Number of points for interpolation grid
CONTOUR_LEVELS = 20;          % Number of contour levels 
INTERP_METHOD = 'linear';      
SHOW_GRID = false;            
MARKER_SIZE = 50;             
UNIT_LABEL = ' \mathrm{[lbf/(in/s)]}'; 

% Load results data
load("G:\.shortcut-targets-by-id\1vCayBu0JWPEaCjSa5KhpGMqdHFvsMCFY\Senior_Design\Data Collection\matfiles\valving_results_data.mat")
%% Extract Data
run_fields = fieldnames(results);
run_fields = run_fields(~cellfun(@isempty, regexp(run_fields, "^r\d+$")));

% Initialize storage arrays
num_runs = numel(run_fields);
hsc_vals = zeros(num_runs, 1);
hsr_vals = zeros(num_runs, 1);
lsc_vals = zeros(num_runs, 1);
lsr_vals = zeros(num_runs, 1);

% Storage for piecewise linear parameters (will hold original values: N/(m/s))
C_LS_pos = zeros(num_runs, 1);
C_HS_pos = zeros(num_runs, 1);
C_LS_neg = zeros(num_runs, 1);
C_HS_neg = zeros(num_runs, 1);
for i = 1:num_runs
    rf = run_fields{i};
    
    % Get valve settings
    hsc_vals(i) = results.(rf).valving.hsc;
    hsr_vals(i) = results.(rf).valving.hsr;
    lsc_vals(i) = results.(rf).valving.lsc;
    lsr_vals(i) = results.(rf).valving.lsr;
    
    % Get piecewise linear parameters
    if isfield(results.(rf), 'PW_fit_all')
        % Positive velocity (compression)
        if isfield(results.(rf).PW_fit_all, 'pos')
            C_LS_pos(i) = results.(rf).PW_fit_all.pos.C_LS;
            C_HS_pos(i) = results.(rf).PW_fit_all.pos.C_HS;
        else
            C_LS_pos(i) = NaN;
            C_HS_pos(i) = NaN;
        end
        
        % Negative velocity (rebound)
        if isfield(results.(rf).PW_fit_all, 'neg')
            C_LS_neg(i) = results.(rf).PW_fit_all.neg.C_LS;
            C_HS_neg(i) = results.(rf).PW_fit_all.neg.C_HS;
        else
            C_LS_neg(i) = NaN;
            C_HS_neg(i) = NaN;
        end
    end
end

% Create high-resolution grids
lsc_fine = linspace(min(lsc_vals), max(lsc_vals), GRID_RESOLUTION);
hsc_fine = linspace(min(hsc_vals), max(hsc_vals), GRID_RESOLUTION);
[LSC_grid, HSC_grid] = meshgrid(lsc_fine, hsc_fine);
lsr_fine = linspace(min(lsr_vals), max(lsr_vals), GRID_RESOLUTION);
hsr_fine = linspace(min(hsr_vals), max(hsr_vals), GRID_RESOLUTION);
[LSR_grid, HSR_grid] = meshgrid(lsr_fine, hsr_fine);

%% Piecewise Linear Damping Coefficients
figure('Name', 'Piecewise Linear Damping Coefficients', 'Position', [100, 100, 1000, 700]);

% C_LS Compression 
subplot(2, 2, 1);
CLS_grid = griddata(lsc_vals, hsc_vals, C_LS_pos, LSC_grid, HSC_grid, INTERP_METHOD);
contourf(LSC_grid, HSC_grid, CLS_grid, CONTOUR_LEVELS, 'LineStyle', 'none');
caxis([min(C_LS_pos), max(C_LS_pos)]);
cb1 = colorbar;
% All Times New Roman, fixed LaTeX
cb1.Label.String = '$C_{LS}$ [lbf/(in/s)]';
cb1.Label.Interpreter = 'latex';
cb1.FontName = 'Times New Roman'; 
hold on;
scatter(lsc_vals, hsc_vals, MARKER_SIZE, C_LS_pos, 'filled', 'MarkerEdgeColor','k');
xlabel('LSC Setting','FontName','Times New Roman','FontWeight', 'bold');
ylabel('HSC Setting','FontName','Times New Roman','FontWeight', 'bold');
title('$C_{LS}$','Interpreter','latex','FontName','Times New Roman');
box off
set(gca, 'FontName', 'Times New Roman'); % Set axes numbers font
% Force Y-ticks to be integers
y_ticks = get(gca, 'YTick');
y_ticks_int = unique(round(y_ticks));
set(gca, 'YTick', y_ticks_int);

% C_HS Compression
subplot(2, 2, 2);
CHS_grid = griddata(lsc_vals, hsc_vals, C_HS_pos, LSC_grid, HSC_grid, INTERP_METHOD);
contourf(LSC_grid, HSC_grid, CHS_grid, CONTOUR_LEVELS, 'LineStyle', 'none');
caxis([min(C_HS_pos), max(C_HS_pos)]);
cb2 = colorbar;
% All Times New Roman, fixed LaTeX
cb2.Label.String = '$C_{HS}$ [lbf/(in/s)]';
cb2.Label.Interpreter = 'latex';
cb2.FontName = 'Times New Roman';
hold on;
scatter(lsc_vals, hsc_vals, MARKER_SIZE, C_HS_pos, 'filled', 'MarkerEdgeColor','k');
xlabel('LSC Setting','FontName','Times New Roman','FontWeight', 'bold');
ylabel('HSC Setting','FontName','Times New Roman','FontWeight', 'bold');
title('$C_{HS}$','Interpreter','latex','FontName','Times New Roman');
box off
set(gca, 'FontName', 'Times New Roman'); % Set axes numbers font
% Force Y-ticks to be integers
y_ticks = get(gca, 'YTick');
y_ticks_int = unique(round(y_ticks));
set(gca, 'YTick', y_ticks_int);

% C_LS Rebound 
subplot(2, 2, 3);
CLS_grid = griddata(lsr_vals, hsr_vals, C_LS_neg, LSR_grid, HSR_grid, INTERP_METHOD);
contourf(LSR_grid, HSR_grid, CLS_grid, CONTOUR_LEVELS, 'LineStyle', 'none');
caxis([min(C_LS_neg), max(C_LS_neg)]);
cb3 = colorbar;
% All Times New Roman, fixed LaTeX
cb3.Label.String = '$C_{LS}$ [lbf/(in/s)]';
cb3.Label.Interpreter = 'latex';
cb3.FontName = 'Times New Roman';
hold on;
scatter(lsr_vals, hsr_vals, MARKER_SIZE, C_LS_neg, 'filled', 'MarkerEdgeColor','k');
xlabel('LSR Setting','FontName','Times New Roman','FontWeight', 'bold');
ylabel('HSR Setting','FontName','Times New Roman','FontWeight', 'bold');
title('$C_{LS}$','Interpreter','latex','FontName','Times New Roman');
box off
set(gca, 'FontName', 'Times New Roman'); % Set axes numbers font
% Force Y-ticks to be integers
y_ticks = get(gca, 'YTick');
y_ticks_int = unique(round(y_ticks));
set(gca, 'YTick', y_ticks_int);

% C_HS Rebound
subplot(2, 2, 4);
CHS_grid = griddata(lsr_vals, hsr_vals, C_HS_neg, LSR_grid, HSR_grid, INTERP_METHOD);
contourf(LSR_grid, HSR_grid, CHS_grid, CONTOUR_LEVELS, 'LineStyle', 'none');
caxis([min(C_HS_neg), max(C_HS_neg)]);
cb4 = colorbar;
% All Times New Roman, fixed LaTeX
cb4.Label.String = '$C_{HS}$ [lbf/(in/s)]';
cb4.Label.Interpreter = 'latex';
cb4.FontName = 'Times New Roman';
hold on;
scatter(lsr_vals, hsr_vals, MARKER_SIZE, C_HS_neg, 'filled', 'MarkerEdgeColor','k');
xlabel('LSR Setting','FontName','Times New Roman','FontWeight', 'bold');
ylabel('HSR Setting','FontName','Times New Roman','FontWeight', 'bold');
title('$C_{HS}$','Interpreter','latex','FontName','Times New Roman');
box off
set(gca, 'FontName', 'Times New Roman'); % Set axes numbers font
% Force Y-ticks to be integers
y_ticks = get(gca, 'YTick');
y_ticks_int = unique(round(y_ticks));
set(gca, 'YTick', y_ticks_int);

% Adjust subplot spacing for tighter layout
set(gcf, 'Units', 'normalized');
h = findall(gcf, 'Type', 'axes');
for i = 1:length(h)
    pos = get(h(i), 'Position');
    set(h(i), 'Position', [pos(1), pos(2), pos(3)*1.05, pos(4)*1.05]);
end

% Add centered text labels for Compression and Rebound
% Adjusted vertical position (0.94 -> 0.93) and (0.48 -> 0.47)
annotation('textbox', [0.35, 0.94, 0.3, 0.05], 'String', 'Compression Damping', ...
    'FontName', 'Times New Roman', 'FontSize', 14, 'FontWeight', 'bold', ...
    'HorizontalAlignment', 'center', 'EdgeColor', 'none');
annotation('textbox', [0.35, 0.48, 0.3, 0.05], 'String', 'Rebound Damping', ...
    'FontName', 'Times New Roman', 'FontSize', 14, 'FontWeight', 'bold', ...
    'HorizontalAlignment', 'center', 'EdgeColor', 'none');