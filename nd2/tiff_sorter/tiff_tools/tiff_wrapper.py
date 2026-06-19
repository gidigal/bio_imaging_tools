from tiff_tools.tiff_reader import get_tiff_generator
from pathlib import Path

class TiffWrapper:
    _instance = None

    @classmethod
    def instance(cls, input_dir):
        if TiffWrapper._instance is not None:
                TiffWrapper._instance = TiffWrapper(input_dir)
        else:
            TiffWrapper._instance = TiffWrapper(input_dir)
        return TiffWrapper._instance

    def __init__(self, input_dir):
        self.input_dir = input_dir

    def get_input_file(self):
        return self.input_dir

    def get_multipoints_number(self):
        return 1

    def get_channels_number(self):
        return 1

    def get_channel_names(self):
        return ['1']

    def get_timepoints(self):
        directory_path = Path(self.input_dir)
        return sum(1 for item in directory_path.iterdir() if item.is_file())

    def nd2_images_reader_generator(self, multipoint, channel, roi, report_strategy):
        return get_tiff_generator(self.input_dir, report_strategy)