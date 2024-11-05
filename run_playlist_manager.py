# run_playlist_manager.py

from PyQt6.QtWidgets import QApplication
import sys
import os
import logging
from pathlib import Path
import traceback
from datetime import datetime

def force_logging():
    """Force immediate logging to both file and console."""
    # Ensure directory exists
    log_dir = Path.home() / ".m3u_library_manager" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"app_{timestamp}.log"
    
    # Force immediate writing
    handlers = [
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True
    )
    
    # Write test message
    logging.info(f"Logging initialized to {log_file}")
    logging.info(f"Python version: {sys.version}")
    logging.info(f"PyQt version: {QApplication.applicationVersion()}")
    
    return log_file

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

def main():
    # Initialize logging first
    log_file = force_logging()
    logging.info("Starting application")
    
    try:
        # Create QApplication first
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        
        # Install exception hooks
        install_exception_hooks()
        
        # Import window only after logging is set up
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
                    window.deleteLater()
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

if __name__ == "__main__":
    sys.exit(main())