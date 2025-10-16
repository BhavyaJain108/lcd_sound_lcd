import numpy as np
import cv2
import time
import threading
from typing import Dict, Any
from .base_effect import BaseEffect

class TheFlippy(BaseEffect):
    """Auto-flip effect that toggles horizontal flip every second when active."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.description = "Auto-flip effect - S=toggle, A=beat sync mode"
        
        # Effect state
        self.active = False
        self.frame_count = 0
        self.frames_per_flip = 120  # Start at slowest (120 frames)
        self.beat_sync_mode = False  # Whether to sync flips to beat
        self.last_beat_flip_time = 0  # Track when we last flipped on beat
        self.flip_state = False  # Current flip state (False = normal, True = flipped)
        
        # Frame-based limits
        self.min_frames_per_flip = 1    # Fastest (every frame)
        self.max_frames_per_flip = 120  # Slowest (every 120 frames)
        
        # Key handling
        self.app_ref = None  # Will be set by the app when effect is created
        
    def set_app_reference(self, app):
        """Set reference to main app for key simulation."""
        self.app_ref = app
        # Print frame range once when first activated
        if not hasattr(self, '_range_printed'):
            print(f"📊 TheFlippy frame range: {self.min_frames_per_flip} - {self.max_frames_per_flip} frames per flip")
            self._range_printed = True
        
    def process_frame(self, frame: np.ndarray, audio_data: Dict[str, Any]) -> np.ndarray:
        """Process frame and handle auto-flip timing."""
        
        if not self.active:
            return frame
        
        # Handle beat sync mode
        if self.beat_sync_mode and 'beat_info' in audio_data:
            beat_info = audio_data['beat_info']
            if beat_info['is_beat']:
                # Only flip if we haven't flipped recently for this beat
                current_time = beat_info.get('last_beat_time', 0)
                if current_time != self.last_beat_flip_time:
                    self.flip_state = not self.flip_state
                    self.last_beat_flip_time = current_time
                    # Toggle the app's flip state
                    if self.app_ref:
                        self.app_ref.flip_horizontal = self.flip_state
        elif not self.beat_sync_mode:
            # Original per-frame flipping
            self.frame_count += 1
            if self.frame_count >= self.frames_per_flip:
                self.frame_count = 0
                # Toggle the app's flip state silently
                if self.app_ref:
                    self.app_ref.flip_horizontal = not self.app_ref.flip_horizontal
        
        return frame
            
    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameter values."""
        return {
            'active': self.active,
            'frames_per_flip': self.frames_per_flip,
            'beat_sync_mode': self.beat_sync_mode,
            'flip_state': self.flip_state
        }
        
    def set_parameter(self, name: str, value: Any) -> bool:
        """Set parameter value."""
        if name == 'active':
            was_active = self.active
            self.active = bool(value)
            if self.active and not was_active:
                # Just started - reset frame counter
                self.frame_count = 0
                print(f"🟢 TheFlippy started - flipping every {self.frames_per_flip} frames")
            elif not self.active and was_active:
                print("🔴 TheFlippy stopped")
            return True
        elif name == 'frames_per_flip':
            self.frames_per_flip = int(value)
            return True
        elif name == 'toggle':
            # Special parameter to toggle the effect
            self.set_parameter('active', not self.active)
            return True
        elif name == 'beat_sync_mode':
            self.beat_sync_mode = bool(value)
            mode = "ON (beat-synced)" if self.beat_sync_mode else "OFF (per-frame)"
            print(f"🎵 TheFlippy beat sync: {mode}")
            return True
        elif name == 'toggle_beat_sync':
            self.set_parameter('beat_sync_mode', not self.beat_sync_mode)
            return True
        elif name == 'increase_frequency':
            # Decrease frames = increase frequency
            new_frames = max(self.min_frames_per_flip, self.frames_per_flip - 1)
            if new_frames != self.frames_per_flip:
                self.frames_per_flip = new_frames
                print(f"⬆️ TheFlippy: flip every {self.frames_per_flip} frames")
            return True
        elif name == 'decrease_frequency':
            # Increase frames = decrease frequency
            new_frames = min(self.max_frames_per_flip, self.frames_per_flip + 1)
            if new_frames != self.frames_per_flip:
                self.frames_per_flip = new_frames
                print(f"⬇️ TheFlippy: flip every {self.frames_per_flip} frames")
            return True
        return False
        
    def handle_key_press(self, key: int, app_ref) -> bool:
        """Handle key press events. Returns True if key was handled."""
        if key == ord('s'):
            # Set app reference and toggle
            self.set_app_reference(app_ref)
            self.set_parameter('toggle', True)
            return True
        elif key == 0:  # Up arrow (Mac) - increase frequency
            self.set_app_reference(app_ref)
            self.set_parameter('increase_frequency', True)
            return True
        elif key == 1:  # Down arrow (Mac) - decrease frequency
            self.set_app_reference(app_ref)
            self.set_parameter('decrease_frequency', True)
            return True
        elif key == ord('a'):  # A key - toggle beat sync mode
            self.set_app_reference(app_ref)
            self.set_parameter('toggle_beat_sync', True)
            return True
        return False