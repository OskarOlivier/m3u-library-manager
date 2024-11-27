# gui/windows/pages/maintenance/components/file_locator_panel.py

from pathlib import Path
from typing import Optional, Set, Dict
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from gui.components.panels.base_file_panel import BaseFilePanel
from gui.components.styles.colors import (
   SUCCESS_COLOR,
   ERROR_COLOR,
   WARNING_COLOR,
   PRIMARY_ACCENT
)

class FileLocatorPanel(BaseFilePanel):
    """Panel for handling missing files with location suggestions."""
    
    # Signals
    locate_requested = pyqtSignal(object)  # Request to locate files
    scan_requested = pyqtSignal(object)    # Request to scan locations
    repair_requested = pyqtSignal(object)  # Request to repair file references
    alternative_selected = pyqtSignal(object, object)  # Selected alternative location
    
    def __init__(self, state, parent: Optional[QWidget] = None):
        # Instance variables that need to be set before parent init
        self.state = state
        self.sync_direction = 'both'
        self.alternatives: Dict[Path, Set[Path]] = {}  # Initialize alternatives dict
        self.add_remote_btn = None
        self.delete_local_btn = None
        self.add_local_btn = None
        self.delete_remote_btn = None
        self.verify_btn = None
        
        # Call parent init which will call setup_action_buttons
        super().__init__(title="Missing Files", parent=parent)
        
    def setup_action_buttons(self):
        """Set up sync-specific action buttons."""
        # Scan button
        self.scan_btn = self._create_button(
            "Scan Library",
            lambda: self._request_scan()
        )
        
        # Locate button
        self.locate_btn = self._create_button(
            "Locate Selected",
            lambda: self._request_locate()
        )
        
        # Repair button
        self.repair_btn = self._create_button(
            "Repair References",
            lambda: self._request_repair()
        )
        
        # Add buttons to layout
        self.action_layout.addWidget(self.scan_btn)
        self.action_layout.addWidget(self.locate_btn)
        self.action_layout.addWidget(self.repair_btn)
        
        # Initially disable action buttons
        self._update_button_states()
        
        # Add filter buttons
        filter_layout = self.create_filter_section()
        self.action_layout.addLayout(filter_layout)
        
    def create_filter_section(self):
        """Create filter buttons for different file states."""
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(4)
        
        # Filter by state buttons
        self.show_all_btn = self._create_button(
            "All",
            lambda: self.filter_files("all")
        )
        self.show_unlocated_btn = self._create_button(
            "Unlocated",
            lambda: self.filter_files("unlocated")
        )
        self.show_alternatives_btn = self._create_button(
            "Has Alternatives",
            lambda: self.filter_files("alternatives")
        )
        
        filter_layout.addWidget(self.show_all_btn)
        filter_layout.addWidget(self.show_unlocated_btn)
        filter_layout.addWidget(self.show_alternatives_btn)
        
        return filter_layout
        
    def _request_locate(self):
        """Request location search for selected files."""
        files = self.get_selected_files()
        if files:
            self.locate_requested.emit(files)
            
    def _request_scan(self):
        """Request library scan for selected files."""
        files = self.get_checked_files()
        if files:
            self.scan_requested.emit(files)
            
    def _request_repair(self):
        """Request repair of file references."""
        # Only repair files that have alternatives
        files = {f for f in self.get_checked_files() 
                if f in self.alternatives and self.alternatives[f]}
        if files:
            self.repair_requested.emit(files)
            
    def _update_button_states(self):
        """Update button enabled states based on selection and available actions."""
        has_selected = bool(self.get_selected_files())
        has_checked = bool(self.get_checked_files())
        has_alternatives = any(self.alternatives.get(f) 
                             for f in self.get_checked_files())
        
        # Selection buttons
        self.check_all_btn.setEnabled(bool(self.files))
        self.uncheck_all_btn.setEnabled(has_checked)
        
        # Action buttons
        self.locate_btn.setEnabled(has_selected)
        self.scan_btn.setEnabled(has_checked)
        self.repair_btn.setEnabled(has_checked and has_alternatives)
        
    def set_alternatives(self, original_path: Path, alternative_paths: Set[Path]):
        """Set alternative locations for a missing file."""
        self.alternatives[original_path] = alternative_paths
        
        # Update visual state
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            widget = self.file_list.itemWidget(item)
            if widget and widget.file_path == original_path:
                if alternative_paths:
                    widget.set_status_color(WARNING_COLOR)
                else:
                    widget.set_status_color(ERROR_COLOR)
                break
                
    def start_location_search(self, files: Set[Path]):
        """Start file location search visual state."""
        self.set_loading(True)
        self._set_files_status(files, PRIMARY_ACCENT)
        self._disable_actions()
        
    def finish_location_search(self, found: Dict[Path, Set[Path]], not_found: Set[Path]):
        """Update visual state after location search completion."""
        self.set_loading(False)
        
        # Update alternatives and visual state
        for original, alternatives in found.items():
            self.set_alternatives(original, alternatives)
            
        self._set_files_status(not_found, ERROR_COLOR)
        self._update_button_states()
        
    def _set_files_status(self, files: Set[Path], color: str):
        """Set status color for specified files."""
        for file_path in files:
            for i in range(self.file_list.count()):
                item = self.file_list.item(i)
                widget = self.file_list.itemWidget(item)
                if widget and widget.file_path == file_path:
                    widget.set_status_color(color)
                    break
                    
    def _disable_actions(self):
        """Disable all action buttons during operations."""
        for button in [self.scan_btn, self.locate_btn, self.repair_btn,
                      self.check_all_btn, self.uncheck_all_btn]:
            button.setEnabled(False)
            
    def filter_files(self, filter_type: str):
        """Filter displayed files based on their state."""
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            widget = self.file_list.itemWidget(item)
            if not widget:
                continue
                
            show = False
            if filter_type == 'all':
                show = True
            elif filter_type == 'unlocated':
                show = widget.file_path not in self.alternatives
            elif filter_type == 'alternatives':
                show = (widget.file_path in self.alternatives and 
                       bool(self.alternatives[widget.file_path]))
                
            item.setHidden(not show)
            
    def cleanup(self):
        """Clean up resources."""
        super().cleanup()
        self.alternatives.clear()