import numpy as np
import cv2
import json
import os
from typing import Dict, Any, List
from .base_effect import BaseEffect

class Miner(BaseEffect):
    """Motion-revealed gradient effect - colors are 'mined' through movement."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.description = "Motion-revealed gradient - ←/→ to change gradient, S=toggle"
        
        # Effect state
        self.active = True
        self.current_gradient_index = 0
        self.gradients = []
        self.current_gradient_lut = None
        
        # Motion tracking
        self.velocity_map = None
        self.previous_frame_hsv = None
        self.cached_frame_size = None
        
        # Parameters
        self.decay_factor = 0.92  # How quickly static pixels lose mining progress
        self.sensitivity = 120.0  # How much change needed to dig deeper (much harder to reach deep colors)
        self.accumulation_rate = 0.7  # How fast motion builds up depth (much slower)
        self.movement_threshold = 15.0  # Minimum change to register as movement (filter camera noise)
        
        # Load gradients
        self._load_gradients()
        
    def _load_gradients(self):
        """Load all gradient JSON files from gradients folder."""
        gradients_path = "gradients"
        if not os.path.exists(gradients_path):
            print("❌ Gradients folder not found")
            return
            
        try:
            for filename in os.listdir(gradients_path):
                if filename.endswith('.json'):
                    filepath = os.path.join(gradients_path, filename)
                    with open(filepath, 'r') as f:
                        gradient_data = json.load(f)
                        self.gradients.append(gradient_data)
                        
            if self.gradients:
                print(f"⛏️ Loaded {len(self.gradients)} gradients for mining")
                self._generate_current_lut()
            else:
                print("❌ No gradient files found")
                
        except Exception as e:
            print(f"❌ Error loading gradients: {e}")
            
    def _generate_current_lut(self):
        """Generate OpenCV-compatible lookup table from current gradient."""
        if not self.gradients:
            return
            
        gradient = self.gradients[self.current_gradient_index]
        stops = gradient['stops']
        
        # Create 256-entry lookup table for each channel (BGR format for OpenCV)
        b_lut = np.zeros(256, dtype=np.uint8)
        g_lut = np.zeros(256, dtype=np.uint8) 
        r_lut = np.zeros(256, dtype=np.uint8)
        
        for i in range(256):
            # Normalize depth to 0-1 range
            depth = i / 255.0
            
            # Get RGB color from gradient
            color = self._interpolate_gradient_color(stops, depth)
            
            # OpenCV uses BGR, so reverse the order
            b_lut[i] = color[2]  # Blue
            g_lut[i] = color[1]  # Green  
            r_lut[i] = color[0]  # Red
            
        # Combine into OpenCV LUT format
        self.current_gradient_lut = np.column_stack((b_lut, g_lut, r_lut))
            
    def _interpolate_gradient_color(self, stops: List, position: float) -> List[int]:
        """Interpolate color at given position in gradient."""
        # Clamp position to [0, 1]
        position = max(0.0, min(1.0, position))
        
        # Find surrounding stops
        for i in range(len(stops) - 1):
            stop1 = stops[i]
            stop2 = stops[i + 1]
            
            if position <= stop2['position']:
                # Interpolate between stop1 and stop2
                if stop1['position'] == stop2['position']:
                    return stop1['color']
                    
                t = (position - stop1['position']) / (stop2['position'] - stop1['position'])
                
                color = []
                for j in range(3):  # RGB only
                    c1 = stop1['color'][j]
                    c2 = stop2['color'][j]
                    interpolated = c1 + t * (c2 - c1)
                    color.append(int(np.clip(interpolated, 0, 255)))
                    
                return color
                
        # If we get here, use the last stop
        return stops[-1]['color'][:3]
        
    def _calculate_hsv_change(self, current_hsv: np.ndarray, previous_hsv: np.ndarray) -> np.ndarray:
        """Calculate HSV change magnitude between frames."""
        # Handle hue wraparound (0-179 in OpenCV)
        h_diff = np.abs(current_hsv[:, :, 0].astype(float) - previous_hsv[:, :, 0].astype(float))
        h_diff = np.minimum(h_diff, 180 - h_diff)  # Circular distance
        
        # Saturation and value differences
        s_diff = np.abs(current_hsv[:, :, 1].astype(float) - previous_hsv[:, :, 1].astype(float))
        v_diff = np.abs(current_hsv[:, :, 2].astype(float) - previous_hsv[:, :, 2].astype(float))
        
        # Combined magnitude (normalized to 0-255 range)
        change_magnitude = np.sqrt((h_diff/180)**2 + (s_diff/255)**2 + (v_diff/255)**2) * 255
        return change_magnitude
        
    def process_frame(self, frame: np.ndarray, audio_data: Dict[str, Any]) -> np.ndarray:
        """Apply motion-revealed gradient effect."""
        if frame is None or not self.active or self.current_gradient_lut is None:
            return frame
            
        # Initialize or check frame size
        current_frame_size = frame.shape[:2]
        if (self.velocity_map is None or 
            self.cached_frame_size != current_frame_size):
            self.velocity_map = np.zeros(current_frame_size, dtype=np.float32)
            self.cached_frame_size = current_frame_size
            
        # Convert to HSV for change detection
        current_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        if self.previous_frame_hsv is not None:
            # Calculate HSV change magnitude
            change_magnitude = self._calculate_hsv_change(current_hsv, self.previous_frame_hsv)
            
            # Apply movement threshold to filter out camera noise/jitter
            significant_change = np.where(change_magnitude > self.movement_threshold, 
                                        change_magnitude, 0)
            
            # Update velocity map with exponential accumulation
            # velocity = decay * velocity + accumulation_rate * change^2 (exponential)
            exponential_change = np.power(significant_change / 255.0, 2) * 255.0
            self.velocity_map = (self.decay_factor * self.velocity_map + 
                               self.accumulation_rate * exponential_change)
            
        # Store current frame for next iteration
        self.previous_frame_hsv = current_hsv.copy()
        
        # Convert velocity to gradient depth using tanh for smooth saturation
        gradient_depth = np.tanh(self.velocity_map / self.sensitivity)
        
        # Convert depth to gradient colors
        depth_indices = (gradient_depth * 255).astype(np.uint8)
        mined_colors = self.current_gradient_lut[depth_indices]
        
        # Get base gradient color (depth 0) for static pixels
        base_color = self.current_gradient_lut[0]  # First color in gradient
        base_colors = np.full_like(frame, base_color, dtype=np.uint8)
        
        # Blend from base color to mined colors based on depth
        # Static pixels (depth=0) show base color, moving pixels show deeper colors
        mined_colors_float = mined_colors.astype(np.float32)
        base_colors_float = base_colors.astype(np.float32)
        gradient_depth_3d = np.stack([gradient_depth, gradient_depth, gradient_depth], axis=2)
        
        result = ((1.0 - gradient_depth_3d) * base_colors_float + 
                 gradient_depth_3d * mined_colors_float).astype(np.uint8)
        
        return result
        
    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameter values."""
        gradient_name = self.gradients[self.current_gradient_index]['name'] if self.gradients else "None"
        return {
            'active': self.active,
            'current_gradient': gradient_name,
            'gradient_index': self.current_gradient_index,
            'decay_factor': self.decay_factor,
            'sensitivity': self.sensitivity,
            'accumulation_rate': self.accumulation_rate
        }
        
    def set_parameter(self, name: str, value: Any) -> bool:
        """Set parameter value."""
        if name == 'active':
            self.active = bool(value)
            status = "ON" if self.active else "OFF"
            print(f"⛏️ Miner effect: {status}")
            return True
        elif name == 'toggle':
            self.set_parameter('active', not self.active)
            return True
        elif name == 'next_gradient':
            if self.gradients:
                self.current_gradient_index = (self.current_gradient_index + 1) % len(self.gradients)
                self._generate_current_lut()
                gradient_name = self.gradients[self.current_gradient_index]['name']
                print(f"⛏️➡️ Mining: {gradient_name}")
            return True
        elif name == 'prev_gradient':
            if self.gradients:
                self.current_gradient_index = (self.current_gradient_index - 1) % len(self.gradients)
                self._generate_current_lut()
                gradient_name = self.gradients[self.current_gradient_index]['name']
                print(f"⛏️⬅️ Mining: {gradient_name}")
            return True
        return False
        
    def handle_key_press(self, key: int, app_ref) -> bool:
        """Handle key press events."""
        if key == ord('s'):
            self.set_parameter('toggle', True)
            return True
        elif key == 2:  # Left arrow - previous gradient
            self.set_parameter('prev_gradient', True)
            return True
        elif key == 3:  # Right arrow - next gradient
            self.set_parameter('next_gradient', True)
            return True
        return False
        
    def reset(self):
        """Reset effect to default state."""
        self.active = True
        self.velocity_map = None
        self.previous_frame_hsv = None
        self.cached_frame_size = None
        
    def cleanup(self):
        """Cleanup resources."""
        self.velocity_map = None
        self.previous_frame_hsv = None