# gui/windows/pages/maintenance/components/sort_panel.py

from typing import Optional, List
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QPushButton, QButtonGroup)
from PyQt6.QtCore import Qt, pyqtSignal
import logging

from gui.components.styles.colors import (
    TEXT_COLOR,
    BACKGROUND_COLOR,
    PRIMARY_ACCENT,
    SUCCESS_COLOR,
    WARNING_COLOR
)
from gui.components.styles.fonts import TITLE_FONT
from gui.components.styles.layouts import PANEL_MARGINS, PANEL_SPACING
from ..state import PlaylistAnalysis  # Add this import

class SortPanel(QWidget):
    """Panel for sorting playlist files and showing current sort state."""
    
    # Signals
    sort_requested = pyqtSignal(str)  # Emits sort method key
    
    # Available sort methods
    SORT_METHODS = {
        'path_asc': ('File Path (A-Z)', True),
        'path_desc': ('File Path (Z-A)', False),
        'duration_asc': ('Duration (Shortest)', True),
        'duration_desc': ('Duration (Longest)', False),
        'bpm_asc': ('BPM (Slowest)', True),
        'bpm_desc': ('BPM (Fastest)', False),
        'custom': ('Custom Order', None)  # Special case for analysis only
    }
    
    def __init__(self, state, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.state = state
        self.buttons = {}
        self.current_method = None
        self.analysis_result = None
        self.setup_ui()
        self.connect_signals()
            
    def setup_ui(self):
        """Set up the sorting panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*PANEL_MARGINS)
        layout.setSpacing(PANEL_SPACING)
        
        # Title and analysis status
        header_layout = QHBoxLayout()
        
        title = QLabel("Sort Options")
        title.setFont(TITLE_FONT)
        title.setStyleSheet(f"color: {TEXT_COLOR};")
        header_layout.addWidget(title)
        
        self.status_label = QLabel()
        self.status_label.setFont(TITLE_FONT)
        self.status_label.setStyleSheet(f"color: {SUCCESS_COLOR};")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(self.status_label)
        
        layout.addLayout(header_layout)
        
        # Sort buttons container
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(4)
        
        # Create button group for exclusive selection
        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)
        
        # Create sort buttons
        sort_methods = {
            'path_asc': ('File Path (A-Z)', True),
            'path_desc': ('File Path (Z-A)', False),
            'duration_asc': ('Duration (Shortest)', True),
            'duration_desc': ('Duration (Longest)', False),
            'bpm_asc': ('BPM (Slowest)', True),
            'bpm_desc': ('BPM (Fastest)', False),
            'custom': ('Custom Order', None)  # Make sure to include custom in initial setup
        }
        
        # Store references to all buttons
        self.buttons = {}
        
        for method_key, (label, _) in sort_methods.items():
            button = QPushButton(label)
            button.setCheckable(True)
            button.setFont(TITLE_FONT)
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BACKGROUND_COLOR};
                    color: {TEXT_COLOR};
                    border: none;
                    border-radius: 2px;
                    padding: 8px 16px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background-color: #404040;
                }}
                QPushButton:checked {{
                    background-color: {PRIMARY_ACCENT};
                }}
                QPushButton:disabled {{
                    background-color: #1A1A1A;
                    color: #666666;
                }}
            """)
            
            # Hide custom button initially - only shown when detected
            if method_key == 'custom':
                button.hide()
                
            self.button_group.addButton(button)
            buttons_layout.addWidget(button)
            self.buttons[method_key] = button  # Make sure to store reference
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        # Sort action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(PANEL_SPACING)
        
        self.sort_btn = QPushButton("Sort")
        self.sort_btn.setFont(TITLE_FONT)
        self.sort_btn.setEnabled(False)
        self.sort_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PRIMARY_ACCENT};
                color: white;
                border: none;
                border-radius: 2px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #1982D4;
            }}
            QPushButton:pressed {{
                background-color: #106EBE;
            }}
            QPushButton:disabled {{
                background-color: #1A1A1A;
                color: #666666;
            }}
        """)
        action_layout.addWidget(self.sort_btn)
        
        layout.addLayout(action_layout)
        
    def connect_signals(self):
        """Connect internal signals."""
        self.button_group.buttonClicked.connect(self._on_method_selected)
        self.sort_btn.clicked.connect(self._on_sort_clicked)
        
        # Connect to state signals
        self.state.playlist_selected.connect(self._on_playlist_selected)
        self.state.playlist_deselected.connect(self._on_playlist_deselected)
        self.state.analysis_completed.connect(self._on_analysis_completed)
        
    def _on_method_selected(self, button):
        """Handle sort method selection."""
        # Find the method key for the selected button
        for method, btn in self.buttons.items():
            if btn == button:
                self.current_method = method
                break
                
        # Don't enable sort button for custom order
        self.sort_btn.setEnabled(self.current_method != 'custom')
        
    def _on_sort_clicked(self):
        """Handle sort button click."""
        if self.current_method and self.current_method != 'custom':
            self.sort_requested.emit(self.current_method)
           
    def _on_playlist_selected(self, playlist_path: Path):
        """Handle playlist selection."""
        # Enable sort options except custom
        for method, button in self.buttons.items():
            if method != 'custom':
                button.setEnabled(True)
                
        # Check for existing analysis
        analysis = self.state.get_analysis(playlist_path)
        if analysis:
            self.logger.debug(f"Found existing analysis for {playlist_path.name}")
            self.logger.debug(f"Sort method: {analysis.sort_method}")
            self._highlight_detected_sort_method(analysis.sort_method)
            self._update_status(analysis)
        else:
            self._clear_sort_method()

    def _clear_sort_method(self):
        """Clear sort method selection."""
        self.button_group.setExclusive(False)
        for button in self.buttons.values():
            button.setChecked(False)
            if button == self.buttons['custom']:
                button.hide()
        self.button_group.setExclusive(True)
        self.status_label.clear()
        
    def _update_status(self, analysis: PlaylistAnalysis):
        """Update status display based on analysis."""
        if analysis.missing_files:
            self.status_label.setText(f"{len(analysis.missing_files)} missing files")
            self.status_label.setStyleSheet(f"color: {WARNING_COLOR};")
        else:
            self.status_label.setText("All files valid")
            self.status_label.setStyleSheet(f"color: {SUCCESS_COLOR};")

    def _on_analysis_completed(self, playlist_path: Path, analysis):
        """Handle completed analysis."""
        self.logger.debug(f"Received analysis completion for {playlist_path.name}")
        self.logger.debug(f"Sort method: {analysis.sort_method}")
        self._highlight_detected_sort_method(analysis.sort_method)
        self._update_status(analysis)
            
    def _on_playlist_deselected(self):
        """Handle playlist deselection."""
        # Clear and disable sort options
        self.button_group.setExclusive(False)
        for button in self.buttons.values():
            button.setChecked(False)
            button.setEnabled(False)
            if button == self.buttons['custom']:
                button.hide()
        self.button_group.setExclusive(True)
        
        self.current_method = None
        self.sort_btn.setEnabled(False)
        self.status_label.clear()
        self.analysis_result = None
       
    def _on_analysis_completed(self, playlist_path: Path, analysis):
        """Handle completed analysis results."""
        if hasattr(analysis, 'sort_method'):
            self.analysis_result = analysis
            
            # Update sort method display
            self._highlight_detected_sort_method(analysis.sort_method)
            
            # Update status
            if analysis.missing_files:
                self.status_label.setText(f"{len(analysis.missing_files)} missing files")
                self.status_label.setStyleSheet(f"color: {WARNING_COLOR};")
            else:
                self.status_label.setText("All files valid")
                self.status_label.setStyleSheet(f"color: {SUCCESS_COLOR};")
            
    def _highlight_detected_sort_method(self, detected_method: Optional[str]):
        """Highlight the detected sort method button."""
        # Clear current selection
        self.button_group.setExclusive(False)
        for button in self.buttons.values():
            button.setChecked(False)
        self.button_group.setExclusive(True)
        
        if detected_method in self.buttons:
            # Known sort method detected
            self.buttons[detected_method].setChecked(True)
            self.buttons['custom'].hide()
        else:
            # Custom or unknown sort order
            self.buttons['custom'].show()
            self.buttons['custom'].setChecked(True)
            
    def get_analysis_result(self):
        """Get current analysis result."""
        return self.analysis_result
        
    def cleanup(self):
        """Clean up resources."""
        # Clear state
        self.current_method = None
        self.analysis_result = None
        
        # Clear selection
        self.button_group.setExclusive(False)
        for button in self.buttons.values():
            button.setChecked(False)
            if button == self.buttons['custom']:
                button.hide()
        self.button_group.setExclusive(True)
        
        # Clear status
        self.status_label.clear()
        
        # Clear references
        self.buttons.clear()