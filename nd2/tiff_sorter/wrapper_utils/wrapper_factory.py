from nd2_tools.nd2_wrapper import ND2Wrapper
from tiff_tools.tiff_wrapper import TiffWrapper

def get_wrapper(input_file, input_dir):
    res = None
    if input_file is not None:
        res =  ND2Wrapper.instance(input_file)
    else:
        res = TiffWrapper.instance(input_dir)
    return res

