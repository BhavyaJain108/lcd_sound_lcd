import numpy as np
import cv2
from typing import Dict, Any
from .base_effect import BaseEffect

class Spotlight(BaseEffect):
    """Face isolation effect - shows only the user's face, masks out everything else."""
    
    def __init__(self, name: str):
        super().__init__(name)
        self.description = "Face isolation effect - S=toggle"
        
        # Effect state
        self.active = True
        
        # Face detection setup
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Face tracking state
        self.last_face_box = None
        self.face_detection_interval = 2  # Detect face every N frames for performance (increased rate)
        self.frame_count = 0
        self.face_padding = 30  # Extra pixels around detected face
        
        # Smoothing for face box (reduce jitter)
        self.box_smoothing = 0.7  # Higher = more stable, lower = more responsive
        
    def process_frame(self, frame: np.ndarray, audio_data: Dict[str, Any]) -> np.ndarray:
        """Apply face isolation effect."""
        if frame is None or not self.active:
            return frame
            
        height, width = frame.shape[:2]
        
        # Only detect face every N frames for performance
        self.frame_count += 1
        if self.frame_count % self.face_detection_interval == 0 or self.last_face_box is None:
            self.last_face_box = self._detect_face(frame)
            
        # If no face detected, return original frame
        if self.last_face_box is None:
            return frame
            
        # Create mask using edge detection for more precise face outline
        mask = self._create_edge_based_mask(frame, self.last_face_box)
        
        # Apply Gaussian blur to mask edges for softer transition
        mask = cv2.GaussianBlur(mask, (15, 15), 0)
        
        # Create 3-channel mask
        mask_3d = np.stack([mask, mask, mask], axis=2) / 255.0
        
        # Apply mask: keep face area, black out everything else
        result = frame.astype(np.float32) * mask_3d
        return result.astype(np.uint8)
        
    def _detect_face(self, frame: np.ndarray) -> tuple:
        """Detect face in frame and return bounding box with smoothing."""
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5,
            minSize=(60, 60),  # Minimum face size
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        if len(faces) == 0:
            return None
            
        # Take the largest face (closest to camera)
        largest_face = max(faces, key=lambda face: face[2] * face[3])
        x, y, w, h = largest_face
        
        # Smooth the face box if we have a previous detection
        if self.last_face_box is not None:
            prev_x, prev_y, prev_w, prev_h = self.last_face_box
            x = int(self.box_smoothing * prev_x + (1 - self.box_smoothing) * x)
            y = int(self.box_smoothing * prev_y + (1 - self.box_smoothing) * y)
            w = int(self.box_smoothing * prev_w + (1 - self.box_smoothing) * w)
            h = int(self.box_smoothing * prev_h + (1 - self.box_smoothing) * h)
            
        return (x, y, w, h)
    
    def _create_edge_based_mask(self, frame: np.ndarray, face_box: tuple) -> np.ndarray:
        """Create mask using edge detection for more precise face outline."""
        height, width = frame.shape[:2]
        x, y, w, h = face_box
        
        # Add padding and ensure bounds
        x_padded = max(0, x - self.face_padding)
        y_padded = max(0, y - self.face_padding)
        x_end = min(width, x + w + self.face_padding)
        y_end = min(height, y + h + self.face_padding)
        
        # Extract face region
        face_region = frame[y_padded:y_end, x_padded:x_end]
        
        if face_region.size == 0:
            # Fallback to elliptical mask if face region is invalid
            return self._create_elliptical_mask(frame, face_box)
        
        # Convert to grayscale for edge detection
        gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        
        # Apply bilateral filter to reduce noise while keeping edges sharp
        filtered = cv2.bilateralFilter(gray_face, 9, 75, 75)
        
        # Edge detection with Canny
        edges = cv2.Canny(filtered, 50, 150)
        
        # Dilate edges to make them thicker
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        edges = cv2.dilate(edges, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create mask for face region
        face_mask = np.zeros_like(gray_face)
        
        if len(contours) > 0:
            # Find the largest contour (should be face outline)
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Fill the largest contour
            cv2.fillPoly(face_mask, [largest_contour], 255)
            
            # If the contour is too small, fall back to elliptical mask
            contour_area = cv2.contourArea(largest_contour)
            face_area = gray_face.shape[0] * gray_face.shape[1]
            
            if contour_area < face_area * 0.1:  # Less than 10% of face region
                face_mask = self._create_simple_ellipse(gray_face.shape)
        else:
            # No contours found, use elliptical fallback
            face_mask = self._create_simple_ellipse(gray_face.shape)
        
        # Create full-frame mask
        full_mask = np.zeros((height, width), dtype=np.uint8)
        full_mask[y_padded:y_end, x_padded:x_end] = face_mask
        
        return full_mask
    
    def _create_elliptical_mask(self, frame: np.ndarray, face_box: tuple) -> np.ndarray:
        """Fallback elliptical mask."""
        height, width = frame.shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        x, y, w, h = face_box
        
        center_x = x + w // 2
        center_y = y + h // 2
        axes = (w // 2 + self.face_padding, h // 2 + self.face_padding)
        
        cv2.ellipse(mask, (center_x, center_y), axes, 0, 0, 360, 255, -1)
        return mask
    
    def _create_simple_ellipse(self, shape: tuple) -> np.ndarray:
        """Create simple ellipse for face region."""
        mask = np.zeros(shape, dtype=np.uint8)
        center_x, center_y = shape[1] // 2, shape[0] // 2
        axes = (shape[1] // 3, shape[0] // 3)
        cv2.ellipse(mask, (center_x, center_y), axes, 0, 0, 360, 255, -1)
        return mask
        
    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameter values."""
        return {
            'active': self.active,
            'face_padding': self.face_padding,
            'has_face': self.last_face_box is not None
        }
        
    def set_parameter(self, name: str, value: Any) -> bool:
        """Set parameter value."""
        if name == 'active':
            self.active = bool(value)
            status = "ON" if self.active else "OFF"
            print(f"🎭 Spotlight effect: {status}")
            return True
        elif name == 'toggle':
            self.set_parameter('active', not self.active)
            return True
        return False
        
    def handle_key_press(self, key: int, app_ref) -> bool:
        """Handle key press events."""
        # S key to toggle effect
        if key == ord('s'):
            self.set_parameter('toggle', True)
            return True
        return False
        
    def reset(self):
        """Reset effect to default state."""
        self.active = True
        self.last_face_box = None
        self.frame_count = 0
        
    def cleanup(self):
        """Cleanup resources."""
        self.last_face_box = None