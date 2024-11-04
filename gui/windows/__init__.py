# gui/windows/__init__.py
"""Windows package initialization."""

from .main_window import MainWindow
from .pages.sync.sync_page import SyncPage

__all__ = ['MainWindow', 'SyncPage']