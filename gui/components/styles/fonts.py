# gui/components/styles/fonts.py

from PyQt6.QtGui import QFont

# Base font family
BASE_FONT_FAMILY = "Segoe UI"

# Font sizes
LARGE_SIZE = 14
MEDIUM_SIZE = 11
SMALL_SIZE = 10
TINY_SIZE = 9

# Common font configurations
TITLE_FONT = QFont(BASE_FONT_FAMILY, MEDIUM_SIZE)
TITLE_FONT.setBold(True)

HEADER_FONT = QFont(BASE_FONT_FAMILY, MEDIUM_SIZE)

BUTTON_FONT = QFont(BASE_FONT_FAMILY, SMALL_SIZE)

TEXT_FONT = QFont(BASE_FONT_FAMILY, SMALL_SIZE)

COUNT_FONT = QFont(BASE_FONT_FAMILY, SMALL_SIZE)

STATUS_FONT = QFont(BASE_FONT_FAMILY, SMALL_SIZE)

# Helper function for font variations
def get_font(size: int = SMALL_SIZE, bold: bool = False, italic: bool = False) -> QFont:
    """Create a font with specified properties."""
    font = QFont(BASE_FONT_FAMILY, size)
    if bold:
        font.setBold(True)
    if italic:
        font.setItalic(True)
    return font