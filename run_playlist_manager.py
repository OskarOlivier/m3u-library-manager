from PyQt6.QtWidgets import QApplication
import sys
from system_tray import SystemTrayApp

def main():
    # Create application
    app = QApplication(sys.argv)
    
    # Set up global stylesheet if needed
    app.setStyle("Fusion")
    
    # Create system tray app (must keep a reference)
    tray_app = SystemTrayApp(app)
    
    # Store reference to prevent garbage collection
    app.tray_app = tray_app
    
    # Run event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()