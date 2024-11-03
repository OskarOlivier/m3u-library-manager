#!/usr/bin/env python3
"""Script to verify the codebase structure after migration."""

import os
import logging
from pathlib import Path
from typing import Dict, List, Set

class StructureVerifier:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('verifier')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(handler)
        return logger

    def verify_core_structure(self) -> List[str]:
        """Verify core module structure."""
        required_dirs = [
            'core/analysis',
            'core/matching',
            'core/playlist',
            'core/sync',
            'core/common'
        ]
        
        issues = []
        for dir_path in required_dirs:
            full_path = self.root_dir / dir_path
            if not full_path.exists():
                issues.append(f"Missing core directory: {dir_path}")
            if not (full_path / '__init__.py').exists():
                issues.append(f"Missing __init__.py in: {dir_path}")
        return issues

    def verify_gui_structure(self) -> List[str]:
        """Verify GUI module structure."""
        required_dirs = [
            'gui/widgets',
            'gui/windows',
            'gui/windows/pages',
            'gui/dialogs'
        ]
        
        required_files = [
            'gui/windows/pages/curation_page.py',
            'gui/windows/pages/explore_page.py',
            'gui/windows/pages/sync_page.py'
        ]
        
        issues = []
        # Check directories
        for dir_path in required_dirs:
            full_path = self.root_dir / dir_path
            if not full_path.exists():
                issues.append(f"Missing GUI directory: {dir_path}")
            if not (full_path / '__init__.py').exists():
                issues.append(f"Missing __init__.py in: {dir_path}")
        
        # Check files
        for file_path in required_files:
            if not (self.root_dir / file_path).exists():
                issues.append(f"Missing page file: {file_path}")
        
        return issues

    def verify_test_structure(self) -> List[str]:
        """Verify test directory structure."""
        required_dirs = [
            'tests/core/analysis',
            'tests/core/matching',
            'tests/core/playlist',
            'tests/gui',
            'tests/utils'
        ]
        
        required_files = [
            'tests/core/analysis/test_bpm_analyzer.py',
            'tests/core/playlist/test_playlist_manager.py',
            'tests/core/matching/test_song_matcher.py',
            'tests/utils/test_m3u_library.py'
        ]
        
        issues = []
        for dir_path in required_dirs:
            full_path = self.root_dir / dir_path
            if not full_path.exists():
                issues.append(f"Missing test directory: {dir_path}")
            if not (full_path / '__init__.py').exists():
                issues.append(f"Missing __init__.py in: {dir_path}")
                
        for file_path in required_files:
            if not (self.root_dir / file_path).exists():
                issues.append(f"Missing test file: {file_path}")
        
        return issues

    def verify_old_paths_removed(self) -> List[str]:
        """Verify old paths have been removed."""
        should_not_exist = [
            'gui/components',
            'gui/windows/pages/curation',
            'gui/windows/pages/explore',
            'gui/windows/pages/sync',
            'infrastructure'
        ]
        
        issues = []
        for path in should_not_exist:
            if (self.root_dir / path).exists():
                issues.append(f"Old path still exists: {path}")
        return issues

    def list_all_python_files(self):
        """List all Python files in the project."""
        self.logger.info("\nPython files in project:")
        for path in sorted(self.root_dir.rglob('*.py')):
            if '.git' not in str(path):
                self.logger.info(f"  {path.relative_to(self.root_dir)}")

    def verify_structure(self):
        """Run all structure verifications."""
        self.logger.info("Starting structure verification...")
        
        all_issues = []
        
        self.logger.info("\nVerifying core structure...")
        all_issues.extend(self.verify_core_structure())
        
        self.logger.info("\nVerifying GUI structure...")
        all_issues.extend(self.verify_gui_structure())
        
        self.logger.info("\nVerifying test structure...")
        all_issues.extend(self.verify_test_structure())
        
        self.logger.info("\nChecking for old paths...")
        all_issues.extend(self.verify_old_paths_removed())
        
        if all_issues:
            self.logger.warning("\nStructure issues found:")
            for issue in all_issues:
                self.logger.warning(f"- {issue}")
        else:
            self.logger.info("\nAll structure checks passed!")
            
        self.list_all_python_files()

def main():
    root_dir = Path(__file__).parent
    verifier = StructureVerifier(root_dir)
    verifier.verify_structure()

if __name__ == '__main__':
    main()