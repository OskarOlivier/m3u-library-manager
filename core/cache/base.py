# core/cache/base.py
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
import logging

class CacheBase(QObject):
    """Base class for all caches with initialization and event handling."""
    
    initialized = pyqtSignal()
    updated = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._initialized = False
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @property
    def is_initialized(self) -> bool:
        return self._initialized
        
    def _set_initialized(self):
        self._initialized = True
        self.initialized.emit()
        
    def _report_error(self, error: str):
        self.logger.error(error)
        self.error_occurred.emit(error)