#!/usr/bin/env python3
"""
Test diamond formula using diamond width directly.
Width will always be odd.
"""

def is_in_O_region(pos_x, cycle_y, diamond_width):
    """Determine if position should be O in an O-diamond."""
    # For diamond_width=5, the expected pattern is:
    # Row 0: OOOOOI (5 O's, then I's)
    # Row 1: IOOOII (1 I, 3 O's, then I's)  
    # Row 2: IIOIII (2 I's, 1 O, then I's) - center row
    # Row 3: IOOOII (mirror of row 1)
    # Row 4: OOOOOI (mirror of row 0)
    
    center = diamond_width // 2  # For width=5, center=2
    
    # Distance from center row
    if cycle_y <= center:
        dist_from_center = cycle_y
    else:
        dist_from_center = diamond_width - 1 - cycle_y
    
    # Number of O's starts at diamond_width and shrinks toward center
    # Row 0 (dist=2): 5 O's
    # Row 1 (dist=1): 3 O's  
    # Row 2 (dist=0): 1 O
    num_Os = diamond_width - (dist_from_center * 2)
    
    # Number of I's on the left side
    num_left_Is = dist_from_center
    
    # Check if this position is in the O region
    # Pattern: [I's][O's][I's] within each diamond
    return num_left_Is <= pos_x < (num_left_Is + num_Os)

def get_pixel_value(x, y, n):
    """Get pixel value using the formula from DIAMOND_FORMULA.TXT"""
    cycle_length = n + 1
    row = y % cycle_length
    
    # Handle symmetry: rows mirror within first n rows
    # Row 0 = Row (n-1), Row 1 = Row (n-2), etc.
    if row > n // 2:
        row = n - 1 - row
    
    # Row pattern: (n-2*row) 0's, (2*row+1) 1's
    num_zeros = n - 2*row
    
    # Apply offset (shift pattern to the right by row positions)
    adjusted_x = (x - row) % cycle_length
    
    # Determine if in 0 region or 1 region
    if adjusted_x < num_zeros:
        return 'O'  # 0 becomes O
    else:
        return 'I'  # 1 becomes I

def test_diamond_width(width=5, display_width=20, display_height=10):
    """Test with specific diamond width."""
    print(f"Diamond width: {width}")
    print(f"Display: {display_width}x{display_height}")
    print()
    
    for y in range(display_height):
        row_str = ""
        for x in range(display_width):
            pixel = get_pixel_value(x, y, width)
            row_str += pixel
        print(f"Row {y}: {row_str}")

if __name__ == "__main__":
    print("=== Diamond Width Formula Test ===")
    
    # Test n=11 
    print("n=11 (rows 0 to 10, 36 pixels wide):")
    for y in range(11):
        row_str = ""
        for x in range(36):
            pixel = get_pixel_value(x, y, 11)
            row_str += pixel
        print(f"Row {y}: {row_str}")
    
    print()