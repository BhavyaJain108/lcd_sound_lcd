import numpy as np
import librosa
from scipy import signal
from typing import Dict, List, Optional, Callable
import threading
import time
from .beat_detector import BeatDetector

class AudioAnalyzer:
    def __init__(self, sample_rate: int = 44100, fft_size: int = 1024):
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.hop_length = fft_size // 4
        
        # Audio analysis parameters
        self.freq_bins = fft_size // 2 + 1
        self.frequencies = np.fft.fftfreq(fft_size, 1/sample_rate)[:self.freq_bins]
        
        # Beat detection
        self.beat_threshold = 1.3
        self.onset_threshold = 0.5
        self.tempo_history = []
        self.tempo_history_size = 10
        
        # Real-time analysis state
        self.audio_buffer = np.zeros(fft_size * 2)
        self.spectrum_history = []
        self.spectrum_history_size = 20
        self.rms_history = []
        self.rms_history_size = 30
        
        # Analysis results
        self.current_spectrum = np.zeros(self.freq_bins)
        self.current_rms = 0.0
        self.current_tempo = 120.0
        self.current_beat = False
        self.current_onset = False
        
        # Frequency band analysis
        self.frequency_bands = self._create_frequency_bands()
        self.band_energies = np.zeros(len(self.frequency_bands))
        
        # Callbacks
        self.analysis_callbacks = []
        
        # Threading
        self.analysis_lock = threading.Lock()
        
        # Global beat detector
        self.beat_detector = BeatDetector(sample_rate=sample_rate)
        
    def _create_frequency_bands(self) -> List[tuple]:
        """Create frequency bands for analysis (bass, mid, treble, etc.)"""
        return [
            (20, 60),      # Sub-bass
            (60, 250),     # Bass
            (250, 500),    # Low midrange
            (500, 2000),   # Midrange
            (2000, 4000),  # Upper midrange
            (4000, 6000),  # Presence
            (6000, 20000)  # Brilliance
        ]
        
    def add_analysis_callback(self, callback: Callable[[Dict], None]):
        """Add callback function for analysis results."""
        self.analysis_callbacks.append(callback)
        
    def process_audio_frame(self, audio_data: np.ndarray, timestamp: float):
        """Process a single frame of audio data."""
        with self.analysis_lock:
            # Update audio buffer
            self.audio_buffer = np.roll(self.audio_buffer, -len(audio_data))
            self.audio_buffer[-len(audio_data):] = audio_data
            
            # Perform analysis
            self._analyze_spectrum()
            self._analyze_energy()
            self._analyze_rhythm()
            self._analyze_frequency_bands()
            
            # Update global beat detector
            self.beat_detector.process_audio_frame(audio_data, timestamp)
            
            # Create analysis results
            results = self._create_analysis_results(timestamp)
            
            # Call callbacks
            for callback in self.analysis_callbacks:
                try:
                    callback(results)
                except Exception as e:
                    print(f"Error in analysis callback: {e}")
                    
    def _analyze_spectrum(self):
        """Perform FFT analysis on current audio buffer."""
        if len(self.audio_buffer) < self.fft_size:
            return
            
        # Apply window function
        windowed = self.audio_buffer[-self.fft_size:] * np.hanning(self.fft_size)
        
        # Compute FFT
        fft = np.fft.fft(windowed)
        magnitude = np.abs(fft[:self.freq_bins])
        
        # Convert to dB scale
        magnitude_db = 20 * np.log10(magnitude + 1e-10)
        
        # Smooth the spectrum
        self.current_spectrum = magnitude_db
        
        # Update spectrum history
        self.spectrum_history.append(magnitude_db.copy())
        if len(self.spectrum_history) > self.spectrum_history_size:
            self.spectrum_history.pop(0)
            
    def _analyze_energy(self):
        """Analyze RMS energy of the signal."""
        if len(self.audio_buffer) < self.fft_size:
            return
            
        # Calculate RMS
        frame = self.audio_buffer[-self.fft_size:]
        rms = np.sqrt(np.mean(frame ** 2))
        self.current_rms = rms
        
        # Update RMS history
        self.rms_history.append(rms)
        if len(self.rms_history) > self.rms_history_size:
            self.rms_history.pop(0)
            
    def _analyze_rhythm(self):
        """Analyze rhythm, beat detection, and tempo."""
        if len(self.rms_history) < 10:
            self.current_beat = False
            self.current_onset = False
            return
            
        # Simple beat detection using energy changes
        recent_rms = np.array(self.rms_history[-10:])
        rms_mean = np.mean(recent_rms)
        rms_std = np.std(recent_rms)
        
        # Beat detection threshold
        current_energy = self.current_rms
        beat_threshold = rms_mean + (self.beat_threshold * rms_std)
        
        self.current_beat = current_energy > beat_threshold
        
        # Onset detection (simpler version)
        if len(self.rms_history) >= 3:
            energy_diff = self.rms_history[-1] - self.rms_history[-2]
            self.current_onset = energy_diff > self.onset_threshold * rms_std
        else:
            self.current_onset = False
            
        # Tempo estimation (basic)
        if len(self.spectrum_history) >= 5:
            try:
                # Use spectral features for tempo estimation
                combined_spectrum = np.mean(self.spectrum_history[-5:], axis=0)
                tempo = self._estimate_tempo_from_spectrum(combined_spectrum)
                self.tempo_history.append(tempo)
                
                if len(self.tempo_history) > self.tempo_history_size:
                    self.tempo_history.pop(0)
                    
                self.current_tempo = np.median(self.tempo_history)
            except:
                pass
                
    def _estimate_tempo_from_spectrum(self, spectrum: np.ndarray) -> float:
        """Estimate tempo from spectral features."""
        # Simple tempo estimation based on spectral energy
        # This is a placeholder - real tempo detection is more complex
        low_freq_energy = np.mean(spectrum[1:20])  # Low frequency energy
        tempo = np.clip(60 + low_freq_energy * 2, 60, 200)
        return tempo
        
    def _analyze_frequency_bands(self):
        """Analyze energy in different frequency bands."""
        if len(self.current_spectrum) == 0:
            return
            
        for i, (low_freq, high_freq) in enumerate(self.frequency_bands):
            # Find frequency bin indices
            low_bin = int(low_freq * self.fft_size / self.sample_rate)
            high_bin = int(high_freq * self.fft_size / self.sample_rate)
            
            # Ensure bins are within range
            low_bin = max(0, min(low_bin, len(self.current_spectrum) - 1))
            high_bin = max(low_bin + 1, min(high_bin, len(self.current_spectrum)))
            
            # Calculate band energy
            band_energy = np.mean(self.current_spectrum[low_bin:high_bin])
            self.band_energies[i] = band_energy
            
    def _create_analysis_results(self, timestamp: float) -> Dict:
        """Create analysis results dictionary."""
        return {
            'timestamp': timestamp,
            'spectrum': self.current_spectrum.copy(),
            'frequencies': self.frequencies.copy(),
            'rms': self.current_rms,
            'tempo': self.current_tempo,
            'beat': self.current_beat,
            'onset': self.current_onset,
            'frequency_bands': {
                'sub_bass': self.band_energies[0],
                'bass': self.band_energies[1], 
                'low_mid': self.band_energies[2],
                'mid': self.band_energies[3],
                'high_mid': self.band_energies[4],
                'presence': self.band_energies[5],
                'brilliance': self.band_energies[6]
            },
            'band_energies': self.band_energies.copy(),
            'beat_info': self.beat_detector.get_beat_info()
        }
        
    def get_dominant_frequency(self) -> float:
        """Get the dominant frequency in the current spectrum."""
        if len(self.current_spectrum) == 0:
            return 0.0
            
        max_idx = np.argmax(self.current_spectrum)
        return self.frequencies[max_idx]
        
    def get_spectral_centroid(self) -> float:
        """Calculate spectral centroid (brightness measure)."""
        if len(self.current_spectrum) == 0:
            return 0.0
            
        # Convert from dB back to linear scale for centroid calculation
        linear_spectrum = 10 ** (self.current_spectrum / 20)
        
        if np.sum(linear_spectrum) == 0:
            return 0.0
            
        centroid = np.sum(self.frequencies * linear_spectrum) / np.sum(linear_spectrum)
        return centroid
        
    def get_spectral_rolloff(self, rolloff_threshold: float = 0.85) -> float:
        """Calculate spectral rolloff frequency."""
        if len(self.current_spectrum) == 0:
            return 0.0
            
        linear_spectrum = 10 ** (self.current_spectrum / 20)
        total_energy = np.sum(linear_spectrum)
        
        if total_energy == 0:
            return 0.0
            
        cumulative_energy = np.cumsum(linear_spectrum)
        rolloff_idx = np.where(cumulative_energy >= rolloff_threshold * total_energy)[0]
        
        if len(rolloff_idx) == 0:
            return self.frequencies[-1]
            
        return self.frequencies[rolloff_idx[0]]
        
    def reset(self):
        """Reset analyzer state."""
        with self.analysis_lock:
            self.audio_buffer = np.zeros(self.fft_size * 2)
            self.spectrum_history = []
            self.rms_history = []
            self.tempo_history = []
            self.current_spectrum = np.zeros(self.freq_bins)
            self.current_rms = 0.0
            self.current_tempo = 120.0
            self.current_beat = False
            self.current_onset = False
            self.band_energies = np.zeros(len(self.frequency_bands))