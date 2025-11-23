clear, clc, close all

% load test data
load("G:\.shortcut-targets-by-id\1vCayBu0JWPEaCjSa5KhpGMqdHFvsMCFY\Senior_Design\Data Collection\matfiles\valving_test_data.mat")

%ouput
out_path = "G:\.shortcut-targets-by-id\1vCayBu0JWPEaCjSa5KhpGMqdHFvsMCFY\Senior_Design\Data Collection\matfiles";
out_name = "valving_results_data.mat";

% Configurable bin counts
Nbins_FD = 300;
Nbins_FV = 200;
Nbins_FV_all = 200;
max_vel_bin_width = 0.25;

%% processing
run_fields = fieldnames(test_data);
% Only keep "rX" (avoid run_guide)
run_fields = run_fields( ~cellfun(@isempty, regexp(run_fields, "^r\d+$")) );
results = struct();

for ri = 1:numel(run_fields)
    rf = run_fields{ri};
    results.(rf).valving = test_data.(rf).valving;
    freq_fields = fieldnames(test_data.(rf));
    freq_fields = freq_fields(~strcmp(freq_fields,"valving"));
    
    for fi = 1:numel(freq_fields)
        ff = freq_fields{fi};
        d = test_data.(rf).(ff);
        v = d.velocity(:);
        x = d.disp(:);
        f = d.force(:);
        a = d.accel(:);
        
        % split the data by accel & deccel
        accel_mask = a > 0;
        decel_mask = a < 0;
        fd_pos_mask = v > 0;   % positive velocity → "accel"
        fd_neg_mask = v < 0;   % negative velocity → "decel"
        
        % FD (velocity sign) - uses Nbins_FD
        [x_bins, fd_mean_pos, fd_unc_pos] = bin_profile(x(fd_pos_mask), f(fd_pos_mask), Nbins_FD);
        [~,      fd_mean_neg, fd_unc_neg] = bin_profile(x(fd_neg_mask), f(fd_neg_mask), Nbins_FD);
        
        results.(rf).(ff).FD.pos.disp = x_bins;
        results.(rf).(ff).FD.pos.mean = fd_mean_pos;
        results.(rf).(ff).FD.pos.unc  = fd_unc_pos;
        
        results.(rf).(ff).FD.neg.disp = x_bins;
        results.(rf).(ff).FD.neg.mean = fd_mean_neg;
        results.(rf).(ff).FD.neg.unc  = fd_unc_neg;
        
        % FV (split by accel sign) - uses Nbins_FV
        [v_bins, fv_mean_acc, fv_unc_acc] = bin_profile(v(accel_mask), f(accel_mask), Nbins_FV);
        [~,      fv_mean_dec, fv_unc_dec] = bin_profile(v(decel_mask), f(decel_mask), Nbins_FV);
        
        results.(rf).(ff).FV.pos.velocity = v_bins;
        results.(rf).(ff).FV.pos.mean     = fv_mean_acc;
        results.(rf).(ff).FV.pos.unc      = fv_unc_acc;
        
        results.(rf).(ff).FV.neg.velocity = v_bins;
        results.(rf).(ff).FV.neg.mean     = fv_mean_dec;
        results.(rf).(ff).FV.neg.unc      = fv_unc_dec;
        
        % FV_all - uses Nbins_FV_all
        [v_bins2, fv_mean_all, fv_unc_all] = bin_profile(v, f, Nbins_FV_all);
        
        results.(rf).(ff).FV_all.velocity = v_bins2;
        results.(rf).(ff).FV_all.mean     = fv_mean_all;
        results.(rf).(ff).FV_all.unc      = fv_unc_all;
        
        % Max velocity region
        vmax_pos = max(v);
        vmax_neg = min(v);
        pos_mask = v >= (vmax_pos - max_vel_bin_width) & v <= (vmax_pos + max_vel_bin_width);
        neg_mask = v >= (vmax_neg - max_vel_bin_width) & v <= (vmax_neg + max_vel_bin_width);
        
        results.(rf).(ff).maxV.pos.mean_force = mean(f(pos_mask));
        results.(rf).(ff).maxV.pos.unc_force  = uncertainty_tn(f(pos_mask));
        results.(rf).(ff).maxV.pos.vmax       = vmax_pos;
        
        results.(rf).(ff).maxV.neg.mean_force = mean(f(neg_mask));
        results.(rf).(ff).maxV.neg.unc_force  = uncertainty_tn(f(neg_mask));
        results.(rf).(ff).maxV.neg.vmax       = vmax_neg;
    end
end

save(fullfile(out_path, out_name), "results");

function [bin_centers, mean_y, unc_y] = bin_profile(x, y, Nbins)
    edges = linspace(min(x), max(x), Nbins+1);
    bin_centers = 0.5 * (edges(1:end-1) + edges(2:end));
    
    % Force column vectors
    bin_centers = bin_centers(:);
    mean_y      = zeros(Nbins,1);
    unc_y       = zeros(Nbins,1);
    
    for b = 1:Nbins
        mask = x >= edges(b) & x < edges(b+1);
        if any(mask)
            mean_y(b) = mean(y(mask));
            unc_y(b)  = uncertainty_tn(y(mask));
        else
            mean_y(b) = NaN;
            unc_y(b)  = NaN;
        end
    end
end

function unc = uncertainty_tn(data)
    % Calculate uncertainty using t-distribution
    % Returns the standard error of the mean multiplied by t-critical value
    % for 95% confidence interval
    
    n = numel(data);
    
    if n <= 1
        unc = NaN;
        return;
    end
    
    % Standard error of the mean
    sem = std(data) / sqrt(n);
    dof = n - 1;
    
    % t-critical value for 99% confidence (two-tailed)
    t_crit = tinv(0.995, dof);
    
    % Uncertainty
    unc = t_crit * sem;
end