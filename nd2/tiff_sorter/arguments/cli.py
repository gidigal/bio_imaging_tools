import click
import os
from arguments.arguments import Arguments
from arguments.int_list_or_int import IntListOrInt
from gui.main_window import MainWindow
from works.single_process_orchestrator import SingleProcessOrchestrator
from works.multi_process_orchestrator import MultiProcessOrchestrator


def validate_args(gui, input_file, roi_file, matlab_output_dir, piv_params_file, calibration_file,
                  z_axis_profile_output_dir, z_axis_profile_single_output_file, z_axis_profile_plot,
                  output_dir):
    # Input file is required when gui is not selected
    if gui is False and input_file is None:
        raise click.UsageError(
            "--input_file is required when --gui is not selected"
        )

    # Make sure input file exists
    if input_file is not None and os.path.isfile(input_file) is False:
        raise FileNotFoundError(f"Missing input file {input_file}")

    # Constraint 3: pivlab options must all be provided together or not at all
    pivlab_args = [matlab_output_dir, piv_params_file, calibration_file]
    if any(pivlab_args) and not all(pivlab_args):
        raise click.UsageError(
            "Pivlab use-case requires all three options together: "
            "--matlab_output_dir, --piv_params_file, --calibration_file"
        )

    # Make sure input piv_parmas_file and calibration_file exist
    if all(pivlab_args):
        if os.path.isfile(piv_params_file) is False:
            raise FileNotFoundError(f"Missing piv_params_file {piv_params_file}")
        if os.path.isfile(calibration_file) is False:
            raise FileNotFoundError(f"Missing calibration_file {calibration_file}")

    if roi_file is not None and os.path.isfile(roi_file) is False:
        raise FileNotFoundError(f"Missing roi_file {piv_params_file}")

    # Constraint 4: z-axis-profile requires at least one output method
    is_pivlab = all(pivlab_args)
    is_z_axis = z_axis_profile_output_dir or z_axis_profile_plot
    if not is_pivlab and not is_z_axis and not output_dir:
        raise click.UsageError(
            "No use-case selected. Provide --output_dir (tiff-write), "
            "all pivlab options, or at least one of "
            "--z_axis_profile_output_dir / --z_axis_profile_plot"
        )

    # Constraint: user cannot state he wants a single output for z-axis-profile results and don't set output directory
    if z_axis_profile_single_output_file and z_axis_profile_output_dir is None:
        raise click.UsageError(
            "When setting z_axis_profile_single_output_file user must set also z_axis_profile_output_dir"
        )

    # Constraint 5: pivlab and z-axis-profile are mutually exclusive
    if is_pivlab and is_z_axis:
        raise click.UsageError(
            "--matlab_output_dir/--piv_params_file/--calibration_file (pivlab) "
            "and --z_axis_profile_output_dir/--z_axis_profile_plot (z-axis-profile) "
            "are mutually exclusive use-cases"
        )


@click.command()
@click.option('--gui', is_flag=True, help='[all] Set arguments using graphical user interface')
@click.option('--input_file', help='[tiff-write pivlab z-axis-profile] Input *.nd2 file full path name')
@click.option('--output_dir',
              help='[tiff-write] Path to directory where tiff files will be written')
@click.option('--multipoints', type=IntListOrInt(), default=None,
              help='[all] Multipoints to process. Single value (2) or list ([0,2])')
@click.option('--channels', type=IntListOrInt(), default=None,
              help='[all] Channels to process. Single value (1) or list ([0,1,3])')
@click.option('--parallel', is_flag=True, help='[all] Whether to perform parallel computation using processes '
                                               'assigned to [multipoint, channel] combinations')
@click.option('--roi_file',
              help='[all] json file with region of interest settings. '
                   'If omitted, the full image is used.')
@click.option('--matlab_output_dir',
              help='[pivlab] Path to directory where pivlab results will be written')
@click.option('--piv_params_file',
              help='[pivlab] See https://github.com/gidigal/bio_imaging_tools/blob/main/README.md#piv_parameters')
@click.option('--calibration_file',
              help='[pivlab] See https://github.com/gidigal/bio_imaging_tools/blob/main/README.md#calibration_file')
@click.option('--z_axis_profile_output_dir',
              help='[z-axis-profile] Path to directory where csv_utils files will be written')
@click.option('--z_axis_profile_single_output_file', is_flag=True,
              help='[z-axis-profile] A single csv_utils file will be created to all positions')
@click.option('--z_axis_profile_plot', is_flag=True,
              help='[z-axis-profile] Plot the z-axis-profile values to graph')
def cli(gui, input_file, multipoints, channels, parallel, roi_file, output_dir, matlab_output_dir, piv_params_file,
        calibration_file, z_axis_profile_output_dir, z_axis_profile_single_output_file, z_axis_profile_plot):
    """Process --input_file (.nd2) according to the selected use-case(s).

    \b
    Use-cases:
      gui              : --gui
      tiff-write       : --output_dir
      pivlab           : --matlab_output_dir + --piv_params_file + --calibration_file
      z-axis-profile   : --z_axis_profile_output_dir (with or without z_axis_profile_single_output_file)
                        and/or --z_axis_profile_plot

    \b
    Constraints:
      - input_file is mandatory to all use-cases but gui
      - pivlab and z-axis-profile are mutually exclusive
      - tiff-write can be combined with either of the above
      - roi_file is optional for all use-cases
    """
    validate_args(gui, input_file, roi_file, matlab_output_dir, piv_params_file, calibration_file,
                  z_axis_profile_output_dir, z_axis_profile_single_output_file, z_axis_profile_plot, output_dir)

    arguments = Arguments.instance()

    arguments.set(
        gui=gui, input_file=input_file,
        multipoints=multipoints, channels=channels,
        parallel=parallel, roi_file=roi_file,
        output_dir=output_dir,
        matlab_output_dir=matlab_output_dir, piv_params_file=piv_params_file,
        calibration_file=calibration_file,
        z_axis_profile_output_dir=z_axis_profile_output_dir,
        z_axis_profile_single_output_file=z_axis_profile_single_output_file,
        z_axis_profile_plot=z_axis_profile_plot
    )

    # Your pipeline logic here (or call run_pipeline(Arguments.instance()))
    if arguments.is_gui():
        main_window = MainWindow("ND2TiffExporter")
        main_window.start()

    orchestrator = None
    if arguments.parallel:
        orchestrator = MultiProcessOrchestrator()
    else:
        orchestrator = SingleProcessOrchestrator()
    orchestrator.run()


