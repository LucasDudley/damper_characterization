clear, clc, close all

% Load out test data
load("G:\.shortcut-targets-by-id\1vCayBu0JWPEaCjSa5KhpGMqdHFvsMCFY\Senior_Design\Data Collection\matfiles\valving_results_data.mat")

runNums = [10];
freqField = 'f1_053';

plot_multi_runs(results, runNums, freqField)

%% Plot multiple runs on single figure


% Specify runs to plot
runs = [71, 76, 77, 78]; % our data to plot
lissajous_freq = 'f1_053'; 


% Plot all runs together
plot_runs_comparison(results, runs, lissajous_freq);

%% Function to plot multiple runs on one figure

function plot_runs_comparison(results, runs, lissajous_freq)
    % Inputs:
    %   results        - Results structure containing run data
    %   runs           - Vector of run numbers to plot (e.g., [1, 2, 3])
    %   lissajous_freq - Frequency field name (e.g., 'f0_211', 'f1_053')
    
    % Colors & markers
    colors  = lines(length(runs));
    markers = {'o','s','d','^','v','>','<','p','h'};   % cycle markers

    figure('Name', 'Force-Velocity Comparison | Multiple Runs');
    hold on; grid off;

    h_legend = [];
    legend_str = {};

    for r = 1:length(runs)
        runNum = runs(r);
        rf = sprintf("r%d", runNum);

        if ~isfield(results, rf)
            warning("Run %d not found in results, skipping", runNum);
            continue;
        end

        run_data = results.(rf);
        color     = colors(r,:);
        marker    = markers{ mod(r-1, numel(markers)) + 1 };

        % Check frequency
        if ~isfield(run_data, lissajous_freq)
            warning("Frequency %s not found for run %d, skipping", lissajous_freq, runNum);
            continue;
        end

        d_liss = run_data.(lissajous_freq);

        % --- Plot FV_all mean and uncertainty as shaded band ---
        fill_shaded(d_liss.FV_all.velocity, d_liss.FV_all.mean, d_liss.FV_all.unc, color);

        % Solid mean line
        h_liss = plot(d_liss.FV_all.velocity, d_liss.FV_all.mean, ...
                      'Color', color, 'LineWidth', 1.2);

        if r == 1
            h_lissajous = h_liss;
        end

        % --- Extrema Error Bars (Better styling) ---
        all_fields = fieldnames(run_data);
        freq_fields = all_fields(startsWith(all_fields, 'f'));

        for f = 1:length(freq_fields)
            freq = freq_fields{f};
            d = run_data.(freq);
            mv = d.maxV;

            % POS
            h_err = errorbar(mv.pos.vmax, mv.pos.mean_force, mv.pos.unc_force, ...
                    'LineStyle','none', ...          % no connecting line
                    'Marker', marker, ...
                    'MarkerFaceColor', color, ...
                    'MarkerEdgeColor', 'k', ...
                    'Color', color * 0.5, ...        % slightly darker error bar
                    'LineWidth', 1, ...
                    'CapSize', 0);                   % remove caps

            % NEG
            errorbar(mv.neg.vmax, mv.neg.mean_force, mv.neg.unc_force, ...
                    'LineStyle','none', ...
                    'Marker', marker, ...
                    'MarkerFaceColor', color, ...
                    'MarkerEdgeColor', 'k', ...
                    'Color', color * 0.5, ...
                    'LineWidth', 1, ...
                    'CapSize', 0);

            if r == 1 && f == 1
                h_data = h_err;
            end
        end

        % Add legend element
        valve = run_data.valving;
        valve_str = sprintf("HSC %.1f | HSR %.1f | LSC %.1f | LSR %.1f", ...
                            valve.hsc, valve.hsr, valve.lsc, valve.lsr);

        h_legend(end+1) = plot(NaN, NaN, 'Color', color, ...
                               'LineWidth', 1.6, 'Marker', marker, ...
                               'MarkerFaceColor', color, 'MarkerEdgeColor','k');

        legend_str{end+1} = valve_str;
    end

    % --- Zero reference axes ---
    plot(xlim, [0 0], 'k--', 'LineWidth', 0.8, 'HandleVisibility','off');
    plot([0 0], ylim, 'k--', 'LineWidth', 0.8, 'HandleVisibility','off');

    % Aesthetics
    set(gca, 'FontName', 'Times New Roman');

    xlabel('\bfVelocity\rm [\itin/s\rm]');
    ylabel('\bfForce\rm [\itlbf\rm]');

    leg = legend(h_legend, legend_str, 'Location','best', 'FontSize',9);
    title(leg,'Valve Settings','FontWeight','bold','FontName','Times New Roman');

end


%% Helper function to format frequency names

function fill_shaded(x, y_mean, y_unc, facecolor)

    x = x(:);
    y_mean = y_mean(:);
    y_unc  = y_unc(:);

    y_upper = y_mean + y_unc;
    y_lower = y_mean - y_unc;

    fill([x; flipud(x)], [y_upper; flipud(y_lower)], ...
         facecolor, 'FaceAlpha', 0.23, 'EdgeColor', 'none');
end
