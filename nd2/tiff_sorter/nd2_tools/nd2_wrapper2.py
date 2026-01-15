from nd2 import ND2File
from tqdm import tqdm
import time
import os
import tifffile


class ND2Wrapper2:
    def __init__(self, input_file):
        self.input_file = input_file
        self.nd2_file = ND2File(self.input_file)
        self.xarr = self.nd2_file.to_xarray(delayed=True)

    def get_multipoints_number(self):
        res = 1
        if 'V' in self.nd2_file.sizes:
            res = self.nd2_file.sizes['V']
        return res

    def get_channels_number(self):
        res = 1
        if 'C' in self.nd2_file.sizes:
            res = self.nd2_file.sizes['C']
        return res

    def get_time_points(self):
        res = 1
        if 'T' in self.nd2_file.sizes:
            res = self.nd2_file.sizes['T']
        return res

    def get_channel_names(self):
        channel_names = []
        if 'channels' in self.nd2_file.metadata:
            channel_names = self.nd2_file.metadata['channels']
        else:
            # Fallback if names aren't available
            num_channels = self.get_channels_number()
            channel_names = [f"Channel {i + 1}" for i in range(num_channels)]
        return channel_names

    def get_image(self, multipoint, channel, timepoint, roi=None):
        # Build dimension selection with INTEGER positions
        isel_dict = {}
        if 'V' in self.xarr.dims:
            isel_dict['V'] = multipoint
        if 'C' in self.xarr.dims:
            isel_dict['C'] = channel
        if 'T' in self.xarr.dims:
            isel_dict['T'] = timepoint
        # Select dimensions by INTEGER position
        result = self.xarr.isel(**isel_dict)
        # Apply ROI crop if provided
        if roi is not None:
            x_min, y_min, x_max, y_max = roi
            result = result.isel(Y=slice(y_min, y_max), X=slice(x_min, x_max))
        return result.values

    def get_first_images(self):
        res = {}
        multipoints = self.get_multipoints_number()
        channels = self.get_channels_number()
        for multipoint in range(multipoints):
            for channel in range(channels):
                key = str(multipoint) + '_' + str(channel)
                res[key] = self.get_image(multipoint, channel, 0)
        return res

    def extract_tiffs(self, output_dir, roi_data):
        start_time = time.time()
        read_time = 0
        write_time = 0

        print("Input: " + self.input_file)
        print("Output: " + output_dir)

        # Open the ND2 file
        images = self.nd2_file
        print(f"Image shape: {images.sizes}")
        time_points = self.get_time_points()
        channels = self.get_channels_number()
        multi_points = self.get_multipoints_number()
        total_planes = time_points * channels * multi_points

        with tqdm(total=total_planes, desc=f"Exporting planes", position=0, leave=True) as progress_bar:

            # Iterate through multipoints (if they exist)

            for fov in range(multi_points):
                tqdm.write(f"Processing FOV {fov + 1}/{multi_points}")

                for channel in range(channels):
                    directory_name = f"FOV_{fov + 1}_Channel_{channel + 1}"
                    roi = None
                    x_min = None
                    y_min = None
                    x_max = None
                    y_max = None
                    if roi_data is not None:
                        roi = roi_data[f"{fov}_{channel}"]
                        x_min, y_min, x_max, y_max = roi
                        directory_name += f"_ROI_{x_min}_{y_min}_{x_max}_{y_max}"

                    # Create output directory
                    channel_dir = os.path.join(output_dir, directory_name)
                    os.makedirs(channel_dir, exist_ok=True)

                    frame_idx = 0

                    for t in tqdm(range(time_points), desc=f"FOV {fov + 1} Ch {channel + 1}", position=1,
                                  leave=False):
                        read_start = time.time()
                        img = self.get_image(fov, channel, t, roi=roi)
                        read_time += time.time() - read_start

                        # Save as TIFF - raw pixel data, no scaling or color mapping
                        output_path = os.path.join(channel_dir, f"img_{frame_idx:04d}.tif")
                        write_start = time.time()
                        tifffile.imwrite(output_path, img, photometric='minisblack')
                        write_time += time.time() - write_start

                        frame_idx += 1

                        # Update progress bar
                        progress_bar.update(1)

                    tqdm.write(f"  Saved {frame_idx} frames to {channel_dir}")
                    tqdm.write(f"  Data type: {img.dtype}, min: {img.min()}, max: {img.max()}")
        end_time = time.time()
        print(f"\n=== Performance Summary ===")
        print(f"Total time: {end_time - start_time:.2f} seconds")
        print(f"Read time: {read_time:.2f} seconds")
        print(f"Write time: {write_time:.2f} seconds")

    def close(self):
        self.nd2_file.close()


