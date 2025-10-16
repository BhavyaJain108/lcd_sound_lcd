import cv2
import sounddevice as sd
import numpy as np
from typing import List, Dict, Optional, Callable
from threading import Thread, Event
import queue

class MediaInputManager:
    def __init__(self):
        self.camera_devices = []
        self.audio_devices = []
        self.current_camera = None
        self.current_audio = None
        self.camera_stream = None
        self.audio_stream = None
        self.audio_queue = queue.Queue()
        self.frame_callback = None
        self.audio_callback = None
        self.is_running = False
        self.stop_event = Event()
        
    def discover_devices(self):
        """Discover all available camera and audio devices."""
        self._discover_cameras()
        self._discover_audio()
        
    def _discover_cameras(self):
        """Find all available camera devices."""
        self.camera_devices = []
        # Suppress OpenCV errors during discovery
        import os
        os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
        
        for i in range(5):  # Check first 5 camera indices (usually enough)
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    name = f"Camera {i}"
                    self.camera_devices.append({
                        'id': i,
                        'name': name,
                        'resolution': (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 
                                     int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
                    })
                cap.release()
                
    def _discover_audio(self):
        """Find all available audio input devices."""
        devices = sd.query_devices()
        self.audio_devices = []
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:  # Input device
                self.audio_devices.append({
                    'id': i,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'sample_rate': device['default_samplerate']
                })
                
    def set_camera_device(self, device_id: int, resolution: tuple = None):
        """Set the active camera device."""
        if self.camera_stream:
            self.camera_stream.release()
            
        self.camera_stream = cv2.VideoCapture(device_id)
        if resolution:
            self.camera_stream.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
            self.camera_stream.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
            
        self.current_camera = device_id
        
    def set_audio_device(self, device_id: int, sample_rate: int = 44100, 
                        block_size: int = 1024, channels: int = 1):
        """Set the active audio device."""
        self.current_audio = {
            'device_id': device_id,
            'sample_rate': sample_rate,
            'block_size': block_size,
            'channels': channels
        }
        
    def set_frame_callback(self, callback: Callable[[np.ndarray], None]):
        """Set callback function for video frames."""
        self.frame_callback = callback
        
    def set_audio_callback(self, callback: Callable[[np.ndarray, float], None]):
        """Set callback function for audio data."""
        self.audio_callback = callback
        
    def start_streaming(self):
        """Start both camera and audio streaming."""
        if not self.camera_stream or not self.current_audio:
            raise ValueError("Camera and audio devices must be set before streaming")
            
        self.is_running = True
        self.stop_event.clear()
        
        # Start camera thread
        self.camera_thread = Thread(target=self._camera_loop, daemon=True)
        self.camera_thread.start()
        
        # Start audio stream
        self._start_audio_stream()
        
    def _camera_loop(self):
        """Main camera capture loop."""
        while self.is_running and not self.stop_event.is_set():
            ret, frame = self.camera_stream.read()
            if ret and self.frame_callback:
                self.frame_callback(frame)
                
    def _audio_callback_internal(self, indata, frames, time, status):
        """Internal audio callback that forwards to user callback."""
        if status:
            print(f"Audio callback status: {status}")
            
        if self.audio_callback:
            # Convert to mono if needed
            audio_data = indata[:, 0] if indata.shape[1] > 1 else indata.flatten()
            self.audio_callback(audio_data, time.inputBufferAdcTime)
            
    def _start_audio_stream(self):
        """Start the audio input stream."""
        self.audio_stream = sd.InputStream(
            device=self.current_audio['device_id'],
            channels=self.current_audio['channels'],
            samplerate=self.current_audio['sample_rate'],
            blocksize=self.current_audio['block_size'],
            callback=self._audio_callback_internal
        )
        self.audio_stream.start()
        
    def stop_streaming(self):
        """Stop all streaming."""
        self.is_running = False
        self.stop_event.set()
        
        if self.audio_stream:
            self.audio_stream.stop()
            self.audio_stream.close()
            
        if hasattr(self, 'camera_thread'):
            self.camera_thread.join(timeout=1.0)
            
    def get_camera_devices(self) -> List[Dict]:
        """Get list of available camera devices."""
        return self.camera_devices.copy()
        
    def get_audio_devices(self) -> List[Dict]:
        """Get list of available audio devices."""
        return self.audio_devices.copy()
        
    def get_current_camera_info(self) -> Optional[Dict]:
        """Get info about current camera device."""
        if not self.camera_stream:
            return None
            
        return {
            'device_id': self.current_camera,
            'resolution': (int(self.camera_stream.get(cv2.CAP_PROP_FRAME_WIDTH)),
                         int(self.camera_stream.get(cv2.CAP_PROP_FRAME_HEIGHT))),
            'fps': self.camera_stream.get(cv2.CAP_PROP_FPS)
        }
        
    def get_current_audio_info(self) -> Optional[Dict]:
        """Get info about current audio device."""
        return self.current_audio.copy() if self.current_audio else None
        
    def __del__(self):
        """Cleanup resources."""
        self.stop_streaming()
        if self.camera_stream:
            self.camera_stream.release()