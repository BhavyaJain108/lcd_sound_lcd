#!/usr/bin/env python3
"""
Simple BPM Detector - Just shows the current BPM in a small popup
"""

import sys
import numpy as np
import librosa
import sounddevice as sd
from collections import deque
import threading
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class BPMDetector(QThread):
    """Simple BPM detection thread."""
    bpm_updated = pyqtSignal(float)
    
    def __init__(self, sample_rate=22050):
        super().__init__()
        self.sample_rate = sample_rate
        self.buffer_duration = 10.0  # 10 seconds for better tempo detection
        self.buffer_size = int(sample_rate * self.buffer_duration)
        self.audio_buffer = deque(maxlen=self.buffer_size)
        self.running = False
        self.current_bpm = 120.0
        
    def run(self):
        self.running = True
        
        def audio_callback(indata, frames, time, status):
            if self.running:
                audio_data = indata[:, 0]  # Take first channel
                self.audio_buffer.extend(audio_data)
                
        try:
            with sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                blocksize=1024,
                callback=audio_callback
            ):
                last_analysis = 0
                while self.running:
                    current_time = time.time()
                    # Analyze every 0.5 seconds
                    if current_time - last_analysis > 0.5 and len(self.audio_buffer) >= self.sample_rate:
                        self.analyze_bpm()
                        last_analysis = current_time
                    time.sleep(0.1)
        except Exception as e:
            print(f"Audio error: {e}")
            
    def analyze_bpm(self):
        """Analyze BPM from current buffer."""
        try:
            if len(self.audio_buffer) < self.sample_rate:
                return
                
            audio_array = np.array(list(self.audio_buffer))
            
            # Simple tempo detection
            tempo, _ = librosa.beat.beat_track(
                y=audio_array,
                sr=self.sample_rate,
                hop_length=512
            )
            
            # Extract scalar from numpy array and convert to float
            new_bpm = float(tempo.item()) if hasattr(tempo, 'item') else float(tempo)
            if 60 <= new_bpm <= 200:  # Reasonable BPM range
                # Simple smoothing
                self.current_bpm = 0.7 * self.current_bpm + 0.3 * new_bpm
                self.bpm_updated.emit(self.current_bpm)
                
        except Exception as e:
            print(f"BPM analysis error: {e}")
            
    def stop(self):
        self.running = False
        self.quit()
        self.wait()

class BPMWindow(QWidget):
    """Simple BPM display window."""
    
    def __init__(self):
        super().__init__()
        self.current_bpm = 120.0
        self.setup_ui()
        
        # Start BPM detection
        self.detector = BPMDetector()
        self.detector.bpm_updated.connect(self.update_bpm)
        self.detector.start()
        
    def setup_ui(self):
        """Setup the minimal UI."""
        self.setWindowTitle("BPM")
        self.setGeometry(100, 100, 200, 120)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        
        # Make window stay on top
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # BPM display
        self.bpm_label = QLabel("120.0")
        self.bpm_label.setAlignment(Qt.AlignCenter)
        self.bpm_label.setStyleSheet("""
            QLabel {
                font-size: 36px;
                font-weight: bold;
                color: #00ff00;
                background-color: #000000;
                border: 2px solid #333333;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.bpm_label)
        
        # BPM text
        bpm_text = QLabel("BPM")
        bpm_text.setAlignment(Qt.AlignCenter)
        bpm_text.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #ffffff;
            }
        """)
        layout.addWidget(bpm_text)
        
        # Set window style
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
            }
        """)
        
    def update_bpm(self, bpm):
        """Update the BPM display."""
        self.current_bpm = bpm
        self.bpm_label.setText(f"{bpm:.1f}")
        
        # Change color based on BPM range
        if bpm < 90:
            color = "#4169e1"  # Blue - slow
        elif bpm < 120:
            color = "#00ff00"  # Green - moderate
        elif bpm < 140:
            color = "#ffa500"  # Orange - fast
        else:
            color = "#ff0000"  # Red - very fast
            
        self.bpm_label.setStyleSheet(f"""
            QLabel {{
                font-size: 36px;
                font-weight: bold;
                color: {color};
                background-color: #000000;
                border: 2px solid #333333;
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        
    def closeEvent(self, event):
        """Clean shutdown."""
        if hasattr(self, 'detector'):
            self.detector.stop()
        event.accept()
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    
    window = BPMWindow()
    window.show()
    
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("Interrupted")

if __name__ == "__main__":
    main()