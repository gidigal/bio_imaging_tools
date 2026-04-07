# bio_imaging_tools
tools to support reasearch using microscope images

## Calibration file
The `--calibration_file` argument expects a JSON file with the following fields:

| Field          | Type   | Required | Description                               |
|----------------|--------|----------|-------------------------------------------|
| `time_step`    | int    | ✅       | interval in seconds between frames        |
| `pixel_size_um`| float  | ✅       | the size of pixel in micrometers          |
| `mag`          | float  | ✅       | the value of mag knob in Nikon microscope |

All fields are required.

## PIV Parameters
The `--piv_params_file` argument expects a JSON file.
For full PIVlab documentation, see:
- [PIVlab GitHub Wiki](https://github.com/Shrediquette/PIVlab/wiki)
- [PIVlab source with inline comments (Accuracy.m)](https://github.com/Shrediquette/PIVlab/blob/main/help/Accuracy.m)

Image Pre-processing (passed to PIVlab_preproc):

| JSON field        | PIVlab name       | Description                                             |
|-------------------|-------------------|---------------------------------------------------------|
| `clahe`           | CLAHE             | 1 = enable, 0 = disable                                 |
| `clahesize`       | CLAHE size        | CLAHE window size (px)                                  |
| `highp`           | Highpass          | 1 = enable highpass filter, 0 = disable                 |
| `highpsize`       | Highpass size     | Highpass kernel size                                    |
| `intenscap`       | Clipping          | 1 = enable intensity clipping, 0 = disable              |
| `wienerwurst`     | Wiener            | 1 = enable Wiener2 adaptive denoise filter, 0 = disable |
| `wienerwurstsize` | Wiener size       | Wiener2 window size                                     |
| `minintens`       | Minimum intensity | Min intensity of input image (0 = no change)            |
| `maxintens`       | Maximum intensity | Max intensity of input image (1 = no change)            |

CLAHE is enabled by default and locally enhances contrast in images. The other filters are optional and can be explored via tooltip hints in the GUI.

PIV Analysis (passed to piv_FFTmulti):

| JSON field              | Description                                                                                                                   |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| `interrogationarea`     | Size (px) of the first-pass interrogation window. Larger = better SNR but lower resolution. Recommended starting point: 128px |
| `step`                  | Grid spacing between interrogation areas (px). Controls vector density                                                        |
| `passes`                | Number of multi-pass iterations. More passes = better accuracy but slower                                                     |
| `int2`, `int3`, `int4`  | Interrogation area sizes for passes 2, 3, and 4 — should decrease progressively (e.g. 64, 32, 16)                             |
| `subpixfinder`          | Sub-pixel estimator: 1 = 1D Gaussian, 2 = 2D Gaussian (from source: SUBPIXGAUSS vs SUBPIX2DGAUSS)                             |
| `imdeform`              |  Window deformation method: "*linear" or "*spline"                                                                            |
| `repeat`                | Enable repeated correlation (0/1) — part of "extreme" robustness mode                                                         |
| `repeat_last_pass`      | Repeat the last pass (0/1)                                                                                                    |
| `do_linear_correlation` | Use linear (non-circular) cross-correlation (0/1) — part of "high" robustness mode                                            |
| `mask_auto`             | Enable automatic masking (0/1)                                                                                                |
| `delta_diff_min`        | Minimum displacement difference to stop iterating between passes                                                              |










