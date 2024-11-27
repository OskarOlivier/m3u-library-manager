# gui/components/panels/base_file_panel.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QFrame, QPushButton, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path
from typing import Optional, Set, Dict
import logging

from gui.components.widgets.file_item import FileItem
from gui.components.widgets.count_label import CountLabel
from gui.components.widgets.progress_bar import ProgressWidget
from gui.components.styles.layouts import (
    PANEL_MARGINS, 
    PANEL_SPACING,
    PLAYLIST_ITEM_LAYOUT
)
from gui.components.styles.fonts import TITLE_FONT
from gui.components.styles.colors import (
    TEXT_COLOR,
    BACKGROUND_COLOR,
    SECONDARY_TEXT,
    ITEM_HOVER,
    ITEM_SELECTED,
    PRIMARY_ACCENT
)

class BaseFilePanel(QWidget):
    """Base panel for displaying and managing file items."""
    
    files_selected = pyqtSignal(set)  # Emits set of selected file paths
    operation_requested = pyqtSignal(str, set)  # Emits (operation_type, file_paths)
    count_changed = pyqtSignal(int)  # Emits new file count
    
    def __init__(self, title: str = "Files", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.title = title
        self.logger = logging.getLogger(self.__class__.__name__)
        self.file_widgets: Dict[Path, FileItem] = {}
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*PANEL_MARGINS)
        layout.setSpacing(PANEL_SPACING)
        
        # Header with title and count
        header = QHBoxLayout()
        header.setSpacing(PANEL_SPACING)
        
        self.title_label = QLabel(self.title)
        self.title_label.setFont(TITLE_FONT)
        self.title_label.setStyleSheet(f"color: {TEXT_COLOR};")
        header.addWidget(self.title_label)
        
        self.count_label = CountLabel()
        header.addWidget(self.count_label)
        layout.addLayout(header)
        
        # Progress bar
        self.progress_widget = ProgressWidget()
        layout.addWidget(self.progress_widget)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.file_list.setFrameShape(QFrame.Shape.NoFrame)
        self.file_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.file_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.file_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {BACKGROUND_COLOR};
                border: none;
                border-radius: 4px;
                padding: 4px;
                outline: none;
            }}
            QListWidget::item {{
                background-color: transparent;
                padding: 0px;
                border-radius: 4px;
                border: none;
            }}
            QListWidget::item:selected {{
                background-color: transparent;
            }}
            QListWidget::item:hover {{
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {BACKGROUND_COLOR};
                width: 8px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #666666;
                min-height: 20px;
                border-radius: 4px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #888888;
            }}
            QScrollBar::add-line:vertical, 
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, 
            QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        layout.addWidget(self.file_list)
        
        # Button container
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(PANEL_SPACING)
        
        # Selection buttons
        self.check_all_btn = self._create_button(
            "Check All",
            self._check_all_items
        )
        self.uncheck_all_btn = self._create_button(
            "Uncheck All",
            self._uncheck_all_items
        )
        
        button_layout.addWidget(self.check_all_btn)
        button_layout.addWidget(self.uncheck_all_btn)
        layout.addWidget(button_frame)
        
        # Action buttons container
        self.action_frame = QFrame()
        self.action_layout = QHBoxLayout(self.action_frame)
        self.action_layout.setContentsMargins(0, 0, 0, 0)
        self.action_layout.setSpacing(PANEL_SPACING)
        layout.addWidget(self.action_frame)
        
    def _create_button(self, text: str, callback: Optional[callable] = None,
                      enabled: bool = True) -> QPushButton:
        """Create a styled button."""
        button = QPushButton(text)
        button.setFont(TITLE_FONT)
        button.setEnabled(enabled)
        
        if callback:
            button.clicked.connect(callback)
            
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {BACKGROUND_COLOR};
                color: {TEXT_COLOR};
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: {ITEM_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {ITEM_SELECTED};
            }}
            QPushButton:disabled {{
                background-color: #1A1A1A;
                color: {SECONDARY_TEXT};
            }}
        """)
        
        return button
        
    def connect_signals(self):
        """Connect internal signals."""
        self.file_list.itemSelectionChanged.connect(self._on_selection_changed)
        
    def add_files(self, files: Set[Path], clear_existing: bool = True):
        """Add files to the panel."""
        try:
            if clear_existing:
                self.clear_files()
                
            for file_path in sorted(files):
                # Create list item
                item = QListWidgetItem(self.file_list)
                
                # Create file widget
                widget = FileItem(file_path)
                widget.checkbox_changed.connect(self._on_item_checked)
                
                # Set item size
                item.setSizeHint(widget.sizeHint())
                self.file_list.addItem(item)
                self.file_list.setItemWidget(item, widget)
                
                # Store reference
                self.file_widgets[file_path] = widget
                
            # Update count
            self.count_label.set_count(len(self.file_widgets), "files")
            self.count_changed.emit(len(self.file_widgets))
            self._update_button_states()
            
        except Exception as e:
            self.logger.error(f"Error adding files: {e}")
            self.count_label.set_error()
            
    def clear_files(self):
        """Clear all files from the panel."""
        self.file_list.clear()
        self.file_widgets.clear()
        self.count_label.set_count(0, "files")
        self.count_changed.emit(0)
        self._update_button_states()
        
    def get_checked_files(self) -> Set[Path]:
        """Get set of checked file paths."""
        return {path for path, widget in self.file_widgets.items() 
                if widget.is_checked()}
        
    def get_selected_files(self) -> Set[Path]:
        """Get set of selected file paths."""
        paths = set()
        for item in self.file_list.selectedItems():
            widget = self.file_list.itemWidget(item)
            if isinstance(widget, FileItem):
                paths.add(widget.file_path)
        return paths
        
    def _check_all_items(self):
        """Check all file items."""
        for widget in self.file_widgets.values():
            widget.set_checked(True, emit=False)
        self._on_item_checked()
        
    def _uncheck_all_items(self):
        """Uncheck all file items."""
        for widget in self.file_widgets.values():
            widget.set_checked(False, emit=False)
        self._on_item_checked()
        
    def _on_selection_changed(self):
        """Handle file selection changes."""
        selected = self.get_selected_files()
        self.files_selected.emit(selected)
        self._update_button_states()
        
    def _on_item_checked(self):
        """Handle checkbox state changes."""
        self._update_button_states()
        
    def _update_button_states(self):
        """Update button enabled states."""
        has_checked = bool(self.get_checked_files())
        has_files = bool(self.file_widgets)
        
        self.check_all_btn.setEnabled(has_files)
        self.uncheck_all_btn.setEnabled(has_checked)
        
    def set_error_state(self, file_paths: Set[Path]):
        """Set error state for specific files."""
        for path, widget in self.file_widgets.items():
            widget.set_error_state(path in file_paths)
            
    def cleanup(self):
        """Clean up resources."""
        try:
            self.logger.debug("Cleaning up base file panel")
            # Clear file widgets
            for widget in self.file_widgets.values():
                widget.deleteLater()
            self.file_widgets.clear()
            
            # Clear list widget
            self.file_list.clear()
            
            # Disconnect signals
            try:
                self.file_list.itemSelectionChanged.disconnect()
                self.files_selected.disconnect()
                self.operation_requested.disconnect()
                self.count_changed.disconnect()
            except Exception:
                pass  # Ignore disconnection errors
                
        except Exception as e:
            self.logger.error(f"Error during base file panel cleanup: {e}")