import numpy as np
import cv2
from typing import Dict, Any
from .base_effect import BaseEffect
from .gradient_overlay_simple import GradientOverlaySimple

class KiAlt(BaseEffect):
    """Ki Alternate Algorithm effect with gradient support."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.description = "Ki Alternate Algorithm - S=toggle, ↑/↓=pixel_width, ←/→=gradient, +/−=speed, [/]=opacity"
        
        self.active = True
        self.global_frame_counter = 0
        self.pixel_width = 19  # Default pixel width
        self.min_pixel_width = 9
        self.max_pixel_width = 199
        self.time_multiplier = 1  # Speed multiplier (1 = normal speed)
        self.gradient_opacity = 100  # Gradient opacity for I pixels (starts at 100% like original)
        self.invert_mask = None
        self.cached_frame_size = None
        
        # Gradient system using existing gradient overlay
        self.gradient_system = GradientOverlaySimple("ki_alt_gradients")
        
    def _find_nearest_center(self, x: int, y: int, pixel_width: int, image_width: int, image_height: int):
        """Find the nearest grid center to the given pixel position."""
        p = pixel_width
        q = (p - 1) // 2
        
        # Safety check
        if q <= 0:
            return (0, 0)
            
        possible_centers = []
        
        # Type 1 centers: (2x*q, 2y*q)
        max_grid_x = image_width // (2 * q) + 2
        max_grid_y = image_height // (2 * q) + 2
        
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
        
        # If equidistant from multiple centers or no centers found, return default
        if len(nearest_centers) != 1:
            return (0, 0)
        
        return nearest_centers[0]
    
    def _should_invert_pixel(self, x: int, y: int, time_param: int, pixel_width: int, image_width: int, image_height: int) -> bool:
        """Determine if pixel should be inverted using the ki_alternate algorithm."""
        try:
            # Step 1: Find nearest center
            center = self._find_nearest_center(x, y, pixel_width, image_width, image_height)
            
            # Safety check
            if center is None:
                return False
            
            center_x, center_y = center
            
            # Step 2: Calculate Manhattan distance
            distance = abs(x - center_x) + abs(y - center_y)
            
            # Step 3: Apply time-based threshold
            threshold = time_param // 2
            is_invert = distance <= threshold
            
            # Step 4: Determine center type and apply inversion
            q = (pixel_width - 1) // 2
            if q > 0:
                is_type2_center = (center_x // q) % 2 == 1 and (center_y // q) % 2 == 1
                if is_type2_center:
                    is_invert = not is_invert
            
            return is_invert
        except Exception as e:
            # For any error, default to not inverting (keep original)
            return False

    def _generate_ki_alternate_mask_direct(self, frame_shape: tuple, time_param: int, pixel_width: int, frame_counter: int):
        """Generate boolean mask using direct mathematical calculation O(1) per pixel."""
        try:
            height, width = frame_shape[:2]
            
            # Safety checks
            if pixel_width <= 0 or time_param < 0:
                self.invert_mask = np.zeros((height, width), dtype=bool)
                return
            
            # Calculate q
            q = (pixel_width - 1) // 2
            if q <= 0:
                self.invert_mask = np.zeros((height, width), dtype=bool)
                return
            
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
            # Each cycle is pixel_width frames
            cycle_number = frame_counter // pixel_width
            if cycle_number % 2 == 1:
                pattern_mask = ~pattern_mask
                
            self.invert_mask = pattern_mask
            
            # Cache the frame size this mask was generated for
            self.cached_frame_size = frame_shape[:2]
            
        except Exception as e:
            height, width = frame_shape[:2]
            self.invert_mask = np.zeros((height, width), dtype=bool)
            self.cached_frame_size = frame_shape[:2]
        
    def process_frame(self, frame: np.ndarray, audio_data: Dict[str, Any]) -> np.ndarray:
        """Apply Ki Alternate Algorithm with gradient coloring to I pixels."""
        if frame is None or not self.active:
            return frame
            
        self.global_frame_counter += 1
        
        # Time parameter is frame count multiplied by speed, then modded by pixel_width
        time = (self.global_frame_counter * self.time_multiplier) % self.pixel_width
        
        # Generate Ki alternate algorithm mask
        self._generate_ki_alternate_mask_direct(frame.shape, time, self.pixel_width, self.global_frame_counter * self.time_multiplier)
        
        result = frame.copy()
        
        # Apply gradient with see-saw opacity
        if self.invert_mask is not None and self.gradient_system.current_gradient_lut is not None:
            # Get luminance values for all pixels
            gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
            
            # Calculate see-saw opacities (handle negative values for seamless looping)
            abs_opacity = abs(self.gradient_opacity)
            i_opacity = abs_opacity / 100.0  # I pixel gradient opacity
            o_opacity = (100 - abs_opacity) / 100.0  # O pixel gradient opacity (opposite)
            
            # Apply gradient to I pixels (True in mask)
            i_mask_indices = np.where(self.invert_mask)
            if len(i_mask_indices[0]) > 0:
                luminance_values = gray[i_mask_indices]
                luminance_values = np.clip(luminance_values, 0, len(self.gradient_system.current_gradient_lut) - 1)
                
                # Blend original with gradient based on i_opacity
                original_i_pixels = result[i_mask_indices]
                gradient_i_pixels = self.gradient_system.current_gradient_lut[luminance_values]
                result[i_mask_indices] = (1.0 - i_opacity) * original_i_pixels + i_opacity * gradient_i_pixels
            
            # Apply gradient to O pixels (False in mask) 
            o_mask_indices = np.where(~self.invert_mask)
            if len(o_mask_indices[0]) > 0:
                luminance_values = gray[o_mask_indices]
                luminance_values = np.clip(luminance_values, 0, len(self.gradient_system.current_gradient_lut) - 1)
                
                # Blend original with gradient based on o_opacity
                original_o_pixels = result[o_mask_indices]
                gradient_o_pixels = self.gradient_system.current_gradient_lut[luminance_values]
                result[o_mask_indices] = (1.0 - o_opacity) * original_o_pixels + o_opacity * gradient_o_pixels
        elif self.invert_mask is not None:
            # Fallback to inversion if no gradient available
            for channel in range(result.shape[2]):
                result[:, :, channel][self.invert_mask] = 255 - result[:, :, channel][self.invert_mask]
        
        return result
        
    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameter values."""
        return {
            'active': self.active,
            'global_frame_counter': self.global_frame_counter,
            'pixel_width': self.pixel_width,
            'time_multiplier': self.time_multiplier,
            'gradient_opacity': self.gradient_opacity
        }
        
    def set_parameter(self, name: str, value: Any) -> bool:
        """Set parameter value."""
        if name == 'active':
            self.active = bool(value)
            status = "ON" if self.active else "OFF"
            print(f"📊 Frame counter: {status}")
            return True
        elif name == 'toggle':
            self.set_parameter('active', not self.active)
            return True
        elif name == 'reset_counter':
            self.global_frame_counter = 0
            print(f"🔄 Frame counter reset to 0")
            return True
        elif name == 'pixel_width':
            new_value = max(self.min_pixel_width, min(self.max_pixel_width, int(value)))
            if new_value != self.pixel_width:
                self.pixel_width = new_value
                print(f"◊ Pixel width: {self.pixel_width}")
            return True
        return False
        
    def handle_key_press(self, key: int, app_ref) -> bool:
        """Handle key press events."""
        if key == ord('s'):
            self.set_parameter('toggle', True)
            return True
        elif key == ord('r'):
            self.set_parameter('reset_counter', True)
            return True
        elif key == 0:  # Up arrow - increase pixel width
            new_width = self.pixel_width + 10  # Increase by 10 pixels
            self.set_parameter('pixel_width', new_width)
            return True
        elif key == 1:  # Down arrow - decrease pixel width
            new_width = self.pixel_width - 10  # Decrease by 10 pixels
            self.set_parameter('pixel_width', new_width)
            return True
        elif key == 2:  # Left arrow - previous gradient
            if self.gradient_system.gradients:
                self.gradient_system.current_gradient_index = (self.gradient_system.current_gradient_index - 1) % len(self.gradient_system.gradients)
                self.gradient_system._generate_current_lut()
            return True
        elif key == 3:  # Right arrow - next gradient
            if self.gradient_system.gradients:
                self.gradient_system.current_gradient_index = (self.gradient_system.current_gradient_index + 1) % len(self.gradient_system.gradients)
                self.gradient_system._generate_current_lut()
            return True
        elif key == ord('+') or key == ord('='):  # Plus key - increase speed
            self.time_multiplier += 1
            return True
        elif key == ord('-'):  # Minus key - decrease speed
            self.time_multiplier = max(1, self.time_multiplier - 1)  # Don't go below 1
            return True
        elif key == ord(']'):  # Right bracket - increase gradient opacity
            self.gradient_opacity += 1
            # Loop: when it goes past 100, wrap to -100 (same visual effect as 100)
            if self.gradient_opacity > 100:
                self.gradient_opacity = -100
            print(f"◊ Gradient opacity: {self.gradient_opacity}% (I={abs(self.gradient_opacity)}%, O={100-abs(self.gradient_opacity)}%)")
            return True
        elif key == ord('['):  # Left bracket - decrease gradient opacity
            self.gradient_opacity -= 1
            # Loop: when it goes past -100, wrap to 100
            if self.gradient_opacity < -100:
                self.gradient_opacity = 100
            print(f"◊ Gradient opacity: {self.gradient_opacity}% (I={abs(self.gradient_opacity)}%, O={100-abs(self.gradient_opacity)}%)")
            return True
        return False
        
    def reset(self):
        """Reset effect to default state."""
        self.global_frame_counter = 0
        self.pixel_width = 19
        self.time_multiplier = 1
        self.gradient_opacity = 100
        self.invert_mask = None
        self.cached_frame_size = None
        
    def cleanup(self):
        """Cleanup resources."""
        self.invert_mask = None