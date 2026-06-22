function result = process_single_pair_pivlab(image1, image2, piv_params)
    % Convert all numeric params to double (Python passes integers as int64)
    piv_params.clahe = double(piv_params.clahe);
    piv_params.clahesize = double(piv_params.clahesize);
    piv_params.highp = double(piv_params.highp);
    piv_params.highpsize = double(piv_params.highpsize);
    piv_params.intenscap = double(piv_params.intenscap);
    piv_params.wienerwurst = double(piv_params.wienerwurst);
    piv_params.wienerwurstsize = double(piv_params.wienerwurstsize);
    piv_params.minintens = double(piv_params.minintens);
    piv_params.maxintens = double(piv_params.maxintens);
    piv_params.interrogationarea = double(piv_params.interrogationarea);
    piv_params.step = double(piv_params.step);
    piv_params.subpixfinder = double(piv_params.subpixfinder);
    piv_params.passes = double(piv_params.passes);
    piv_params.int2 = double(piv_params.int2);
    piv_params.int3 = double(piv_params.int3);
    piv_params.int4 = double(piv_params.int4);
    piv_params.repeat = double(piv_params.repeat);
    piv_params.mask_auto = double(piv_params.mask_auto);
    piv_params.do_linear_correlation = double(piv_params.do_linear_correlation);
    piv_params.repeat_last_pass = double(piv_params.repeat_last_pass);
    piv_params.delta_diff_min = double(piv_params.delta_diff_min);
    piv_params.cal_fact = double(piv_params.cal_fact);

    % Preprocess
    image1 = preproc.PIVlab_preproc(image1, [], ...
        piv_params.clahe, piv_params.clahesize, ...
        piv_params.highp, piv_params.highpsize, ...
        piv_params.intenscap, ...
        piv_params.wienerwurst, piv_params.wienerwurstsize, ...
        piv_params.minintens, piv_params.maxintens);

    image2 = preproc.PIVlab_preproc(image2, [], ...
        piv_params.clahe, piv_params.clahesize, ...
        piv_params.highp, piv_params.highpsize, ...
        piv_params.intenscap, ...
        piv_params.wienerwurst, piv_params.wienerwurstsize, ...
        piv_params.minintens, piv_params.maxintens);

    % PIV computation
    [x, y, u, v, typevector, corr_map, ~] = piv.piv_FFTmulti(image1, image2, ...
        piv_params.interrogationarea, ...
        piv_params.step, ...
        piv_params.subpixfinder, ...
        [], [], ...
        piv_params.passes, ...
        piv_params.int2, ...
        piv_params.int3, ...
        piv_params.int4, ...
        piv_params.imdeform, ...
        piv_params.repeat, ...
        piv_params.mask_auto, ...
        piv_params.do_linear_correlation, ...
        0, ...
        piv_params.repeat_last_pass, ...
        piv_params.delta_diff_min);

    % Calibration factors
    calu = piv_params.cal_fact;
    calv = piv_params.cal_fact;

    % Save raw unclamped u/v for storage (matches PIVlab convention)
    u_raw = u;
    v_raw = v;

    % Hard clamp before post-processing to prevent spurious vectors from
    % contaminating the median filter neighborhood (cascade rejection).
    % Replace px_limit with a physically-motivated value once confirmed
    % with the researcher (current: 10 px/frame heuristic).
    px_limit = 10;
    u(abs(u) > px_limit) = NaN;
    v(abs(v) > px_limit) = NaN;

    % Post-processing using simple median (matches her PIVlab version).
    % Her PIVlab uses the old simple median; our installed version uses
    % the newer Westerweel & Scarano normalized median which is more
    % aggressive. We replicate her exact algorithm inline to match results.
    u_filt = u;
    v_filt = v;

    % Step 1: velocity limits (in physical units via cal_fact)
    u_filt(u_filt * calu < -50) = NaN; u_filt(u_filt * calu > 50) = NaN;
    v_filt(u_filt * calu < -50) = NaN; v_filt(u_filt * calu > 50) = NaN;
    v_filt(v_filt * calv < -50) = NaN; v_filt(v_filt * calv > 50) = NaN;
    u_filt(v_filt * calv < -50) = NaN; u_filt(v_filt * calv > 50) = NaN;

    % Step 2: simple local median check (matches her older PIVlab version)
    neigh_filt = medfilt2(u_filt, [3,3], 'symmetric');
    try
        neigh_filt = misc.inpaint_nans(neigh_filt);
    catch
        neigh_filt = NaN(size(neigh_filt));
    end
    neigh_filt = abs(neigh_filt - u_filt);
    u_filt(neigh_filt > 3) = NaN;

    neigh_filt = medfilt2(v_filt, [3,3], 'symmetric');
    try
        neigh_filt = misc.inpaint_nans(neigh_filt);
    catch
        neigh_filt = NaN(size(neigh_filt));
    end
    neigh_filt = abs(neigh_filt - v_filt);
    v_filt(neigh_filt > 3) = NaN;

    % Step 3: stdev check
    meanu = mean(u_filt(:), 'omitnan');
    std2u = std(u_filt(:), 'omitnan');
    meanv = mean(v_filt(:), 'omitnan');
    std2v = std(v_filt(:), 'omitnan');
    u_filt(u_filt < meanu - 5*std2u) = NaN;
    u_filt(u_filt > meanu + 5*std2u) = NaN;
    v_filt(v_filt < meanv - 5*std2v) = NaN;
    v_filt(v_filt > meanv + 5*std2v) = NaN;

    % Cross-NaN: if either component is NaN, set both to NaN
    u_filt(isnan(v_filt)) = NaN;
    v_filt(isnan(u_filt)) = NaN;

    % Build typevector_filt (before inpainting, while NaNs still mark outliers)
    typevector_filt = typevector;
    typevector_filt(isnan(u_filt)) = 2;
    typevector_filt(isnan(v_filt)) = 2;
    typevector_filt(typevector == 0) = 0;

    % Interpolate missing data using same function as her PIVlab version
    u_filt = misc.inpaint_nans(u_filt);
    v_filt = misc.inpaint_nans(v_filt);

    % Package results
    result = struct();
    result.x               = x;
    result.y               = y;
    result.u               = u_raw;   % raw unclamped, matches PIVlab convention
    result.v               = v_raw;
    result.typevector      = typevector;
    result.u_filt          = u_filt;
    result.v_filt          = v_filt;
    result.typevector_filt = typevector_filt;
    result.correlation_map = corr_map;

    vel_mag = sqrt(u_raw.^2 + v_raw.^2);
    result.velocity_magnitude = vel_mag;
    result.mean_velocity      = mean(vel_mag(:), 'omitnan');
    result.max_velocity       = max(vel_mag(:));

    result.u_calibrated                  = u_filt * piv_params.cal_fact;
    result.v_calibrated                  = v_filt * piv_params.cal_fact;
    result.velocity_magnitude_calibrated = sqrt(result.u_calibrated.^2 + result.v_calibrated.^2);
end