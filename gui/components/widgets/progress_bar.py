# gui/components/widgets/progress_bar.py

from PyQt6.QtWidgets import QProgressBar, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtProperty, QPropertyAnimation, QEasingCurve
import logging

from gui.components.styles.colors import (
    PROGRESS_BACKGROUND,
    PROGRESS_FILL,
    PRIMARY_ACCENT
)
from gui.components.styles.layouts import PROGRESS_BAR_HEIGHT

class ProgressBar(QProgressBar):
    """
    Enhanced progress bar with smooth animations and consistent styling.
    Supports both determinate and indeterminate states.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._animation = None
        self._fade_timer = None
        self._auto_hide = True
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setup_ui()
        
    def setup_ui(self):
        """Configure progress bar appearance."""
        self.setFixedHeight(PROGRESS_BAR_HEIGHT)
        self.setTextVisible(False)
        self.setRange(0, 100)
        self.setValue(0)
        
        self.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: {PROGRESS_BAR_HEIGHT // 2}px;
                background-color: {PROGRESS_BACKGROUND};
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                border-radius: {PROGRESS_BAR_HEIGHT // 2}px;
                background-color: {PROGRESS_FILL};
            }}
        """)
        
    def set_progress(self, value: int, animate: bool = True):
        """
        Set progress value with optional animation.
        
        Args:
            value: Progress value (0-100)
            animate: Whether to animate the change
        """
        try:
            # Ensure value is in valid range
            value = max(0, min(100, value))
            
            if not animate:
                self.setValue(value)
                self._handle_completion(value)
                return
                
            # Stop existing animation if any
            if self._animation is not None:
                self._animation.stop()
                
            # Create and start new animation
            self._animation = QPropertyAnimation(self, b"value")
            self._animation.setDuration(300)  # 300ms animation
            self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._animation.setStartValue(self.value())
            self._animation.setEndValue(value)
            self._animation.start()
            
            # Handle completion
            self._animation.finished.connect(
                lambda: self._handle_completion(value))
            
        except Exception as e:
            self.logger.error(f"Error setting progress: {e}")
            self.setValue(value)  # Fallback to instant update
            
    def _handle_completion(self, value: int):
        """Handle progress completion and auto-hide."""
        if value >= 100 and self._auto_hide:
            # Start fade timer
            if self._fade_timer is None:
                self._fade_timer = QTimer(self)
                self._fade_timer.setSingleShot(True)
                self._fade_timer.timeout.connect(self.hide)
            
            self._fade_timer.start(1000)  # Hide after 1 second
            
    def start_indeterminate(self):
        """Start indeterminate progress mode."""
        self.setRange(0, 0)  # Makes the progress bar indeterminate
        self.show()
        
        # Style for indeterminate mode
        self.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: {PROGRESS_BAR_HEIGHT // 2}px;
                background-color: {PROGRESS_BACKGROUND};
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                border-radius: {PROGRESS_BAR_HEIGHT // 2}px;
                background-color: {PRIMARY_ACCENT};
            }}
        """)
        
    def stop_indeterminate(self):
        """Stop indeterminate progress mode."""
        self.setRange(0, 100)
        self.setValue(0)
        self.setup_ui()  # Restore original styling
        
    def set_auto_hide(self, enabled: bool):
        """Enable or disable auto-hide on completion."""
        self._auto_hide = enabled
        
    def cleanup(self):
        """Clean up resources."""
        if self._animation is not None:
            self._animation.stop()
            self._animation = None
            
        if self._fade_timer is not None:
            self._fade_timer.stop()
            self._fade_timer = None

class ProgressWidget(QWidget):
    """
    Container widget that combines progress bar with optional label.
    Provides a complete progress indication solution.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the progress widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Create progress bar
        self.progress_bar = ProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Initially hidden
        self.hide()
        
    def set_progress(self, value: int, animate: bool = True):
        """Set progress value."""
        self.show()
        self.progress_bar.set_progress(value, animate)
        
    def start_indeterminate(self):
        """Start indeterminate progress."""
        self.show()
        self.progress_bar.start_indeterminate()
        
    def stop_indeterminate(self):
        """Stop indeterminate progress."""
        self.progress_bar.stop_indeterminate()
        if self.progress_bar._auto_hide:
            self.hide()
            
    def set_auto_hide(self, enabled: bool):
        """Set auto-hide behavior."""
        self.progress_bar.set_auto_hide(enabled)
        
    def cleanup(self):
        """Clean up resources."""
        self.progress_bar.cleanup()