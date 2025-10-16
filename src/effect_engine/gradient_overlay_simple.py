import numpy as np
import cv2
import json
import os
from typing import Dict, Any, List, Tuple
from .base_effect import BaseEffect

class GradientOverlaySimple(BaseEffect):
    """Gradient color grading effect using luminance mapping with Color blend mode."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.description = "Color grading effect using gradients - ←/→ to change gradient, ↑/↓ for opacity"
        
        # Effect state
        self.active = True
        self.opacity = 50  # 0-100%
        self.current_gradient_index = 0
        self.gradients = []
        self.current_gradient_lut = None
        
        # Load gradients from folder
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
                print(f"📊 Loaded {len(self.gradients)} gradients")
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
            # Normalize luminance to 0-1 range
            luminance = i / 255.0
            
            # Get RGB color from gradient
            color = self._interpolate_gradient_color(stops, luminance)
            
            # OpenCV uses BGR, so reverse the order
            b_lut[i] = color[2]  # Blue
            g_lut[i] = color[1]  # Green  
            r_lut[i] = color[0]  # Red
            
        # Combine into OpenCV LUT format (256, 3) for grayscale to BGR conversion
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
        
    def process_frame(self, frame: np.ndarray, audio_data: Dict[str, Any]) -> np.ndarray:
        """Apply gradient color grading to frame using fast OpenCV LUT."""
        if frame is None:
            return frame
        if self.current_gradient_lut is None:
            return frame
        if not self.active:
            return frame
            
        # Convert to grayscale for luminance mapping
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply gradient LUT using simple numpy indexing for now (until LUT format is fixed)
        gradient_frame = self.current_gradient_lut[gray]
        
        # Simple alpha blend with original frame based on opacity
        if self.opacity < 100:
            alpha = self.opacity / 100.0
            result = cv2.addWeighted(frame, 1.0 - alpha, gradient_frame, alpha, 0)
        else:
            result = gradient_frame
            
        return result
        
    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameter values."""
        gradient_name = self.gradients[self.current_gradient_index]['name'] if self.gradients else "None"
        return {
            'active': self.active,
            'opacity': self.opacity,
            'current_gradient': gradient_name,
            'gradient_index': self.current_gradient_index
        }
        
    def set_parameter(self, name: str, value: Any) -> bool:
        """Set parameter value."""
        if name == 'active':
            self.active = bool(value)
            status = "ON" if self.active else "OFF"
            print(f"🎨 Gradient overlay: {status}")
            return True
        elif name == 'opacity':
            self.opacity = max(0, min(100, int(value)))
            return True
        elif name == 'toggle':
            self.set_parameter('active', not self.active)
            return True
        elif name == 'next_gradient':
            if self.gradients:
                self.current_gradient_index = (self.current_gradient_index + 1) % len(self.gradients)
                self._generate_current_lut()
                gradient_name = self.gradients[self.current_gradient_index]['name']
                print(f"➡️ Gradient: {gradient_name}")
            return True
        elif name == 'prev_gradient':
            if self.gradients:
                self.current_gradient_index = (self.current_gradient_index - 1) % len(self.gradients)
                self._generate_current_lut()
                gradient_name = self.gradients[self.current_gradient_index]['name']
                print(f"⬅️ Gradient: {gradient_name}")
            return True
        elif name == 'increase_opacity':
            new_opacity = min(100, self.opacity + 5)
            if new_opacity != self.opacity:
                self.opacity = new_opacity
                print(f"⬆️ Opacity: {self.opacity}%")
            return True
        elif name == 'decrease_opacity':
            new_opacity = max(0, self.opacity - 5)
            if new_opacity != self.opacity:
                self.opacity = new_opacity
                print(f"⬇️ Opacity: {self.opacity}%")
            return True
        return False
        
    def handle_key_press(self, key: int, app_ref) -> bool:
        """Handle key press events."""
        if key == ord('s'):
            self.set_parameter('toggle', True)
            return True
        elif key == 2:  # Left arrow (Mac) - previous gradient
            self.set_parameter('prev_gradient', True)
            return True
        elif key == 3:  # Right arrow (Mac) - next gradient
            self.set_parameter('next_gradient', True)
            return True
        elif key == 0:  # Up arrow (Mac) - increase opacity
            self.set_parameter('increase_opacity', True)
            return True
        elif key == 1:  # Down arrow (Mac) - decrease opacity
            self.set_parameter('decrease_opacity', True)
            return True
        return False