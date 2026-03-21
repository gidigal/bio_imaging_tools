import json
import sys
import os
from works.single_process_orchestrator import SingleProcessOrchestrator
from works.multi_process_orchestrator import MultiProcessOrchestrator
from profiling.profiler import Profiler

if __name__ == "__main__":
    test_data_file = sys.argv[1]
    with open(test_data_file, 'r') as file:
        test_data = json.load(file)
    test_output_folder = test_data['test_output_folder']
    os.makedirs(test_output_folder, exist_ok=True)
    os.makedirs(test_output_folder+'\\single', exist_ok=True)
    os.makedirs(test_output_folder+'\\multi', exist_ok=True)
    os.makedirs(test_output_folder + '\\single\\matlab', exist_ok=True)
    os.makedirs(test_output_folder + '\\multi\\matlab', exist_ok=True)
    args_dict = {}
    args_dict['input_file'] = test_data['input_file']
    args_dict['calibration_file'] = test_data['calibration_file']
    args_dict['piv_params_file'] = test_data['piv_params_file']
    # Single test
    args_dict['output_dir'] = test_output_folder+'\\single'
    args_dict['matlab_output_dir'] = test_output_folder+'\\single\\matlab'
    orchestrator = SingleProcessOrchestrator(args_dict)
    orchestrator.run()
    single_total_time = Profiler.instance().get_total_time()
    # Start a new profiler instance
    Profiler.refresh()
    # Multi test
    args_dict['output_dir'] = test_output_folder+'\\multi'
    args_dict['matlab_output_dir'] = test_output_folder+'\\multi\\matlab'
    orchestrator = MultiProcessOrchestrator(args_dict)
    orchestrator.run()
    multi_total_time = Profiler.instance().get_total_time()
    # Is there an improvement utilizing multi cores ?
    print(f"single: {single_total_time:.2f} seconds, multi: {multi_total_time:.2f} seconds {(multi_total_time/single_total_time)*100:.2f} diff")
