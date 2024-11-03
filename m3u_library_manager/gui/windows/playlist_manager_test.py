# gui/windows/playlist_manager_test.py

from PyQt6.QtWidgets import QApplication, QVBoxLayout, QMainWindow, QWidget, QSizePolicy
from pathlib import Path
from playlist_manager import PlaylistItem  # Assuming PlaylistItem class is in this module

class PlaylistTestWindow(QMainWindow):
    """Main window for testing PlaylistItem stretching"""

    def __init__(self):
        super().__init__()

        # Main container widget and layout
        main_widget = QWidget(self)
        main_layout = QVBoxLayout(main_widget)

        # Ensure main_widget stretches horizontally
        main_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Populate with PlaylistItems
        for i in range(5):
            item = PlaylistItem(Path(f"Sample Playlist {i+1}"), 10 * (i + 1))
            item.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            main_layout.addWidget(item)

        # Set the main widget with adjusted policies as central widget
        self.setCentralWidget(main_widget)
        self.setWindowTitle("Playlist Item Stretch Test")
        self.resize(600, 400)

# Run in isolated environment
if __name__ == "__main__":
    app = QApplication([])
    window = PlaylistTestWindow()
    window.show()
    app.exec()

