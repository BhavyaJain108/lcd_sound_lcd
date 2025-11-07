#!/usr/bin/env python3
"""
Test Ki Alt Algorithm Pattern Generation
Shows the pattern for n=41, t=[0,41)
"""
import numpy as np

def generate_ki_alt_mask(width, height, time_param, pixel_width):
    """Generate Ki Alt mask using direct mathematical calculation."""
    
    # Calculate q
    q = (pixel_width - 1) // 2
    if q <= 0:
        return np.zeros((height, width), dtype=bool)
    
    # Create coordinate grids
    Y, X = np.meshgrid(np.arange(height), np.arange(width), indexing='ij')
    
    # Find which 2q×2q cell each pixel is in
    cell_x = X // (2 * q)
    cell_y = Y // (2 * q)
    
    # The 4 candidate centers for any pixel are:
    # Type 1: (cell_x * 2q, cell_y * 2q) - bottom-left corner
    # Type 1: ((cell_x+1) * 2q, cell_y * 2q) - bottom-right corner  
    # Type 1: (cell_x * 2q, (cell_y+1) * 2q) - top-left corner
    # Type 2: ((cell_x*2+1) * q, (cell_y*2+1) * q) - center of cell
    
    # Calculate distances to all 4 candidate centers
    center1_x = cell_x * (2 * q)
    center1_y = cell_y * (2 * q)
    dist1 = np.abs(X - center1_x) + np.abs(Y - center1_y)
    
    center2_x = (cell_x + 1) * (2 * q)
    center2_y = cell_y * (2 * q)
    dist2 = np.abs(X - center2_x) + np.abs(Y - center2_y)
    
    center3_x = cell_x * (2 * q)
    center3_y = (cell_y + 1) * (2 * q)
    dist3 = np.abs(X - center3_x) + np.abs(Y - center3_y)
    
    center4_x = (cell_x + 1) * (2 * q)
    center4_y = (cell_y + 1) * (2 * q) 
    dist4 = np.abs(X - center4_x) + np.abs(Y - center4_y)
    
    center5_x = (cell_x * 2 + 1) * q
    center5_y = (cell_y * 2 + 1) * q
    dist5 = np.abs(X - center5_x) + np.abs(Y - center5_y)
    
    # Find which center is nearest for each pixel
    min_dist = np.minimum(np.minimum(np.minimum(dist1, dist2), np.minimum(dist3, dist4)), dist5)
    
    # Determine if nearest center is type 2 (center5)
    is_type2_nearest = (dist5 == min_dist)
    
    # Apply time-based threshold  
    # Use modulo to ensure proper cycling
    effective_time = time_param % pixel_width
    threshold = effective_time // 2
    base_invert = min_dist <= threshold
    
    # Apply center type inversion for type 2 centers
    pattern_mask = np.where(is_type2_nearest, ~base_invert, base_invert)
    
    # Flip the entire pattern every cycle
    # Full cycle is 2 * pixel_width (since threshold goes 0 to pixel_width//2)
    cycle_number = time_param // (2 * pixel_width)
    if time_param <= 32:  # Debug for first few values
        print(f"DEBUG: t={time_param}, cycle_number={cycle_number}, flip={(cycle_number % 2 == 1)}")
    if cycle_number % 2 == 1:
        pattern_mask = ~pattern_mask
        
    invert_mask = pattern_mask
    
    return invert_mask

def print_mask(mask, title):
    """Print mask as I/O pattern."""
    print(f"\n{title}:")
    for row in mask:
        line = ""
        for pixel in row:
            line += "I" if pixel else "O"
        print(line)

if __name__ == "__main__":
    # Test with n=15, grid size 40x40
    pixel_width = 15
    width, height = 40, 40  # 40x40 grid
    
    print(f"Ki Alt Algorithm Test (n={pixel_width})")
    print(f"Grid size: {width}x{height}")
    print(f"q = (n-1)//2 = {(pixel_width-1)//2}")
    
    # Show patterns for t=[0,30] to see full animation cycle
    for t in range(0, 31):
        mask = generate_ki_alt_mask(width, height, t, pixel_width)
        print_mask(mask, f"t={t}")
        print()  # Extra line between patterns