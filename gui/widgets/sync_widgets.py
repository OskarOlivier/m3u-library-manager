# gui/widgets/sync_widgets.py
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QCheckBox, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt, QSize
from pathlib import Path

class FileItem(QWidget):
    """Custom widget for file item with fixed checkbox"""
    def __init__(self, file_path: Path, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)
        
        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setFixedSize(20, 20)
        layout.addWidget(self.checkbox)
        
        # File name (preserve exact name from file)
        from utils.m3u.parser import read_m3u
        self.file_path = file_path
        file_name = file_path.name
        
        # Create label using raw filename
        from PyQt6.QtWidgets import QLabel
        self.label = QLabel(file_name)
        self.label.setStyleSheet("color: white;")
        layout.addWidget(self.label)
        
        # Ensure widget takes full width
        layout.addStretch()
        
    def isChecked(self) -> bool:
        return self.checkbox.isChecked()
        
    def setChecked(self, checked: bool):
        self.checkbox.setChecked(checked)

class FileListWidget(QListWidget):
    """Custom list widget with fixed-position checkboxes"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet("""
            QListWidget {
                background-color: #2D2D2D;
                border: none;
                border-radius: 2px;
                padding: 4px;
            }
            QListWidget::item {
                background-color: transparent;
                padding: 2px;
                margin: 1px;
            }
            QListWidget::item:hover {
                background-color: #404040;
            }
            QListWidget::item:selected {
                background-color: #0078D4;
            }
            QCheckBox {
                spacing: 0px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        
    def add_file_item(self, file_path: Path) -> QListWidgetItem:
        """Add a new file item with fixed-position checkbox"""
        item = QListWidgetItem(self)
        self.addItem(item)
        
        file_widget = FileItem(file_path)
        item.setSizeHint(file_widget.sizeHint())
        self.setItemWidget(item, file_widget)
        
        return item
        
    def get_checked_files(self) -> set[Path]:
        """Get all checked file paths"""
        checked_files = set()
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget and widget.isChecked():
                checked_files.add(widget.file_path)
        return checked_files
        
    def set_all_checked(self, checked: bool):
        """Set all items checked/unchecked"""
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if widget:
                widget.setChecked(checked)