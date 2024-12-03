# gui/windows/pages/proximity/visualization/styling.py

from PyQt6.QtGui import QColor, QPen, QBrush, QFont
from typing import Dict

class GraphStyles:
   """Defines visual styling for graph elements."""
   
   COLORS = {
        'background': QColor(32, 32, 32, 255),
        'node_default': QColor(64, 64, 64, 255),
        'node_hover': QColor(80, 80, 80, 255),
        'node_selected': QColor(0, 120, 212, 255),
        'node_highlighted': QColor(80, 80, 80, 255),
        'edge_default': QColor(204, 204, 204, 155),
        'edge_highlighted': QColor(0, 120, 212, 255),
        'edge_hover': QColor(0, 120, 212, 255)
   }

   NODE_STYLES = {
       'default': {
           'brush': QBrush(QColor(COLORS['node_default'])),
           'pen': QPen(QColor('#1E1E1E'), 2),
           'size': 30
       },
       'hover': {
           'brush': QBrush(QColor(COLORS['node_hover'])),
           'pen': QPen(QColor('#0078D4'), 2),
           'size': 32
       },
       'selected': {
           'brush': QBrush(QColor(COLORS['node_selected'])),
           'pen': QPen(QColor('#0078D4'), 2),
           'size': 34
       },
       'highlighted': {
           'brush': QBrush(QColor(COLORS['node_highlighted'])),
           'pen': QPen(QColor('#0078D4'), 2),
           'size': 32
       }
   }

   _edge_default_color = QColor(COLORS['edge_default'])
   _edge_default_color.setAlphaF(0.3)
   
   EDGE_STYLES = {
       'default': QPen(_edge_default_color, 1),
       'highlighted': QPen(QColor(COLORS['edge_highlighted']), 2),
       'hover': QPen(QColor(COLORS['edge_hover']), 2),
       'faded': QPen(QColor(COLORS['edge_default']).darker(200), 1)
   }

   _base_font = QFont('Segoe UI', 11)
   _label_font = QFont('Segoe UI', 11)
   _label_font.setBold(True)

   LABEL_STYLES = {
       'base_font': _base_font,
       'label_font': _label_font,
       'color': '#FFFFFF',
       'faded_color': '#808080',
   }

   @classmethod
   def get_node_style(cls, state: str) -> Dict:
       return cls.NODE_STYLES.get(state, cls.NODE_STYLES['default'])

   @classmethod
   def get_edge_style(cls, highlighted: bool = False, hovered: bool = False, faded: bool = False) -> QPen:
       if highlighted:
           return cls.EDGE_STYLES['highlighted']
       elif hovered:
           return cls.EDGE_STYLES['hover']
       elif faded:
           return cls.EDGE_STYLES['faded']
       return cls.EDGE_STYLES['default']