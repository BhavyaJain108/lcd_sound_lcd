#!/usr/bin/env python3
"""Test script to generate I/O masks using the ki_alternate algorithm."""

# Import the algorithm from the new file
from ki_alternate_algorithm import should_invert_pixel, generate_mask

def print_mask(mask, n: int, t: int):
    """Print the mask in a formatted way."""
    print(f"\n--- Mask for n={n}, t={t} ---")
    # Convert boolean mask to I/O string
    for row in mask:
        line = ""
        for pixel in row:
            line += "I" if pixel else "O"
        print(line)
    print()

def main():
    """Test the algorithm for 31 pixel width, times 0-15."""
    pixel_width = 31
    grid_size = 31  # Same size as pixel width for cleaner patterns
    
    # Test times 0 through 15
    for time in range(16):
        mask = generate_mask(grid_size, grid_size, time, pixel_width)
        print_mask(mask, pixel_width, time)

if __name__ == "__main__":
    main()