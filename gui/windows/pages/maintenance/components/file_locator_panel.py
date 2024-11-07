# gui/windows/pages/maintenance/components/file_locator_panel.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QListWidget, QListWidgetItem, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from pathlib import Path
from typing import List, Optional, Set

class FileListWidget(QListWidget):
    """Custom list widget for file display with selection handling"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the list widget UI"""
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.setStyleSheet("""
            QListWidget {
                background-color: #2D2D2D;
                border: none;
                border-radius: 2px;
                padding: 4px;
            }
            QListWidget::item {
                color: white;
                padding: 6px;
                margin: 2px;
                border-radius: 2px;
            }
            QListWidget::item:hover {
                background-color: #404040;
            }
            QListWidget::item:selected {
                background-color: #0078D4;
            }
        """)

class FileLocatorPanel(QWidget):
    """Panel for displaying and managing file lists"""
    
    filesLocated = pyqtSignal(list)  # Emits list of located files
    progressUpdated = pyqtSignal(int)
    
    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.current_files: Set[Path] = set()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the panel UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("Missing Files")
        title.setFont(QFont("Segoe UI", 11))
        title.setStyleSheet("color: white;")
        header.addWidget(title)
        
        # File count
        self.count_label = QLabel("0 files")
        self.count_label.setFont(QFont("Segoe UI", 10))
        self.count_label.setStyleSheet("color: #999999;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header.addWidget(self.count_label)
        
        layout.addLayout(header)
        
        # File list
        self.file_list = FileListWidget()
        layout.addWidget(self.file_list)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.locate_btn = QPushButton("Locate Files")
        self.locate_btn.clicked.connect(self.on_locate_clicked)
        
        self.clear_btn = QPushButton("Clear List")
        self.clear_btn.clicked.connect(self.clear_files)
        
        for btn in [self.locate_btn, self.clear_btn]:
            btn.setFont(QFont("Segoe UI", 10))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2D2D2D;
                    color: white;
                    border: none;
                    border-radius: 2px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #404040;
                }
                QPushButton:pressed {
                    background-color: #505050;
                }
                QPushButton:disabled {
                    background-color: #1A1A1A;
                    color: #666666;
                }
            """)
            button_layout.addWidget(btn)
            
        layout.addLayout(button_layout)
        
    def set_files(self, files: List[Path]):
        """Update the file list display"""
        self.file_list.clear()
        self.current_files = set(files)
        
        for file_path in sorted(files):
            item = QListWidgetItem(file_path.name)
            item.setData(Qt.ItemDataRole.UserRole, str(file_path))
            self.file_list.addItem(item)
            
        self.count_label.setText(f"{len(files)} files")
        self.locate_btn.setEnabled(len(files) > 0)
        
    def clear_files(self):
        """Clear the file list"""
        self.file_list.clear()
        self.current_files.clear()
        self.count_label.setText("0 files")
        self.locate_btn.setEnabled(False)
        
    def get_selected_files(self) -> List[Path]:
        """Get list of selected file paths"""
        selected = []
        for item in self.file_list.selectedItems():
            path = Path(item.data(Qt.ItemDataRole.UserRole))
            selected.append(path)
        return selected
    
    def on_locate_clicked(self):
        """Handle locate button click"""
        selected = self.get_selected_files()
        if selected:
            self.filesLocated.emit(selected)
            
    def update_progress(self, value: int):
        """Update progress value"""
        self.progressUpdated.emit(value)