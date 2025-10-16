#!/usr/bin/env python3
"""
Simple test for diamond grid formula to debug the Ki effect.
Creates a small grid and shows the row assignments visually.
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

def test_diamond_grid(width=20, height=20, edge_length=5):
    """Test the diamond formula on a small grid."""
    print(f"Testing diamond grid: {width}x{height} pixels, edge_length={edge_length}")
    print("O = Original (even rows), I = Inverted (odd rows)")
    print()
    
    # Create and display the grid with row numbers
    for y in range(height):
        row_str = ""
        row_nums = ""
        for x in range(width):
            row_num = calculate_diamond_row(x, y, edge_length)
            letter = "I" if row_num % 2 == 1 else "O"
            row_str += letter
            row_nums += f"{row_num%10}"  # Show last digit of row number
        print(f"Y{y:2d}: {row_str}")
        print(f"    {row_nums}")  # Row numbers below each pattern
    
    print()
    
    # Show some specific coordinates and their calculations
    print("Detailed calculations for some points:")
    test_points = [(0,0), (5,0), (0,5), (5,5), (10,10), (2,3), (7,8)]
    
    for x, y in test_points:
        if x < width and y < height:
            diamond_u = (x + y) / edge_length
            diamond_v = (-x + y) / edge_length
            grid_u = int(diamond_u)
            grid_v = int(diamond_v)
            row = grid_u + grid_v
            letter = "I" if row % 2 == 1 else "O"
            
            print(f"({x:2d},{y:2d}): diamond_u={diamond_u:5.1f}, diamond_v={diamond_v:5.1f}, "
                  f"grid_u={grid_u:2d}, grid_v={grid_v:2d}, row={row:2d} -> {letter}")

if __name__ == "__main__":
    print("=== Diamond Grid Formula Test ===")
    
    # Test with different edge lengths
    for edge_len in [3, 5, 7]:
        print(f"\n{'='*50}")
        test_diamond_grid(width=15, height=15, edge_length=edge_len)
        
    print("\n=== Looking for patterns ===")
    print("If you see any merged rectangles or irregular patterns,")
    print("that's where the formula is going wrong!")