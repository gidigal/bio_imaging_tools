from nd2reader import ND2Reader
import numpy as np
from PIL import Image
from tqdm import tqdm
import time
import os
import tifffile
from config.settings import Settings


def convert_to_pil_image(frame_data):
    pil_image = None
    # If the image data is 16-bit (common in microscopy), you might need to convert it
    # to 8-bit for standard display/saving with PIL, or work with 16-bit if PIL supports the mode.
    # PIL can handle 'I;16' mode for 16-bit grayscale images.
    # For a general solution, you can scale to 8-bit if appropriate for visualization:

    # Determine the pixel type and scale if necessary
    if frame_data.dtype == np.uint16:
        # Scale to 0-255 for standard 8-bit representation (if applicable for your data)
        # Otherwise use mode='I;16' for 16-bit integer
        max_val = np.max(frame_data)
        if max_val > 0:
            frame_data_scaled = (frame_data * 255.0 / max_val).astype(np.uint8)
        else:
            frame_data_scaled = frame_data.astype(np.uint8)

        # Convert the NumPy array to a PIL Image object
        pil_image = Image.fromarray(frame_data_scaled, 'L')  # Use 'L' for grayscale 8-bit

    elif frame_data.ndim == 3:  # Handle RGB/multichannel images
        pil_image = Image.fromarray(frame_data, 'RGB')
    else:
        pil_image = Image.fromarray(frame_data)
    return pil_image


def should_handle_multipoint_channel_combination(roi_data):
    return roi_data is not None and len(roi_data.keys()) > 0


def get_channel_dir(output_dir,  multipoint, channel, roi):
    directory_name = f"FOV_{multipoint + 1}_Channel_{channel + 1}"
    if roi is not None :
        x_min, y_min, x_max, y_max = roi
        directory_name += f"_ROI_{x_min}_{y_min}_{x_max}_{y_max}"
    return os.path.join(output_dir, directory_name)


class ND2Wrapper:
    _instance = None

    @classmethod
    def instance(cls, input_file):
        if ND2Wrapper._instance is not None:
            current_input_file = ND2Wrapper._instance.get_input_file()
            if current_input_file != input_file:
                ND2Wrapper._instance.close()
                ND2Wrapper._instance = ND2Wrapper(input_file)
        else:
            ND2Wrapper._instance = ND2Wrapper(input_file)
        return ND2Wrapper._instance

    def __init__(self, input_file):
        self.input_file = input_file
        self.nd2_reader = ND2Reader(self.input_file)

    def get_input_file(self):
        return self.input_file

    def get_multipoints_number(self):
        res = 1
        if 'v' in self.nd2_reader.axes:
            res = self.nd2_reader.sizes['v']
        return res

    def get_channels_number(self):
        res = 1
        if 'c' in self.nd2_reader.axes:
            res = self.nd2_reader.sizes['c']
        return res

    def get_channel_names(self):
        channel_names = []
        if 'channels' in self.nd2_reader.metadata:
            channel_names = self.nd2_reader.metadata['channels']
        else:
            # Fallback if names aren't available
            num_channels = self.get_channels_number()
            channel_names = [f"Channel {i + 1}" for i in range(num_channels)]
        return channel_names

    def get_image(self, multipoint, channel, timepoint, roi=None):
        res = None
        if 'v' in self.nd2_reader.axes and 'c' in self.nd2_reader.axes and 't' in self.nd2_reader.axes:
            res = self.nd2_reader.get_frame_2D(v=multipoint, c=channel, t=timepoint)
        elif 'v' in self.nd2_reader.axes and 't' in self.nd2_reader.axes:
            res = self.nd2_reader.get_frame_2D(v=multipoint, t=timepoint)
        elif 'c' in self.nd2_reader.axes and 't' in self.nd2_reader.axes:
            res = self.nd2_reader.get_frame_2D(c=channel, t=timepoint)
        elif 'v' in self.nd2_reader.axes and 'c' in self.nd2_reader.axes:
            res = self.nd2_reader.get_frame_2D(v=multipoint, c=channel)
        elif 'c' in self.nd2_reader.axes:
            res = self.nd2_reader.get_frame_2D(c=channel)
        else:
            res = self.nd2_reader[timepoint] if 't' in self.nd2_reader.axes else self.nd2_reader[0]
        if roi is not None:
            x_min, y_min, x_max, y_max = roi
            res = res[y_min:y_max, x_min:x_max]
        return res

    def get_first_images(self):
        res = {}
        multipoints = self.get_multipoints_number()
        channels = self.get_channels_number()
        for multipoint in range(multipoints):
            for channel in range(channels):
                key = str(multipoint) + '_' + str(channel)
                res[key] = self.get_image(multipoint, channel, 0)
        return res

    def nd2_images_reader_generator(self, multipoint, channel, roi, report_strategy):
        skip_missing_roi = Settings.instance().get("roi_skip_empty") == "true"
        images = self.nd2_reader
        # Iterate through time points
        if 't' in images.axes:
            num_frames = images.sizes['t']
        else:
            num_frames = 1
        for t in range(num_frames):
            read_start = time.time()
            img = self.get_image(multipoint, channel, t, roi=roi)
            report_strategy.report_time('read', time.time() - read_start)
            report_strategy.read_progress()
            yield img

    def nd2_images_writer_generator(self, read_generator, channel_dir, report_strategy):
        frame_idx = 0
        for image in read_generator:
            # Save as TIFF - raw pixel data, no scaling or color mapping
            output_path = os.path.join(channel_dir, f"img_{frame_idx:04d}.tif")
            write_start = time.time()
            tifffile.imwrite(output_path, image, photometric='minisblack')
            report_strategy.report_time('write', time.time() - write_start)
            report_strategy.write_progress()
            frame_idx += 1
            yield image

    def nd2_images_generator(self, multipoint=0, channel=0, roi=None, output_dir=None):
        total_planes = self.get_total_planes()
        read_progress_bar = tqdm(total=total_planes, desc=f"Reading planes", position=0, leave=True) if output_dir is None else None
        read_generator = self.nd2_images_reader_generator(multipoint, channel, roi, read_progress_bar)
        res = None
        if output_dir is None:
            res = read_generator
        else:
            channel_dir = get_channel_dir(output_dir, multipoint, channel, roi)
            write_progress_bar = tqdm(total=total_planes, desc=f"Writing planes", position=0, leave=True)
            res = self.nd2_images_writer_generator(read_generator, channel_dir, write_progress_bar)
        return res

    def get_total_planes(self):
        images = self.nd2_reader
        return images.sizes['t'] * self.get_channels_number() * self.get_multipoints_number()

    def get_timepoints(self):
        return self.nd2_reader.sizes['t']

    def get_total_plane_pairs(self):
        planes = self.nd2_reader.sizes['t']
        channels = self.get_channels_number()
        multipoints = self.get_multipoints_number()
        return (planes-1)*multipoints*channels

    def extract_tiffs(self, output_dir, roi_data):
        start_time = time.time()
        read_time = 0
        write_time = 0

        print("Input: " + self.input_file)
        print("Output: " + output_dir)
        images = self.nd2_reader
        print(f"Image shape: {images.sizes}")
        print(f"Available axes: {images.axes}")

        total_planes = images.sizes['t'] * self.get_channels_number() * self.get_multipoints_number()

        skip_missing_roi = Settings.instance().get("roi_skip_empty") == "true"

        with tqdm(total=total_planes, desc=f"Exporting planes", position=0, leave=True) as progress_bar:

            # Iterate through multipoints (if they exist)
            if 'v' in images.axes:
                num_fovs = images.sizes['v']
            else:
                num_fovs = 1

            for fov in range(num_fovs):
                tqdm.write(f"Processing FOV {fov + 1}/{num_fovs}")

                # Get number of channels
                if 'c' in images.axes:
                    num_channels = images.sizes['c']
                else:
                    num_channels = 1

                for channel in range(num_channels):
                    key = f"{fov}_{channel}"

                    extract_image_series = True
                    if should_handle_multipoint_channel_combination(roi_data):
                        if key not in roi_data.keys() and skip_missing_roi:
                            extract_image_series = False

                    if extract_image_series is True:
                        directory_name = f"FOV_{fov + 1}_Channel_{channel + 1}"
                        roi = None
                        x_min = None
                        y_min = None
                        x_max = None
                        y_max = None
                        if roi_data is not None and key in roi_data.keys() and roi_data[key] is not None:
                            roi = roi_data[key]
                            x_min, y_min, x_max, y_max = roi
                            directory_name += f"_ROI_{x_min}_{y_min}_{x_max}_{y_max}"

                        # Create output directory
                        channel_dir = os.path.join(output_dir, directory_name)
                        os.makedirs(channel_dir, exist_ok=True)

                        frame_idx = 0

                        # Iterate through time points
                        if 't' in images.axes:
                            num_frames = images.sizes['t']
                        else:
                            num_frames = 1

                        for t in tqdm(range(num_frames), desc=f"FOV {fov + 1} Ch {channel + 1}", position=1,
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
        self.nd2_reader.close()

