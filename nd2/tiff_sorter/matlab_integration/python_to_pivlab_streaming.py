# python_to_pivlab_streaming.py
"""
Memory-efficient PIVlab processing - process frame pairs one at a time
"""

import matlab.engine
import numpy as np
import time
from pathlib import Path
from config.settings import Settings


class PIVlabStreamProcessor:
    """
    Process images with PIVlab in streaming mode
    Only 2 frames in memory at a time
    """
    
    def __init__(self, report_strategy):
        self.eng = None
        self.report_strategy = report_strategy
        
    def start_matlab(self):
        """Start MATLAB engine"""
        if self.eng is None:
            print("Starting MATLAB engine...")
            matlab_start = time.time()
            self.eng = matlab.engine.start_matlab()
            self.report_strategy.report_time('matlab_start',  time.time()-matlab_start)            
            print("✓ MATLAB engine started")
            matlab_add_path = time.time()
            current_dir = str(Path(__file__).parent.absolute())
            self.eng.addpath(current_dir, nargout=0)
            pivlab_root = Settings.instance().get('pivlab_root')
            self.eng.addpath(pivlab_root)
            self.report_strategy.report_time('matlab_add_path', time.time()-matlab_add_path)
        
        return self.eng
    
    def stop_matlab(self):
        """Stop MATLAB engine"""
        if self.eng is not None:
            self.eng.quit()
            self.eng = None
            print("MATLAB engine stopped")
    
    def process_frame_pair(self, img1, img2, piv_params):
        """
        Process a single pair of frames
        
        Parameters:
        -----------
        img1, img2 : ndarray
            2D numpy arrays (consecutive frames)
        piv_params : dict
            PIV parameters
        
        Returns:
        --------
        dict : PIV results for this pair
        """
        
        if self.eng is None:
            self.start_matlab()

        t1 = time.time()
        # Convert to MATLAB format
        matlab_img1 = self._numpy_to_matlab(img1)
        matlab_img2 = self._numpy_to_matlab(img2)

        t2 = time.time()

        # Prepare parameters
        if piv_params is None:
            piv_params = {
                'passes': [64.0, 32.0, 16.0],
                'overlap': 0.5,
                'subpixel_method': 'Gauss2x3',
                'validation': True,
                'smoothing': True,
                'CLAHE_num_tiles': 64, # Number of tiles across the image
                'vel_limit_min': -50,
                'vel_limit_max': 50,
                'stdev_threshold': 5
            }
        
        matlab_params = self._dict_to_matlab_struct(piv_params)

        t3 = time.time()

        # Call MATLAB function (using the manual version that works)
        matlab_result = self.eng.process_single_pair_pivlab(
            matlab_img1, 
            matlab_img2, 
            matlab_params,
            nargout=1
        )

        t4 = time.time()
        
        # Convert back to Python
        result = {
            'x': np.array(matlab_result['x']),
            'y': np.array(matlab_result['y']),
            'u': np.array(matlab_result['u']),
            'v': np.array(matlab_result['v']),
            'typevector': np.array(matlab_result['typevector']),
            'velocity_magnitude': np.array(matlab_result['velocity_magnitude']),
            'mean_velocity': float(matlab_result['mean_velocity']),
            'max_velocity': float(matlab_result['max_velocity']),
            'u_calibrated': np.array(matlab_result['u_calibrated']),
            'v_calibrated': np.array(matlab_result['v_calibrated']),
            'velocity_magnitude_calibrated': np.array(matlab_result['velocity_magnitude_calibrated']),
        }

        t5 = time.time()

        self.report_strategy.report_time('convert_to_matlab_format', t2-t1)
        self.report_strategy.report_time('dict_to_matlab_struct', t3 - t2)
        self.report_strategy.report_time('process_single_pair_pivlab', t4 - t3)
        self.report_strategy.report_time('convert_back_to_python', t5 - t4)
        return result
    
    def process_image_generator(self, image_generator, piv_params, report_strategy):
        """
        Process images from a generator (memory efficient!)
        
        Parameters:
        -----------
        image_generator : generator
            Generator that yields 2D numpy arrays (one frame at a time)
        piv_params : dict
            PIV parameters
        
        Yields:
        -------
        dict : PIV results for each consecutive pair
        """
        
        if self.eng is None:
            self.start_matlab()
        
        prev_frame = None
        frame_count = 0
        pair_count = 0
        
        for frame in image_generator:
            frame_count += 1
            
            if prev_frame is not None:
                # Process this pair
                #print(f"Processing pair {pair_count + 1} (frames {frame_count-1} and {frame_count})...")
                
                result = self.process_frame_pair(prev_frame, frame, piv_params)


                result['pair_index'] = pair_count
                result['frame_indices'] = (frame_count - 1, frame_count)

                report_strategy.matlab_progress()
                
                pair_count += 1
                yield result
            
            # Update for next iteration
            prev_frame = frame
        
        # print(f"Processed {pair_count} pairs from {frame_count} frames")

    def _numpy_to_matlab(self, np_array):
        """Convert numpy 2D array to MATLAB uint16 array"""
        if np_array.dtype != np.uint16:
            np_array = np_array.astype(np.uint16)
        return matlab.uint16(np_array)
    
    def _dict_to_matlab_struct(self, py_dict):
        """Convert Python dict to MATLAB struct"""
        struct_dict = {}
        for key, value in py_dict.items():
            if isinstance(value, list):
                struct_dict[key] = matlab.double(value)
            else:
                struct_dict[key] = value
        return struct_dict
    
    def __enter__(self):
        """Context manager entry"""
        self.start_matlab()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_matlab()
        return False  # Don't suppress exceptions


# ND2 Reader Generator

def nd2_frame_generator(nd2_path, channel=0, position=0, roi=None):
    """
    Generator that yields frames from nd2 file one at a time
    Memory efficient - only one frame in memory
    
    Parameters:
    -----------
    nd2_path : str
        Path to nd2 file
    channel : int
        Channel index
    position : int
        Position/field index
    roi : tuple or None
        (y1, y2, x1, x2) to crop, or None for full frame
    
    Yields:
    -------
    ndarray : 2D frame
    """
    
    from nd2reader import ND2Reader
    
    with ND2Reader(nd2_path) as images:
        print(f"ND2 info: {images.sizes}")
        print(f"Channels: {images.metadata['channels']}")
        
        # Determine number of timepoints
        if 't' in images.sizes:
            num_frames = images.sizes['t']
        else:
            num_frames = len(images)
        
        print(f"Processing {num_frames} frames from channel {channel}, position {position}")
        
        for t in range(num_frames):
            # Read single frame
            try:
                frame = images.get_frame_2D(c=channel, t=t, v=position)
            except:
                # Fallback for different nd2 structures
                frame = images[t]
            
            # Apply ROI if specified
            if roi is not None:
                y1, y2, x1, x2 = roi
                frame = frame[y1:y2, x1:x2]
            
            yield frame

