# gui/components/styles/layouts.py

# Margins (left, top, right, bottom)
WINDOW_MARGINS = (12, 12, 12, 12)
PANEL_MARGINS = (8, 8, 8, 8)
WIDGET_MARGINS = (6, 6, 6, 6)
NO_MARGINS = (0, 0, 0, 0)

# Spacing
WINDOW_SPACING = 12
PANEL_SPACING = 8
WIDGET_SPACING = 6
TIGHT_SPACING = 4

# Standard sizes
BUTTON_HEIGHT = 32
ICON_SIZE = 16
PROGRESS_BAR_HEIGHT = 4

# Panel dimensions
PANEL_MIN_WIDTH = 200
PANEL_MAX_WIDTH = 300
PANEL_MIN_HEIGHT = 300

# List item dimensions
ITEM_HEIGHT = 32
ITEM_PADDING = 8
COUNT_MIN_WIDTH = 50  # New constant for count label width

# Widget-specific layouts
PLAYLIST_ITEM_LAYOUT = {
    'height': ITEM_HEIGHT,
    'padding': ITEM_PADDING,
    'margins': WIDGET_MARGINS,
    'count_width': COUNT_MIN_WIDTH
}

# Helper functions
def get_margins(size: str = 'panel') -> tuple[int, int, int, int]:
    """Get standard margins based on size category."""
    return {
        'window': WINDOW_MARGINS,
        'panel': PANEL_MARGINS,
        'widget': WIDGET_MARGINS,
        'none': NO_MARGINS
    }.get(size, PANEL_MARGINS)

def get_spacing(size: str = 'panel') -> int:
    """Get standard spacing based on size category."""
    return {
        'window': WINDOW_SPACING,
        'panel': PANEL_SPACING,
        'widget': WIDGET_SPACING,
        'tight': TIGHT_SPACING
    }.get(size, PANEL_SPACING)