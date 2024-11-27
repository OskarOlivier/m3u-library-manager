# run_playlist_manager.py

import os
import sys
from pathlib import Path
import logging
import traceback
from datetime import datetime
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import asyncio

from utils.logging.config import setup_logging
from core.cache.relationship_cache import RelationshipCache
from core.events.event_bus import EventBus
from app.config import Config

if os.name == 'nt':  # Only on Windows
    import ctypes
    # Tell Windows not to scale the application
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

def qt_message_handler(mode, context, message):
    """Handle Qt debug messages"""
    if mode == Qt.QtMsgType.QtInfoMsg:
        logging.info(f"Qt: {message}")
    elif mode == Qt.QtMsgType.QtWarningMsg:
        logging.warning(f"Qt: {message}")
    elif mode == Qt.QtMsgType.QtCriticalMsg:
        logging.error(f"Qt: {message}")
    elif mode == Qt.QtMsgType.QtFatalMsg:
        logging.critical(f"Qt: {message}")
    else:
        logging.debug(f"Qt: {message}")

def install_exception_hooks():
    """Install global exception handlers"""
    def exception_hook(exctype, value, tb):
        """Handle uncaught exceptions"""
        error_msg = ''.join(traceback.format_exception(exctype, value, tb))
        logging.critical(f"Uncaught exception:\n{error_msg}")
        sys.__excepthook__(exctype, value, tb)
    
    sys.excepthook = exception_hook

async def initialize_core_systems():
    """Initialize core systems asynchronously."""
    try:
        # Get cache instance
        cache = RelationshipCache.get_instance()
        logging.info("Initializing relationship cache...")
        
        # Initialize cache with playlists directory
        await cache.initialize(Path(Config.PLAYLISTS_DIR))
        logging.info("Relationship cache initialized successfully")
        
    except Exception as e:
        logging.error(f"Failed to initialize core systems: {e}", exc_info=True)
        raise

def main():
    # Initialize logging first
    log_dir = Path.home() / ".m3u_library_manager" / "logs"
    log_file = setup_logging(log_dir, debug=True)
    logging.info("Starting application")
    
    try:
        # Create QApplication first
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        
        # Install exception hooks and Qt message handler
        install_exception_hooks()
        qInstallMessageHandler(qt_message_handler)
        
        # Initialize core systems
        logging.info("Initializing core systems...")
        asyncio.run(initialize_core_systems())
        
        # Import window only after logging and core systems are set up
        from gui.windows.main_window import MainWindow
        
        # Create window with try-except
        try:
            window = MainWindow()
            window.show()
            logging.info("Window created and shown")
        except Exception as e:
            logging.critical(f"Failed to create window: {e}", exc_info=True)
            raise
            
        # Set up clean exit
        def clean_exit():
            try:
                logging.info("Application exiting")
                if window:
                    logging.debug("Cleaning up window")
                    window.cleanup_application()
            except Exception as e:
                logging.error(f"Error during cleanup: {e}", exc_info=True)
                
        app.aboutToQuit.connect(clean_exit)
        
        # Run event loop with try-except
        try:
            logging.info("Entering event loop")
            return app.exec()
        except Exception as e:
            logging.critical(f"Event loop error: {e}", exc_info=True)
            raise
            
    except Exception as e:
        logging.critical(f"Application error: {e}", exc_info=True)
        raise
    finally:
        logging.info(f"Log file location: {log_file}")
        
def setup_logging(log_dir: Path, debug: bool = True):
    """Configure logging for all components"""
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Setup file handler
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(log_dir / f"app_{timestamp}.log", encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    loggers_to_configure = [
        'song_matcher',
        'string_utils',
        'window_handler',
        'playlist_manager',
        'relationship_cache'  # Added relationship cache logger
    ]
    
    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG if debug else logging.INFO)
        # Don't add handlers - they'll inherit from root logger

if __name__ == "__main__":
    sys.exit(main())