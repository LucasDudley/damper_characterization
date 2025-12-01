function [hsc_ohlins, lsc_ohlins, hsr_ohlins, lsr_ohlins] = naming_swap(hsc_ref, lsc_ref, hsr_ref, lsr_ref)
    %input AME441 naming convention -> Ohlins naming convention

    % low speed naming is the same:
    lsc_ohlins = lsc_ref;
    lsr_ohlins = lsr_ref;

    % high speed naming is flipped:
    slope_comp = (4.3 - 0) / (0 -5.25); %output max - min / input max - min
    offset_comp = 4.3;

    slope_rebound = (4.3 - 0) / (0 -4.75); %output max - min / input max - min
    offset_rebound = 4.3;

    hsc_ohlins = offset_comp + slope_comp*hsc_ref;
    hsr_ohlins = offset_rebound + slope_rebound*hsr_ref;

end