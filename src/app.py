import numpy as np
import cv2
import time
import threading
import math
from typing import Optional, Dict, Any

from .media_input import MediaInputManager
from .audio_analyzer import AudioAnalyzer
from .effect_engine import EffectEngine
from .output_renderer import OutputRenderer
from .qt_video_display import QtVideoDisplay

class AudioVisualApp:
    """Main application controller for audio-visual effects system."""
    
    def __init__(self):
        # Core components
        self.media_input = MediaInputManager()
        self.audio_analyzer = AudioAnalyzer()
        self.effect_engine = EffectEngine()
        self.output_renderer = OutputRenderer()
        
        # Application state
        self.running = False
        self.initialized = False
        self.camera_frame = None      # Raw frame from camera
        self.processed_frame = None   # Frame after effects processing
        self.current_audio_data = {}
        self.flip_horizontal = False
        self.current_effect_index = 0  # 0 = no effect, 1+ = effects
        
        # Threading
        self.main_loop_thread = None
        self.frame_lock = threading.Lock()
        
        # Performance monitoring
        self.fps_counter = 0
        self.fps_timer = time.time()
        self.processing_fps = 0
        
        # Configuration
        self.config = {
            'video_fps': 30,
            'audio_sample_rate': 44100,
            'audio_block_size': 1024,
            'video_resolution': (1280, 720),
            'render_backend': 'qt'
        }
        
        # Qt video display
        self.qt_display = QtVideoDisplay("Audio-Visual Effects")
        
    def initialize(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the application.
        
        Args:
            config: Optional configuration dictionary
        """
        if config:
            self.config.update(config)
            
        # Discover available devices
        self.media_input.discover_devices()
        
        cameras = self.media_input.get_camera_devices()
        audio_devices = self.media_input.get_audio_devices()
        
        # Set default devices if available
        if cameras:
            self.media_input.set_camera_device(
                cameras[0]['id'], 
                self.config['video_resolution']
            )
            
        if audio_devices:
            # Skip BlackHole and use a real mic if available
            selected_audio = audio_devices[0]
            for device in audio_devices:
                if 'blackhole' not in device['name'].lower():
                    selected_audio = device
                    break
                    
            self.media_input.set_audio_device(
                selected_audio['id'],
                self.config['audio_sample_rate'],
                self.config['audio_block_size']
            )
            
        # Set up callbacks
        self.media_input.set_frame_callback(self._on_frame_received)
        self.media_input.set_audio_callback(self._on_audio_received)
        self.audio_analyzer.add_analysis_callback(self._on_audio_analysis)
        
        # Initialize Qt display
        self.qt_display.initialize()
        self.qt_display.set_key_callback(self._on_key_press)
        
        # Effects are now directly registered in EffectEngine
        
        self.initialized = True
        print(f"🎥 {len(cameras)} camera(s) | 🎤 {len(audio_devices)} audio device(s) | Ready!")
        
    def start(self):
        """Start the application."""
        if not self.initialized:
            raise RuntimeError("Application must be initialized before starting")
            
        print("Starting Audio-Visual Effects System...")
        
        self.running = True
        
        # Start media input streaming
        self.media_input.start_streaming()
        
        # Start main processing loop in background
        self.main_loop_thread = threading.Thread(target=self._main_loop, daemon=True)
        self.main_loop_thread.start()
        
        print("Controls: ESC=quit | C=camera | M=mic | F=flip | V=effects | (effects add their own keys)")
        
        # Run renderer on main thread (required for Qt)
        self._render_loop()
        
    def stop(self):
        """Stop the application."""
        print("Stopping Audio-Visual Effects System...")
        
        self.running = False
        
        # Stop components
        self.media_input.stop_streaming()
        
        # Close Qt display
        self.qt_display.close()
        
        # Wait for main loop to finish
        if self.main_loop_thread:
            self.main_loop_thread.join(timeout=2.0)
            
        print("System stopped.")
        
    def _on_frame_received(self, frame: np.ndarray):
        """Callback for new video frames."""
        with self.frame_lock:
            self.camera_frame = frame.copy()
            
    def _on_audio_received(self, audio_data: np.ndarray, timestamp: float):
        """Callback for new audio data."""
        # Process audio through analyzer
        self.audio_analyzer.process_audio_frame(audio_data, timestamp)
        
    def _on_audio_analysis(self, analysis_data: Dict[str, Any]):
        """Callback for audio analysis results."""
        self.current_audio_data = analysis_data
        
    def _main_loop(self):
        """Main processing loop."""
        while self.running:
            start_time = time.time()
            
            # Get current camera frame
            with self.frame_lock:
                camera_frame = self.camera_frame.copy() if self.camera_frame is not None else None
                
            # Process frame through effects
            if camera_frame is not None:
                try:
                    if self.current_effect_index == 0:
                        # No effect - show raw camera
                        result_frame = camera_frame
                    else:
                        # Process through effect engine
                        result_frame = self.effect_engine.process_frame(
                            camera_frame, self.current_audio_data
                        )
                    
                    # Update the processed frame buffer
                    with self.frame_lock:
                        self.processed_frame = result_frame
                    
                except Exception as e:
                    print(f"Error in main processing loop: {e}")
                    # Keep original frame
                    
            # Calculate processing FPS
            self.fps_counter += 1
            if time.time() - self.fps_timer >= 1.0:
                self.processing_fps = self.fps_counter
                self.fps_counter = 0
                self.fps_timer = time.time()
                
            # Frame rate limiting
            elapsed = time.time() - start_time
            target_frame_time = 1.0 / self.config['video_fps']
            if elapsed < target_frame_time:
                time.sleep(target_frame_time - elapsed)
                
    def _render_loop(self):
        """Main rendering loop (runs on main thread)."""
        while self.running and self.qt_display.is_window_open():
            # Get processed frame
            with self.frame_lock:
                frame = self.processed_frame.copy() if self.processed_frame is not None else None
                
            # Display frame
            if frame is not None:
                # Apply flip if enabled
                if self.flip_horizontal:
                    frame = cv2.flip(frame, 1)
                self.qt_display.set_frame(frame)
                
            # Process Qt events
            self.qt_display.process_events()
                
            time.sleep(1.0 / self.config['video_fps'])
            
        # Cleanup
        self.qt_display.close()
        
        
    def _switch_camera(self):
        """Switch to next available camera."""
        cameras = self.media_input.get_camera_devices()
        if len(cameras) <= 1:
            return
            
        current_id = self.media_input.current_camera
        next_id = (current_id + 1) % len(cameras)
        
        was_running = self.media_input.is_running
        if was_running:
            self.media_input.stop_streaming()
            
        self.media_input.set_camera_device(cameras[next_id]['id'], self.config['video_resolution'])
        print(f"📷 Switched to {cameras[next_id]['name']}")
        
        if was_running:
            self.media_input.start_streaming()
            
    def _switch_microphone(self):
        """Switch to next available microphone."""
        audio_devices = self.media_input.get_audio_devices()
        if len(audio_devices) <= 1:
            return
            
        current_id = self.media_input.current_audio['device_id']
        current_idx = next((i for i, d in enumerate(audio_devices) if d['id'] == current_id), 0)
        next_idx = (current_idx + 1) % len(audio_devices)
        
        was_running = self.media_input.is_running
        if was_running:
            self.media_input.stop_streaming()
            
        self.media_input.set_audio_device(
            audio_devices[next_idx]['id'],
            self.config['audio_sample_rate'],
            self.config['audio_block_size']
        )
        print(f"🎤 Switched to {audio_devices[next_idx]['name']}")
        
        if was_running:
            self.media_input.start_streaming()
            
    def _toggle_flip(self):
        """Toggle horizontal flip."""
        self.flip_horizontal = not self.flip_horizontal
        status = "ON" if self.flip_horizontal else "OFF"
        print(f"🔄 Horizontal flip: {status}")
        
    def _switch_effect(self):
        """Switch to next visual effect."""
        available_effects = self.effect_engine.get_effect_list()
        
        # Total options: 0 (no effect) + number of available effects
        total_options = 1 + len(available_effects)
        
        # Switch to next effect
        self.current_effect_index = (self.current_effect_index + 1) % total_options
        
        # Clear existing effect chain
        self.effect_engine.effect_chain.clear()
        
        if self.current_effect_index == 0:
            print("📺 Raw camera feed")
        else:
            # Create and add the selected effect
            effect_name = available_effects[self.current_effect_index - 1]
            instance_name = f"current_effect"
            
            # Remove old instance if exists
            self.effect_engine.remove_effect(instance_name)
            
            # Create new effect instance
            if self.effect_engine.create_effect(effect_name, instance_name):
                self.effect_engine.add_to_chain(instance_name)
                print(f"✨ Effect: {effect_name}")
            else:
                print(f"❌ Failed to load effect: {effect_name}")
                self.current_effect_index = 0
                
    def _delegate_key_to_effect(self, key: int) -> bool:
        """Delegate key press to current effect. Returns True if handled."""
        if self.current_effect_index > 0:
            effect_instance = self.effect_engine.get_effect_instance("current_effect")
            if effect_instance:
                return effect_instance.handle_key_press(key, self)
        return False
                
            
                    
            
        
                
    def _on_key_press(self, key):
        """Handle key press events from Qt display."""
        if key == 27:  # ESC
            self.stop()
        elif key == ord('c'):  # Switch camera
            self._switch_camera()
        elif key == ord('m'):  # Switch microphone
            self._switch_microphone()
        elif key == ord('f'):  # Basic horizontal flip
            self.flip_horizontal = not self.flip_horizontal
            status = "ON" if self.flip_horizontal else "OFF"
            print(f"🔄 Horizontal flip: {status}")
        elif key == ord('v'):  # Switch visual effect
            self._switch_effect()
        else:
            # Try to let current effect handle the key first
            if not self._delegate_key_to_effect(key):
                # Effect didn't handle it, ignore unknown keys
                pass
            
    def _on_mouse_click(self, pos, button):
        """Handle mouse click events."""
        pass
        
    def get_camera_devices(self):
        """Get available camera devices."""
        return self.media_input.get_camera_devices()
        
    def get_audio_devices(self):
        """Get available audio devices."""
        return self.media_input.get_audio_devices()
        
    def set_camera_device(self, device_id: int):
        """Change camera device."""
        was_running = self.running
        if was_running:
            self.media_input.stop_streaming()
            
        self.media_input.set_camera_device(device_id, self.config['video_resolution'])
        
        if was_running:
            self.media_input.start_streaming()
            
    def set_audio_device(self, device_id: int):
        """Change audio device."""
        was_running = self.running
        if was_running:
            self.media_input.stop_streaming()
            
        self.media_input.set_audio_device(
            device_id,
            self.config['audio_sample_rate'],
            self.config['audio_block_size']
        )
        
        if was_running:
            self.media_input.start_streaming()
            
    def get_effect_engine(self) -> EffectEngine:
        """Get the effect engine for effect management."""
        return self.effect_engine
        
    def get_audio_analyzer(self) -> AudioAnalyzer:
        """Get the audio analyzer."""
        return self.audio_analyzer
        
    def get_output_renderer(self) -> OutputRenderer:
        """Get the output renderer."""
        return self.output_renderer
        
    def get_current_audio_data(self) -> Dict[str, Any]:
        """Get current audio analysis data."""
        return self.current_audio_data.copy()
        
    def get_processing_fps(self) -> float:
        """Get current processing FPS."""
        return self.processing_fps
        
    def get_status(self) -> Dict[str, Any]:
        """Get system status information."""
        camera_info = self.media_input.get_current_camera_info()
        audio_info = self.media_input.get_current_audio_info()
        
        return {
            'running': self.running,
            'initialized': self.initialized,
            'processing_fps': self.processing_fps,
            'camera_info': camera_info,
            'audio_info': audio_info,
            'effect_chain': self.effect_engine.get_effect_chain(),
            'available_effects': self.effect_engine.get_effect_list()
        }
        
    def cleanup(self):
        """Cleanup all resources."""
        self.stop()
        self.effect_engine.cleanup()
        
    def __del__(self):
        """Destructor."""
        self.cleanup()