import sys
from gui.main_window import MainWindow
from nd2_tools.nd2_manager import ND2Manager
import os.path
from works.single_process_orchestrator import SingleProcessOrchestrator
from works.multi_process_orchestrator import MultiProcessOrchestrator
import json
import ast
import numbers

def show_ui(args):
    return len(args) > 0 and args[0] == '-ui'


def parse_args(args):
    res = {}
    for i in range(len(args)):
        if args[i] == '-input_file' and i < len(args) - 1:
            res['input_file'] = args[i + 1]
        if args[i] == '-output_dir' and i < len(args) - 1:
            res['output_dir'] = args[i + 1]
        if args[i] == '-matlab_output_dir' and i < len(args) - 1:
            res['matlab_output_dir'] = args[i + 1]
        if args[i] == '-calibration_file' and i < len(args) - 1:
            res['calibration_file'] = args[i + 1]
        if args[i] == '-piv_params_file' and i < len(args) - 1:
            res['piv_params_file'] = args[i + 1]
        if args[i] == '-roi_file' and i < len(args) - 1:
            res['roi_file'] = args[i + 1]
        if args[i] == '-z_axis_profile_output_dir' and i < len(args) - 1:
            res['z_axis_profile_output_dir'] = args[i + 1]
        if args[i] == '-z_axis_profile_plot':
            res['z_axis_profile_plot'] = True
        if args[i].startswith("-multipoints="):
            multipoints = ast.literal_eval(args[i].split('=')[1])
            if isinstance(multipoints, numbers.Number):
                res['multipoints'] = [multipoints]
            else:
                res['multipoints'] = multipoints
        if args[i].startswith("-channels="):
            channels = ast.literal_eval(args[i].split('=')[1])
            if isinstance(channels, numbers.Number):
                res['channels'] = [channels]
            else:
                res['channels'] = channels

    return res


def test_args(args_dict):
    res = True
    if 'input_file' in args_dict.keys():
        if os.path.isfile(args_dict['input_file']) is False:
            print('-input_file refers to non-existing file: ' + args_dict['input_file'])
            res = False
        else:
            if 'matlab_output_dir' in args_dict.keys():
                if 'calibration_file' not in args_dict.keys() or 'piv_params_file' not in args_dict.keys():
                    print('When using PIVLab integration (-output_matlab_dir) you must also declare -piv_params_file '
                          'and -calibration_file')
                    res = False
                else:
                    if os.path.isfile(args_dict['calibration_file']) is False:
                        print('-calibration_file refers to non-existing file: ' + args_dict['calibration_file'])
                        res = False
                    else:
                        if os.path.isfile(args_dict['piv_params_file']) is False:
                            print('-piv_params_file refers to non-existing file: ' + args_dict['piv_params_file'])
                            res = False
            if 'roi_file' in args_dict.keys() and os.path.isfile(args_dict['roi_file']) is False:
                print('-roi_file refers to non-existing file: ' + args_dict['roi_file'])
                res = False
    else:
        print('Please specify input file using -input_file parameter')
        res = False
    return res


def start_working(args_dict):
    orchestrator = SingleProcessOrchestrator(args_dict)
    orchestrator.run()


def main(args):
    initialized = False
    nd2_wrapper = None
    roi_data = None
    input_file = None
    output_dir = None
    output_matlab_file = None
    calibration_file = None
    piv_params_file = None
    args_dict = {}

    nd2_manager = ND2Manager()
    # UI
    if show_ui(args):
        main_window = MainWindow("ND2TiffExporter", nd2_manager)
        main_window.start()
        args_dict = main_window.get_args()
    else:
        args_dict = parse_args(args)
    initialized = test_args(args_dict)
    if initialized is True:
        if 'roi_file' in args_dict.keys():
            with open(args_dict['roi_file'], 'r') as roi_file:
                args_dict['roi'] = json.load(roi_file)
        start_working(args_dict)

if __name__ == "__main__":
    # sys.argv[0] is the script name itself, so we slice from index 1
    command_line_arguments = sys.argv[1:]
    main(command_line_arguments)
