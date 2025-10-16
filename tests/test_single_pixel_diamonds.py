#!/usr/bin/env python3
"""
Test for single pixel diamonds (edge_length=1) to see the pure tessellation pattern.
This shows what the ideal diamond grid should look like.
"""

def calculate_diamond_row(x: int, y: int, edge_length: int) -> int:
    """Same formula as in Ki effect."""
    # Transform to diamond grid coordinates
    diamond_u = (x + y) / edge_length
    diamond_v = (-x + y) / edge_length
    
    # Get integer grid coordinates with offset to fix boundary issues
    grid_u = int(diamond_u + 0.5)
    grid_v = int(diamond_v + 0.5)
    
    # Row calculation for alternating pattern
    row = grid_u + grid_v
    return row

def test_single_pixel_diamonds(width=20, height=20):
    """Test with edge_length=1 (each pixel is a diamond)."""
    edge_length = 1
    print(f"Single pixel diamonds: {width}x{height} pixels, edge_length={edge_length}")
    print("O = Original (even rows), I = Inverted (odd rows)")
    print("Each pixel should be its own diamond")
    print()
    
    # Create and display the grid
    for y in range(height):
        row_str = ""
        row_nums = ""
        for x in range(width):
            row_num = calculate_diamond_row(x, y, edge_length)
            letter = "I" if row_num % 2 == 1 else "O"
            row_str += letter
            row_nums += f"{row_num%10}"
        print(f"Y{y:2d}: {row_str}")
        print(f"    {row_nums}")
    
    print()
    print("=== Analysis ===")
    print("For single pixel diamonds, we should see a checkerboard pattern")
    print("where adjacent pixels alternate between O and I")
    print("This shows us the pure mathematical pattern our formula creates")

if __name__ == "__main__":
    print("=== Single Pixel Diamond Test ===")
    test_single_pixel_diamonds(width=15, height=15)