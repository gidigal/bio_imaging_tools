from nd2_tools.nd2_wrapper import ND2Wrapper
from nd2_tools.nd2_wrapper import get_experiment_interval_ms
from matlab_integration.python_to_pivlab_streaming import PIVlabStreamProcessor
from matlab_integration.save_to_mat import save_results_to_mat
import json
import collections
import os
import csv
import io


def generate_z_profile_csv(mean_values, experiment_interval_sec):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["[sec]", "Mean"])
    for i, mean in enumerate(mean_values):
        writer.writerow([i * experiment_interval_sec, mean])
    return buffer.getvalue()


class ND2Worker:
    def __init__(self, multipoint, channel, args_dict, report_strategy, pivlab_stream_processor=None):
        self.multipoint = multipoint
        self.channel = channel
        self.args_dict = args_dict
        self.report_strategy = report_strategy
        self.rw_generator = None
        self.matlab_generator = None
        self.mean_generator = None
        self.nd2_wrapper = ND2Wrapper.instance(self.args_dict["input_file"])
        self.pivlab_stream_processor = pivlab_stream_processor
        self.mean_results = None

    def get_multipoint(self):
        return self.multipoint

    def get_channel(self):
        return self.channel

    def get_args_dict(self):
        return self.args_dict

    def should_write_tiffs(self):
        return "output_dir" in self.args_dict.keys()

    def should_run_matlab(self):
        return 'matlab_output_dir' in self.args_dict.keys()

    def should_z_axis_profile(self):
        keys = self.args_dict.keys()
        return 'z_axis_profile_output_dir' in keys or 'z_axis_profile_plot' in keys

    def prepare_generator(self):
        roi = None
        if 'roi' in self.args_dict.keys():
            key = f"{self.multipoint}_{self.channel}"
            if key in self.args_dict['roi'].keys():
                roi = self.args_dict["roi"][key]
        self.rw_generator = self.nd2_wrapper.nd2_images_reader_generator(self.multipoint,
                                                                         self.channel, roi,
                                                                         self.report_strategy)
        if 'output_dir' in self.args_dict.keys():
            channel_names = self.nd2_wrapper.get_channel_names()
            channel_dir = f"multipoint_{self.multipoint}_channel_{channel_names[self.channel]}"
            channel_dir_full = os.path.join(self.args_dict['output_dir'], channel_dir)
            os.makedirs(channel_dir_full, exist_ok=True)

            self.rw_generator = self.nd2_wrapper.nd2_images_writer_generator(self.rw_generator,
                                                                             channel_dir_full,
                                                                             self.report_strategy)
        if self.should_run_matlab():
            if self.pivlab_stream_processor is None:
                self.pivlab_stream_processor = PIVlabStreamProcessor(self.report_strategy)
            calibration = None
            with open(self.args_dict['calibration_file'], 'r') as calibration_file:
                calibration = json.load(calibration_file)
            piv_params = None
            with open(self.args_dict['piv_params_file'], 'r') as piv_params_file:
                piv_params = json.load(piv_params_file)
            piv_params['cal_fact'] = calibration['pixel_size_um'] / calibration['mag'] / calibration['time_step']
            self.matlab_generator = self.pivlab_stream_processor.process_image_generator(self.rw_generator,
                                                                                         piv_params,
                                                                                         self.report_strategy)
        if self.should_z_axis_profile():
            self.mean_generator = (
                self.nd2_wrapper.nd2_z_axis_profile_generator(self.rw_generator, self.report_strategy))

    def save(self, matlab_results):
        matlab_output_dir = self.args_dict['matlab_output_dir']
        os.makedirs(matlab_output_dir, exist_ok=True)
        frames = self.nd2_wrapper.get_timepoints()
        channel_name = self.nd2_wrapper.get_channel_names()[self.channel]
        matlab_output_file = (matlab_output_dir + "\\" +
                              f"multipoint_{self.multipoint}_channel_{channel_name}_{frames}_frames.mat")
        save_results_to_mat(matlab_results, matlab_output_file)

    def save_mean(self, mean_results):
        mean_output_dir = self.args_dict['z_axis_profile_output_dir']
        os.makedirs(mean_output_dir, exist_ok=True)
        channel_name = self.nd2_wrapper.get_channel_names()[self.channel]
        frames = self.nd2_wrapper.get_timepoints()
        output_file = (mean_output_dir + "\\" +
                       f"z_profile_multipoint_{self.multipoint}_channel_{channel_name}_{frames}_frames.csv")
        experiment_interval_sec = get_experiment_interval_ms(self.nd2_wrapper.get_input_file()) / 1000.0
        csv_content = generate_z_profile_csv(mean_results, experiment_interval_sec)
        with open(output_file, "w", newline="") as f:
            f.write(csv_content)

    def run_matlab(self):
        results = []
        try:
            # Collect results as they're generated
            results = list(self.matlab_generator)
            # write results to file
            self.save(results)
        except KeyboardInterrupt:
            print("\nProcessing interrupted by user")

    def run_tiff_extraction(self):
        collections.deque(self.rw_generator, maxlen=0)

    def get_mean_results(self):
        return self.mean_results

    def run_z_axis_profile(self):
        self.mean_results = list(self.mean_generator)
        self.save_mean(self.mean_results)
        self.report_strategy.mean_write_progress()

    def run(self):
        self.prepare_generator()
        if self.should_run_matlab():
            self.run_matlab()
        else:
            if self.should_z_axis_profile() is False:
                self.run_tiff_extraction()
            else:
                self.run_z_axis_profile()
