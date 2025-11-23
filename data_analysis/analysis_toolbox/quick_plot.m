clear, clc, close all

%load data
load("G:\.shortcut-targets-by-id\1vCayBu0JWPEaCjSa5KhpGMqdHFvsMCFY\Senior_Design\Data Collection\matfiles\valving_test_data.mat")
load("G:\.shortcut-targets-by-id\1vCayBu0JWPEaCjSa5KhpGMqdHFvsMCFY\Senior_Design\Data Collection\matfiles\valving_results_data.mat")

%% plot test_data
plot_raw(test_data, 56, "f0_632");

%% plot results
plot_processed(results, 57, "f0_632");

%% quick plot helpers

function plot_raw(all_data, runNum, freqField)

    % access run
    runField = sprintf("r%d", runNum);

    if ~isfield(all_data, runField)
        error("Run %d not found.", runNum);
    end

    if ~isfield(all_data.(runField), freqField)
        error("Frequency field '%s' not found for run %d.", freqField, runNum);
    end

    d   = all_data.(runField).(freqField);
    val = all_data.(runField).valving;   % valving struct

    % Build valving string: HSC/HSR/LSC/LSR
    valve_str = sprintf("HSC %.1f | HSR %.1f | LSC %.1f | LSR %.1f", ...
                        val.hsc, val.hsr, val.lsc, val.lsr);

    disp_str  = "Displacement (in)";
    vel_str   = "Velocity (in/s)";
    force_str = "Force (N)";
    temp_str  = "Temperature (C)";
    accel_str = "Acceleration (in/s^2)";

    % Force vs Displacement
    figure;
    scatter(d.disp, d.force, 18, d.temp, 'filled');
    grid on;
    xlabel(disp_str);
    ylabel(force_str);
    title({ ...
        sprintf("Run %d | %s | Force–Displacement", runNum, freqField), ...
        valve_str ...
    }, "Interpreter","none");
    cb = colorbar;
    cb.Label.String = temp_str;
    colormap turbo;

    % Force vs Velocity
    figure;
    scatter(d.velocity, d.force, 18, d.temp, 'filled');
    grid on;
    xlabel(vel_str);
    ylabel(force_str);
    title({ ...
        sprintf("Run %d | %s | Force–Velocity", runNum, freqField), ...
        valve_str ...
    }, "Interpreter","none");
    cb = colorbar;
    cb.Label.String = temp_str;
    colormap turbo;

    % Displacement vs Velocity (color = Acceleration)
    figure;
    scatter(d.disp, d.velocity, 18, d.accel, 'filled');
    grid on;
    xlabel(disp_str);
    ylabel(vel_str);
    title({ ...
        sprintf("Run %d | %s | Displacement–Velocity", runNum, freqField), ...
        valve_str ...
    }, "Interpreter","none");
    cb = colorbar;
    cb.Label.String = accel_str;
    colormap turbo;

end

function plot_processed(results, runNum, freqField)
    
%access run
    rf = sprintf("r%d", runNum);
    
    if ~isfield(results, rf)
        error("Run %d not found in results", runNum);
    end
    
    if ~isfield(results.(rf), freqField)
        error("Frequency field %s not found for run %d", freqField, runNum);
    end
    
    d = results.(rf).(freqField);
    valve = results.(rf).valving;
    valve_str = sprintf("HSC %.1f | HSR %.1f | LSC %.1f | LSR %.1f", ...
                        valve.hsc, valve.hsr, valve.lsc, valve.lsr);
    
    figure;
    hold on; grid on;
    
    % Force–Displacement pos
    subplot(2,1,1); hold on;
    fill_shaded(d.FD.pos.disp, d.FD.pos.mean, d.FD.pos.unc, [0 0.447 0.741]);
    h1 = plot(d.FD.pos.disp, d.FD.pos.mean, 'Color', [0 0.447 0.741], 'LineWidth', 1.4);
    
    % Force–Displacement neg
    fill_shaded(d.FD.neg.disp, d.FD.neg.mean, d.FD.neg.unc, [0.850 0.325 0.098]);
    h2 = plot(d.FD.neg.disp, d.FD.neg.mean, 'Color', [0.850 0.325 0.098], 'LineWidth', 1.4);
    
    xlabel("Displacement (in)");
    ylabel("Force (N)");
    title({sprintf("Run %d | %s | Force–Displacement", runNum, freqField), valve_str}, "Interpreter", "none");
    legend([h1, h2], "Accel", "Decel");
    
    % Force–Velocity accel
    subplot(2,1,2); hold on;
    fill_shaded(d.FV.pos.velocity, d.FV.pos.mean, d.FV.pos.unc, [0 0.447 0.741]);
    h3 = plot(d.FV.pos.velocity, d.FV.pos.mean, 'Color', [0 0.447 0.741], 'LineWidth', 1.4);
    
    % Force–Velocity decel
    fill_shaded(d.FV.neg.velocity, d.FV.neg.mean, d.FV.neg.unc, [0.850 0.325 0.098]);
    h4 = plot(d.FV.neg.velocity, d.FV.neg.mean, 'Color', [0.850 0.325 0.098], 'LineWidth', 1.4);
    
    % Force–Velocity all
    fill_shaded(d.FV_all.velocity, d.FV_all.mean, d.FV_all.unc, [0.466 0.674 0.188]);
    h7 = plot(d.FV_all.velocity, d.FV_all.mean, 'Color', [0.466 0.674 0.188], 'LineWidth', 1.4);
    
    % Max Velocity Force points
    mv = d.maxV;
    h5 = errorbar(mv.pos.vmax, mv.pos.mean_force, mv.pos.unc_force, ...
        'r.', 'MarkerSize', 20, 'LineWidth', 1.8);
    h6 = errorbar(mv.neg.vmax, mv.neg.mean_force, mv.neg.unc_force, ...
        'b.', 'MarkerSize', 20, 'LineWidth', 1.8);
    
    xlabel("Velocity (in/s)");
    ylabel("Force (N)");
    title({sprintf("Run %d | %s | Force–Velocity", runNum, freqField), valve_str}, "Interpreter", "none");
    legend([h3, h4, h7, h5, h6], "Accel", "Decel", "Mean-All", "+Vmax", "-Vmax");
end


function fill_shaded(x, y_mean, y_unc, facecolor)
    % Creates a filled band using mean ± uncertainty
    x = x(:);
    y_mean = y_mean(:);
    y_unc  = y_unc(:);
    
    % Upper and lower bounds
    y_upper = y_mean + y_unc;
    y_lower = y_mean - y_unc;
    
    % Polygon
    fill([x; flipud(x)], [y_upper; flipud(y_lower)], ...
         facecolor, 'FaceAlpha', 0.25, 'EdgeColor', 'none');
end