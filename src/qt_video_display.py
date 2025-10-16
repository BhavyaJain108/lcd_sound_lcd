import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QKeySequence
import cv2

class VideoDisplayWidget(QLabel):
    """Qt widget for displaying video frames."""
    
    key_pressed = pyqtSignal(int)  # Signal for key press events
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: black;")
        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(False)  # No stretching - we'll handle aspect ratio
        self.setText("Video Display")
        
        # Cache for efficient cropping
        self.cached_crop_region = None
        self.cached_frame_size = None
        self.cached_widget_size = None
        
        # Flip state
        self.flip_horizontal = False
        
    def set_frame(self, frame):
        """Update the displayed frame with center-crop to fill widget."""
        if frame is None:
            return
            
        # Debug: check if frames are being processed
        # print(f"Processing frame, flip_horizontal={self.flip_horizontal}")
            
        h, w = frame.shape[:2]
        widget_size = self.size()
        current_frame_size = (w, h)
        current_widget_size = (widget_size.width(), widget_size.height())
        
        # Check if we need to recalculate crop region
        if (self.cached_crop_region is None or 
            self.cached_frame_size != current_frame_size or 
            self.cached_widget_size != current_widget_size):
            
            # Calculate crop region (same logic as before but cached)
            widget_w, widget_h = current_widget_size
            
            # Calculate scale to fill entire widget
            scale_w = widget_w / w
            scale_h = widget_h / h
            scale = max(scale_w, scale_h)  # Fill entire widget
            
            # Calculate what size the scaled frame would be
            scaled_w = int(w * scale)
            scaled_h = int(h * scale)
            
            # Calculate crop region in original frame coordinates
            if scaled_w > widget_w:
                # Crop horizontally
                crop_w = int(widget_w / scale)
                crop_h = h
                crop_x = (w - crop_w) // 2
                crop_y = 0
            else:
                # Crop vertically
                crop_w = w
                crop_h = int(widget_h / scale)
                crop_x = 0
                crop_y = (h - crop_h) // 2
            
            # Cache the crop region
            self.cached_crop_region = (crop_x, crop_y, crop_w, crop_h)
            self.cached_frame_size = current_frame_size
            self.cached_widget_size = current_widget_size
        
        # Apply cached crop region
        crop_x, crop_y, crop_w, crop_h = self.cached_crop_region
        cropped_frame = frame[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w]
        
        # Apply horizontal flip if enabled
        if self.flip_horizontal:
            cropped_frame = cv2.flip(cropped_frame, 1)
            print(f"🔄 Applying flip to frame")
        
        # Convert OpenCV BGR to RGB
        rgb_frame = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        
        # Create QImage from cropped frame
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Convert to QPixmap and scale to exact widget size
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(widget_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        
        self.setPixmap(scaled_pixmap)
        
    def keyPressEvent(self, event):
        """Handle key press events."""
        key = event.key()
        modifiers = event.modifiers()
        
        # Handle Shift+Number combinations for gap setting
        if modifiers & Qt.ShiftModifier and Qt.Key_1 <= key <= Qt.Key_9:
            # Shift+Number: use 300 + digit for gap setting
            gap_key = 300 + (key - Qt.Key_1 + 1)
            self.key_pressed.emit(gap_key)
        else:
            # Convert Qt key codes to OpenCV-style key codes
            key_map = {
                Qt.Key_Escape: 27,
                Qt.Key_C: ord('c'),
                Qt.Key_M: ord('m'),
                Qt.Key_F: ord('f'),
                Qt.Key_V: ord('v'),
                Qt.Key_R: ord('r'),
                Qt.Key_S: ord('s'),
                Qt.Key_D: ord('d'),
                Qt.Key_Up: 0,     # Mac up arrow key code
                Qt.Key_Down: 1,   # Mac down arrow key code
                Qt.Key_Left: 2,   # Mac left arrow key code
                Qt.Key_Right: 3,  # Mac right arrow key code
                # Number keys
                Qt.Key_1: ord('1'),
                Qt.Key_2: ord('2'),
                Qt.Key_3: ord('3'),
                Qt.Key_4: ord('4'),
                Qt.Key_5: ord('5'),
                Qt.Key_6: ord('6'),
                Qt.Key_7: ord('7'),
                Qt.Key_8: ord('8'),
                Qt.Key_9: ord('9')
            }
            
            opencv_key = key_map.get(key, key)
            self.key_pressed.emit(opencv_key)

class VideoDisplayWindow(QMainWindow):
    """Main Qt window for video display."""
    
    key_pressed = pyqtSignal(int)
    
    def __init__(self, title="Audio-Visual Effects"):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(800, 600)  # Initial size but no minimum restriction
        self.setMinimumSize(1, 1)  # Allow window to be resized to any size
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove all margins
        layout.setSpacing(0)  # Remove spacing between widgets
        central_widget.setLayout(layout)
        
        # Create video display widget
        self.video_widget = VideoDisplayWidget()
        layout.addWidget(self.video_widget)
        
        # Connect signals
        self.video_widget.key_pressed.connect(self.key_pressed.emit)
        
        # Make widget focusable for key events
        self.video_widget.setFocusPolicy(Qt.StrongFocus)
        self.video_widget.setFocus()
        
    def set_frame(self, frame):
        """Update the displayed frame."""
        self.video_widget.set_frame(frame)
        

class QtVideoDisplay:
    """Qt-based video display manager."""
    
    def __init__(self, title="Audio-Visual Effects"):
        self.app = None
        self.window = None
        self.title = title
        self.key_callback = None
        
    def initialize(self):
        """Initialize Qt application and window."""
        # Create QApplication if it doesn't exist
        if QApplication.instance() is None:
            self.app = QApplication(sys.argv)
        else:
            self.app = QApplication.instance()
            
        # Create main window
        self.window = VideoDisplayWindow(self.title)
        self.window.key_pressed.connect(self._on_key_press)
        self.window.show()
        
    def set_frame(self, frame):
        """Update the displayed frame."""
        if self.window:
            self.window.set_frame(frame)
            
    def set_flip_horizontal(self, flip):
        """Set horizontal flip state."""
        if self.window:
            self.window.video_widget.flip_horizontal = flip
            print(f"🔧 Qt flip state updated to: {flip}")
            
    def set_key_callback(self, callback):
        """Set callback for key press events."""
        self.key_callback = callback
        
    def _on_key_press(self, processed_key):
        """Handle processed key press events."""
        if self.key_callback:
            self.key_callback(processed_key)
            
    def process_events(self):
        """Process Qt events (non-blocking)."""
        if self.app:
            self.app.processEvents()
            
    def is_window_open(self):
        """Check if window is still open."""
        return self.window is not None and self.window.isVisible()
        
    def close(self):
        """Close the window and cleanup."""
        if self.window:
            self.window.close()
            self.window = None