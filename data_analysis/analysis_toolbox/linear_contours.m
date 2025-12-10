clear, clc, close all
s = settings;
s.matlab.appearance.figure.GraphicsTheme.TemporaryValue= 'light';

%% PLOTTING PARAMETERS 
GRID_RESOLUTION = 25;
CONTOUR_LEVELS = 25;
INTERP_METHOD = 'linear';
SHOW_GRID = false;
MARKER_SIZE = 45;

% Load results data
EXCLUDE_RUNS = {'r1', 'r2', 'r3', 'r4', 'r5', 'r6'};
load("G:\.shortcut-targets-by-id\1vCayBu0JWPEaCjSa5KhpGMqdHFvsMCFY\Senior_Design\Data Collection\matfiles\valving_results_data.mat")

%% Extract Data
run_fields = fieldnames(results);
run_fields = run_fields(~cellfun(@isempty, regexp(run_fields, "^r\d+$")));
run_fields = run_fields(~ismember(run_fields, EXCLUDE_RUNS));

num_runs = numel(run_fields);

% Settings
hsc_vals = zeros(num_runs, 1);
hsr_vals = zeros(num_runs, 1);
lsc_vals = zeros(num_runs, 1);
lsr_vals = zeros(num_runs, 1);
run_names = cell(num_runs, 1);

% Results
C_LS_pos = zeros(num_runs, 1);
C_HS_pos = zeros(num_runs, 1);
C_LS_neg = zeros(num_runs, 1);
C_HS_neg = zeros(num_runs, 1);
F0_pos   = zeros(num_runs, 1);
F0_neg   = zeros(num_runs, 1);

% R2 separated by LS/HS (Assumes R2_LS and R2_HS exist in struct)
R2_LS_pos = zeros(num_runs, 1);
R2_HS_pos = zeros(num_runs, 1);
R2_LS_neg = zeros(num_runs, 1);
R2_HS_neg = zeros(num_runs, 1);

for i = 1:num_runs
    rf = run_fields{i};
    run_names{i} = rf;
    
    hsc_vals(i) = results.(rf).valving.hsc;
    hsr_vals(i) = results.(rf).valving.hsr;
    lsc_vals(i) = results.(rf).valving.lsc;
    lsr_vals(i) = results.(rf).valving.lsr;
    
    if isfield(results.(rf), 'PW_fit_all')
        % --- COMPRESSION (POS) ---
        if isfield(results.(rf).PW_fit_all, 'pos')
            C_LS_pos(i) = results.(rf).PW_fit_all.pos.C_LS;
            C_HS_pos(i) = results.(rf).PW_fit_all.pos.C_HS;
            
            % F0 Check
            if isfield(results.(rf).PW_fit_all.pos, 'F0')
                F0_pos(i) = results.(rf).PW_fit_all.pos.F0;
            else
                F0_pos(i) = NaN;
            end
            
            % R2 Extraction (Checks for specific LS/HS R2, defaults to global R2 if specific missing)
            if isfield(results.(rf).PW_fit_all.pos, 'R2_LS')
                R2_LS_pos(i) = results.(rf).PW_fit_all.pos.R2_LS;
            elseif isfield(results.(rf).PW_fit_all.pos, 'R2')
                R2_LS_pos(i) = results.(rf).PW_fit_all.pos.R2; % Fallback
            else
                R2_LS_pos(i) = NaN;
            end
            
            if isfield(results.(rf).PW_fit_all.pos, 'R2_HS')
                R2_HS_pos(i) = results.(rf).PW_fit_all.pos.R2_HS;
            elseif isfield(results.(rf).PW_fit_all.pos, 'R2')
                R2_HS_pos(i) = results.(rf).PW_fit_all.pos.R2; % Fallback
            else
                R2_HS_pos(i) = NaN;
            end
        else
            C_LS_pos(i) = NaN; C_HS_pos(i) = NaN; F0_pos(i) = NaN;
            R2_LS_pos(i) = NaN; R2_HS_pos(i) = NaN;
        end
        
        % --- REBOUND (NEG) ---
        if isfield(results.(rf).PW_fit_all, 'neg')
            C_LS_neg(i) = results.(rf).PW_fit_all.neg.C_LS;
            C_HS_neg(i) = results.(rf).PW_fit_all.neg.C_HS;
            
            if isfield(results.(rf).PW_fit_all.neg, 'F0')
                F0_neg(i) = results.(rf).PW_fit_all.neg.F0;
            else
                F0_neg(i) = NaN;
            end
            
            % R2 Extraction
            if isfield(results.(rf).PW_fit_all.neg, 'R2_LS')
                R2_LS_neg(i) = results.(rf).PW_fit_all.neg.R2_LS;
            elseif isfield(results.(rf).PW_fit_all.neg, 'R2')
                R2_LS_neg(i) = results.(rf).PW_fit_all.neg.R2; % Fallback
            else
                R2_LS_neg(i) = NaN;
            end
            
            if isfield(results.(rf).PW_fit_all.neg, 'R2_HS')
                R2_HS_neg(i) = results.(rf).PW_fit_all.neg.R2_HS;
            elseif isfield(results.(rf).PW_fit_all.neg, 'R2')
                R2_HS_neg(i) = results.(rf).PW_fit_all.neg.R2; % Fallback
            else
                R2_HS_neg(i) = NaN;
            end
        else
            C_LS_neg(i) = NaN; C_HS_neg(i) = NaN; F0_neg(i) = NaN;
            R2_LS_neg(i) = NaN; R2_HS_neg(i) = NaN;
        end
    end
end

% Grids
lsc_fine = linspace(min(lsc_vals), max(lsc_vals), GRID_RESOLUTION);
hsc_fine = linspace(min(hsc_vals), max(hsc_vals), GRID_RESOLUTION);
[LSC_grid, HSC_grid] = meshgrid(lsc_fine, hsc_fine);

lsr_fine = linspace(min(lsr_vals), max(lsr_vals), GRID_RESOLUTION);
hsr_fine = linspace(min(hsr_vals), max(hsr_vals), GRID_RESOLUTION);
[LSR_grid, HSR_grid] = meshgrid(lsr_fine, hsr_fine);

%% Figure 1: Damping Coefficients (CLS, CHS, F0)
figure('Name', 'Piecewise Linear Damping Coefficients', 'Position', [10, 10, 1000, 1050]);

% C_LS Compression 
subplot(3, 2, 1);
CLS_grid = griddata(lsc_vals, hsc_vals, C_LS_pos, LSC_grid, HSC_grid, INTERP_METHOD);
contourf(LSC_grid, HSC_grid, CLS_grid, CONTOUR_LEVELS, 'LineStyle', 'none');
caxis([min(C_LS_pos), max(C_LS_pos)]);
cb1 = colorbar;
cb1.Label.String = '$C_{LS}$ [lbf/(in/s)]';
cb1.Label.Interpreter = 'latex';
cb1.FontName = 'Times New Roman'; 
hold on;
s1 = scatter(lsc_vals, hsc_vals, MARKER_SIZE, C_LS_pos, 'filled', 'MarkerEdgeColor','k');
s1.ButtonDownFcn = @(src,event) showRunInfo(src, event, lsc_vals, hsc_vals, run_names, R2_pos, 'compression');
xlabel('LSC Setting','FontName','Times New Roman','FontWeight', 'bold');
ylabel('HSC Setting','FontName','Times New Roman','FontWeight', 'bold');
title('$C_{LS}$','Interpreter','latex','FontName','Times New Roman');
box off
set(gca, 'FontName', 'Times New Roman');
ytick = unique(round(get(gca,'YTick')));
set(gca,'YTick', ytick);

% C_LS Rebound 
subplot(3, 2, 2);
CLS_grid = griddata(lsr_vals, hsr_vals, C_LS_neg, LSR_grid, HSR_grid, INTERP_METHOD);
contourf(LSR_grid, HSR_grid, CLS_grid, CONTOUR_LEVELS, 'LineStyle', 'none');
caxis([min(C_LS_neg), max(C_LS_neg)]);
cb2 = colorbar;
cb2.Label.String = '$C_{LS}$ [lbf/(in/s)]';
cb2.Label.Interpreter = 'latex';
cb2.FontName = 'Times New Roman';
hold on;
s2 = scatter(lsr_vals, hsr_vals, MARKER_SIZE, C_LS_neg, 'filled', 'MarkerEdgeColor','k');
s2.ButtonDownFcn = @(src,event) showRunInfo(src, event, lsr_vals, hsr_vals, run_names, R2_neg, 'rebound');
xlabel('LSR Setting','FontName','Times New Roman','FontWeight', 'bold');
ylabel('HSR Setting','FontName','Times New Roman','FontWeight', 'bold');
title('$C_{LS}$','Interpreter','latex','FontName','Times New Roman');
box off
set(gca, 'FontName', 'Times New Roman');
ytick = unique(round(get(gca,'YTick')));
set(gca,'YTick', ytick);

% C_HS Compression
subplot(3, 2, 3);
CHS_grid = griddata(lsc_vals, hsc_vals, C_HS_pos, LSC_grid, HSC_grid, INTERP_METHOD);
contourf(LSC_grid, HSC_grid, CHS_grid, CONTOUR_LEVELS, 'LineStyle', 'none');
caxis([min(C_HS_pos), max(C_HS_pos)]);
cb3 = colorbar;
cb3.Label.String = '$C_{HS}$ [lbf/(in/s)]';
cb3.Label.Interpreter = 'latex';
cb3.FontName = 'Times New Roman';
hold on;
s3 = scatter(lsc_vals, hsc_vals, MARKER_SIZE, C_HS_pos, 'filled', 'MarkerEdgeColor','k');
s3.ButtonDownFcn = @(src,event) showRunInfo(src, event, lsc_vals, hsc_vals, run_names, R2_pos, 'compression');
xlabel('LSC Setting','FontName','Times New Roman','FontWeight', 'bold');
ylabel('HSC Setting','FontName','Times New Roman','FontWeight', 'bold');
title('$C_{HS}$','Interpreter','latex','FontName','Times New Roman');
box off
set(gca, 'FontName', 'Times New Roman');
ytick = unique(round(get(gca,'YTick')));
set(gca,'YTick', ytick);

% C_HS Rebound
subplot(3, 2, 4);
CHS_grid = griddata(lsr_vals, hsr_vals, C_HS_neg, LSR_grid, HSR_grid, INTERP_METHOD);
contourf(LSR_grid, HSR_grid, CHS_grid, CONTOUR_LEVELS, 'LineStyle', 'none');
caxis([min(C_HS_neg), max(C_HS_neg)]);
cb4 = colorbar;
cb4.Label.String = '$C_{HS}$ [lbf/(in/s)]';
cb4.Label.Interpreter = 'latex';
cb4.FontName = 'Times New Roman';
hold on;
s4 = scatter(lsr_vals, hsr_vals, MARKER_SIZE, C_HS_neg, 'filled', 'MarkerEdgeColor','k');
s4.ButtonDownFcn = @(src,event) showRunInfo(src, event, lsr_vals, hsr_vals, run_names, R2_neg, 'rebound');
xlabel('LSR Setting','FontName','Times New Roman','FontWeight', 'bold');
ylabel('HSR Setting','FontName','Times New Roman','FontWeight', 'bold');
title('$C_{HS}$','Interpreter','latex','FontName','Times New Roman');
box off
set(gca, 'FontName', 'Times New Roman');
ytick = unique(round(get(gca,'YTick')));
set(gca,'YTick', ytick);

% F0 Compression
subplot(3, 2, 5);
F0_grid = griddata(lsc_vals, hsc_vals, F0_pos, LSC_grid, HSC_grid, INTERP_METHOD);
contourf(LSC_grid, HSC_grid, F0_grid, CONTOUR_LEVELS, 'LineStyle', 'none');
F0_pos_valid = F0_pos(~isnan(F0_pos));
if ~isempty(F0_pos_valid) && (max(F0_pos_valid) > min(F0_pos_valid))
    caxis([min(F0_pos_valid), max(F0_pos_valid)]);
end
cb5 = colorbar;
cb5.Label.String = '$F_0$ [lbf]';
cb5.Label.Interpreter = 'latex';
cb5.FontName = 'Times New Roman';
hold on;
s5 = scatter(lsc_vals, hsc_vals, MARKER_SIZE, F0_pos, 'filled', 'MarkerEdgeColor','k');
s5.ButtonDownFcn = @(src,event) showRunInfo(src, event, lsc_vals, hsc_vals, run_names, R2_pos, 'compression');
xlabel('LSC Setting','FontName','Times New Roman','FontWeight', 'bold');
ylabel('HSC Setting','FontName','Times New Roman','FontWeight', 'bold');
title('$F_0$','Interpreter','latex','FontName','Times New Roman');
box off
set(gca, 'FontName', 'Times New Roman');
ytick = unique(round(get(gca,'YTick')));
set(gca,'YTick', ytick);

% F0 Rebound
subplot(3, 2, 6);
F0_grid = griddata(lsr_vals, hsr_vals, F0_neg, LSR_grid, HSR_grid, INTERP_METHOD);
contourf(LSR_grid, HSR_grid, F0_grid, CONTOUR_LEVELS, 'LineStyle', 'none');
F0_neg_valid = F0_neg(~isnan(F0_neg));
if ~isempty(F0_neg_valid) && (max(F0_neg_valid) > min(F0_neg_valid))
    caxis([min(F0_neg_valid), max(F0_neg_valid)]);
end
cb6 = colorbar;
cb6.Label.String = '$F_0$ [lbf]';
cb6.Label.Interpreter = 'latex';
cb6.FontName = 'Times New Roman';
hold on;
s6 = scatter(lsr_vals, hsr_vals, MARKER_SIZE, F0_neg, 'filled', 'MarkerEdgeColor','k');
s6.ButtonDownFcn = @(src,event) showRunInfo(src, event, lsr_vals, hsr_vals, run_names, R2_neg, 'rebound');
xlabel('LSR Setting','FontName','Times New Roman','FontWeight', 'bold');
ylabel('HSR Setting','FontName','Times New Roman','FontWeight', 'bold');
title('$F_0$','Interpreter','latex','FontName','Times New Roman');
box off
set(gca, 'FontName', 'Times New Roman');
ytick = unique(round(get(gca,'YTick')));
set(gca,'YTick', ytick);

% Column Headers
ax1 = subplot(3,2,1);
ax2 = subplot(3,2,2);
p1 = get(ax1,'Position');
p2 = get(ax2,'Position');

annotation('textbox', [p1(1), p1(2)+p1(4)+0.02, p1(3), 0.03], 'String', 'Compression', ...
    'FontName', 'Times New Roman', 'FontSize', 14, 'FontWeight', 'bold', ...
    'HorizontalAlignment', 'center', 'EdgeColor', 'none');
annotation('textbox', [p2(1), p2(2)+p2(4)+0.02, p2(3), 0.03], 'String', 'Rebound', ...
    'FontName', 'Times New Roman', 'FontSize', 14, 'FontWeight', 'bold', ...
    'HorizontalAlignment', 'center', 'EdgeColor', 'none');

%% Figure 2: R² Values
%% Figure 2: R² Values (LS & HS split)
figure('Name', 'R² Goodness of Fit', 'Position', [1150, 100, 1000, 800]);

% --- Row 1: LOW SPEED (LS) ---

% R2 LS Compression
subplot(2, 2, 1);
R2_grid = griddata(lsc_vals, hsc_vals, R2_LS_pos, LSC_grid, HSC_grid, INTERP_METHOD);
contourf(LSC_grid, HSC_grid, R2_grid, CONTOUR_LEVELS, 'LineStyle', 'none');
valid_data = R2_LS_pos(~isnan(R2_LS_pos));
if ~isempty(valid_data) && (max(valid_data) > min(valid_data))
    caxis([min(valid_data), max(valid_data)]);
end
cb = colorbar; cb.Label.String = '$R^2_{LS}$'; cb.Label.Interpreter = 'latex';
hold on;
s = scatter(lsc_vals, hsc_vals, MARKER_SIZE, R2_LS_pos, 'filled', 'MarkerEdgeColor','k');
s.ButtonDownFcn = @(src,event) showRunInfo(src, event, lsc_vals, hsc_vals, run_names, R2_LS_pos, 'compression');
xlabel('LSC Setting'); ylabel('HSC Setting');
title('Compression LS $R^2$','Interpreter','latex');
set(gca, 'FontName', 'Times New Roman'); axis square; box off;

% R2 LS Rebound
subplot(2, 2, 2);
R2_grid = griddata(lsr_vals, hsr_vals, R2_LS_neg, LSR_grid, HSR_grid, INTERP_METHOD);
contourf(LSR_grid, HSR_grid, R2_grid, CONTOUR_LEVELS, 'LineStyle', 'none');
valid_data = R2_LS_neg(~isnan(R2_LS_neg));
if ~isempty(valid_data) && (max(valid_data) > min(valid_data))
    caxis([min(valid_data), max(valid_data)]);
end
cb = colorbar; cb.Label.String = '$R^2_{LS}$'; cb.Label.Interpreter = 'latex';
hold on;
s = scatter(lsr_vals, hsr_vals, MARKER_SIZE, R2_LS_neg, 'filled', 'MarkerEdgeColor','k');
s.ButtonDownFcn = @(src,event) showRunInfo(src, event, lsr_vals, hsr_vals, run_names, R2_LS_neg, 'rebound');
xlabel('LSR Setting'); ylabel('HSR Setting');
title('Rebound LS $R^2$','Interpreter','latex');
set(gca, 'FontName', 'Times New Roman'); axis square; box off;

% --- Row 2: HIGH SPEED (HS) ---

% R2 HS Compression
subplot(2, 2, 3);
R2_grid = griddata(lsc_vals, hsc_vals, R2_HS_pos, LSC_grid, HSC_grid, INTERP_METHOD);
contourf(LSC_grid, HSC_grid, R2_grid, CONTOUR_LEVELS, 'LineStyle', 'none');
valid_data = R2_HS_pos(~isnan(R2_HS_pos));
if ~isempty(valid_data) && (max(valid_data) > min(valid_data))
    caxis([min(valid_data), max(valid_data)]);
end
cb = colorbar; cb.Label.String = '$R^2_{HS}$'; cb.Label.Interpreter = 'latex';
hold on;
s = scatter(lsc_vals, hsc_vals, MARKER_SIZE, R2_HS_pos, 'filled', 'MarkerEdgeColor','k');
s.ButtonDownFcn = @(src,event) showRunInfo(src, event, lsc_vals, hsc_vals, run_names, R2_HS_pos, 'compression');
xlabel('LSC Setting'); ylabel('HSC Setting');
title('Compression HS $R^2$','Interpreter','latex');
set(gca, 'FontName', 'Times New Roman'); axis square; box off;

% R2 HS Rebound
subplot(2, 2, 4);
R2_grid = griddata(lsr_vals, hsr_vals, R2_HS_neg, LSR_grid, HSR_grid, INTERP_METHOD);
contourf(LSR_grid, HSR_grid, R2_grid, CONTOUR_LEVELS, 'LineStyle', 'none');
valid_data = R2_HS_neg(~isnan(R2_HS_neg));
if ~isempty(valid_data) && (max(valid_data) > min(valid_data))
    caxis([min(valid_data), max(valid_data)]);
end
cb = colorbar; cb.Label.String = '$R^2_{HS}$'; cb.Label.Interpreter = 'latex';
hold on;
s = scatter(lsr_vals, hsr_vals, MARKER_SIZE, R2_HS_neg, 'filled', 'MarkerEdgeColor','k');
s.ButtonDownFcn = @(src,event) showRunInfo(src, event, lsr_vals, hsr_vals, run_names, R2_HS_neg, 'rebound');
xlabel('LSR Setting'); ylabel('HSR Setting');
title('Rebound HS $R^2$','Interpreter','latex');
set(gca, 'FontName', 'Times New Roman'); axis square; box off;

%% Callback function
function showRunInfo(~, event, x_vals, y_vals, run_names, R2_vals, damping_type)
    click_pos = event.IntersectionPoint(1:2);
    distances = sqrt((x_vals - click_pos(1)).^2 + (y_vals - click_pos(2)).^2);
    [~, idx] = min(distances);
    
    run_name = run_names{idx};
    ax = gca;
    delete(findall(ax, 'Tag', 'RunInfoText'));
    
    label_str = sprintf('%s\nR²=%.3f', run_name, R2_vals(idx));
    
    text(x_vals(idx), y_vals(idx), sprintf('  %s', label_str), ...
        'FontName', 'Times New Roman', 'FontSize', 9, 'FontWeight', 'bold', ...
        'BackgroundColor', 'white', 'EdgeColor', 'black', 'Margin', 2, ...
        'Tag', 'RunInfoText', 'HorizontalAlignment', 'left');
end