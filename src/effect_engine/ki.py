import numpy as np
import cv2
from typing import Dict, Any
from .base_effect import BaseEffect

class Ki(BaseEffect):
    """Diamond grid effect with animated diamond tessellation."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.description = "Diamond grid effect - Up/Down=size, S=toggle"
        
        # Effect state
        self.active = True
        self.diamond_width = 63  # Width of each diamond
        self.max_diamond_width = 189  # 3x the original max (9*9*3 = 243, but let's use 189 for 3x63)
        self.min_diamond_width = 9    # Minimum size
        self.size_increment = 9       # Same increment as original (9 pixels per step)
        
        # Animation state
        self.animation_frame = 0      # Current frame in animation cycle
        self.frame_counter = 0        # Counter for timing
        
        # Pre-computed masks
        self.base_mask = None         # Static diamond pattern
        self.animation_masks = {}     # Cache for animation frame masks
        self.cached_frame_size = None
        
    def _should_invert_pixel(self, x: int, y: int, n: int) -> bool:
        """Determine if pixel should be inverted using the diamond formula."""
        cycle_length = n + 1
        row = y % cycle_length
        
        # Handle symmetry: rows mirror within first n rows
        if row > n // 2:
            row = n - 1 - row
        
        # Row pattern: (n-2*row) 0's, (2*row+1) 1's
        num_zeros = n - 2*row
        
        # Apply offset (shift pattern to the right by row positions)
        adjusted_x = (x - row) % cycle_length
        
        # Return True for I (invert), False for O (original)
        return adjusted_x >= num_zeros
        
    def _generate_invert_mask(self, frame_shape: tuple):
        """Generate boolean mask for which pixels to invert using diamond formula."""
        height, width = frame_shape[:2]
        
        # Create mask
        self.invert_mask = np.zeros((height, width), dtype=bool)
        
        # Calculate mask for each pixel using the diamond formula
        for y in range(height):
            for x in range(width):
                self.invert_mask[y, x] = self._should_invert_pixel(x, y, self.diamond_width)
                
        # Cache the frame size this mask was generated for
        self.cached_frame_size = frame_shape[:2]
        
        
    def process_frame(self, frame: np.ndarray, audio_data: Dict[str, Any]) -> np.ndarray:
        """Apply diamond grid inversion effect."""
        if frame is None or not self.active:
            return frame
            
        # Check if we need to regenerate mask
        current_frame_size = frame.shape[:2]
        if (self.invert_mask is None or 
            self.cached_frame_size != current_frame_size):
            self._generate_invert_mask(frame.shape)
            
        # Apply inversion mask
        result = frame.copy()
        # Invert each color channel separately to avoid broadcasting issues
        for channel in range(result.shape[2]):
            result[:, :, channel][self.invert_mask] = 255 - result[:, :, channel][self.invert_mask]
        
        return result
        
    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameter values."""
        return {
            'active': self.active,
            'diamond_width': self.diamond_width,
            'cached_frame_size': self.cached_frame_size
        }
        
    def set_parameter(self, name: str, value: Any) -> bool:
        """Set parameter value."""
        if name == 'active':
            self.active = bool(value)
            status = "ON" if self.active else "OFF"
            print(f"◊ Ki effect: {status}")
            return True
        elif name == 'toggle':
            self.set_parameter('active', not self.active)
            return True
        elif name == 'diamond_width':
            new_value = max(self.min_diamond_width, min(self.max_diamond_width, int(value)))
            if new_value != self.diamond_width:
                self.diamond_width = new_value
                # Force mask regeneration on next frame
                self.invert_mask = None
                print(f"◊ Diamond width: {self.diamond_width}px")
            return True
        return False
        
    def handle_key_press(self, key: int, app_ref) -> bool:
        """Handle key press events."""
        # Up arrow - increase diamond size
        if key == 0:  # Up arrow (Mac)
            new_width = self.diamond_width + self.size_increment
            self.set_parameter('diamond_width', new_width)
            return True
        # Down arrow - decrease diamond size
        elif key == 1:  # Down arrow (Mac)
            new_width = self.diamond_width - self.size_increment
            self.set_parameter('diamond_width', new_width)
            return True
        # S key to toggle effect
        elif key == ord('s'):
            self.set_parameter('toggle', True)
            return True
        return False
        
    def reset(self):
        """Reset effect to default state."""
        self.diamond_width = 63
        self.invert_mask = None
        self.cached_frame_size = None
        
    def cleanup(self):
        """Cleanup resources."""
        self.invert_mask = None