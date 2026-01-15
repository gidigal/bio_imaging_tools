import sys
from gui.main_window import MainWindow
from gui.roi_window import ROIWindow
from nd2_tools.nd2_manager import ND2Manager


def main(args):
    initialized = False
    nd2_wrapper = None
    roi_data = None
    nd2_manager = ND2Manager()
    #UI
    if len(args) == 0:
        main_window = MainWindow("ND2TiffExporter", nd2_manager)
        main_window.start()
        [input_file, output_dir, roi_data, initialized] = main_window.get_args()
    elif args[0] == '-roi':
        input_file = args[1]
        output_dir = args[2]
        nd2_wrapper = nd2_manager.get(input_file=input_file)
        roi_window = ROIWindow(nd2_wrapper)
        roi_window.start()
        roi_data = roi_window.get_roi_data()
        initialized = roi_window.start_hit
    else:
        input_file = args[0]
        output_dir = args[1]
        nd2_wrapper = nd2_manager.get(input_file=input_file)
        initialized = True

    if initialized is True and\
        input_file is not None and len(input_file) > 0 and\
            output_dir is not None and len(output_dir) > 0:
        nd2_wrapper = nd2_manager.get(input_file=input_file)
        nd2_wrapper.extract_tiffs(output_dir, roi_data)
    

if __name__ == "__main__":
    # sys.argv[0] is the script name itself, so we slice from index 1
    command_line_arguments = sys.argv[1:]
    main(command_line_arguments)