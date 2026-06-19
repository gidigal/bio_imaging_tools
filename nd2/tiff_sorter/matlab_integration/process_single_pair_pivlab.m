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

    % Package results
    % Post-processing (validation + outlier replacement)
    % r parameters mirror PIVlab's default post-processing settings
    calu     = piv_params.cal_fact;
    calv     = piv_params.cal_fact;
    valid_vel = [-50; 50; -50; 50];
    do_stdev_check  = 1;
    stdthresh       = 5;
    do_local_median = 1;
    neigh_thresh    = 3;

    [u_filt, v_filt] = PIVlab_postproc(u, v, ...
        calu, calv, valid_vel, ...
        do_stdev_check, stdthresh, ...
        do_local_median, neigh_thresh);

    typevector_filt = typevector;
    typevector_filt(isnan(u_filt)) = 2;
    typevector_filt(isnan(v_filt)) = 2;
    typevector_filt(typevector == 0) = 0;

    % Interpolate missing data (inpaint_nans)
    u_filt = inpaint_nans(u_filt, 4);
    v_filt = inpaint_nans(v_filt, 4);

    % Package results
    result = struct();
    result.x = x;
    result.y = y;
    result.u = u;
    result.v = v;
    result.typevector       = typevector;
    result.u_filt           = u_filt;
    result.v_filt           = v_filt;
    result.typevector_filt  = typevector_filt;
    result.correlation_map  = corr_map;

    vel_mag = sqrt(u.^2 + v.^2);
    result.velocity_magnitude = vel_mag;
    result.mean_velocity      = mean(vel_mag(:), 'omitnan');
    result.max_velocity       = max(vel_mag(:));

    result.u_calibrated = u_filt * piv_params.cal_fact;
    result.v_calibrated = v_filt * piv_params.cal_fact;
    result.velocity_magnitude_calibrated = sqrt(result.u_calibrated.^2 + result.v_calibrated.^2);
end