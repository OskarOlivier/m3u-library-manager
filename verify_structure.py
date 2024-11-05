# verify_structure.py

import os
from pathlib import Path

def verify_page_structure():
    """Verify the pages directory structure exists."""
    root = Path('.')
    
    required_dirs = [
        'gui/windows/pages',
        'gui/windows/pages/sync',
        'gui/windows/pages/sync/components',
        'gui/windows/pages/explore',
    ]
    
    required_files = [
        'gui/windows/pages/__init__.py',
        'gui/windows/pages/base.py',
        'gui/windows/pages/curation_page.py',
        'gui/windows/pages/sync/sync_page.py',
        'gui/windows/pages/explore/explore_page.py',
    ]
    
    # Create directories
    for dir_path in required_dirs:
        path = root / dir_path
        if not path.exists():
            print(f"Creating directory: {dir_path}")
            path.mkdir(parents=True, exist_ok=True)
    
    # Verify files
    missing_files = []
    for file_path in required_files:
        path = root / file_path
        if not path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("\nMissing required files:")
        for file in missing_files:
            print(f"- {file}")
    else:
        print("\nAll required files present!")

if __name__ == '__main__':
    verify_page_structure()