# bio_imaging_tools
Tools to support research using microscope images. Currently, a main tool is developed to address automations from ND2 (Nikon's Microscope format) files. Code is written mainly in Python, with small Matlab addition for Pivlab integration.

## split_channels - name under construction
This script supports 3 automations from ND2 files:
1. tiff-write - Extracting tiff files - organized in folders per <multipoint, channel> combinations.
2. pivlab - Calculating particle velocity using [Pivlab](https://www.mathworks.com/matlabcentral/fileexchange/27659-pivlab-particle-image-velocimetry-piv-tool-with-gui).
3. z-axis-profile - Calculating average signal intensity (z-axis-profile in [Fiji](https://imagej.net/software/fiji/))  
  
The script currently supports command line arguments only.

### Supported arguments
| Argument                            | Type   | automation\s   | Required   | Description                                                                                             |  
|-------------------------------------|--------|----------------|------------|---------------------------------------------------------------------------------------------------------|  
| --input_file                        | String | all            | ✅         | Input *.nd2 file full path name                                                                         |  
| --output_dir                        | String | tiff-write     | ✅         | Path to folder where tiff files will be written                                                         |  
| --multipoints                       | String | all            | Optional   | Multipoints to process. Single value (2) or list ([0,2])                                                |  
| --channels                          | String | all            | Optional   | Channels to process. Single value (1) or list ([0,1,3])                                                 |
| --parallel                          | None   | all            | Optional   | Whether to perform parallel computation using processes assigned to [multipoint, channel] combinations  |  
| --roi_file                          | String | all            | Optional   | json file with region of interest settings                                                              |  
| --matlab_output_dir                 | String | pivlab         | ✅         | Path to folder where pivlab results will be written                                                     |  
| --piv_params_file                   | String | pivlab         | ✅         | Path to json file with pivlab parameters. See more below                                                |  
| --calibration_file                  | String | pivlab         | ✅         | Path to json file with calibration values. See more below                                               |  
| --z_axis_profile_output_dir         | String | z-axis-profile | ✅         | Path to folder where csv files with results will be written                                             |  
| --z_axis_profile_single_output_file | None   | z-axis-profile | Optional   | Whether to create single csv file for all multipoints                                                   |  
| --z_axis_profile_plot               | None   | z-axis-profile | Optional   | Plot the z-axis-profile values to graph                                                                 |  

### Examples for running split_channels script:  
```
python split_channels.py --input_file="D:\temp\a.nd2" --output_dir="D:\temp\output" --multipoints=[0,1] --parallel  
```
  
Extract the tiffs from D:\temp\a.nd2 file into requested output D:\temp\output directory, handling the first and second multipoints only, employing parallel approach (each multipoint will be dealt in a different CPU core).  
Please note: Using double quotes for paths is important when there are spaces in the path.  
```
python split_channels.py --input_file="D:\temp\a.nd2" --matlab_output_dir="D:\temp\output" --piv_params_file="D:\temp\piv.json" --calibration_file="D:\temp\calibration.json"  
```  
Calculate particle velocity for all multipoints and channels for input D:\temp\a.nd2 file, generate *.mat files (for each multipoint) into requested output directory D:\temp\output, using required setting files for pivlab and calibration.  
Please note: Though it is possible to spread the work on multipoints using --parallel, since Pivlab is already making use of Matlab's parallelization package (if exists), it is in question how effective it is to use this argument in Pivlab scenario.
  
```
python split_channels.py --input_file="D:\temp\a.nd2" --z_axis_profile_output_dir="D:\temp\output" --z_axis_profile_single_output_file --z_axis_profile_plot 
```
Calculate average signal intensity for input D:\temp\a.nd2 file, output the results to D:\temp\output, generates results to a single csv file and plot the results graphically in addition to generated csv file.    

## Calibration file
The `--calibration_file` argument expects a JSON file with the following fields:  
"cal_formula" field defines which calibration formula is used:  
For "pixel_size" value, the formula is pixel_size_um / mag / time_step  
For "fov" (field of view) value, the formula is fov_um / image_width_pixels / mag / time_step

| Field                | Type  | Required  | Description                               |  
|----------------------|-------|-----------|-------------------------------------------|  
| `time_step`          | int   | ✅        | interval in seconds between frames        |  
| `pixel_size_um`      | float | ✅        | the size of pixel in micrometers          |  
| `mag`                | float | ✅        | the value of mag knob in Nikon microscope |  
| `fov_um`             | float | ✅        | field of view width in µm                 |  
| `image_width_pixels` | int   | ✅        | the width of image in pixels              |  


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


## Installation instructions for Windows
Required applications: Git and Python
1. Install [Git for windows](https://git-scm.com/install/windows)
2. Open command prompt with administrator rights (right click and select "Run as administrator" and click "Yes" for the questions)
3. Clone the repository:  
git clone https://github.com/gidigal/bio_imaging_tools.git
4. Install Python. Your Python version is dependent on [Matlab version and its supported python versions for matlab engine](https://www.mathworks.com/support/requirements/python-compatibility.html)
5. Create Python virtual environment  
python -m venv venv
6. Activate the virtual environment  
venv\Scripts\activate.bat
7. Install bio_imaging_tools packages, defined in nd2/tiff_sorter/scripts/requirements.txt  
pip install -r <path to bio_imaging_tools\nd2\tiff_sorter\scripts\requirements.txt file>
8. Open matlab and run "matlabroot" from its terminal to find Matlab's installation location.
9. Change directory to <Matlab root>\extern\engines\python  
cd <Matlab root>\extern\engines\python
10. Install Matlab engine (MATLAB R2022b and Newer)  
python -m pip install .  
(MATLAB R2022a and Older))  
python setup.py install
11. Find Pivlab's installation directory by entering "which PIVlab_GUI.m" in Matlab's terminal.
12. Open bio_imaging_tools\nd2\tiff_sorter\settings.json in text editor.
13. Change "pivlab_root" to point to Pivlab's path. Use "/" as path separator or "\\".










