# run_playlist_manager.py

from PyQt6.QtWidgets import QApplication
import sys
from gui.windows.main_window import MainWindow
from gui.dialogs.credentials_dialog import PasswordDialog
import logging
from pathlib import Path

def setup_logging():
    """Configure application logging."""
    log_dir = Path.home() / ".m3u_library_manager" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # File handler
    log_file = log_dir / "app.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(console_handler)

def main():
    """Main application entry point."""
    # Set up logging
    setup_logging()
    logger = logging.getLogger('main')
    
    try:
        # Create application
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Run event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()