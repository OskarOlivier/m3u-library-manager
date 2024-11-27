# gui/components/widgets/count_label.py

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

from gui.components.styles.fonts import COUNT_FONT
from gui.components.styles.colors import SECONDARY_TEXT, TEXT_COLOR

class CountLabel(QLabel):
    """
    A specialized label for displaying item counts with consistent styling.
    Supports different count types (files, playlists, etc.) and formatting.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.set_count(0)
        
    def setup_ui(self):
        """Configure label appearance."""
        self.setFont(COUNT_FONT)
        self.setStyleSheet(f"color: {SECONDARY_TEXT};")
        self.setAlignment(Qt.AlignmentFlag.AlignRight | 
                         Qt.AlignmentFlag.AlignVCenter)
        
    def set_count(self, count: int, item_type: str = "items"):
        """
        Update the displayed count with formatting.
        
        Args:
            count: Number of items
            item_type: Type of items being counted (e.g., "playlists", "files")
        """
        if count == 0:
            self.setText(f"No {item_type}")
        elif count == 1:
            # Handle singular form
            singular = item_type[:-1] if item_type.endswith('s') else item_type
            self.setText(f"1 {singular}")
        else:
            self.setText(f"{count:,} {item_type}")
            
    def set_loading(self):
        """Show loading state."""
        self.setStyleSheet(f"color: {SECONDARY_TEXT};")
        self.setText("Loading...")
        
    def set_error(self, error_text: str = "Error"):
        """Show error state."""
        self.setStyleSheet(f"color: {TEXT_COLOR};")
        self.setText(error_text)
        
    def clear(self):
        """Clear the count display."""
        self.setText("")