# gui/windows/pages/curation/components/song_selection_widget.py

from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton, 
                           QMenu, QWidgetAction, QToolTip)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
from pathlib import Path
from typing import Optional
import logging

from gui.components.styles.colors import (
    TEXT_COLOR,
    BACKGROUND_COLOR,
    ITEM_HOVER,
    ITEM_SELECTED,
    SECONDARY_TEXT,
    WARNING_COLOR
)
from gui.components.styles.fonts import TEXT_FONT
from core.matching.song_matcher import SongMatchResult

class MatchOptionWidget(QWidget):
    """Widget for displaying a single match option in the dropdown."""
    
    clicked = pyqtSignal(Path)
    
    def __init__(self, file_path: Path, probability: float, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.probability = probability
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # File path label - show relative path
        self.path_label = QLabel(str(file_path.relative_to(Path('E:/Albums'))))
        self.path_label.setFont(TEXT_FONT)
        self.path_label.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(self.path_label)
        
        # Add tooltip with full path
        self.setToolTip(str(file_path))
        
        # Probability label
        prob_text = f"{probability:.1f}%"
        self.prob_label = QLabel(prob_text)
        self.prob_label.setFont(TEXT_FONT)
        self.prob_label.setStyleSheet(f"color: {SECONDARY_TEXT};")
        self.prob_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.prob_label)
        
        self.setStyleSheet(f"""
            MatchOptionWidget {{
                background-color: {BACKGROUND_COLOR};
                border-radius: 2px;
                padding: 4px;
            }}
            MatchOptionWidget:hover {{
                background-color: {ITEM_HOVER};
            }}
        """)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.file_path)

class SongSelectionWidget(QWidget):
    """Widget for displaying current song with dropdown for alternatives."""
    
    selection_changed = pyqtSignal(Path)  # Emits selected file path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger('song_selection_widget')
        self.current_file: Optional[Path] = None
        self.current_song: Optional[SongMatchResult] = None
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)
        
        # Song info label
        self.song_label = QLabel("No song playing")
        self.song_label.setFont(TEXT_FONT)
        self.song_label.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(self.song_label)
        
        # File path button - shows current selection and opens dropdown
        self.file_button = QPushButton()
        self.file_button.setFont(TEXT_FONT)
        self.file_button.setStyleSheet(f"""
            QPushButton {{
                color: {SECONDARY_TEXT};
                background-color: transparent;
                border: none;
                text-align: right;
                padding: 4px 8px;
            }}
            QPushButton:hover {{
                color: {TEXT_COLOR};
                background-color: {ITEM_HOVER};
                border-radius: 2px;
            }}
        """)
        self.file_button.clicked.connect(self._show_matches_menu)
        self.file_button.setToolTip("Click to show all matches")
        layout.addWidget(self.file_button)
        
        # Initially hide file button
        self.file_button.hide()
                
    def cleanup(self):
        """Clean up resources."""
        try:
            self.file_button.clicked.disconnect()
            if hasattr(self, 'song_label'):
                self.song_label.deleteLater()
                self.song_label = None
            if hasattr(self, 'file_button'):
                self.file_button.deleteLater()
                self.file_button = None
            self.current_file = None
            self.current_song = None
        except Exception as e:
            logging.getLogger('song_selection_widget').error(f"Error during cleanup: {e}")

    def update_song(self, song_info: SongMatchResult):
        """Update displayed song and available matches."""
        if not hasattr(self, 'song_label') or not self.song_label:
            return
            
        self.current_song = song_info
        
        # Update song label
        self.song_label.setText(f"Current: {song_info.artist} - {song_info.title}")
        
        # Update color based on number of matches
        if len(song_info.matches) > 1:
            self.song_label.setStyleSheet(f"color: {WARNING_COLOR};")
        else:
            self.song_label.setStyleSheet(f"color: {TEXT_COLOR};")
        
        # Update file button with best match - WITHOUT EMITTING SIGNALS
        if song_info.matches:
            self.current_file = song_info.matches[0][0]  # Best match
            relative_path = self.current_file.relative_to(Path('E:/Albums'))
            self.file_button.setText(str(relative_path))
            self.file_button.setToolTip(str(self.current_file))
            self.file_button.show()
            
            # Initial selection should be emitted ONCE here
            self.selection_changed.emit(self.current_file)
            
            # Update button color for multiple matches
            if len(song_info.matches) > 1:
                self.file_button.setStyleSheet("""
                    QPushButton {
                        color: %s;
                        background-color: transparent;
                        border: none;
                        text-align: right;
                        padding: 4px 8px;
                    }
                    QPushButton:hover {
                        color: %s;
                        background-color: %s;
                        border-radius: 2px;
                    }
                """ % (WARNING_COLOR, WARNING_COLOR, ITEM_HOVER))
            else:
                self.file_button.setStyleSheet("""
                    QPushButton {
                        color: %s;
                        background-color: transparent;
                        border: none;
                        text-align: right;
                        padding: 4px 8px;
                    }
                    QPushButton:hover {
                        color: %s;
                        background-color: %s;
                        border-radius: 2px;
                    }
                """ % (SECONDARY_TEXT, TEXT_COLOR, ITEM_HOVER))
        else:
            self.current_file = None
            self.file_button.hide()
            
    def clear_song(self):
        """Clear current song display."""
        self.song_label.setText("No song playing")
        self.file_button.hide()
        self.current_file = None
        self.current_song = None
        
    def _show_matches_menu(self):
        """Show dropdown menu with all matches."""
        if not self.current_song or not self.current_song.matches:
            return
            
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {BACKGROUND_COLOR};
                border: 1px solid {ITEM_HOVER};
                border-radius: 2px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 4px 8px;
            }}
            QMenu::item:selected {{
                background-color: {ITEM_HOVER};
                border-radius: 2px;
            }}
        """)
        
        for file_path, probability in self.current_song.matches:
            # Create option widget with relative path display
            option = MatchOptionWidget(file_path, probability * 100)
            option.clicked.connect(self._on_match_selected)
            
            # Create action to hold widget
            action = QWidgetAction(menu)
            action.setDefaultWidget(option)
            menu.addAction(action)
            
        # Show menu below button
        menu.popup(self.file_button.mapToGlobal(
            self.file_button.rect().bottomLeft()
        ))
        
    def _on_match_selected(self, file_path: Path):
        """Handle match selection from dropdown."""
        if file_path != self.current_file:
            self.current_file = file_path
            # Display relative path but store full path
            rel_path = file_path.relative_to(Path('E:/Albums'))
            self.file_button.setText(str(rel_path))
            self.file_button.setToolTip(str(file_path))  # Full path in tooltip
            self.selection_changed.emit(file_path)