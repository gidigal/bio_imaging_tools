import click
from nd2_tools.nd2_wrapper import ND2Wrapper
import os
import json


class Arguments:
    _instance = None

    def __init__(self):
        self.input_file = None
        self.gui = False
        self.multipoints = None
        self.channels = None
        self.parallel = False
        self.roi_file = None
        self.roi = None
        self.output_dir = None
        self.matlab_output_dir = None
        self.piv_params_file = None
        self.calibration_file = None
        self.z_axis_profile_output_dir = None
        self.z_axis_profile_plot = False

    def fill_in_multipoints_channels(self):
        nd2_wrapper = ND2Wrapper.instance(self.input_file)
        if self.multipoints is None:
            self.multipoints = list(range(nd2_wrapper.get_multipoints_number()))
        if self.channels is None:
            self.channels = list(range(nd2_wrapper.get_channels_number()))

    def set(self, input_file, gui=False, roi_file=None,
            multipoints=None, channels=None,
            parallel = False, output_dir=None,
            matlab_output_dir=None, piv_params_file=None, calibration_file=None,
            z_axis_profile_output_dir=None, z_axis_profile_plot=False):
        self.input_file = input_file
        self.gui = gui
        self.output_dir = output_dir
        self.multipoints = multipoints
        self.channels = channels
        if self.multipoints is None or self.channels is None:
            self.fill_in_multipoints_channels()
        self.parallel = parallel
        self.roi_file = roi_file
        if self.roi_file is not None:
            with open(self.roi_file, 'r') as roi_file:
                self.roi = json.load(roi_file)
        self.matlab_output_dir = matlab_output_dir
        self.piv_params_file = piv_params_file
        self.calibration_file = calibration_file
        self.z_axis_profile_output_dir = z_axis_profile_output_dir
        self.z_axis_profile_plot = z_axis_profile_plot

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set_instance(cls, instance):
        cls._instance = instance

    def is_gui(self):
        return self.gui

    def is_tiff_write(self):
        return self.output_dir is not None

    def is_pivlab(self):
        return all([self.matlab_output_dir, self.piv_params_file, self.calibration_file])

    def is_z_axis_profile(self):
        return self.z_axis_profile_output_dir is not None or self.z_axis_profile_plot

    def should_plot_z_axis_profile(self):
        return self.z_axis_profile_plot

    def should_write_z_axis_profile(self):
        return self.z_axis_profile_output_dir is not None

    def get_multipoints(self, available):
        """Returns multipoints to process, or all available if not specified."""
        return self.multipoints if self.multipoints is not None else list(available)

    def get_channels(self, available):
        """Returns channels to process, or all available if not specified."""
        return self.channels if self.channels is not None else list(available)

    def should_parallel(self):
        return self.parallel


if __name__ == '__main__':
    cli()
