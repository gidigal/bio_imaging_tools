# save_to_mat.py
"""
Save PIV results to MATLAB .mat files
"""

import scipy.io
import numpy as np
from matlab_integration.python_to_pivlab_streaming import PIVlabStreamProcessor, nd2_frame_generator
from pathlib import Path

def save_results_to_mat(results, output_file):
    """
    Save PIV results to a .mat file that MATLAB can open
    
    Parameters:
    -----------
    results : list of dict
        List of PIV results from process_image_generator
    output_file : str
        Output .mat file path
    """
    
    # Organize results for MATLAB
    num_pairs = len(results)
    
    # Pre-allocate arrays (MATLAB-friendly structure)
    mat_data = {
        'num_pairs': num_pairs,
        'mean_velocity': np.array([r['mean_velocity'] for r in results]),
        'max_velocity': np.array([r['max_velocity'] for r in results]),
        'pair_indices': np.array([r['pair_index'] for r in results]),
    }
    
    # Store velocity fields as cell arrays (MATLAB cell arrays)
    # Each cell contains a 2D array
    x_cells = np.empty((num_pairs,), dtype=object)
    y_cells = np.empty((num_pairs,), dtype=object)
    u_cells = np.empty((num_pairs,), dtype=object)
    v_cells = np.empty((num_pairs,), dtype=object)
    vel_mag_cells = np.empty((num_pairs,), dtype=object)
    typevector_cells = np.empty((num_pairs,), dtype=object)
    
    for i, result in enumerate(results):
        x_cells[i] = result['x']
        y_cells[i] = result['y']
        u_cells[i] = result['u']
        v_cells[i] = result['v']
        vel_mag_cells[i] = result['velocity_magnitude']
        typevector_cells[i] = result['typevector']
    
    mat_data['x'] = x_cells
    mat_data['y'] = y_cells
    mat_data['u'] = u_cells
    mat_data['v'] = v_cells
    mat_data['velocity_magnitude'] = vel_mag_cells
    mat_data['typevector'] = typevector_cells
    
    # Save to .mat file
    scipy.io.savemat(output_file, mat_data)
    print(f"Results saved to {output_file}")
    print(f"  {num_pairs} velocity fields")
    print(f"  Mean velocity: {np.mean(mat_data['mean_velocity']):.2f} px/frame")


def save_results_incrementally(nd2_path, output_file, piv_params=None, roi=None):
    """
    Process nd2 and save results incrementally to .mat file
    
    Parameters:
    -----------
    nd2_path : str
        Path to nd2 file
    output_file : str
        Output .mat file path
    piv_params : dict
        PIV parameters
    roi : tuple
        (y1, y2, x1, x2) or None
    """
    
    if piv_params is None:
        piv_params = {
            'passes': [64.0, 32.0, 16.0],
            'overlap': 0.5,
            'subpixel_method': 'Gauss2x3',
            'validation': True,
            'smoothing': True
        }
    
    results = []
    
    with PIVlabStreamProcessor() as processor:
        frame_gen = nd2_frame_generator(nd2_path, channel=0, position=0, roi=roi)
        
        for piv_result in processor.process_image_generator(frame_gen, piv_params):
            results.append(piv_result)
            print(f"  Pair {piv_result['pair_index']}: "
                  f"mean_vel={piv_result['mean_velocity']:.2f}")
    
    # Save all results to .mat file
    save_results_to_mat(results, output_file)
    
    return results


def process_multipoint_to_mat(nd2_path, output_dir, piv_params=None):
    """
    Process all positions in nd2 file and save each to separate .mat file
    
    Parameters:
    -----------
    nd2_path : str
        Path to nd2 file
    output_dir : str
        Directory to save .mat files
    piv_params : dict
        PIV parameters
    """
    
    from nd2reader import ND2Reader
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get number of positions
    with ND2Reader(nd2_path) as images:
        num_positions = images.sizes.get('v', 1)
        num_channels = images.sizes.get('c', 1)
    
    print(f"Processing {num_positions} positions, {num_channels} channels")
    
    if piv_params is None:
        piv_params = {
            'passes': [64.0, 32.0, 16.0],
            'overlap': 0.5,
            'subpixel_method': 'Gauss2x3',
            'validation': True,
            'smoothing': True
        }
    
    with PIVlabStreamProcessor() as processor:
        
        for pos in range(num_positions):
            for ch in range(num_channels):
                
                print(f"\n--- Position {pos}, Channel {ch} ---")
                
                # Process this position/channel
                frame_gen = nd2_frame_generator(nd2_path, channel=ch, position=pos)
                
                results = []
                for result in processor.process_image_generator(frame_gen, piv_params):
                    results.append(result)
                    print(f"  Pair {result['pair_index']}: mean_vel={result['mean_velocity']:.2f}")
                
                # Save to .mat file
                output_file = output_path / f"piv_pos{pos:02d}_ch{ch:02d}.mat"
                save_results_to_mat(results, str(output_file))
    
    print(f"\nAll results saved to {output_dir}")


# Example usage functions

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python save_to_mat.py <nd2_file> [output.mat]")
        print("\nExample:")
        print("  python save_to_mat.py data.nd2 results.mat")
        sys.exit(1)
    
    nd2_file = sys.argv[1]
    
    if len(sys.argv) > 2:
        output_mat = sys.argv[2]
    else:
        # Auto-generate output filename
        output_mat = Path(nd2_file).stem + "_piv_results.mat"
    
    print(f"Input: {nd2_file}")
    print(f"Output: {output_mat}\n")
    
    # Process and save
    roi = (100, 400, 100, 400)  # Adjust as needed, or set to None
    save_results_incrementally(nd2_file, output_mat, roi=roi)
    
    print("\n✓ Done! You can now open the .mat file in MATLAB:")
    print(f"  >> load('{output_mat}')")
