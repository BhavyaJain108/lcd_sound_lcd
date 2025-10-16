import cv2
import pygame
import numpy as np
from typing import Optional, Tuple, Callable
import threading
import time

class OutputRenderer:
    """Handles rendering and display of processed video frames."""
    
    def __init__(self, window_title: str = "Audio-Visual Effects"):
        self.window_title = window_title
        self.window_size = (1280, 720)
        self.fullscreen = False
        self.display_fps = 30
        
        # Rendering backends
        self.backend = "pygame"  # "pygame" or "opencv"
        
        # Pygame specific
        self.pygame_screen = None
        self.pygame_clock = None
        self.pygame_initialized = False
        
        # OpenCV specific
        self.cv_window_created = False
        
        # Frame management
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.running = False
        self.render_thread = None
        
        # Performance monitoring
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.actual_fps = 0
        
        # Event callbacks
        self.key_callback = None
        self.mouse_callback = None
        self.resize_callback = None
        
    def initialize(self, backend: str = "pygame", window_size: tuple = None):
        """
        Initialize the renderer.
        
        Args:
            backend: "pygame" or "opencv"
            window_size: (width, height) tuple
        """
        self.backend = backend
        if window_size:
            self.window_size = window_size
            
        if backend == "pygame":
            self._initialize_pygame()
        elif backend == "opencv":
            self._initialize_opencv()
        else:
            raise ValueError(f"Unsupported backend: {backend}")
            
    def _initialize_pygame(self):
        """Initialize Pygame for rendering."""
        pygame.init()
        pygame.display.set_caption(self.window_title)
        
        flags = pygame.DOUBLEBUF
        if self.fullscreen:
            flags |= pygame.FULLSCREEN
            
        self.pygame_screen = pygame.display.set_mode(self.window_size, flags)
        self.pygame_clock = pygame.time.Clock()
        self.pygame_initialized = True
        
    def _initialize_opencv(self):
        """Initialize OpenCV for rendering."""
        cv2.namedWindow(self.window_title, cv2.WINDOW_AUTOSIZE)
        if self.fullscreen:
            cv2.setWindowProperty(self.window_title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        self.cv_window_created = True
        
    def set_window_size(self, width: int, height: int):
        """Set window size."""
        self.window_size = (width, height)
        
        if self.backend == "pygame" and self.pygame_initialized:
            flags = pygame.DOUBLEBUF
            if self.fullscreen:
                flags |= pygame.FULLSCREEN
            self.pygame_screen = pygame.display.set_mode(self.window_size, flags)
            
    def set_fullscreen(self, fullscreen: bool):
        """Toggle fullscreen mode."""
        self.fullscreen = fullscreen
        
        if self.backend == "pygame" and self.pygame_initialized:
            flags = pygame.DOUBLEBUF
            if fullscreen:
                flags |= pygame.FULLSCREEN
            self.pygame_screen = pygame.display.set_mode(self.window_size, flags)
        elif self.backend == "opencv" and self.cv_window_created:
            if fullscreen:
                cv2.setWindowProperty(self.window_title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty(self.window_title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                
    def set_display_fps(self, fps: int):
        """Set target display FPS."""
        self.display_fps = fps
        
    def set_callbacks(self, key_callback: Callable = None, mouse_callback: Callable = None, 
                     resize_callback: Callable = None):
        """Set event callbacks."""
        self.key_callback = key_callback
        self.mouse_callback = mouse_callback
        self.resize_callback = resize_callback
        
    def update_frame(self, frame: np.ndarray):
        """
        Update the frame to be rendered.
        
        Args:
            frame: Video frame as numpy array (H, W, 3) in BGR format
        """
        if frame is None:
            return
            
        with self.frame_lock:
            # Resize frame to fit window
            resized_frame = self._resize_frame(frame)
            self.current_frame = resized_frame
            
    def _resize_frame(self, frame: np.ndarray) -> np.ndarray:
        """Resize frame to fit window while maintaining aspect ratio."""
        if frame is None:
            return None
            
        h, w = frame.shape[:2]
        window_w, window_h = self.window_size
        
        # Calculate scaling factor
        scale = min(window_w / w, window_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize frame
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # Create centered frame on black background
        output = np.zeros((window_h, window_w, 3), dtype=np.uint8)
        
        # Calculate position to center the frame
        y_offset = (window_h - new_h) // 2
        x_offset = (window_w - new_w) // 2
        
        output[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized
        
        return output
        
    def start_rendering(self):
        """Start the rendering loop in a separate thread."""
        if self.running:
            return
            
        self.running = True
        self.render_thread = threading.Thread(target=self._render_loop, daemon=True)
        self.render_thread.start()
        
    def stop_rendering(self):
        """Stop the rendering loop."""
        self.running = False
        if self.render_thread:
            self.render_thread.join(timeout=1.0)
            
    def _render_loop(self):
        """Main rendering loop."""
        while self.running:
            start_time = time.time()
            
            if self.backend == "pygame":
                self._render_pygame()
            elif self.backend == "opencv":
                self._render_opencv()
                
            # Handle events
            self._handle_events()
            
            # Calculate actual FPS
            self.fps_counter += 1
            if time.time() - self.fps_timer >= 1.0:
                self.actual_fps = self.fps_counter
                self.fps_counter = 0
                self.fps_timer = time.time()
                
            # Frame rate limiting
            elapsed = time.time() - start_time
            target_frame_time = 1.0 / self.display_fps
            if elapsed < target_frame_time:
                time.sleep(target_frame_time - elapsed)
                
    def _render_pygame(self):
        """Render using Pygame."""
        if not self.pygame_initialized:
            return
            
        with self.frame_lock:
            if self.current_frame is not None:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
                
                # Create pygame surface
                frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
                
                # Clear screen and blit frame
                self.pygame_screen.fill((0, 0, 0))
                self.pygame_screen.blit(frame_surface, (0, 0))
                
        pygame.display.flip()
        
    def _render_opencv(self):
        """Render using OpenCV."""
        if not self.cv_window_created:
            return
            
        with self.frame_lock:
            if self.current_frame is not None:
                cv2.imshow(self.window_title, self.current_frame)
                
    def _handle_events(self):
        """Handle window events."""
        if self.backend == "pygame":
            self._handle_pygame_events()
        elif self.backend == "opencv":
            self._handle_opencv_events()
            
    def _handle_pygame_events(self):
        """Handle Pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.key_callback:
                    self.key_callback(event.key)
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_F11:
                    self.set_fullscreen(not self.fullscreen)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.mouse_callback:
                    self.mouse_callback(event.pos, event.button)
            elif event.type == pygame.VIDEORESIZE:
                if self.resize_callback:
                    self.resize_callback(event.w, event.h)
                    
    def _handle_opencv_events(self):
        """Handle OpenCV events."""
        key = cv2.waitKey(1) & 0xFF
        if key != 255:  # Key pressed
            if self.key_callback:
                self.key_callback(key)
            if key == 27:  # Escape key
                self.running = False
                
    def save_frame(self, filename: str):
        """Save current frame to file."""
        with self.frame_lock:
            if self.current_frame is not None:
                cv2.imwrite(filename, self.current_frame)
                return True
        return False
        
    def get_actual_fps(self) -> float:
        """Get actual rendering FPS."""
        return self.actual_fps
        
    def is_running(self) -> bool:
        """Check if renderer is running."""
        return self.running
        
    def cleanup(self):
        """Cleanup resources."""
        self.stop_rendering()
        
        if self.backend == "pygame" and self.pygame_initialized:
            pygame.quit()
        elif self.backend == "opencv" and self.cv_window_created:
            cv2.destroyAllWindows()
            
    def __del__(self):
        """Destructor."""
        self.cleanup()