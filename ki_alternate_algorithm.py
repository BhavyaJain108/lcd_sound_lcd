#!/usr/bin/env python3
"""
Ki Alternate Algorithm - Working Implementation

This file contains just the core algorithm without any effect framework dependencies.
Use this as reference for implementing the algorithm in a proper effect.
"""
import numpy as np

def find_nearest_center(x: int, y: int, pixel_width: int, image_width: int, image_height: int):
    """Find the nearest grid center to the given pixel position.
    
    Centers are at:
    1. (2x*q, 2y*q) where x,y are integers and q=(pixel_width-1)/2  
    2. ((2x+1)*q, (2y+1)*q) where x,y are integers
    
    Returns (center_x, center_y) or None if equidistant from multiple centers
    """
    p = pixel_width
    q = (p - 1) // 2
    possible_centers = []
    
    # Type 1 centers: (2x*q, 2y*q)
    max_grid_x = image_width // (2 * q) + 2 if q > 0 else 2
    max_grid_y = image_height // (2 * q) + 2 if q > 0 else 2
    
    for grid_y in range(-1, max_grid_y + 1):
        for grid_x in range(-1, max_grid_x + 1):
            center_x = 2 * grid_x * q
            center_y = 2 * grid_y * q
            possible_centers.append((center_x, center_y))
    
    # Type 2 centers: ((2x+1)*q, (2y+1)*q)
    for grid_y in range(-1, max_grid_y + 1):
        for grid_x in range(-1, max_grid_x + 1):
            center_x = (2 * grid_x + 1) * q
            center_y = (2 * grid_y + 1) * q
            possible_centers.append((center_x, center_y))
    
    # Find the nearest center(s)
    min_distance = float('inf')
    nearest_centers = []
    
    for center_x, center_y in possible_centers:
        distance = abs(x - center_x) + abs(y - center_y)
        if distance < min_distance:
            min_distance = distance
            nearest_centers = [(center_x, center_y)]
        elif distance == min_distance:
            nearest_centers.append((center_x, center_y))
    
    # If equidistant from multiple centers, return None
    if len(nearest_centers) > 1:
        return None
    
    return nearest_centers[0] if nearest_centers else (0, 0)

def should_invert_pixel(x: int, y: int, time: int, pixel_width: int, image_width: int, image_height: int) -> bool:
    """Determine if pixel should be inverted using the ki_alternate algorithm."""
    # Step 1: Find nearest center
    center = find_nearest_center(x, y, pixel_width, image_width, image_height)
    
    # If equidistant from multiple centers, remain O
    if center is None:
        return False
    
    center_x, center_y = center
    
    # Step 2: Calculate Manhattan distance
    distance = abs(x - center_x) + abs(y - center_y)
    
    # Step 3: Apply time-based threshold
    threshold = time // 2
    is_invert = distance <= threshold
    
    # Step 4: Determine center type and apply inversion
    q = (pixel_width - 1) // 2
    if q > 0:
        is_type2_center = (center_x // q) % 2 == 1 and (center_y // q) % 2 == 1
        if is_type2_center:
            is_invert = not is_invert
    
    return is_invert

def generate_mask(width: int, height: int, time: int, pixel_width: int):
    """Generate I/O mask for given dimensions and parameters."""
    import numpy as np
    
    mask = np.zeros((height, width), dtype=bool)
    for y in range(height):
        for x in range(width):
            mask[y, x] = should_invert_pixel(x, y, time, pixel_width, width, height)
    
    return mask

if __name__ == "__main__":
    # Test the algorithm
    import numpy as np
    
    # Test with n=9, t=0 (matches your effect settings)
    mask = generate_mask(10, 10, 0, 9)
    
    print("Ki Alternate Algorithm Test (n=9, t=0):")
    for row in mask:
        line = ""
        for pixel in row:
            line += "I" if pixel else "O"
        print(line)