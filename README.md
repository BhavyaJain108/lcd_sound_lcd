# Audio-Visual Effects System

A modular Python framework for creating real-time audio-reactive visual effects using camera input and microphone audio, plus an ultra-minimal gradient creator tool.

## Applications

### 1. Audio-Visual Effects System
- **Modular Architecture**: Clean separation of concerns with pluggable components
- **Real-time Processing**: Low-latency audio and video processing
- **Audio Analysis**: FFT analysis, beat detection, frequency band analysis
- **Effect Engine**: Plugin-based effect system for easy extensibility
- **OpenCV Rendering**: Optimized for macOS main thread requirements
- **Device Management**: Automatic discovery and switching of cameras/microphones
- **Dynamic Resizing**: Center-crop scaling with manual resolution control

### 2. Gradient Creator Tool
- **Ultra-Minimal UI**: Single-column layout with essential controls only
- **Dual Input Modes**: Eyedropper from images or color wheel selection
- **Always-Visible Gradient**: Live preview with highlighted active color stops
- **Drag & Drop**: Load images by dropping or right-click menu
- **Auto-Save**: Timestamp-based gradient files in JSON format
- **Intuitive Workflow**: Click stops to select, drag to move, double-click to remove

## Quick Start

1. **Setup Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run Audio-Visual Effects**:
   ```bash
   python main.py
   ```

3. **Run Gradient Creator**:
   ```bash
   python gradient_creator.py
   ```

## Controls

### Main Application
- **ESC**: Quit application
- **C**: Switch camera device
- **M**: Switch microphone device  
- **F**: Toggle horizontal flip
- **V**: Cycle through visual effects (including "no effect" mode)

### Effect-Specific Controls
Each effect has its own control scheme when active:

#### TheFlippy (Auto-Flip Effect)
Creates automatic horizontal flipping at adjustable intervals or beat-synced.
- **S**: Toggle effect on/off
- **↑**: Increase flip frequency (fewer frames between flips)
- **↓**: Decrease flip frequency (more frames between flips)
- **A**: Toggle beat sync mode (flips to audio beats vs. fixed timing)
- **Range**: 1-120 frames per flip (at 30fps: 30 flips/sec to 0.25 flips/sec)

#### GradientOverlaySimple (Color Grading)
Applies color grading using saved gradients based on luminance mapping.
- **S**: Toggle effect on/off
- **←**: Previous gradient
- **→**: Next gradient
- **↑**: Increase opacity (+5%)
- **↓**: Decrease opacity (-5%)
- **Range**: 0-100% opacity, uses gradients from `gradients/` folder

#### TheStutter (Motion Trail Effect)
Shows previous frames with decreasing opacity for motion trails.
- **S**: Toggle effect on/off
- **1-9**: Set number of frames to show (including current)
- **↑**: Increase opacity ratio (+5%) - how much of previous frame shows
- **↓**: Decrease opacity ratio (-5%)
- **Frame Count**: 1-9 frames, **Opacity Ratio**: 0-90%

#### Ki (Diamond Grid Effect)
Creates diamond patterns with color inversion using tessellation.
- **S**: Toggle effect on/off
- **1-9**: Set diamond width (number × 9 pixels)
- **Range**: Numbers 1-9 create diamond widths of 9-81 pixels

#### Miner (Motion-Revealed Gradients)
Reveals gradient colors through movement - static areas show base color, moving areas "mine" deeper colors.
- **S**: Toggle effect on/off
- **←**: Previous gradient
- **→**: Next gradient
- Uses gradients from `gradients/` folder

#### Spotlight (Face Isolation)
Uses face detection to isolate and highlight the user's face, masking everything else.
- **S**: Toggle effect on/off
- Automatically detects face using OpenCV Haar cascades
- Applies soft edge masking around detected face

### Gradient Creator Tool
A standalone application for creating color gradients used by GradientOverlaySimple and Miner effects.

#### Interface Elements
- **📚 (Top Button)**: Toggle between Create mode and Library mode
- **🎨/📷 (Middle Button)**: Toggle between Color Wheel mode and Image Eyedropper mode
- **💾 (Bottom Button)**: Save current gradient with timestamp
- **🗑️ (Library Mode)**: Delete selected gradient from library

#### Create Mode Controls
- **Image Mode (📷)**:
  - **Drag & Drop**: Load images into the tool
  - **Right-Click**: Load/change/clear image via context menu
  - **Click Image**: Pick color with eyedropper
- **Color Wheel Mode (🎨)**:
  - **Click Color Box**: Select saturation/value
  - **Hue Slider**: Adjust hue (rainbow slider)
  - **Color Preview**: Shows currently selected color

#### Gradient Editor (Always Visible in Create Mode)
- **Click Gradient**: Select existing color stop or add new one
- **Drag Stop**: Move color stop position along gradient
- **Double-Click Stop**: Remove color stop (minimum 2 required)
- **Active Stop**: Highlighted with white/black outline
- Changes to color picker automatically update the active stop

#### Library Mode Controls
- **Single Click**: Select gradient for deletion
- **Double Click**: Load gradient into editor and return to Create mode
- **🗑️ Button**: Delete selected gradient file
- **Gradients**: Sorted by creation time (newest first)

#### Workflow
1. **Create Gradient**: Use Image mode to pick colors from photos or Color Wheel mode for manual selection
2. **Add Stops**: Click on gradient bar to add color stops at specific positions
3. **Adjust Colors**: Select stops and pick new colors using either mode
4. **Position Stops**: Drag stops to adjust color transitions
5. **Save**: Use 💾 to save with timestamp (e.g., `gradient_20251016_143052.json`)
6. **Manage**: Use 📚 to view, load, or delete saved gradients

#### Tips
- **Gradients are automatically available** in GradientOverlaySimple and Miner effects
- **File Format**: JSON files stored in `gradients/` folder
- **Image Sources**: Use photos, artwork, or any image for color inspiration
- **Color Transitions**: More stops create smoother transitions

## Architecture

```
MediaInputManager ──┐
                    ├──► EffectEngine ──► OutputRenderer
AudioAnalyzer ──────┘
```

### Core Components

- **MediaInputManager**: Handles camera and microphone input
- **AudioAnalyzer**: Real-time audio analysis (FFT, beat detection, etc.)
- **EffectEngine**: Plugin-based effect processing system
- **OutputRenderer**: Display and rendering management
- **AudioVisualApp**: Main application controller

## Creating Effects

Create custom effects by inheriting from `BaseEffect`:

```python
from src.effect_engine import BaseEffect
import numpy as np

class MyEffect(BaseEffect):
    def __init__(self, name):
        super().__init__(name)
        self.description = "My custom effect"
        
    def process_frame(self, frame, audio_data):
        # Process frame based on audio_data
        # audio_data contains: spectrum, rms, beat, tempo, etc.
        return modified_frame
        
    def get_parameters(self):
        return {"intensity": 1.0}
        
    def set_parameter(self, name, value):
        if name == "intensity":
            self.intensity = value
            return True
        return False
        
    def handle_key_press(self, key, app_ref):
        # Optional: Handle custom key presses for this effect
        # Return True if key was handled, False otherwise
        if key == ord('x'):  # Example: X key does something
            # Custom effect logic here
            return True
        return False
```

### Adding Effects to the System

1. **Create your effect file** in `src/effect_engine/` (e.g., `my_effect.py`)
2. **Import and register** in `src/effect_engine/effect_engine.py`:

```python
# Add import
from .my_effect import MyEffect

# Add to effect_classes dictionary
self.effect_classes = {
    'TheFlippy': TheFlippy,
    'MyEffect': MyEffect  # Add your effect here
}
```

3. **Use V key** in the app to cycle to your new effect

### Built-in Effects

The system includes 6 built-in effects that demonstrate different visual processing techniques:

#### 1. TheFlippy
Auto-flip effect with frame-based or beat-synced timing.
- Toggles horizontal flip at adjustable intervals
- Can sync to audio beats for rhythmic flipping
- Frame-based timing: 1-120 frames per flip

#### 2. GradientOverlaySimple  
Luminance-based color grading using custom gradients.
- Maps image brightness to gradient colors
- Uses gradients created with the Gradient Creator tool
- Adjustable opacity for subtle or dramatic effects

#### 3. TheStutter
Motion trail effect showing previous frames.
- Creates "motion blur" by overlaying previous frames
- Adjustable frame count (1-9) and opacity decay
- Exponential opacity falloff for natural motion trails

#### 4. Ki
Diamond tessellation with selective color inversion.
- Creates geometric diamond patterns across the image
- Uses mathematical formula for perfect tessellation
- Adjustable diamond size from 9-81 pixels

#### 5. Miner
Motion-revealed gradient coloring.
- Reveals gradient colors through movement detection
- Static areas show base color, moving areas show deeper gradient colors
- Uses HSV change detection for accurate motion tracking

#### 6. Spotlight
Face isolation using computer vision.
- Automatically detects and isolates faces
- Uses OpenCV Haar cascades for face detection
- Soft edge masking with motion smoothing

## Audio Data Format

The audio analyzer provides rich analysis data:

```python
{
    'timestamp': float,
    'spectrum': np.ndarray,      # FFT spectrum
    'frequencies': np.ndarray,   # Frequency bins
    'rms': float,               # RMS energy
    'tempo': float,             # Estimated BPM
    'beat': bool,               # Beat detected
    'onset': bool,              # Onset detected
    'frequency_bands': {        # Energy in frequency bands
        'sub_bass': float,
        'bass': float,
        'low_mid': float,
        'mid': float,
        'high_mid': float,
        'presence': float,
        'brilliance': float
    }
}
```

## API Usage

```python
from src.app import AudioVisualApp

# Create and configure app
app = AudioVisualApp()
app.initialize()

# Access components
effect_engine = app.get_effect_engine()
audio_analyzer = app.get_audio_analyzer()

# Add effects
effect_engine.create_effect("MyEffect", "effect1")
effect_engine.add_to_chain("effect1")

# Start processing
app.start()
```

## Dependencies

### Audio-Visual Effects System
- **opencv-python**: Camera input and image processing
- **sounddevice**: Audio input
- **numpy**: Numerical computations
- **librosa**: Audio analysis
- **scipy**: Signal processing
- **pygetwindow**: Window geometry detection (macOS)
- **matplotlib**: Visualization support

### Gradient Creator Tool
- **PyQt5**: GUI framework for the gradient creator
- **numpy**: Color calculations
- **json**: Gradient file storage

## Requirements

- Python 3.8+
- Camera (webcam) - for audio-visual effects
- Microphone - for audio-visual effects  
- PyQt5 - for gradient creator
- macOS/Linux/Windows support

## Platform Support

- **macOS**: Full support
- **Linux**: Full support  
- **Windows**: Full support

## Performance Tips

- Use lower video resolutions for better performance
- Adjust audio block size based on latency requirements
- Consider using OpenCV backend for better performance on some systems
- Effects are processed in sequence - optimize effect order

## License

MIT License - feel free to use and modify for your projects!