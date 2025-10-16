#!/usr/bin/env python3
"""
Audio-Visual Effects System
Main entry point for the application.
"""

import sys
import time
from src.app import AudioVisualApp

def main():
    """Main application entry point."""
    print("🎵 Audio-Visual Effects System 🎨")
    print("=" * 40)
    
    # Create application instance
    app = AudioVisualApp()
    
    try:
        # Initialize the system
        app.initialize()
        
        # Start the system
        app.start()
        
        # Keep the main thread alive
        while app.running and app.output_renderer.is_running():
            time.sleep(0.1)
            
            # Print status every 5 seconds
            if int(time.time()) % 5 == 0:
                status = app.get_status()
                print(f"Processing FPS: {status['processing_fps']:.1f}, "
                      f"Render FPS: {status['render_fps']:.1f}")
                time.sleep(1)  # Avoid printing multiple times per second
                
    except KeyboardInterrupt:
        print("\nReceived interrupt signal...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        app.cleanup()
        print("Application terminated.")

if __name__ == "__main__":
    main()