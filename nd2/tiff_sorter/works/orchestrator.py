from abc import ABC, abstractmethod
from nd2_tools.nd2_wrapper import ND2Wrapper, get_experiment_interval_ms
from config.settings import Settings
from arguments.arguments import Arguments
from csv_utils.z_axis_profile import generate_z_profile_csv
import os


class Orchestrator(ABC):

    def __init__(self):
        arguments = Arguments.instance()
        self.nd2_wrapper = ND2Wrapper(arguments.input_file)
        self.roi_skip_empty = Settings.instance().get('roi_skip_empty') is True
        [self.progress_data, self.progress_order] = self.get_progress_bars_data()

    def get_progress_bars_data(self):
        arguments = Arguments.instance()
        timepoints = self.nd2_wrapper.get_timepoints()
        multipoints = self.nd2_wrapper.get_multipoints_number()
        if 'multipoints' in arguments.multipoints:
            multipoints = len(arguments.multipoints)
        channels = self.nd2_wrapper.get_channels_number()
        if 'channels' in arguments.channels:
            channels = len(arguments.channels)
        frames = multipoints*channels*timepoints
        data = { 'Read': {'maximum': frames, 'units': 'frames'} }
        order = ['Read']
        if arguments.is_tiff_write():
            data['Write'] = { 'maximum': frames, 'units': 'frames' }
            order.append('Write')
        if arguments.is_pivlab():
            pairs_number = multipoints*channels*(timepoints-1)
            data['Pivlab calls'] = { 'maximum': pairs_number, 'units': 'frame pairs' }
            order.append('Pivlab calls')
        if arguments.is_z_axis_profile():
            multipoint_channel_pairs = multipoints*channels
            data['Mean'] = { 'maximum': frames, 'units': 'frames'}
            order.append('Mean')
            if arguments.z_axis_profile_output_dir is not None and arguments.z_axis_profile_single_output_file is False:
                data['Mean Write'] = { 'maximum' : multipoint_channel_pairs, 'units' : 'series' }
                order.append('Mean Write')
        return [data, order]

    def should_handle_series(self, multipoint, channel):
        arguments = Arguments.instance()
        res = True
        if arguments.roi is not None:
            key = f"{multipoint}_{channel}"
            if key not in arguments.roi and self.roi_skip_empty() :
                res = False
        return res

    def get_multipoint_channel_generator(self):
        arguments = Arguments.instance()
        for multipoint in arguments.multipoints:
            for channel in arguments.channels:
                if self.should_handle_series(multipoint, channel):
                    yield [multipoint, channel]

    def save_z_axis_profile_to_single_file(self, z_axis_profile_data):
        mean_output_dir = Arguments.instance().z_axis_profile_output_dir
        os.makedirs(mean_output_dir, exist_ok=True)
        frames = self.nd2_wrapper.get_timepoints()
        output_file = (mean_output_dir + "\\" +
                       f"z_axis_profile_{frames}_frames.csv")
        experiment_interval_sec = get_experiment_interval_ms(self.nd2_wrapper.get_input_file()) / 1000.0
        csv_content = generate_z_profile_csv(z_axis_profile_data, experiment_interval_sec)
        with open(output_file, "w", newline="") as f:
            f.write(csv_content)


    @abstractmethod
    def run(self):
        pass
