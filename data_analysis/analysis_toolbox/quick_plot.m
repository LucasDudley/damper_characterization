clear, clc
s = settings;
s.matlab.appearance.figure.GraphicsTheme.TemporaryValue= 'light'; %set figure background to light

%load data
load("G:\.shortcut-targets-by-id\1vCayBu0JWPEaCjSa5KhpGMqdHFvsMCFY\Senior_Design\Data Collection\matfiles\valving_test_data.mat")
load("G:\.shortcut-targets-by-id\1vCayBu0JWPEaCjSa5KhpGMqdHFvsMCFY\Senior_Design\Data Collection\matfiles\valving_results_data.mat")
%% plot checks
close all
%f0_211, f0_421, f0_632, f0_842, f1_053

test = 4;
freq = "f1_053";

% plot test_data
plot_raw(test_data, test, freq);

% plot results
plot_processed(results, test, freq);


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
    % Access run
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
    
    % --- FORCE-DISPLACEMENT ---
    figure('Name', sprintf('Run %d | %s | Force-Displacement', runNum, freqField));
    hold on; grid on;
    
    % Force–Displacement pos
    fill_shaded(d.FD.pos.disp, d.FD.pos.mean, d.FD.pos.unc, [0 0.447 0.741]);
    h1 = plot(d.FD.pos.disp, d.FD.pos.mean, 'Color', [0 0.447 0.741], 'LineWidth', 1.4);
    % Force–Displacement neg
    fill_shaded(d.FD.neg.disp, d.FD.neg.mean, d.FD.neg.unc, [0.850 0.325 0.098]);
    h2 = plot(d.FD.neg.disp, d.FD.neg.mean, 'Color', [0.850 0.325 0.098], 'LineWidth', 1.4);
    
    xlabel("Displacement (in)");
    ylabel("Force (N)");
    title({sprintf("Run %d | %s | Force–Displacement", runNum, freqField), valve_str}, ...
          "Interpreter", "none");
    legend([h1, h2], "Accel", "Decel");
    
    % --- FORCE-VELOCITY ---
    figure('Name', sprintf('Run %d | %s | Force-Velocity', runNum, freqField));
    hold on; grid on;
    
    % Force–Velocity accel
    fill_shaded(d.FV.pos.velocity, d.FV.pos.mean, d.FV.pos.unc, [0 0.447 0.741]);
    h3 = plot(d.FV.pos.velocity, d.FV.pos.mean, 'Color', [0 0.447 0.741], 'LineWidth', 1.4);
    % Force–Velocity decel
    fill_shaded(d.FV.neg.velocity, d.FV.neg.mean, d.FV.neg.unc, [0.850 0.325 0.098]);
    h4 = plot(d.FV.neg.velocity, d.FV.neg.mean, 'Color', [0.850 0.325 0.098], 'LineWidth', 1.4);
    % Force–Velocity all
    fill_shaded(d.FV_all.velocity, d.FV_all.mean, d.FV_all.unc, [0.466 0.674 0.188]);
    h7 = plot(d.FV_all.velocity, d.FV_all.mean, 'Color', [0.466 0.674 0.188], 'LineWidth', 1.4);
    
    % --- Polynomial fits (Existing logic) ---
    h_poly = [];
    if isfield(d, 'FV_fit')
        % Positive polynomial fit → only for v > 0
        if isfield(d.FV_fit, 'pos') && ~isempty(d.FV_fit.pos.coeffs)
            v = d.FV_all.velocity(:);
            mask_pos = v > 0;
            if any(mask_pos)
                v_fit_pos = linspace(min(v(mask_pos)), max(v(mask_pos)), 400)';
                f_fit_pos = polyval(d.FV_fit.pos.coeffs, v_fit_pos);
                h_poly(1) = plot(v_fit_pos, f_fit_pos, '--', 'Color', [0 0.2 0.4], 'LineWidth', 2);
            end
        end
        % Negative polynomial fit → only for v < 0
        if isfield(d.FV_fit, 'neg') && ~isempty(d.FV_fit.neg.coeffs)
            v = d.FV_all.velocity(:);
            mask_neg = v < 0;
            if any(mask_neg)
                v_fit_neg = linspace(min(v(mask_neg)), max(v(mask_neg)), 400)';
                f_fit_neg = polyval(d.FV_fit.neg.coeffs, v_fit_neg);
                h_poly(2) = plot(v_fit_neg, f_fit_neg, '--', 'Color', [0.5 0.1 0], 'LineWidth', 2);
            end
        end
    end

    % --- Piecewise Linear fits ---
    h_pw = [];
    if isfield(results.(rf), 'PW_fit_all')
        PW = results.(rf).PW_fit_all;
        
        % Compression (Positive Velocity) PW Fit
        if isfield(PW, 'pos') && ~isnan(PW.pos.C_LS)
            params = PW.pos;
            % The fit stores v_data and f_data (not v_used)
            % Generate velocity points from 0 to max positive velocity
            v_max_pos = max(params.v_data);
            v_plot_pos = linspace(0, v_max_pos, 400)';
            % Calculate force using absolute velocity
            f_pw_pos = calculate_pw_force(abs(v_plot_pos), params);
            h_pw(1) = plot(v_plot_pos, f_pw_pos, '-.', 'Color', [0 0.8 0], 'LineWidth', 2);
        end

        % Rebound (Negative Velocity) PW Fit
        if isfield(PW, 'neg') && ~isnan(PW.neg.C_LS)
            params = PW.neg;
            % Generate velocity points from min negative velocity to 0
            v_min_neg = min(params.v_data);
            v_plot_neg = linspace(v_min_neg, 0, 400)';
            % Calculate force using absolute velocity
            f_pw_neg = calculate_pw_force(abs(v_plot_neg), params);
            h_pw(2) = plot(v_plot_neg, f_pw_neg, '-.', 'Color', [0.8 0 0.8], 'LineWidth', 2);
        end
    end
    
    % Max Velocity Force points
    mv = d.maxV;
    h5 = errorbar(mv.pos.vmax, mv.pos.mean_force, mv.pos.unc_force, ...
        'r.', 'MarkerSize', 20, 'LineWidth', 1.8);
    h6 = errorbar(mv.neg.vmax, mv.neg.mean_force, mv.neg.unc_force, ...
        'b.', 'MarkerSize', 20, 'LineWidth', 1.8);
    
    xlabel("Velocity (in/s)");
    ylabel("Force (N)");
    title({sprintf("Run %d | %s | Force–Velocity", runNum, freqField), valve_str}, ...
          "Interpreter", "none");
    
    % --- Update Legend ---
    h_all = [h3, h4, h7, h_poly, h_pw, h5, h6];
    legend_str = ["Accel", "Decel", "Mean-All", "Poly-Fit-Pos", "Poly-Fit-Neg", "PW-Fit-Pos", "PW-Fit-Neg", "+Vmax", "-Vmax"];

    % Filter the legend handles and strings to only include those that were plotted
    valid_h = h_all(ishandle(h_all));
    valid_str = legend_str(ishandle(h_all));
    
    legend(valid_h, valid_str, 'Location', 'best');
end

function F_out = calculate_pw_force(V_in, params)
% CALCULATE_PW_FORCE Calculates the force based on the 4-parameter piecewise model.
% V_in must be the magnitude (abs) of velocity.
    
    F0 = params.F0;
    C_LS = params.C_LS;
    C_HS = params.C_HS;
    v_knee = params.v_knee;
    
    % Apply the model definition
    
    % 1. Low-Speed Damping component
    F_LS = C_LS * min(V_in, v_knee);
    
    % 2. High-Speed Damping component
    F_HS = C_HS * max(0, V_in - v_knee);
    
    % 3. Total Force
    F_out = F0 + F_LS + F_HS;
end

function fill_shaded(x, y_mean, y_unc, facecolor)

    % Creates a filled band using mean ± uncertainty
    x = x(:);
    y_mean = y_mean(:);
    y_unc  = y_unc(:);

    % Upper and lower bounds
    y_upper = y_mean + y_unc;
    y_lower = y_mean - y_unc;

    fill([x; flipud(x)], [y_upper; flipud(y_lower)], ...
         facecolor, 'FaceAlpha', 0.25, 'EdgeColor', 'none');
end

