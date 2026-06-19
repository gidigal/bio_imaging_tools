# Provides generator for reading tiff files from directory
import tifffile
import glob
import numpy as np


def get_tiff_generator(directory_path, report_strategy):
    tiff_files = sorted(glob.glob(f'{directory_path}/*.tif'))
    for tiff_file in tiff_files:
        image = tifffile.imread(tiff_file)
        report_strategy.read_progress()
        yield np.asarray(image, dtype=np.uint16)  # forces native dtype, copies if needed