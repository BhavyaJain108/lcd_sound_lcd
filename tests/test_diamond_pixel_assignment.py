#!/usr/bin/env python3
"""
Direct pixel assignment approach - determine which diamond each pixel belongs to,
then assign O/I based on diamond position in grid.
"""

def get_diamond_coords(x: int, y: int, edge_length: int) -> tuple:
    """Get which diamond this pixel belongs to."""
    # Transform to diamond coordinate system
    diamond_u = (x + y) / edge_length
    diamond_v = (-x + y) / edge_length
    
    # Get diamond grid coordinates
    diamond_col = int(diamond_u + 0.5)
    diamond_row = int(diamond_v + 0.5)
    
    return (diamond_col, diamond_row)

def should_invert_pixel(x: int, y: int, edge_length: int) -> bool:
    """Direct determination: should this pixel be inverted?"""
    diamond_col, diamond_row = get_diamond_coords(x, y, edge_length)
    
    # Simple checkerboard pattern of diamonds
    # Invert if diamond coordinates sum to odd
    return (diamond_col + diamond_row) % 2 == 1

def test_direct_assignment(width=15, height=15, edge_length=5):
    """Test direct pixel assignment approach."""
    print(f"Direct assignment: {width}x{height} pixels, edge_length={edge_length}")
    print("O = Original, I = Inverted")
    print()
    
    for y in range(height):
        row_str = ""
        coord_str = ""
        for x in range(width):
            should_invert = should_invert_pixel(x, y, edge_length)
            letter = "I" if should_invert else "O"
            row_str += letter
            
            # Show diamond coordinates
            col, row = get_diamond_coords(x, y, edge_length)
            coord_str += f"({col},{row})"[:3]  # Truncate for display
            
        print(f"Y{y:2d}: {row_str}")
        if y < 5:  # Only show coords for first few rows
            print(f"    {coord_str}")
    
    print()
    print("This should create proper diamond tessellation!")

if __name__ == "__main__":
    print("=== Direct Diamond Assignment Test ===")
    test_direct_assignment(width=15, height=15, edge_length=3)
    print()
    test_direct_assignment(width=15, height=15, edge_length=5)