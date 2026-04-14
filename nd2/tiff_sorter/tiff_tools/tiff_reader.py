# Provides generator for reading tiff files from directory
import tifffile
import glob


def get_tiff_generator(directory_path):
    tiff_files = sorted(glob.glob(f'{directory_path}/*.tif'))
    for tiff_file in tiff_files:
        yield tifffile.imread(tiff_file)