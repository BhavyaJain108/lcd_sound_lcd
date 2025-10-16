from abc import ABC, abstractmethod
import numpy as np
from typing import Dict, Any, Optional

class BaseEffect(ABC):
    """Abstract base class for all visual effects."""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.parameters = {}
        self.description = ""
        
    @abstractmethod
    def process_frame(self, frame: np.ndarray, audio_data: Dict[str, Any]) -> np.ndarray:
        """
        Process a video frame with audio data.
        
        Args:
            frame: Input video frame (H, W, 3) numpy array
            audio_data: Audio analysis results dictionary
            
        Returns:
            Processed video frame
        """
        pass
        
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """
        Get effect parameters that can be adjusted.
        
        Returns:
            Dictionary of parameter names and their current values
        """
        pass
        
    @abstractmethod
    def set_parameter(self, name: str, value: Any) -> bool:
        """
        Set an effect parameter.
        
        Args:
            name: Parameter name
            value: Parameter value
            
        Returns:
            True if parameter was set successfully, False otherwise
        """
        pass
        
    def get_parameter_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about effect parameters including ranges and types.
        
        Returns:
            Dictionary mapping parameter names to their info (type, range, default, etc.)
        """
        return {}
        
    def reset(self):
        """Reset effect to initial state."""
        pass
        
    def initialize(self, frame_shape: tuple):
        """
        Initialize effect with frame dimensions.
        
        Args:
            frame_shape: (height, width, channels) of video frames
        """
        pass
        
    def cleanup(self):
        """Cleanup resources when effect is removed."""
        pass
        
    def set_enabled(self, enabled: bool):
        """Enable or disable the effect."""
        self.enabled = enabled
        
    def is_enabled(self) -> bool:
        """Check if effect is enabled."""
        return self.enabled
        
    def get_name(self) -> str:
        """Get effect name."""
        return self.name
        
    def get_description(self) -> str:
        """Get effect description."""
        return self.description
        
    def handle_key_press(self, key: int, app_ref) -> bool:
        """
        Handle key press events for this effect.
        
        Args:
            key: Key code
            app_ref: Reference to main app
            
        Returns:
            True if key was handled by this effect, False to pass to default handler
        """
        return False  # Base implementation doesn't handle any keys