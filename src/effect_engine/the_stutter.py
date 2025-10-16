import numpy as np
import cv2
from typing import Dict, Any, List
from collections import deque
from .base_effect import BaseEffect

class TheStutter(BaseEffect):
    """Frame stuttering effect showing previous frames with decreasing opacity."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.description = "Motion trail effect - Numbers=frame count, Shift+Numbers=gap, ↑/↓=opacity"
        
        # Effect state
        self.active = True
        self.num_frames = 3        # How many frames to show (including current)
        self.frame_gap = 4         # Fixed gap between each frame shown
        self.opacity_step = 50     # % of previous frame (0-90%)
        
        # Frame buffer - dynamic size based on requirements
        self.frame_buffer = deque()
        self.required_buffer_size = self._calculate_buffer_size()
        
    def _calculate_buffer_size(self) -> int:
        """Calculate required buffer size based on current settings."""
        if self.num_frames <= 1:
            return 1
        # Need enough frames to go back: (num_frames - 1) * frame_gap
        return (self.num_frames - 1) * self.frame_gap + 1
        
    def _resize_buffer_if_needed(self):
        """Resize buffer if settings changed."""
        new_size = self._calculate_buffer_size()
        if new_size != self.required_buffer_size:
            self.required_buffer_size = new_size
            # Trim buffer if it's too large
            while len(self.frame_buffer) > self.required_buffer_size:
                self.frame_buffer.popleft()
                
    def process_frame(self, frame: np.ndarray, audio_data: Dict[str, Any]) -> np.ndarray:
        """Apply stutter effect by blending current frame with previous frames."""
        if frame is None or not self.active:
            return frame
            
        # Add current frame to buffer
        self.frame_buffer.append(frame.copy())
        
        # Maintain buffer size
        while len(self.frame_buffer) > self.required_buffer_size:
            self.frame_buffer.popleft()
            
        # Start with current frame at full opacity
        result = frame.copy().astype(np.float32)
        
        # Blend with previous frames
        for i in range(1, self.num_frames):
            frame_index = -(i * self.frame_gap + 1)  # +1 because current frame is at -1
            
            # Check if we have enough frames in buffer
            if len(self.frame_buffer) >= abs(frame_index):
                old_frame = self.frame_buffer[frame_index].astype(np.float32)
                
                # Calculate opacity for this frame (multiplicative decay)
                # Each frame is opacity_step% of the previous frame
                opacity_percent = 100.0 * (self.opacity_step / 100.0) ** i
                opacity = opacity_percent / 100.0
                
                if opacity > 0:
                    # Alpha blend: result = (1-alpha) * result + alpha * old_frame
                    result = (1.0 - opacity) * result + opacity * old_frame
        
        return result.astype(np.uint8)
        
    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameter values."""
        return {
            'active': self.active,
            'num_frames': self.num_frames,
            'frame_gap': self.frame_gap,
            'opacity_step': self.opacity_step,
            'buffer_size': len(self.frame_buffer),
            'required_buffer_size': self.required_buffer_size
        }
        
    def set_parameter(self, name: str, value: Any) -> bool:
        """Set parameter value."""
        if name == 'active':
            self.active = bool(value)
            status = "ON" if self.active else "OFF"
            print(f"🎬 Stutter effect: {status}")
            return True
        elif name == 'toggle':
            self.set_parameter('active', not self.active)
            return True
        elif name == 'num_frames':
            new_value = max(1, min(9, int(value)))
            if new_value != self.num_frames:
                self.num_frames = new_value
                self._resize_buffer_if_needed()
                print(f"📹 Frames: {self.num_frames}")
            return True
        elif name == 'increase_opacity_step':
            new_value = min(90, self.opacity_step + 5)
            if new_value != self.opacity_step:
                self.opacity_step = new_value
                print(f"⬆️ Opacity ratio: {self.opacity_step}%")
            return True
        elif name == 'decrease_opacity_step':
            new_value = max(0, self.opacity_step - 5)
            if new_value != self.opacity_step:
                self.opacity_step = new_value
                print(f"⬇️ Opacity ratio: {self.opacity_step}%")
            return True
        return False
        
    def handle_key_press(self, key: int, app_ref) -> bool:
        """Handle key press events."""
        # Numbers 1-9 for frame count
        if ord('1') <= key <= ord('9'):
            frame_count = key - ord('0')
            self.set_parameter('num_frames', frame_count)
            return True
        # Up arrow - increase opacity step
        elif key == 0:  # Up arrow (Mac)
            self.set_parameter('increase_opacity_step', True)
            return True
        # Down arrow - decrease opacity step  
        elif key == 1:  # Down arrow (Mac)
            self.set_parameter('decrease_opacity_step', True)
            return True
        # S key to toggle effect
        elif key == ord('s'):
            self.set_parameter('toggle', True)
            return True
        return False
        
    def reset(self):
        """Reset effect to default state."""
        self.num_frames = 3
        self.frame_gap = 4
        self.opacity_step = 50
        self.frame_buffer.clear()
        self.required_buffer_size = self._calculate_buffer_size()
        
    def cleanup(self):
        """Cleanup resources."""
        self.frame_buffer.clear()