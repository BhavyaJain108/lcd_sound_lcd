# Future Optimizations

## Color Picker Performance
**Issue**: Hue slider is laggy when dragging - recreating color box pixmap is expensive
**Solutions to explore**:
1. **Qt Built-ins**: Use QColorDialog's native color picker component (C++ optimized)
2. **QtColorWidgets**: Third-party library with pre-optimized HSV selectors
3. **Block Drawing**: Draw 2x2/3x3 blocks instead of individual pixels (75-90% fewer draw calls)
4. **Disable Antialiasing**: `painter.setRenderHint(QPainter.Antialiasing, False)`
5. **Reduced Resolution**: Draw at half-res then scale up (4x fewer pixels)
6. **Pixmap Caching**: Pre-compute common hue values, interpolate between them
7. **QImage Direct**: Create QImage in memory first, convert to QPixmap once

**Priority**: Medium - current implementation works, just not as smooth as desired

## Audio-Visual Effects System
- Effect chain optimization
- GPU acceleration for real-time processing
- Better threading for camera/audio input

### TheFlippy Effect
**Issue**: 'A' key for beat sync mode toggle not being detected by key handler
**Current Status**: Beat sync functionality implemented but 'A' key press not reaching effect
**Investigation needed**:
- Key code mapping differences between platforms
- Qt key event propagation to effects
- Possible conflict with existing key bindings
**Workaround**: Could temporarily use different key (e.g., 'B' for beat sync)
**Priority**: Medium - functionality exists, just needs proper key binding

## Gradient Creator
- Export formats (CSS, SVG, PNG)
- Gradient presets/library
- Undo/redo functionality
- Gradient interpolation modes (linear, cubic, etc.)