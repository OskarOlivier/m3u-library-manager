# verify_structure.py

import os
from pathlib import Path

def verify_gui_structure():
    """Verify GUI directory structure exists."""
    root = Path('.')
    
    required_dirs = [
        'gui',
        'gui/windows',
        'gui/windows/pages',
        'gui/windows/pages/sync',
        'gui/windows/pages/sync/components',
    ]
    
    required_files = [
        'gui/__init__.py',
        'gui/windows/__init__.py',
        'gui/windows/main_window.py',
        'gui/windows/pages/__init__.py',
        'gui/windows/pages/sync/__init__.py',
        'gui/windows/pages/sync/components/__init__.py',
        'gui/windows/pages/sync/sync_page.py',
        'gui/windows/pages/sync/state.py',
        'gui/windows/pages/sync/handlers.py',
        'gui/windows/pages/sync/components/playlist_panel.py',
        'gui/windows/pages/sync/components/file_list_panel.py',
        'gui/windows/pages/sync/components/status_panel.py',
    ]
    
    # Check directories
    for dir_path in required_dirs:
        path = root / dir_path
        if not path.exists():
            print(f"Creating directory: {dir_path}")
            path.mkdir(parents=True, exist_ok=True)
            
    # Check files
    for file_path in required_files:
        path = root / file_path
        if not path.exists():
            print(f"Missing file: {file_path}")

if __name__ == '__main__':
    verify_gui_structure()