import numpy as np
import librosa
from collections import deque
from typing import Dict, Any, Optional
import threading
import time

class BeatDetector:
    """Global beat detection for effects integration."""
    
    def __init__(self, sample_rate: int = 22050, buffer_duration: float = 8.0):
        self.sample_rate = sample_rate
        self.buffer_duration = buffer_duration
        self.buffer_size = int(sample_rate * buffer_duration)
        
        # Audio buffer for accumulation
        self.audio_buffer = deque(maxlen=self.buffer_size)
        
        # Beat detection state
        self.current_bpm = 120.0
        self.last_beat_time = 0.0
        self.beat_times = []
        self.is_beat_frame = False  # True on frames where beat was detected
        
        # Analysis timing
        self.last_analysis_time = 0
        self.analysis_interval = 0.3  # Analyze every 300ms for responsiveness
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Beat detection parameters
        self.bpm_smoothing = 0.8  # Higher = more stable BPM
        self.beat_threshold = 0.6  # Minimum beat strength to register
        
    def process_audio_frame(self, audio_data: np.ndarray, timestamp: float):
        """Process incoming audio frame and update beat detection."""
        with self.lock:
            # Add audio to buffer
            if len(audio_data) > 0:
                self.audio_buffer.extend(audio_data)
            
            # Reset beat flag
            self.is_beat_frame = False
            
            # Perform analysis periodically
            if timestamp - self.last_analysis_time > self.analysis_interval:
                self.analyze_beats(timestamp)
                self.last_analysis_time = timestamp
    
    def analyze_beats(self, current_time: float):
        """Perform beat detection analysis."""
        try:
            if len(self.audio_buffer) < self.sample_rate * 2:  # Need at least 2 seconds
                return
                
            # Convert buffer to numpy array
            audio_array = np.array(list(self.audio_buffer))
            
            # Beat tracking with librosa
            tempo, beats = librosa.beat.beat_track(
                y=audio_array,
                sr=self.sample_rate,
                hop_length=512,
                start_bpm=self.current_bpm,  # Use current BPM as prior
                tightness=100  # Moderate tempo tracking
            )
            
            # Extract and smooth BPM
            new_bpm = float(tempo.item()) if hasattr(tempo, 'item') else float(tempo)
            if 60 <= new_bpm <= 200:  # Reasonable BPM range
                self.current_bpm = (self.bpm_smoothing * self.current_bpm + 
                                  (1 - self.bpm_smoothing) * new_bpm)
            
            # Convert beat frames to time
            if len(beats) > 0:
                beat_times = librosa.frames_to_time(beats, sr=self.sample_rate, hop_length=512)
                buffer_duration = len(audio_array) / self.sample_rate
                
                # Find most recent beat
                recent_beats = beat_times[beat_times > (buffer_duration - 1.0)]  # Last 1 second
                
                if len(recent_beats) > 0:
                    latest_beat_time = buffer_duration - recent_beats[-1]  # Time since last beat
                    
                    # Check if we have a new beat (within last analysis interval)
                    if latest_beat_time < self.analysis_interval * 1.5:
                        current_absolute_time = current_time
                        
                        # Avoid duplicate beat detection
                        if current_absolute_time - self.last_beat_time > 0.2:  # Min 200ms between beats
                            self.is_beat_frame = True
                            self.last_beat_time = current_absolute_time
                            
        except Exception as e:
            print(f"Beat detection error: {e}")
    
    def get_beat_info(self) -> Dict[str, Any]:
        """Get current beat information for effects."""
        with self.lock:
            return {
                'bpm': self.current_bpm,
                'is_beat': self.is_beat_frame,
                'last_beat_time': self.last_beat_time,
                'beat_strength': 1.0 if self.is_beat_frame else 0.0
            }
    
    def is_beat(self) -> bool:
        """Check if current frame is a beat."""
        with self.lock:
            return self.is_beat_frame
    
    def get_bpm(self) -> float:
        """Get current BPM."""
        with self.lock:
            return self.current_bpm
    
    def reset(self):
        """Reset beat detector state."""
        with self.lock:
            self.audio_buffer.clear()
            self.last_beat_time = 0.0
            self.beat_times = []
            self.is_beat_frame = False
            self.current_bpm = 120.0