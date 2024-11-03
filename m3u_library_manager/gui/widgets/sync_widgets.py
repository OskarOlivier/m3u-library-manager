# gui/widgets/sync_widgets.py
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QCheckBox
from PyQt6.QtCore import Qt
from pathlib import Path

class FileListWidget(QListWidget):
    """Custom list widget with checkboxes for file selection"""
    
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
                color: white;
                padding: 4px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #404040;
            }
            QListWidget::item:selected {
                background-color: #0078D4;
            }
            QCheckBox {
                color: white;
            }
        """)
        
    def add_file_item(self, file_path: Path) -> QListWidgetItem:
        """Add a new file item with checkbox"""
        item = QListWidgetItem(self)
        self.addItem(item)
        
        checkbox = QCheckBox(str(file_path))
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Unchecked)
        
        self.setItemWidget(item, checkbox)
        return item
        
    def get_checked_files(self) -> set[Path]:
        """Get all checked file paths"""
        checked_files = set()
        for i in range(self.count()):
            item = self.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checkbox = self.itemWidget(item)
                checked_files.add(Path(checkbox.text()))
        return checked_files
        
    def set_all_checked(self, checked: bool):
        """Set all items checked/unchecked"""
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for i in range(self.count()):
            self.item(i).setCheckState(state)