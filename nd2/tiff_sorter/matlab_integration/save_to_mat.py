# save_to_mat.py
"""
Save PIV results to MATLAB .mat files
"""

import scipy.io
import numpy as np


def _make_col_cell(num_pairs):
    """
    Create a (num_pairs, 1) object array — matches PIVlab's column-vector cell layout.
    """
    arr = np.empty((num_pairs, 1), dtype=object)
    return arr


def _build_pivlab_param_struct(piv_params):
    """
    Build the three PIVlab parameter structs (p, s, r) that PIVlab saves alongside results.
    These allow anyone reopening the .mat file to know exactly what settings were used.

    p  — preprocessing parameters
    s  — PIV / interrogation parameters
    r  — post-processing / validation parameters
    """
    cal = piv_params.get('cal_fact', 1.0)

    p = np.empty((10, 2), dtype=object)
    p[0] = ['ROI', np.array([])]
    p[1] = ['CLAHE', np.array([[int(piv_params.get('clahe', 1))]])]
    p[2] = ['CLAHE size', np.array([[int(piv_params.get('clahesize', 64))]])]
    p[3] = ['Highpass', np.array([[int(piv_params.get('highp', 0))]])]
    p[4] = ['Highpass size', np.array([[int(piv_params.get('highpsize', 15))]])]
    p[5] = ['Clipping', np.array([[int(piv_params.get('intenscap', 0))]])]
    p[6] = ['Wiener', np.array([[int(piv_params.get('wienerwurst', 0))]])]
    p[7] = ['Wiener size', np.array([[int(piv_params.get('wienerwurstsize', 3))]])]
    p[8] = ['Minimum intensity', np.array([[float(piv_params.get('minintens', 0))]])]
    p[9] = ['Maximum intensity', np.array([[float(piv_params.get('maxintens', 1))]])]

    passes = int(piv_params.get('passes', 3))
    s = np.empty((15, 2), dtype=object)
    s[0] = ['Int. area 1', np.array([[int(piv_params.get('interrogationarea', 256))]])]
    s[1] = ['Step size 1', np.array([[int(piv_params.get('step', 64))]])]
    s[2] = ['Subpix. finder', np.array([[int(piv_params.get('subpixfinder', 1))]])]
    s[3] = ['Mask', np.array([])]
    s[4] = ['ROI', np.array([])]
    s[5] = ['Nr. of passes', np.array([[passes]])]
    s[6] = ['Int. area 2', np.array([[int(piv_params.get('int2', 128))]])]
    s[7] = ['Int. area 3', np.array([[int(piv_params.get('int3', 64))]])]
    s[8] = ['Int. area 4', np.array([[int(piv_params.get('int4', 32))]])]
    s[9] = ['Window deformation', np.array([piv_params.get('imdeform', '*linear')])]
    s[10] = ['Repeated Correlation', np.array([[int(piv_params.get('repeat', 0))]])]
    s[11] = ['Disable Autocorrelation', np.array([[0]])]
    s[12] = ['Correlation style', np.array([[int(piv_params.get('do_linear_correlation', 0))]])]
    s[13] = ['Repeat last pass', np.array([[int(piv_params.get('repeat_last_pass', 0))]])]
    s[14] = ['Last pass quality slope', np.array([[float(piv_params.get('delta_diff_min', 0.025))]])]

    r = np.empty((7, 2), dtype=object)
    r[0] = ['Calibration factor, 1 for uncalibrated data', np.array([[float(cal)]])]
    r[1] = ['Calibration factor, 1 for uncalibrated data', np.array([[float(cal)]])]
    r[2] = ['Valid velocities [u_min; u_max; v_min; v_max]',
            np.array([[-50], [50], [-50], [50]], dtype=float)]
    r[3] = ['Stdev check?', np.array([[1]])]
    r[4] = ['Stdev threshold', np.array([[5.0]])]
    r[5] = ['Local median check?', np.array([[1]])]
    r[6] = ['Local median threshold', np.array([[3.0]])]

    return p, s, r


def save_results_to_mat(results, output_file, piv_params=None, image_filenames=None):
    """
    Save PIV results to a .mat file compatible with PIVlab's own output format.

    Parameters:
    -----------
    results : list of dict
        List of PIV results from process_image_generator.
        Each dict must contain: x, y, u, v, typevector, correlation_map,
        mean_velocity, max_velocity, pair_index.
        Optionally: u_filt, v_filt, typevector_filt (if post-processing was applied).
    output_file : str
        Output .mat file path.
    piv_params : dict or None
        PIV parameter dict used during processing. Used to populate the
        PIVlab-style p/s/r parameter structs in the output file.
    image_filenames : list of str or None
        Ordered list of all image filenames (tif/png/etc.) that were processed.
        Used to populate slicedfilename1 / slicedfilename2 per pair.
        If None, filenames are left empty.
    """

    if piv_params is None:
        piv_params = {}

    num_pairs = len(results)

    # ------------------------------------------------------------------- #
    # Per-frame cell arrays — all stored as (num_pairs, 1) column vectors #
    # to match PIVlab's layout                                            #
    # ------------------------------------------------------------------- #
    x_cells = _make_col_cell(num_pairs)
    y_cells = _make_col_cell(num_pairs)
    u_cells = _make_col_cell(num_pairs)
    v_cells = _make_col_cell(num_pairs)
    typevector_cells = _make_col_cell(num_pairs)
    u_filt_cells = _make_col_cell(num_pairs)
    v_filt_cells = _make_col_cell(num_pairs)
    tv_filt_cells = _make_col_cell(num_pairs)
    corr_map_cells = _make_col_cell(num_pairs)
    vel_mag_cells = _make_col_cell(num_pairs)  # your extra, kept for convenience
    fname1_cells = _make_col_cell(num_pairs)
    fname2_cells = _make_col_cell(num_pairs)

    for i, result in enumerate(results):
        x_cells[i, 0] = result['x']
        y_cells[i, 0] = result['y']
        u_cells[i, 0] = result['u']
        v_cells[i, 0] = result['v']
        typevector_cells[i, 0] = result['typevector']
        corr_map_cells[i, 0] = result['correlation_map']
        vel_mag_cells[i, 0] = result['velocity_magnitude']

        # Filtered fields: use dedicated filtered arrays if the pipeline
        # produced them; otherwise fall back to the raw arrays (meaning
        # no filtering/outlier replacement was applied).
        u_filt_cells[i, 0] = result.get('u_filt', result['u'])
        v_filt_cells[i, 0] = result.get('v_filt', result['v'])
        tv_filt_cells[i, 0] = result.get('typevector_filt', result['typevector'])

        # Paired image filenames
        if image_filenames is not None:
            idx = result['pair_index']
            fname1_cells[i, 0] = [image_filenames[idx]]
            fname2_cells[i, 0] = [image_filenames[idx + 1]]
        else:
            fname1_cells[i, 0] = ['']
            fname2_cells[i, 0] = ['']

    # ------------------------------------------------------------------ #
    # Scalar metadata                                                      #
    # ------------------------------------------------------------------ #
    cal_fact = float(piv_params.get('cal_fact', 1.0))
    time_step = int(piv_params.get('time_step', 1))

    # ------------------------------------------------------------------ #
    # PIVlab parameter structs                                             #
    # ------------------------------------------------------------------ #
    p, s, r = _build_pivlab_param_struct(piv_params)

    # ------------------------------------------------------------------ #
    # Assemble mat_data dict                                               #
    # ------------------------------------------------------------------ #
    mat_data = {
        # --- PIVlab-compatible fields ---
        'x': x_cells,
        'y': y_cells,
        'u': u_cells,
        'v': v_cells,
        'typevector': typevector_cells,
        'u_filt': u_filt_cells,
        'v_filt': v_filt_cells,
        'typevector_filt': tv_filt_cells,
        'correlation_map': corr_map_cells,
        'slicedfilename1': fname1_cells,
        'slicedfilename2': fname2_cells,
        'cal_fact': np.array([[cal_fact]]),
        'time_step': np.array([[time_step]], dtype=np.uint8),
        'interpolate_missing_data': np.array([[0]], dtype=np.uint8),
        'pairwise': np.array([[0]], dtype=np.uint8),
        'p': p,
        's': s,
        'r': r,

        # --- your extras (not in PIVlab output, but useful) ---
        'num_pairs': num_pairs,
        'mean_velocity': np.array([r_['mean_velocity'] for r_ in results]),
        'max_velocity': np.array([r_['max_velocity'] for r_ in results]),
        'pair_indices': np.array([r_['pair_index'] for r_ in results]),
        'velocity_magnitude': vel_mag_cells,
    }

    scipy.io.savemat(output_file, mat_data)
    print(f"Results saved to {output_file}")
    print(f"  {num_pairs} velocity fields")
    print(f"  Mean velocity: {np.mean(mat_data['mean_velocity']):.2f} px/frame")