from abc import ABC, abstractmethod
from nd2_tools.nd2_wrapper import ND2Wrapper
import json
from config.settings import Settings
from matlab_integration.python_to_pivlab_streaming import PIVlabStreamProcessor


class Orchestrator(ABC):

    def __init__(self, args_dict):
        self.args_dict = args_dict
        self.nd2_wrapper = ND2Wrapper(args_dict['input_file'])
        self.pivlab_stream_processor = PIVlabStreamProcessor()
        if 'roi_file' in self.args_dict:
            with open(self.args_dict['roi_fie'], 'r') as roi_file:
                self.args_dict['roi'] = json.load(roi_file)
        self.roi_skip_empty = Settings.instance().get('roi_skip_empty') is True
        [self.progress_data, self.progress_order] = self.get_progress_bars_data()

    def get_progress_bars_data(self):
        frames = self.nd2_wrapper.get_total_planes()
        data = { 'Read': {'maximum': frames, 'units': 'frames'} }
        order = ['Read']
        if 'output_dir' in self.args_dict.keys():
            data['Write'] = { 'maximum': frames, 'units': 'frames' }
            order.append('Write')
        if 'matlab_output_dir' in self.args_dict.keys():
            pairs_number = self.nd2_wrapper.get_total_plane_pairs()
            data['Pivlab calls'] = { 'maximum': pairs_number, 'units': 'frame pairs' }
            order.append('Pivlab calls')
        if 'z_axis_profile_output_dir' in self.args_dict.keys():
            multipoint_channel_pairs = self.nd2_wrapper.get_multipoints_number()*self.nd2_wrapper.get_channels_number()
            data['Mean'] = { 'maximum': frames, 'units': 'frames'}
            data['Mean Write'] = { 'maximum' : multipoint_channel_pairs, 'units' : 'series' }
            order.append(['Mean', 'Mean Write'])
        return [data, order]

    def should_handle_series(self, multipoint, channel):
        settings = Settings.instance()
        res = True
        if 'roi' in self.args_dict.keys():
            roi_dict = self.args_dict['roi']
            key = f"{multipoint}_{channel}"
            if key not in roi_dict.keys() and self.roi_skip_empty() :
                res = False
        return res

    def get_multipoint_channel_generator(self):
        multipoints = self.nd2_wrapper.get_multipoints_number()
        channels = self.nd2_wrapper.get_channels_number()
        for multipoint in range(multipoints):
            for channel in range(channels):
                if self.should_handle_series(multipoint, channel):
                    yield [multipoint, channel]



    @abstractmethod
    def run(self):
        pass