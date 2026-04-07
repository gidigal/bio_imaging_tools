from works.single_process_orchestrator import SingleProcessOrchestrator
from arguments.cli import cli


def start_working(args_dict):
    orchestrator = SingleProcessOrchestrator(args_dict)
    orchestrator.run()


    # # UI
    # if show_ui(args):
    #     main_window = MainWindow("ND2TiffExporter", nd2_manager)
    #     main_window.start()
    #     args_dict = main_window.get_args()
    # else:
    #     args_dict = parse_args(args)
    # initialized = test_args(args_dict)
    # if initialized is True:
    #     if 'roi_file' in args_dict.keys():
    #         with open(args_dict['roi_file'], 'r') as roi_file:
    #             args_dict['roi'] = json.load(roi_file)
    #     start_working(args_dict)

if __name__ == "__main__":
    cli()
