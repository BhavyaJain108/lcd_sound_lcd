#!/usr/bin/env python3
"""
Gradient Creator Tool - Ultra Minimal Single Column Version
A PyQt5 application for creating color gradients from images.
"""

import sys
import json
import os
from datetime import datetime
import math
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class ColorStop:
    def __init__(self, position, color):
        self.position = position  # 0.0 to 1.0
        self.color = color  # QColor
        self.rect = QRect()  # For mouse interaction
        self.is_active = False  # Highlight state

class ImagePanel(QWidget):
    color_picked = pyqtSignal(QColor)
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(300, 200)
        self.setAcceptDrops(True)
        
        self.current_pixmap = None
        self.scaled_pixmap = None
        self.image_rect = QRect()
        self.eyedropper_mode = True
        self.has_image = False
        
        self.setStyleSheet("background-color: #f8f8f8; border: 1px solid #ddd;")
        
    def set_eyedropper_mode(self, enabled):
        self.eyedropper_mode = enabled
        if enabled and self.has_image:
            self.setCursor(QCursor(Qt.CrossCursor))
        else:
            self.setCursor(QCursor(Qt.ArrowCursor))
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                self.load_image(file_path)
                
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        if self.has_image:
            change_action = QAction("Change Image", self)
            change_action.triggered.connect(self.upload_image)
            menu.addAction(change_action)
            
            clear_action = QAction("Clear Image", self)
            clear_action.triggered.connect(self.clear_image)
            menu.addAction(clear_action)
        else:
            load_action = QAction("Load Image", self)
            load_action.triggered.connect(self.upload_image)
            menu.addAction(load_action)
        menu.exec_(event.globalPos())
            
    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.load_image(file_path)
            
    def load_image(self, file_path):
        # Clear previous image first
        self.clear_image()
        
        self.current_pixmap = QPixmap(file_path)
        if not self.current_pixmap.isNull():
            self.has_image = True
            if self.eyedropper_mode:
                self.setCursor(QCursor(Qt.CrossCursor))
            self.update_scaled_pixmap()
            self.update()
            print(f"Loaded image: {file_path}")
            
    def clear_image(self):
        """Clear the current image."""
        self.current_pixmap = None
        self.scaled_pixmap = None
        self.has_image = False
        self.setCursor(QCursor(Qt.ArrowCursor))
        self.update()
        print("Image cleared")
            
    def update_scaled_pixmap(self):
        if self.current_pixmap:
            # Scale to fit the available space while maintaining aspect ratio
            widget_size = self.size()
            self.scaled_pixmap = self.current_pixmap.scaled(
                widget_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            
            # Center the scaled image
            x = (widget_size.width() - self.scaled_pixmap.width()) // 2
            y = (widget_size.height() - self.scaled_pixmap.height()) // 2
            self.image_rect = QRect(x, y, self.scaled_pixmap.width(), self.scaled_pixmap.height())
            
    def paintEvent(self, event):
        painter = QPainter(self)
        if self.scaled_pixmap:
            painter.drawPixmap(self.image_rect, self.scaled_pixmap)
        else:
            painter.setPen(QColor(150, 150, 150))
            font = QFont()
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "Drag image here\nor right-click to load/change")
            
    def resizeEvent(self, event):
        if self.current_pixmap:
            self.update_scaled_pixmap()
        super().resizeEvent(event)
            
    def mousePressEvent(self, event):
        if (self.has_image and self.eyedropper_mode and 
            event.button() == Qt.LeftButton and self.image_rect.contains(event.pos())):
            
            local_pos = event.pos() - self.image_rect.topLeft()
            
            if self.scaled_pixmap and self.current_pixmap:
                scale_x = self.current_pixmap.width() / self.scaled_pixmap.width()
                scale_y = self.current_pixmap.height() / self.scaled_pixmap.height()
                
                orig_x = int(local_pos.x() * scale_x)
                orig_y = int(local_pos.y() * scale_y)
                
                if (0 <= orig_x < self.current_pixmap.width() and 
                    0 <= orig_y < self.current_pixmap.height()):
                    image = self.current_pixmap.toImage()
                    color = QColor(image.pixel(orig_x, orig_y))
                    self.color_picked.emit(color)

class GradientEditor(QWidget):
    stop_selected = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
        self.stops = [
            ColorStop(0.0, QColor(255, 0, 0)),
            ColorStop(1.0, QColor(0, 0, 255))
        ]
        self.stops[0].is_active = True
        self.dragging_stop = None
        self.setMinimumHeight(50)
        self.setMaximumHeight(60)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()
        
        # Draw gradient
        gradient = QLinearGradient(0, 0, rect.width(), 0)
        for stop in self.stops:
            gradient.setColorAt(stop.position, stop.color)
        
        painter.fillRect(rect, gradient)
        
        # Draw stops
        for stop in self.stops:
            x = int(stop.position * rect.width())
            stop_rect = QRect(x-8, 0, 16, rect.height())
            stop.rect = stop_rect
            
            # Highlight active stop
            if stop.is_active:
                painter.setPen(QPen(Qt.white, 3))
                painter.setBrush(QBrush(stop.color))
                painter.drawEllipse(stop_rect.center(), 8, 8)
                painter.setPen(QPen(Qt.black, 2))
                painter.setBrush(QBrush(stop.color))
                painter.drawEllipse(stop_rect.center(), 6, 6)
            else:
                painter.setPen(QPen(Qt.black, 2))
                painter.setBrush(QBrush(stop.color))
                painter.drawEllipse(stop_rect.center(), 6, 6)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            for stop in self.stops:
                if stop.rect.contains(event.pos()):
                    self.dragging_stop = stop
                    self.set_active_stop(stop)
                    self.stop_selected.emit(stop)
                    break
            else:
                # Add new stop
                pos = event.pos().x() / self.width()
                new_stop = ColorStop(pos, QColor(128, 128, 128))
                self.stops.append(new_stop)
                self.stops.sort(key=lambda s: s.position)
                self.dragging_stop = new_stop
                self.set_active_stop(new_stop)
                self.stop_selected.emit(new_stop)
                self.update()

    def mouseMoveEvent(self, event):
        if self.dragging_stop:
            new_pos = max(0.0, min(1.0, event.pos().x() / self.width()))
            self.dragging_stop.position = new_pos
            self.update()

    def mouseReleaseEvent(self, event):
        self.dragging_stop = None

    def mouseDoubleClickEvent(self, event):
        for stop in self.stops:
            if stop.rect.contains(event.pos()) and len(self.stops) > 2:
                was_active = stop.is_active
                self.stops.remove(stop)
                if was_active and self.stops:
                    self.set_active_stop(self.stops[0])
                self.update()
                break
                
    def set_active_stop(self, active_stop):
        for stop in self.stops:
            stop.is_active = (stop == active_stop)
        self.update()
        
    def get_active_stop(self):
        for stop in self.stops:
            if stop.is_active:
                return stop
        return None
        
    def update_active_stop_color(self, color):
        active_stop = self.get_active_stop()
        if active_stop:
            active_stop.color = color
            self.update()

class ColorWheelPanel(QWidget):
    color_changed = pyqtSignal(QColor)
    
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8f8f8;")
        
        # Main layout 
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Color picker takes most space
        self.wheel_widget = ColorBox()
        self.wheel_widget.color_changed.connect(self.color_changed.emit)
        self.wheel_widget.color_changed.connect(self.update_color_preview)  # Update preview too
        main_layout.addWidget(self.wheel_widget, 1)  # Stretch factor 1
        
        # Current color preview (same width as color box)
        self.color_preview = QWidget()
        self.color_preview.setFixedHeight(30)
        self.color_preview.setStyleSheet("border: 2px solid #333; border-radius: 4px; background-color: #ff0000;")
        main_layout.addWidget(self.color_preview)
        
        # Hue slider with rainbow gradient
        self.hue_container, self.hue_slider = self.create_hue_slider(0, 359, 0)
        main_layout.addWidget(self.hue_container)
        
        # Connect hue slider
        self.hue_slider.valueChanged.connect(self.update_from_hue_slider)
        
        # Disable slider updates when setting from wheel
        self.updating_from_wheel = False
        
    def create_slider(self, min_val, max_val, default_val, label):
        """Create a styled slider with label."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        label_widget = QLabel(label[0])  # Just first letter (H, S, V)
        label_widget.setFixedWidth(15)
        label_widget.setAlignment(Qt.AlignCenter)
        label_widget.setStyleSheet("font-weight: bold; color: #555;")
        
        # Slider
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                height: 6px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #e1e1e1, stop:1 #c7c7c7);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);
                border: 1px solid #5c5c5c;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #d4d4d4, stop:1 #af8f8f);
            }
        """)
        
        # Value label
        value_label = QLabel(str(default_val))
        value_label.setFixedWidth(30)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("font-size: 11px; color: #666;")
        
        # Update value label when slider changes
        slider.valueChanged.connect(lambda v: value_label.setText(str(v)))
        
        layout.addWidget(label_widget)
        layout.addWidget(slider)
        layout.addWidget(value_label)
        
        return container, slider
        
    def create_hue_slider(self, min_val, max_val, default_val):
        """Create a hue slider with rainbow gradient background."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Label
        label_widget = QLabel("Hue")
        label_widget.setAlignment(Qt.AlignCenter)
        label_widget.setStyleSheet("font-weight: bold; color: #555; font-size: 12px;")
        
        # Slider with rainbow background
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.setFixedHeight(25)
        
        # Create rainbow gradient style
        rainbow_style = """
            QSlider::groove:horizontal {
                border: 1px solid #333;
                height: 15px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff0000, stop:0.17 #ff8000, stop:0.33 #ffff00,
                    stop:0.5 #00ff00, stop:0.67 #00ffff, stop:0.83 #0080ff,
                    stop:1 #8000ff);
                border-radius: 7px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #ffffff, stop:1 #dddddd);
                border: 2px solid #555;
                width: 15px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #ffffff, stop:1 #cccccc);
                border: 2px solid #333;
            }
        """
        slider.setStyleSheet(rainbow_style)
        
        layout.addWidget(label_widget)
        layout.addWidget(slider)
        
        return container, slider
        
    def update_from_hue_slider(self):
        """Handle hue slider changes - updates color box."""
        if self.updating_from_wheel:
            return
            
        h = max(0, min(359, self.hue_slider.value()))
        
        # Update color box hue (which recreates the color space)
        self.wheel_widget.set_hue(h)
        
        # Keep current saturation and value from color box
        _, s, v, _ = self.wheel_widget.current_color.getHsv()
        if s == -1:  # Handle grayscale
            s = 255
            v = 255
        color = QColor.fromHsv(h, s, v)
        
        # Update the color box's current color to the new hue
        self.wheel_widget.current_color = color
        self.wheel_widget.update()
        
        self.update_color_preview(color)
        self.color_changed.emit(color)
        
    def set_color(self, color):
        """Set color from external source (like gradient stop selection)."""
        h, s, v, _ = color.getHsv()
        if h == -1:  # Grayscale color
            h = 0
            
        # Update hue slider without triggering updates
        self.updating_from_wheel = True
        self.hue_slider.setValue(max(0, min(359, h)))
        self.updating_from_wheel = False
        
        # Update color picker and preview
        self.wheel_widget.set_color(color)
        self.update_color_preview(color)
        
    def update_color_preview(self, color):
        """Update the color preview widget."""
        self.color_preview.setStyleSheet(f"""
            border: 2px solid #333; 
            border-radius: 4px; 
            background-color: {color.name()};
        """)

class ColorBox(QWidget):
    color_changed = pyqtSignal(QColor)
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(200, 150)
        self.current_color = QColor(255, 0, 0)
        self.current_hue = 0
        self.current_value = 255
        self.dragging = False
        
        # Create high-quality color box
        self.color_pixmap = None
        self.create_color_pixmap()
        
    def create_color_pixmap(self):
        """Create a high-quality HSV color box."""
        self.color_pixmap = QPixmap(self.size())
        self.color_pixmap.fill(Qt.transparent)
        
        painter = QPainter(self.color_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw HSV color space as a rectangle - use more of the space
        # X-axis: Saturation (0-255), Y-axis: Value (255-0)
        width = self.width() - 10  # Smaller margin
        height = self.height() - 10
        margin = 5
        
        for x in range(width):
            for y in range(height):
                saturation = min(255, int(255 * x / width))
                value = min(255, int(255 * (height - y) / height))  # Invert Y so bright colors are at top
                hue = max(0, min(359, self.current_hue))  # Clamp hue to valid range
                
                color = QColor.fromHsv(hue, saturation, value)
                painter.setPen(color)
                painter.drawPoint(x + margin, y + margin)
                
        # Add border
        painter.setPen(QPen(QColor(180, 180, 180), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(margin, margin, width, height)
        
        painter.end()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw the color box
        if self.color_pixmap:
            painter.drawPixmap(0, 0, self.color_pixmap)
        
        # Draw current color indicator
        h, s, v, _ = self.current_color.getHsv()
        if h != -1:
            margin = 5
            width = self.width() - 10
            height = self.height() - 10
            
            x = margin + int(s * width / 255)
            y = margin + int((255 - v) * height / 255)  # Invert Y
            
            # Draw crosshair indicator
            painter.setPen(QPen(QColor(255, 255, 255), 3))
            painter.drawLine(x - 8, y, x + 8, y)
            painter.drawLine(x, y - 8, x, y + 8)
            
            painter.setPen(QPen(QColor(0, 0, 0), 1))
            painter.drawLine(x - 8, y, x + 8, y)
            painter.drawLine(x, y - 8, x, y + 8)
            
            # Small center dot
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(self.current_color))
            painter.drawEllipse(x - 3, y - 3, 6, 6)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.update_color_from_position(event.pos())
            
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.update_color_from_position(event.pos())
            
    def mouseReleaseEvent(self, event):
        self.dragging = False
        
    def update_color_from_position(self, pos):
        margin = 5
        width = self.width() - 10
        height = self.height() - 10
        
        x = max(0, min(width, pos.x() - margin))
        y = max(0, min(height, pos.y() - margin))
        
        saturation = min(255, int(255 * x / width))
        value = min(255, int(255 * (height - y) / height))  # Invert Y
        hue = max(0, min(359, self.current_hue))
        
        self.current_color = QColor.fromHsv(hue, saturation, value)
        self.color_changed.emit(self.current_color)
        self.update()
        
    def set_color(self, color):
        """Set color and update the box if hue changed."""
        h, s, v, _ = color.getHsv()
        if h == -1:  # Grayscale
            h = 0
            
        self.current_color = color
        
        # If hue changed, recreate the color box
        if h != self.current_hue:
            self.current_hue = h
            self.create_color_pixmap()
            
        self.current_value = v
        self.update()
        
    def set_hue(self, hue):
        """Update hue and recreate color box."""
        if hue != self.current_hue:
            self.current_hue = hue
            h, s, v, _ = self.current_color.getHsv()
            self.current_color = QColor.fromHsv(hue, s, v)
            self.create_color_pixmap()
            self.update()
            
    def resizeEvent(self, event):
        """Handle resize events by recreating the color pixmap."""
        super().resizeEvent(event)
        if hasattr(self, 'current_hue'):
            self.create_color_pixmap()

class LibraryGradientItem(QWidget):
    clicked = pyqtSignal(object)
    double_clicked = pyqtSignal(object)
    
    def __init__(self, gradient_data, filename):
        super().__init__()
        self.gradient_data = gradient_data
        self.filename = filename
        self.selected = False
        
        self.setFixedHeight(70)
        self.setStyleSheet("border: 2px solid transparent; border-radius: 4px; margin: 0px;")
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        
        # Draw gradient (like gradient editor but without stops)
        gradient_rect = QRect(5, 5, rect.width() - 10, rect.height() - 10)
        gradient = QLinearGradient(gradient_rect.left(), 0, gradient_rect.right(), 0)
        
        for stop_data in self.gradient_data['stops']:
            position = stop_data['position']
            color_values = stop_data['color']
            color = QColor(color_values[0], color_values[1], color_values[2], color_values[3])
            gradient.setColorAt(position, color)
            
        painter.fillRect(gradient_rect, gradient)
        
        # Subtle border around gradient
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(gradient_rect)
        
        # Highlight border when selected
        if self.selected:
            painter.setPen(QPen(QColor(100, 150, 255), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect.adjusted(1, 1, -1, -1))
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.set_selected(True)
            self.clicked.emit(self)
            
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self)
            
    def set_selected(self, selected):
        self.selected = selected
        self.update()
        if selected:
            self.setStyleSheet("border: 2px solid #6496ff; border-radius: 4px; background-color: #f0f6ff;")
        else:
            self.setStyleSheet("border: 2px solid transparent; border-radius: 4px; background-color: transparent;")

class MinimalGradientCreator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gradient Creator")
        self.setGeometry(100, 100, 600, 500)
        self.current_mode = 0  # 0 = image, 1 = color wheel
        self.current_view = 0  # 0 = create, 1 = library
        
        # Set close behavior
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Main content area (image and color wheel stack in same space)
        self.content_stack = QStackedWidget()
        
        # Image panel
        self.image_panel = ImagePanel()
        self.content_stack.addWidget(self.image_panel)
        
        # Color wheel panel  
        self.color_wheel = ColorWheelPanel()
        self.content_stack.addWidget(self.color_wheel)
        
        layout.addWidget(self.content_stack)
        
        # Gradient editor at bottom
        self.gradient_editor = GradientEditor()
        layout.addWidget(self.gradient_editor)
        
        # Create library view (hidden initially)
        self.library_view = self.create_library_view()
        self.content_stack.addWidget(self.library_view)
        
        # Library toggle button (top)
        self.library_btn = QPushButton("📚")
        self.library_btn.setFixedSize(40, 40)
        self.library_btn.setParent(main_widget)
        
        # Mode toggle button (middle) 
        self.toggle_btn = QPushButton("🎨")
        self.toggle_btn.setFixedSize(40, 40)
        self.toggle_btn.setParent(main_widget)
        
        # Save button (bottom)
        self.save_btn = QPushButton("💾")
        self.save_btn.setFixedSize(40, 40)
        self.save_btn.setParent(main_widget)
        
        # Delete button (appears in library mode)
        self.delete_btn = QPushButton("🗑️")
        self.delete_btn.setFixedSize(40, 40)
        self.delete_btn.setParent(main_widget)
        self.delete_btn.setVisible(False)
        
        # Start in image mode
        self.set_mode(0)
        
        # Connect signals
        self.image_panel.color_picked.connect(self.on_color_picked)
        self.gradient_editor.stop_selected.connect(lambda stop: self.color_wheel.set_color(stop.color))
        self.color_wheel.color_changed.connect(self.on_color_changed)
        self.library_btn.clicked.connect(self.toggle_view)
        self.toggle_btn.clicked.connect(self.toggle_mode)
        self.save_btn.clicked.connect(self.save_gradient)
        self.delete_btn.clicked.connect(self.delete_selected_gradient)
        
    def set_mode(self, mode):
        self.current_mode = mode
        self.content_stack.setCurrentIndex(mode)
        if mode == 0:  # Image mode
            self.toggle_btn.setText("🎨")  # Show palette icon to switch to color wheel
            self.image_panel.set_eyedropper_mode(True)
        else:  # Color mode
            self.toggle_btn.setText("📷")  # Show image icon to switch to image
            self.image_panel.set_eyedropper_mode(False)
            
    def toggle_mode(self):
        new_mode = 1 - self.current_mode  # Toggle between 0 and 1
        self.set_mode(new_mode)
        
    def on_color_picked(self, color):
        # Update active stop with picked color
        self.gradient_editor.update_active_stop_color(color)
        self.color_wheel.set_color(color)
        
    def on_color_changed(self, color):
        # Update active gradient stop
        self.gradient_editor.update_active_stop_color(color)
        
    def save_gradient(self):
        # Auto-save with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gradient_{timestamp}.json"
        
        gradient_data = {
            'name': filename.replace('.json', ''),
            'stops': [{
                'position': stop.position,
                'color': [stop.color.red(), stop.color.green(), stop.color.blue(), stop.color.alpha()]
            } for stop in self.gradient_editor.stops]
        }
        
        os.makedirs('gradients', exist_ok=True)
        with open(f'gradients/{filename}', 'w') as f:
            json.dump(gradient_data, f, indent=2)
            
        print(f"Saved gradient: {filename}")
        
        # Refresh library if it exists
        if hasattr(self, 'library_layout'):
            self.load_library_gradients()
        
    def create_library_view(self):
        """Create the library view for displaying saved gradients."""
        library_widget = QWidget()
        layout = QVBoxLayout(library_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Gradient Library")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Scrollable area for gradients
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")
        
        self.library_container = QWidget()
        self.library_layout = QVBoxLayout(self.library_container)
        self.library_layout.setAlignment(Qt.AlignTop)
        self.library_layout.setSpacing(1)
        self.library_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area.setWidget(self.library_container)
        layout.addWidget(scroll_area)
        
        # Load existing gradients
        self.load_library_gradients()
        
        return library_widget
        
    def load_library_gradients(self):
        """Load all saved gradients into the library."""
        # Clear existing items
        for i in reversed(range(self.library_layout.count())):
            self.library_layout.itemAt(i).widget().setParent(None)
            
        # Load gradients from files
        if not os.path.exists('gradients'):
            return
            
        gradient_files = [f for f in os.listdir('gradients') if f.endswith('.json')]
        gradient_files.sort(key=lambda f: os.path.getmtime(f'gradients/{f}'), reverse=True)  # Most recent first
        
        for filename in gradient_files:
            try:
                with open(f'gradients/{filename}', 'r') as f:
                    gradient_data = json.load(f)
                self.add_gradient_to_library(gradient_data, filename)
            except Exception as e:
                print(f"Error loading gradient {filename}: {e}")
                
    def add_gradient_to_library(self, gradient_data, filename):
        """Add a single gradient to the library display."""
        gradient_item = LibraryGradientItem(gradient_data, filename)
        gradient_item.clicked.connect(self.on_library_gradient_clicked)
        gradient_item.double_clicked.connect(self.on_library_gradient_double_clicked)
        self.library_layout.addWidget(gradient_item)
        
    def toggle_view(self):
        """Toggle between create and library views."""
        if self.current_view == 0:  # Currently in create mode
            self.current_view = 1
            self.library_btn.setText("🎨")  # Show create icon
            self.content_stack.setCurrentIndex(2)  # Library view
            self.toggle_btn.setVisible(False)
            self.save_btn.setVisible(False)
            self.gradient_editor.setVisible(False)
            self.load_library_gradients()  # Refresh library
        else:  # Currently in library mode
            self.current_view = 0
            self.library_btn.setText("📚")  # Show library icon
            self.content_stack.setCurrentIndex(self.current_mode)  # Back to create view
            self.toggle_btn.setVisible(True)
            self.save_btn.setVisible(True)
            self.gradient_editor.setVisible(True)
            self.delete_btn.setVisible(False)
            
    def on_library_gradient_clicked(self, gradient_item):
        """Handle single click on library gradient - show delete option."""
        # Clear other selections
        for i in range(self.library_layout.count()):
            item = self.library_layout.itemAt(i).widget()
            if item != gradient_item:
                item.set_selected(False)
                
        # Show delete button
        self.delete_btn.setVisible(True)
        self.selected_gradient_item = gradient_item
        
    def on_library_gradient_double_clicked(self, gradient_item):
        """Handle double click on library gradient - load into editor."""
        # Load gradient into editor
        gradient_data = gradient_item.gradient_data
        
        # Clear existing stops
        self.gradient_editor.stops.clear()
        
        # Load new stops
        for stop_data in gradient_data['stops']:
            position = stop_data['position']
            color_values = stop_data['color']
            color = QColor(color_values[0], color_values[1], color_values[2], color_values[3])
            stop = ColorStop(position, color)
            self.gradient_editor.stops.append(stop)
            
        # Set first stop as active
        if self.gradient_editor.stops:
            self.gradient_editor.set_active_stop(self.gradient_editor.stops[0])
            
        self.gradient_editor.update()
        
        # Return to create view
        self.toggle_view()
        
    def delete_selected_gradient(self):
        """Delete the selected gradient from library and filesystem."""
        if hasattr(self, 'selected_gradient_item'):
            filename = self.selected_gradient_item.filename
            try:
                os.remove(f'gradients/{filename}')
                self.selected_gradient_item.setParent(None)
                self.delete_btn.setVisible(False)
                print(f"Deleted gradient: {filename}")
            except Exception as e:
                print(f"Error deleting gradient: {e}")
                
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Keep buttons in top-left corner, stacked vertically
        self.library_btn.move(10, 10)
        self.toggle_btn.move(10, 55)
        self.save_btn.move(10, 100)
        self.delete_btn.move(10, 55)  # Same position as toggle when visible
        
    def closeEvent(self, event):
        """Handle window close event with proper cleanup."""
        try:
            # Clean up any resources
            if hasattr(self, 'image_panel') and self.image_panel.current_pixmap:
                self.image_panel.current_pixmap = None
                self.image_panel.scaled_pixmap = None
                
            if hasattr(self, 'color_wheel'):
                self.color_wheel.deleteLater()
                
            if hasattr(self, 'gradient_editor'):
                self.gradient_editor.deleteLater()
                
            # Accept the close event
            event.accept()
            
            # Force quit application
            QApplication.quit()
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
            event.accept()
            QApplication.quit()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    
    window = MinimalGradientCreator()
    window.show()
    
    try:
        sys.exit(app.exec_())
    except SystemExit:
        pass

if __name__ == "__main__":
    main()